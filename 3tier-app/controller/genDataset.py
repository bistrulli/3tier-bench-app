import numpy as np
import scipy.io as sp
import os
import time
import matplotlib.pyplot as plt
from tqdm import tqdm
import signal
import sys
from pathlib import Path
from sys import platform
import docker
from pymemcache.client.base import Client
from docker_sys import dockersys
import pathlib
import uuid

script_dir=pathlib.Path(__file__).parent.resolve()

def handler(signum, frame):
    print('Signal handler called with signal', signum)
    stopSystem()
    sys.exit(1)

def stopSystem():
    global dck_sys
    dck_sys.stopClient()
    dck_sys.stopSystem()

def getTr():
    prob=np.exp(np.linspace(5,1,10))/np.sum(np.exp(np.linspace(5,1,10)))
    r=np.random.choice([.1,.2,.3,.4,.5,.6,.7,.8,.9,1],p=prob)
    return np.random.rand()*0.1+(r-0.1)

def getServer(X,S,rand):
    #print("queue=",X,"server",S)
    optS=None
    if(rand):
        optS=np.round(np.matrix([np.sum(X),getTr()*14.8+0.2,getTr()*14.8+0.2]),4)
    else:
        #devo definire il numero di server da assegnare
        optS=S
        
        #findBootleneck
        eps=np.ones(S.shape)*10**(-5)
        U=np.divide(np.minimum(X,S),S)
        #print("utiliation=",U)
        b=np.argmax(np.mean(U,axis=0))
        
        #print("bottelneck",b)
         
        optS[0,b]=np.maximum(np.minimum(optS[0,b]*15*np.random.rand(),100),0.1)
        if(b==1):
             optS[0,2]=max(np.random.rand()*optS[0,2]/10.0,0.1)
        else:
             optS[0,1]=max(np.random.rand()*optS[0,1]/10.0,0.1)
    
    #print("New=",optS)
    
    return optS;
        

signal.signal(signal.SIGINT, handler)

repcount=0;

#per npoints intendo il numero di diverso di stati iniziali che considero
rep=100
H=5
ssTime=(H+1)*30
N=3
npoints=ssTime*(rep)
DS_X=np.zeros([npoints//(H+1),N])
DS_U=np.zeros([npoints//(H+1),N*(N+1)])
DS_Y=np.zeros([npoints//(H+1),N*H])
XS=np.zeros([npoints,N]);
X0=None

r = None

point=0;
optS=None
P=None
X0=None
myuuid = uuid.uuid4()

fname="open_loop_3tier_H5"

dck_sys=dockersys()

try:
    for tick in tqdm(range(npoints),ascii=True):
        if((np.mod(tick,ssTime)==0) or tick==0):
            
            #salvo risultati intermedi
            if(tick!=0):
                Path(str(script_dir)+"/../data/%s/"%(str(myuuid)) ).mkdir( parents=True, exist_ok=True )
                sp.savemat(str(script_dir)+"/../data/%s/%s.mat"%(myuuid,fname),{"DS_X":DS_X,"DS_Y":DS_Y,"DS_U":DS_U})
            
            XS[tick,:]=[np.random.randint(low=1,high=100)]+[0]*(N-1)
            X0=XS[[tick],:]
           
            #optS=np.round(np.matrix([np.sum(X0),getTr()*14.8+0.2,getTr()*14.8+0.2]),4)
            optS=getServer(X0,None,True)
            
            dck_sys.stopClient()
            dck_sys.stopSystem()
            
            dck_sys.startSys(True)
            dck_sys.startClient(np.sum(XS[tick,:]))
            
            time.sleep(2)
            
            if(r is not None):
                r.close()
            r = Client("localhost:11211")
            
            r.set("t1_hw","%.4f"%(optS[0,1]))
            r.set("t2_hw","%.4f"%(optS[0,2]))
            dck_sys.setU(optS[0,1], "tier1-cnt")
            dck_sys.setU(optS[0,2], "tier2-cnt")
            
            
            
            #get fake P
            P=np.random.rand(N,N);
            P=P/np.sum(P,1,keepdims=True);
            
            XS[tick,:]=dck_sys.getstate(r)
            #X0=XS[[tick],:]
            
        else:
            XS[tick,:]=dck_sys.getstate(r)
            
            if(np.mod(tick+1,H+1)==0 and tick>=H):
                DS_X[point,:]=XS[tick+1-(H+1)]
                DS_U[point,0:optS.shape[1]]=optS
                DS_U[point,optS.shape[1]:]=P.flatten()
                DS_Y[point,:]=np.reshape(XS[tick-(H-1):tick+1],[1,N*H])
                point+=1
                
                #get fake P
                P=np.random.rand(N,N);
                P=P/np.sum(P,1,keepdims=True);
                
                #gen rnd S
                #optS=np.round(np.matrix([np.sum(X0),getTr()*14.8+0.2,getTr()*14.8+0.2]),4)
                optS=getServer(np.mean(XS[tick-(H-1):tick+1],axis=0,keepdims=True),optS,False)
                
                r.set("t1_hw","%.4f"%(optS[0,1]))
                r.set("t2_hw","%.4f"%(optS[0,2]))
                dck_sys.setU(optS[0,1], "tier1-cnt")
                dck_sys.setU(optS[0,2], "tier2-cnt")
        time.sleep(0.5)
        
    #salvo risultati intermedi
    Path(str(script_dir)+"/../data/%s/"%(str(myuuid)) ).mkdir( parents=True, exist_ok=True )
    sp.savemat(str(script_dir)+"/../data/%s/%s.mat"%(myuuid,fname),{"DS_X":DS_X,"DS_Y":DS_Y,"DS_U":DS_U})
    
    cavg=[]
    e=[]
    for i in range(rep):
        cavg+=np.divide(np.matrix(np.cumsum(XS[(i*ssTime):((i+1)*ssTime),0],axis=0)),np.matrix(np.arange(1,ssTime+1))).tolist()[0]

    plt.figure()
    plt.plot(XS[:,0])
    plt.plot(cavg)
    plt.show()
    
finally:
    stopSystem()
    r.close()
