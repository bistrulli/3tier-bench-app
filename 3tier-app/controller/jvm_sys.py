from system_int import system_interface
import time
import numpy as np
import subprocess
from cgroupspy import trees
from pymemcache.client.base import Client


class jvm_sys(system_interface):
    
    sysRootPath = None
    sys = None
    croot = None
    cgroups = None
    
    def __init__(self, sysRootPath):
        self.sysRootPath = sysRootPath
        self.initCgroups()
    
    def startClient(self):
        pass
    
    def stopClient(self):
        pass
    
    def startSys(self, isCpu):
        cpuEmu = 0 if(isCpu) else 1
        
        self.sys = {}
        self.sys["monitor-cnt"] = subprocess.Popen(["memcached"])
        if(self.waitMemCached()):
            print("connected to memcached")
        else:
            raise ValueError("Impossible to connected to memcached")
        
        # self.sys["tier2-cnt"]=subprocess.Popen(["sudo","cgexec", "-g", "cpu:t2", "--sticky", "java", "-Xmx4G",
        #                              "-Djava.compiler=NONE", "-jar",
        #                              '%s/tier2/target/tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar'%(self.sysRootPath),
        #                              '--cpuEmu', '%d'%(cpuEmu), '--jedisHost', 'localhost'])
        #
        # self.sys["tier1-cnt"]=subprocess.Popen(["sudo","cgexec", "-g", "cpu:t1", "--sticky", "java", "-Xmx4G",
        #                                  "-Djava.compiler=NONE", "-jar",
        #                                  '%s/tier1/target/tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar'%(self.sysRootPath),
        #                                  '--cpuEmu', "%d"%(cpuEmu), '--jedisHost', 'localhost',
        #                                  "--tier2Host","localhost"])
    
    def stopSystem(self):
        pass
    
    def getstate(self, monitor, keys):
        pass
    
    def waitTier(self, tier):
        pass
    
    def waitMemCached(self):
        connected = False
        base_client = Client(("localhost", 11211))
        for i in range(10):
            try:
                client.get('some_key')
                connected = True
                break
            except ConnectionRefusedError:
                print("connection error")
                time.sleep(0.2)
        return connected
    
    def initCgroups(self):        
        out=subprocess.check_output(["sudo","cgget", "-g", "cpu:t1"])
        out.decode("UTF-8")
        if(out.find("Cgroup does not exist")==-1):
            subprocess.check_output(["sudo","cgcreate","-g","cpu:t1"])
        
        out=subprocess.check_output(["sudo","cgget", "-g", "cpu:t2"])
        out.decode("UTF-8")
        if(out.find("Cgroup does not exist")==-1):
            subprocess.check_output(["sudo","cgcreate","-g","cpu:t2"])
        
            
       
            
if __name__ == "__main__":
    jvm_sys = jvm_sys("../")
    
