class system_interface:
    
    keys=None
    N=None
    
    def startClient(self):
        pass
    
    def stopClient(self):
        pass
    
    def startSys(self):
        pass
    
    def stopSystem(self):
        pass
    
    def getstate(self,monitor):
        N=int((len(self.keys)-1)/2)
        str_state=[monitor.get(self.keys[i]) for i in range(len(self.keys))]
        try:
            astate = [float(str_state[0].decode('UTF-8'))]
            gidx = 1;
            for i in range(1, N):
                astate.append(float(str_state[gidx].decode('UTF-8')) + float(str_state[gidx + 1].decode('UTF-8')))
                if(float(str_state[gidx])<0 or float(str_state[gidx + 1])<0):
                    raise ValueError("Error! state < 0")
                gidx += 3
        except:
            print(time.asctime())
            for i in range(len(self.keys)):
                print(str_state[i],self.keys[i])
        
        return astate
    
    def setU(self,RL,cnt_name):
        pass
    



