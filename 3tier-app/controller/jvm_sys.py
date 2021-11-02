from system_int import system_interface
import time
import numpy as np
import subprocess
from cgroupspy import trees
from pymemcache.client.base import Client
import os
import psutil
import requests as req

try:
    javaCmd = os.environ['JAVA_HOME'] + "/bin/java"
except:
    raise ValueError("Need to setup JAVA_HOME env variable")


class jvm_sys(system_interface):
    
    sysRootPath = None
    sys = None
    client = None
    croot = None
    cgroups = None
    period = 100000
    keys = ["think", "e1_bl", "e1_ex", "t1_hw", "e2_bl", "e2_ex", "t2_hw"]
    
    def __init__(self, sysRootPath):
        self.sysRootPath = sysRootPath
        self.initCgroups()
    
    def startClient(self, pop):
        r=Client("localhost:11211")
        r.set("stop","0")
        r.set("started","0")
        r.close()
        
        
        subprocess.Popen([javaCmd, "-Xmx4G",
                         "-Djava.compiler=NONE", "-jar",
                         '%sclient/target/client-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                         '--initPop', '%d' % (pop), '--jedisHost','localhost', '--tier1Host','localhost',
                         '--queues','[\"think\", \"e1_bl\", \"e1_ex\", \"t1_hw\", \"e2_bl\", \"e2_ex\", \"t2_hw\"]'])
        
        self.waitClient()
        
        self.client = self.findProcessIdByName("client-0.0.1")[0]
        
    
    def stopClient(self):
        if(self.client!=None):
            r=Client("localhost:11211")
            r.set("stop","1")
            r.close()
            
            self.client.wait()
            self.client=None
        
    
    def startSys(self, isCpu):
        cpuEmu = 0 if(isCpu) else 1
        
        self.sys = []
        subprocess.Popen(["memcached"])
        self.waitMemCached()
        self.sys.append(self.findProcessIdByName("memcached")[0])
        
        if(not isCpu):
            subprocess.Popen([javaCmd, "-Xmx4G",
                             "-Djava.compiler=NONE", "-jar",
                             '%stier2/target/tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', '%d' % (cpuEmu), '--jedisHost', 'localhost'])
            
            
            self.waitTier2()
            self.sys.append(self.findProcessIdByName("tier2-0.0.1")[0])
            
            
            subprocess.Popen([javaCmd, "-Xmx4G",
                             "-Djava.compiler=NONE", "-jar",
                             '%stier1/target/tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', "%d" % (cpuEmu), '--jedisHost', 'localhost',
                             "--tier2Host", "localhost"])
            
            self.waitTier1()
            self.sys.append(self.findProcessIdByName("tier1-0.0.1")[0])
        else:
            subprocess.Popen(["cgexec", "-g", "cpu:t2", "--sticky", javaCmd, "-Xmx4G",
                             "-Djava.compiler=NONE", "-jar",
                             '%stier2/target/tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', '%d' % (cpuEmu), '--jedisHost', 'localhost'])
            self.waitTier2()
            self.sys.append(self.findProcessIdByName("tier2-0.0.1")[0])
            
            
            subprocess.Popen(["cgexec", "-g", "cpu:t1", "--sticky", javaCmd, "-Xmx4G",
                             "-Djava.compiler=NONE", "-jar",
                             '%stier1/target/tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', "%d" % (cpuEmu), '--jedisHost', 'localhost',
                             "--tier2Host", "localhost"])
            self.waitTier1()
            self.sys.append(self.findProcessIdByName("tier1-0.0.1")[0])
    
    def findProcessIdByName(self,processName):
        '''
        Get a list of all the PIDs of a all the running process whose name contains
        the given string processName
        '''
        listOfProcessObjects = []
        # Iterate over the all the running process
        for proc in psutil.process_iter():
           try:
               pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
               # Check if process name contains the given name string.
               if processName.lower() in pinfo['name'].lower() or processName.lower() in " ".join(proc.cmdline()).lower():
                   listOfProcessObjects.append(proc)
           except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess):
               pass
        if(len(listOfProcessObjects)!=1):
            print(len(listOfProcessObjects))
            raise ValueError("process %s not found!"%processName)
        return listOfProcessObjects;
    
    def stopSystem(self):
        if(self.sys is not None):
            for i in range(len(self.sys),0,-1):
                proc=self.sys[i-1]
                print("killing %s"%(proc.name()+" "+"".join(proc.cmdline())))
                proc.terminate()
                proc.kill()
                proc.wait(timeout=2)
                
        self.sys=None
    
    def getstate(self, monitor):

        N = int((len(self.keys) - 1) / 2)
        str_state = [monitor.get(self.keys[i]) for i in range(len(self.keys))]
        try:
            astate = [float(str_state[0].decode('UTF-8'))]
            gidx = 1;
            for i in range(1, N):
                astate.append(float(str_state[gidx].decode('UTF-8')) + float(str_state[gidx + 1].decode('UTF-8')))
                if(float(str_state[gidx]) < 0 or float(str_state[gidx + 1]) < 0):
                    raise ValueError("Error! state < 0")
                gidx += 3
        except:
            print(time.asctime())
            for i in range(len(self.keys)):
                print(str_state[i], self.keys[i])
        
        return astate
    
    def waitTier1(self):
        connected=False
        limit=100
        atpt=0
        base_client = Client(("localhost", 11211))
        base_client.set("test_ex","1")
        while(atpt<limit and not connected):
            try:
                r = req.get('http://localhost:3000?entry=e1&snd=test')
                connected=True
                break
            except:
                time.sleep(0.2)
            finally:
                atpt+=1
        
        base_client.close()
        if(connected):
            print("connected to tier1")
        else:
            raise ValueError("error while connceting to tier1")
    
    def waitTier2(self):
        connected=False
        limit=100
        atpt=0
        base_client = Client(("localhost", 11211))
        base_client.set("test_ex","1")
        while(atpt<limit and not connected):
            try:
                r = req.get('http://localhost:3001?entry=e2&snd=test')
                connected=True
                break
            except Exception as e:
                time.sleep(0.2)
            finally:
                atpt+=1
        
        base_client.close()
        if(connected):
            print("connected to tier2")
        else:
            raise ValueError("error while connceting to tier2")
    
    def waitClient(self):
        connected=False
        limit=10
        atpt=0
        base_client = Client(("localhost", 11211))
        while(atpt<limit and (base_client.get("started")==None or base_client.get("started").decode('UTF-8')=="0")):
           time.sleep(0.2)
           atpt+=1
            
        
    def waitMemCached(self):
        connected = False
        base_client = Client(("localhost", 11211))
        for i in range(10):
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
        self.cgroups={"tier1":"t1","tier2":"t2"}
        p= subprocess.Popen(["cgget", "-g", "cpu:t1"],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if(str(err).find("Cgroup does not exist") != -1):
            subprocess.check_output(["sudo", "cgcreate", "-g", "cpu:t1","-a","emilio:emilio","-t","emilio:emilio"])
        
        p= subprocess.Popen(["cgget", "-g", "cpu:t2"],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if(str(err).find("Cgroup does not exist") != -1):
            subprocess.check_output(["sudo", "cgcreate", "-g", "cpu:t2","-a","emilio:emilio","-t","emilio:emilio"])
    
    def setU(self,RL,cnt_name):
        found=False
        for cnt in self.sys:
            if(cnt_name.lower() in cnt.name()+" ".join(cnt.cmdline()).lower()):
                print("update control for group, %s",self.cgroups[cnt_name])
                quota=np.round(RL * self.period)
                found=True
                subprocess.Popen(["cgset","-r","cpu.cfs_quota_us=%d"%(max(int(quota),1000)),self.cgroups[cnt_name]])
                break
        
        if(not found):
            raise ValueError("container %s not found during cpulimit update"%(cnt_name))
       
            
if __name__ == "__main__":
    try:
        jvm_sys = jvm_sys("../")
        
        for i in range(1):
            jvm_sys.startSys(True)
            jvm_sys.startClient(100)
                
            mnt = Client("localhost:11211")
            for i in range(100):
                state=jvm_sys.getstate(mnt)
                print(state,np.sum(state))
                jvm_sys.setU(2,"tier1")
                jvm_sys.setU(3,"tier2")
                time.sleep(0.2)
            mnt.close()
            
            jvm_sys.stopClient()
            jvm_sys.stopSystem()
        
    except Exception as e:
        pass
        print(e)
        jvm_sys.stopClient()
        jvm_sys.stopSystem()
        