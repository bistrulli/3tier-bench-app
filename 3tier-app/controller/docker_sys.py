from system_int import system_interface
import docker
import time
from pymemcache.client.base import Client
import numpy as np
import traceback
import socket
import requests as req

class dockersys(system_interface):
    
    sys = None
    client_cnt = None
    dck_client = None
    cnt_names = ["tier1-cnt","tier2-cnt","monitor-cnt"]
    keys = ["think", "e1_bl", "e1_ex", "t1_hw", "e2_bl", "e2_ex", "t2_hw"]
    period = 100000
    isCpu=None
    tier_socket=None
    
    def __init__(self,isCpu=False):
        self.dck_client = docker.from_env()
        self.sys=[]
        self.isCpu=isCpu
        self.tier_socket={}
    
    def startClient(self,initPop):
        r=Client("localhost:11211")
        r.set("stop","0")
        
        self.client_cnt=self.dck_client.containers.run(image="bistrulli/client:gke_0.5",
                              command="java -Xmx4G -jar client-0.0.1-SNAPSHOT-jar-with-dependencies.jar --initPop %d --queues \
                                      '[\"think\", \"e1_bl\", \"e1_ex\", \"t1_hw\", \"e2_bl\", \"e2_ex\", \"t2_hw\"]' \
                                       --jedisHost monitor.app --tier1Host tier1.app"%(initPop),
                              auto_remove=False,
                              detach=True,
                              name="client-cnt",
                              ports={'3333/tcp': 3333},
                              hostname="client.app",
                              network="3tier-app_default",
                              stop_signal="SIGINT")
        
        self.waitRunning(self.client_cnt)
        while(r.get("think")==None):
            time.sleep(0.2)
        
    def getNetworkCne(self):
        net=None
        try:
            net=self.dck_client.networks.get("3tier-app_default")
        except docker.errors.NotFound:
            net=self.dck_client.networks.create("3tier-app_default", driver="bridge")
        return net
    
    def stopClient(self):
        if(self.client_cnt is not None):
            print("stopping client gracefully")
            r=Client("localhost:11211")
            r.set("stop","1")
            r.close()
            self.client_cnt.reload()
            # while(self.client_cnt.status!="exited"):
            #     time.sleep(0.2)
            #     self.client_cnt.reload()
            self.client_cnt.reload()
            self.client_cnt.kill()
            self.client_cnt.remove()
            self.dck_client.containers.prune()
            self.client_cnt=None
            print("client stopping complete")
    
    def startSys(self):
        cpuEmu=0 if(self.isCpu) else 1
        
        self.getNetworkCne()
        
        self.sys.append(self.dck_client.containers.run(image="memcached:1.6.12",
                              auto_remove=True,
                              detach=True,
                              name="monitor-cnt",
                              ports={'11211/tcp': 11211},
                              hostname="monitor.app",
                              network="3tier-app_default",
                              stop_signal="SIGINT",
                              command="memcached -c 2048 -t 20"))
        
        self.waitRunning(self.sys[-1])
        
        self.sys.append(self.dck_client.containers.run(image="bistrulli/tier2:gke_0.5",
                              command=["java","-Xmx4G","-jar","tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar",
                                       "--cpuEmu","%d"%cpuEmu,"--jedisHost","monitor.app","--cgv2","0"],
                              auto_remove=True,
                              detach=True,
                              name="tier2-cnt",
                              ports={'13001/tcp': 13001},
                              hostname="tier2.app",
                              network="3tier-app_default",
                              stop_signal="SIGINT"))
        
        self.waitRunning(self.sys[-1])
        
        self.sys.append(self.dck_client.containers.run(image="bistrulli/tier1:gke_0.5",
                              command=["java","-Xmx4G","-jar","tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar",
                                       "--cpuEmu","%d"%cpuEmu,"--jedisHost","monitor.app","--tier2Host","tier2.app","--cgv2","0"],
                              auto_remove=True,
                              detach=True,
                              name="tier1-cnt",
                              ports={'3000/tcp': 3000,'13000/tcp': 13000},
                              hostname="tier1.app",
                              network="3tier-app_default",
                              stop_signal="SIGINT"))
        
        self.waitRunning(self.sys[-1])
    
    def stopSystem(self):
        for cnt_n in self.cnt_names:
            try:
                cnt=self.dck_client.containers.get(cnt_n)
                print("killing %s "%(cnt.name))
                cnt.reload()
                cnt.kill()
                #cnt.remove()
            except docker.errors.NotFound:
                pass
        self.sys=[]
    
    def waitRunning(self,cnt):
        while(cnt.status!="running"):
            time.sleep(0.2)
            cnt.reload()
        print("Cnt %s is running"%(cnt.name))
        
    def setU(self,RL,cnt_name):
        if(self.isCpu):
            found=False
            for cnt in self.sys:
                if(cnt.name==cnt_name):
                    quota=np.round(RL * self.period)
                    found=True
                    cnt.update(cpu_period=self.period,cpu_quota=max(int(quota),1000))
                    break
        
        if(not found):
            raise ValueError("container %s not found during cpulimit update"%(cnt_name))
    
    
        
    def getstate(self, monitor=None):
        return int(monitor.get("think"))
        # state = self.getStateTcp()
        # return [[state["think"], state["e1_bl"] + state["e1_ex"], state["e2_bl"] + state["e2_ex"]],
        #         [state["think"], state["e1_bl"], state["e1_ex"], state["e2_bl"], state["e2_ex"]]]
    
    def getStateTcp(self):
        tiers = [3333, 13000, 13001]
        sys_state = {}
        
        for tier in tiers: 
            msgFromServer = self.getTierTcpState(tier)
                
            states = msgFromServer.split("$")
            for state in states:
                if(state != None and state != ''):
                    key, val = state.split(":")
                    sys_state[key] = int(val)
        
        return sys_state
    
    def getTierTcpState(self, tier):
        if("%d" % (tier) not in self.tier_socket):
            # Create a TCP socket at client side
            self.tier_socket["%d" % (tier)] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tier_socket["%d" % (tier)].setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.tier_socket["%d" % (tier)].connect(('localhost', tier))
            msg = self.tier_socket["%d" % (tier)].recv(1024)
            if(msg.decode("UTF-8").rstrip("\n") != "connected"):
                raise ValueError("Error while connecting to tier %d msg=%s" % (tier,msg.decode("UTF-8").rstrip("\n")))
        
        self.tier_socket["%d" % (tier)].sendall("getState\n".encode("UTF-8"))
        return self.tier_socket["%d" % (tier)].recv(1024).decode("UTF-8").rstrip("\n")


if __name__ == "__main__":
    
    try:
        dck_sys=dockersys(isCpu=True)
        dck_sys.startSys()
        dck_sys.startClient(1)
        
        mnt=Client("localhost:11211")
        
        while(mnt.get("sim")==None):
                print("waiting sim to start")
                time.sleep(0.1)
                
        pop=float(mnt.get("sim").decode('UTF-8').split("_")[1]);
        
        for i in range(200):
             print([dck_sys.getstate(mnt),pop])
             time.sleep(0.2)
        mnt.close()
    except Exception as ex:
        traceback.print_exception(type(ex), ex, ex.__traceback__)
    finally:
        dck_sys.stopClient()
        dck_sys.stopSystem()
    
    
    