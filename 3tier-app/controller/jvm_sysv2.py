from system_int import system_interface
import time
import numpy as np
import subprocess
from cgroupspy import trees
from pymemcache.client.base import Client
import os
import psutil
import requests as req
import traceback
import matplotlib.pyplot as plt
import socket

try:
    javaCmd = os.environ['JAVA_HOME'] + "/bin/java"
except:
    raise ValueError("Need to setup JAVA_HOME env variable")


class jvm_sys(system_interface):
    
    sysRootPath = None
    sys = None
    client = None
    cgroups = None
    period = 100000
    keys = ["think", "e1_bl", "e1_ex", "t1_hw", "e2_bl", "e2_ex", "t2_hw"]
    isCpu = None
    tier_socket = None
    
    def __init__(self, sysRootPath, isCpu=False):
        self.sysRootPath = sysRootPath
        self.isCpu = isCpu
        self.tier_socket = {}
    
    def startClient(self, pop,sim=False):
        r = Client("localhost:11211")
        r.set("stop", "0")
        r.set("started", "0")
        r.close()
        
        subprocess.Popen([javaCmd, "-Xmx6G",
                         "-Djava.compiler=NONE", "-jar",
                         '%sclient/target/client-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                         '--initPop', '%d' % (pop), '--jedisHost', 'localhost', '--tier1Host', 'localhost',
                         '--queues', '[\"think\", \"e1_bl\", \"e1_ex\", \"t1_hw\", \"e2_bl\", \"e2_ex\", \"t2_hw\"]',
                         '--sim',"%d"%(int(sim))])
        
        self.waitClient()
        
        self.client = self.findProcessIdByName("client-0.0.1")[0]
    
    def resetSys(self):
        self.tier_socket = {}
        self.sys = None
        self.client = None
        self.cgroups = None
    
    def stopClient(self):
        if(self.client != None):
            r = Client("localhost:11211")
            r.set("stop", "1")
            r.set("started", "0")
            r.close()
            
            try:
                self.client.wait(timeout=2)
            except psutil.TimeoutExpired as e:
                print("terminate client forcibly")
                self.client.terminate()
                self.client.kill()
            finally:
                self.client = None
    
    def startSys(self):
        
        if(self.isCpu):
            self.initCgroups()
        
        cpuEmu = 0 if(self.isCpu) else 1
        
        self.sys = []
        subprocess.Popen(["memcached", "-c", "2048", "-t", "20","-u","root"])
        self.waitMemCached()
        self.sys.append(self.findProcessIdByName("memcached")[0])
        
        if(not self.isCpu):
            subprocess.Popen([javaCmd,
                            "-Xmx6G", "-Xms6G",
                             "-XX:+AlwaysPreTouch",
                             "-Djava.compiler=NONE", "-jar",
                             '%stier2/target/tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', '%d' % (cpuEmu), '--jedisHost', 'localhost'])
            
            self.waitTier2()
            self.sys.append(self.findProcessIdByName("tier2-0.0.1")[0])
            
            subprocess.Popen([javaCmd,
                            "-Xmx6G", "-Xms6G",
                             "-Djava.compiler=NONE", "-jar",
                             '%stier1/target/tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', "%d" % (cpuEmu), '--jedisHost', 'localhost',
                             "--tier2Host", "localhost"])
            
            self.waitTier1()
            self.sys.append(self.findProcessIdByName("tier1-0.0.1")[0])
        else:
            subprocess.Popen([ javaCmd, 
                             "-Xmx6G", "-Xms6G",
                             "-Djava.compiler=NONE", "-jar", "-Xint",
                             '%stier2/target/tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', '%d' % (cpuEmu), '--jedisHost', 'localhost',
                             '--cgv2','1'])
            self.waitTier2()
            self.sys.append(self.findProcessIdByName("tier2-0.0.1")[0])
            
            subprocess.Popen([javaCmd,
                            "-Xmx6G", "-Xms6G",
                            "-XX:+AlwaysPreTouch",
                             "-Djava.compiler=NONE", "-jar", "-Xint",
                             '%stier1/target/tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', "%d" % (cpuEmu), '--jedisHost', 'localhost',
                             "--tier2Host", "localhost",'--cgv2','1'])
            self.waitTier1()
            self.sys.append(self.findProcessIdByName("tier1-0.0.1")[0])
    
    def findProcessIdByName(self, processName):
        
        '''
        Get a list of all the PIDs of a all the running process whose name contains
        the given string processName
        '''
        listOfProcessObjects = []
        # Iterate over the all the running process
        for proc in psutil.process_iter():
           if(proc.status() == "zombie"):
               continue
           try:
               pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
               # Check if process name contains the given name string.
               if processName.lower() in pinfo['name'].lower() or processName.lower() in " ".join(proc.cmdline()).lower():
                   listOfProcessObjects.append(proc)
           except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess):
               pass
        if(len(listOfProcessObjects) != 1):
            print(len(listOfProcessObjects))
            raise ValueError("process %s not found!" % processName)
        return listOfProcessObjects;
    
    def stopSystem(self):
        if(self.sys is not None):
            for i in range(len(self.sys), 0, -1):
                proc = self.sys[i - 1]
                print("killing %s" % (proc.name() + " " + "".join(proc.cmdline())))
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except psutil.TimeoutExpired as e:
                    proc.kill()
                
        self.resetSys()
    
    def waitTier1(self):
        connected = False
        limit = 1000
        atpt = 0
        base_client = Client(("localhost", 11211))
        base_client.set("test_ex", "1")
        while(atpt < limit and not connected):
            try:
                r = req.get('http://localhost:3000?entry=e1&snd=test')
                connected = True
                break
            except:
                time.sleep(0.2)
            finally:
                atpt += 1
        
        base_client.close()
        if(connected):
            print("connected to tier1")
        else:
            raise ValueError("error while connceting to tier1")
    
    def waitTier2(self):
        connected = False
        limit = 1000
        atpt = 0
        base_client = Client(("localhost", 11211))
        base_client.set("test_ex", "1")
        while(atpt < limit and not connected):
            try:
                r = req.get('http://localhost:3001?entry=e2&snd=test')
                connected = True
                break
            except Exception as e:
                time.sleep(0.2)
            finally:
                atpt += 1
        
        base_client.close()
        if(connected):
            print("connected to tier2")
        else:
            raise ValueError("error while connceting to tier2")
    
    def waitClient(self):
        connected = False
        limit = 10000
        atpt = 0
        base_client = Client(("localhost", 11211))
        while(atpt < limit and (base_client.get("started") == None or base_client.get("started").decode('UTF-8') == "0")):
           time.sleep(0.2)
           atpt += 1
        
    def waitMemCached(self):
        connected = False
        base_client = Client(("localhost", 11211))
        for i in range(1000):
            try:
                base_client.get('some_key')
                connected = True
                base_client.close()
                break
            except ConnectionRefusedError:
                time.sleep(0.2)
        base_client.close()
        
        if(connected):
            print("connected to memcached")
        else:
            raise ValueError("Impossible to connected to memcached")
        
        time.sleep(0.5)
    
    def initCgroups(self):
        self.cgroups = {"tier1":{"name":"t1", "cg":None}, "tier2":{"name":"t2", "cg":None}} 
        if(os.path.exists("/sys/fs/cgroup/t1")):
            if(not os.path.exists("/sys/fs/cgroup/t1/e1")):
                raise ValueError("e1 cgroupv2 doesn't exist")
            else:
                self.cgroups["tier1"]["cg"]="/sys/fs/cgroup/t1/e1/cpu.max"
        else:
            raise ValueError("t1 cgroupv2 doesn't exist")
        
        if(os.path.exists("/sys/fs/cgroup/t2")):
            if(not os.path.exists("/sys/fs/cgroup/t2/e2")):
                raise ValueError("e2 cgroupv2 doesn't exist")
            else:
                self.cgroups["tier2"]["cg"]="/sys/fs/cgroup/t2/e2/cpu.max"
        else:
            raise ValueError("t2 cgroupv2 doesn't exist")
    
    def setU(self, RL, cnt_name):
        quota = int(np.round(RL * self.period))
        
        cgfile=open(self.cgroups[cnt_name]["cg"],"w")
        cgfile.write("%d %d"%(quota,self.period))
        cgfile.flush()
        cgfile.close()
    
    # def getstate(self, monitor):
    #     N = 2
    #     str_state = [monitor.get(self.keys[i]) for i in range(len(self.keys))]
    #     try:
    #         estate = [float(str_state[i]) for i in range(len(str_state))]
    #         astate = [float(str_state[0].decode('UTF-8'))]
    #
    #         gidx = 1;
    #         for i in range(0, N):
    #             astate.append(float(str_state[gidx].decode('UTF-8')) + float(str_state[gidx + 1].decode('UTF-8')))
    #             if(float(str_state[gidx]) < 0 or float(str_state[gidx + 1]) < 0):
    #                 raise ValueError("Error! state < 0")
    #             gidx += 3
    #     except:
    #         for i in range(len(self.keys)):
    #             print(str_state[i], self.keys[i])
    #
    #     return [astate, estate]
    
    def getstate(self, monitor=None):
        state = self.getStateTcp()
        return [[state["think"], state["e1_bl"] + state["e1_ex"], state["e2_bl"] + state["e2_ex"]],
                [state["think"], state["e1_bl"], state["e1_ex"], state["e2_bl"], state["e2_ex"]]]
        
    # def getStateNetStat(self):
    #     cmd = "netstat -anp | grep :80 | grep ESTABLISHED | wc -l"
    #     ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #     start = time.time()
    #     output = ps.communicate()[0]
    #     print(output, time.time() - start)
    
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
                raise ValueError("Error while connecting to tier msg=%s" % (msg.decode("UTF-8").rstrip("\n")))
        
        self.tier_socket["%d" % (tier)].sendall("getState\n".encode("UTF-8"))
        return self.tier_socket["%d" % (tier)].recv(1024).decode("UTF-8").rstrip("\n")
    
    def testTcpState(self, tier):
        msg = self.getTierTcpState(tier)
        print(msg)
    
    def testSystem(self):
        self.startSys()
        r = Client("localhost:11211")
        try:
            for k in self.keys:
                if(k == "think" or k == "t1_hw" or k == "t2_hw"):
                    continue
                if(r.get(k) is None):
                    raise ValueError("test not passed, key %s should be 0 instead is None" % (k))
                if(r.get(k).decode('UTF-8') != "0"):
                    raise ValueError("test not passed, key %s should be 0 instead is %s" % (k, r.get(k).decode('UTF-8')))
            
            http_req = req.get('http://localhost:3001?entry=e2&snd=test&id=%d' % (np.random.randint(low=0, high=10000000)))
            
            for k in self.keys:
                if(k == "think" or k == "t1_hw" or k == "t2_hw"):
                    continue
                if(r.get(k) is None):
                    raise ValueError("test not passed, key %s should be 0 instead is None" % (k))
                if(r.get(k).decode('UTF-8') != "0"):
                    raise ValueError("test not passed, key %s should be 0 instead is %s" % (k, r.get(k).decode('UTF-8')))
                
            http_req = req.get('http://localhost:3000?entry=e1&snd=test&id=%d' % (np.random.randint(low=0, high=10000000)))
            
            for k in self.keys:
                if(k == "think" or k == "t1_hw" or k == "t2_hw"):
                    continue
                if(r.get(k) is None):
                    raise ValueError("test not passed, key %s should be 0 instead is None" % (k))
                if(r.get(k).decode('UTF-8') != "0"):
                    raise ValueError("test not passed, key %s should be 0 instead is %s" % (k, r.get(k).decode('UTF-8')))
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
            for k in self.keys:
                if(k == "think" or k == "t1_hw" or k == "t2_hw"):
                    continue
                print(k, r.get(k))
        finally:
            self.stopSystem()
            r.close()
    
    def closeStateMonitor(self):
        for idx,key in enumerate(self.tier_socket):
            self.tier_socket[key].sendall("q\n".encode("UTF-8"))
        self.tier_socket={}
       
            
if __name__ == "__main__":
    try:
        isCpu = True
        g = None
        jvm_sys = jvm_sys("../", isCpu)
        
        for i in range(1):
            jvm_sys.startSys()
            jvm_sys.startClient(40,sim=True)
            
            g = Client("localhost:11211")
            
            while(g.get("sim")==None):
                print("waiting sim to start")
                time.sleep(0.2)
            
            g.set("t1_hw", "%f" % (100))
            g.set("t2_hw", "%f" % (100))
            # jvm_sys.setU(1.0, "tier1")
            # jvm_sys.setU(1.0, "tier2")
            
            X = []
            for i in range(360):
                state = jvm_sys.getstate()[0]
                print(state, i, np.sum(state))
                X.append(state[0])
            
                # if(np.mod(i + 1, 6) == 0 and i >= 6):
                #     s1 = np.maximum(np.random.rand() * 10,.1)
                #     s2 = np.maximum(np.random.rand() * 10,.1)
                #     print(s1, s2)
                #     g.set("t1_hw", "%f" % (s1))
                #     g.set("t2_hw", "%f" % (s2))
                #
                #     if(isCpu):
                #         jvm_sys.setU(s1, "tier1")
                #         jvm_sys.setU(s2, "tier2")
                time.sleep(0.3)
            
            print(np.mean(X))
        
            jvm_sys.stopClient()
            jvm_sys.stopSystem()
        
            plt.figure()
            plt.plot(X)
            plt.axhline(y=10, color='r', linestyle='--')
            plt.savefig("queue_test.png")
    except Exception as ex:
        traceback.print_exception(type(ex), ex, ex.__traceback__)
    finally:
        jvm_sys.stopClient()
        jvm_sys.stopSystem()
        jvm_sys.closeStateMonitor()
        if(g is not None):
            g.close()
        
