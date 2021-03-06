from system_int import system_interface
import docker
import time
from pymemcache.client.base import Client
import numpy as np

class dockersys(system_interface):
    
    sys = None
    client_cnt = None
    dck_client = None
    cnt_names = ["tier1-cnt","tier2-cnt","monitor-cnt"]
    keys = ["think", "e1_bl", "e1_ex", "t1_hw", "e2_bl", "e2_ex", "t2_hw"]
    period = 100000
    isCpu=None
    
    def __init__(self,isCpu=False):
        self.dck_client = docker.from_env()
        self.sys=[]
        self.isCpu=isCpu
    
    def startClient(self,initPop):
        r=Client("localhost:11211")
        r.set("stop","0")
        
        self.client_cnt=self.dck_client.containers.run(image="bistrulli/client:gke_0.1",
                              command="java -Xmx4G -jar client-0.0.1-SNAPSHOT-jar-with-dependencies.jar --initPop %d --queues \
                                      '[\"think\", \"e1_bl\", \"e1_ex\", \"t1_hw\", \"e2_bl\", \"e2_ex\", \"t2_hw\"]' \
                                       --jedisHost monitor.app --tier1Host tier1.app"%(initPop),
                              auto_remove=False,
                              detach=True,
                              name="client-cnt",
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
        
        self.sys.append(self.dck_client.containers.run(image="bistrulli/tier2:gke_0.1",
                              command=["java","-Xmx4G","-jar","tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar",
                                       "--cpuEmu","%d"%cpuEmu,"--jedisHost","monitor.app"],
                              auto_remove=True,
                              detach=True,
                              name="tier2-cnt",
                              hostname="tier2.app",
                              network="3tier-app_default",
                              stop_signal="SIGINT"))
        
        self.waitRunning(self.sys[-1])
        
        self.sys.append(self.dck_client.containers.run(image="bistrulli/tier1:gke_0.1",
                              command=["java","-Xmx4G","-jar","tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar",
                                       "--cpuEmu","%d"%cpuEmu,"--jedisHost","monitor.app","--tier2Host","tier2.app"],
                              auto_remove=True,
                              detach=True,
                              name="tier1-cnt",
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


if __name__ == "__main__":
    
    try:
        dck_sys=dockersys(isCpu=False)
        dck_sys.startSys()
        dck_sys.startClient(30)
        
        mnt=Client("localhost:11211")
        for i in range(100):
            print(dck_sys.getstate(mnt))
            time.sleep(0.2)
        mnt.close()
        
        #dck_sys.setU(2, "tier1-k")
        
        dck_sys.stopClient()
        dck_sys.stopSystem()
    except Exception as e:
        print(e)
        dck_sys.stopClient()
        dck_sys.stopSystem()
    
    
    