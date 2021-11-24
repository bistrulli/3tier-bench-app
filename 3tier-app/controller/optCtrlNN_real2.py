'''
Created on 14 mag 2021

@author: emilio
'''
import numpy as np
import matplotlib.pyplot as plt
import time
import tflite_runtime.interpreter as tflite
import os
import scipy.io
from tqdm import tqdm
import casadi
import subprocess
import signal
from cgroupspy import trees
import docker
from pathlib import Path
from pymemcache.client.base import Client
from jvm_sysv2 import jvm_sys
from docker_sys import dockersys

curpath = os.path.realpath(__file__)
plant=None

# tf.compat.v1.disable_eager_execution()

def handler(signum, frame):
    global plant
    print('Signal handler called with signal', signum)
    plant.stopClient()
    plant.stopSystem()

def mitigateBottleneck(S, X, tgt):
    # devo definire il numero di server da assegnare
    # per andare verso target
    optS = S
    
    # findBootleneck
    U = np.divide(np.minimum(X, S), S)
    b = np.argmax(np.mean(U, axis=0))
    if(b == 0):
        return optS
        
    optS[b] = np.minimum(np.maximum(optS[b] + (tgt - X[-1, 0]), 0), np.sum(X[0,:]))
    
    return optS;


def genAfa():
    # r=np.random.choice([.1,.2,.3,.4,.5,.6,.7,.8,.9,1],p=[0.0182,0.0364,0.0545,0.0727,0.0909,0.1091,0.1273,0.1455,0.1636,0.1818])
    r = np.random.choice([.2, .3, .4, .5, .6, .7, .8, .9, 1])
    return np.round(np.random.rand() * 0.1 + (r - 0.1), 4)
    # return np.round(np.random.rand()*0.3+0.7,4)



class optCtrlNN3:
    model = None
    stateVar = None
    Uvar = None
    tfmodel = None
    Xtrain = None
    Utrain = None
    Ytrain = None
    stdx = None
    stdy = None
    stdu = None
    meanx = None
    meany = None
    meanu = None
    pVarMatrix = None
    
    def __init__(self, modelPath, train_data):
        # self.tfmodel=load_model(modelPath)
        self.tfmodel = tflite.Interpreter(model_path=modelPath, num_threads=2)
        
        # questo lo devo sostituire e rendere piu pulito
        DST = scipy.io.loadmat(train_data);
        nzd_t=np.sum(np.sum(DST['DS_X'],1,keepdims=True)>0)

        self.Xtrain = DST['DS_X'][0:nzd_t,:]
        self.Utrain = DST['DS_U'][0:nzd_t,:]
        self.Ytrain = DST['DS_Y'][0:nzd_t,:]
        
        
        
        self.stdx = np.std(self.Xtrain, 0);
        self.stdy = np.std(self.Ytrain, 0);
        self.stdu = np.std(self.Utrain, 0);
        self.meanx = np.mean(self.Xtrain, 0);
        self.meany = np.mean(self.Ytrain, 0);
        self.meanu = np.mean(self.Utrain, 0);
        
    def buildOpt(self, X0, tgt, MU, S, P, Sold_N, H, isAR=False):
        
        input_N = (X0 - self.meanx) / self.stdx
        if(Sold_N is not None):
            Sold = Sold_N * self.stdu + self.meanu
        else:
            Sold = None
        
        lb = [np.sum(X0) - 1]
        ub = [np.sum(X0) + 1]
        for i in range(1, P.shape[0]):
            lb.append(1*10 ** (-1))
            ub.append(30)
        
        for i in range(P.shape[0] * P.shape[1]):
            lb.append(0)
            ub.append(10)
        
        lb = np.matrix(lb).reshape([1, -1])
        ub = np.matrix(ub).reshape([1, -1])
        
        Sin = None
        if(Sold_N is None):
            Sin = np.matrix([np.sum(X0), 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0])
        else:
            Sin = np.matrix(Sold_N)
        
        self.tfmodel.allocate_tensors()
        
        input_details = self.tfmodel.get_input_details()
        output_details = self.tfmodel.get_output_details()
        
        self.tfmodel.set_tensor(input_details[0]['index'], np.float32(input_N))
        self.tfmodel.set_tensor(input_details[1]['index'], np.float32(Sin))
        
        self.tfmodel.invoke()
        # Ypredicted_N=self.tfmodel({'inputx':input_N,'inputu':Sin})
        # Ypredicted_N=[0,np.zeros([1,2,38]),np.zeros([1,10])]
        
        # print(self.tfmodel.get_tensor(output_details[0]['index']).shape)
        # print(self.tfmodel.get_tensor(output_details[1]['index']).shape)
        #print(self.tfmodel.get_tensor(output_details[2]['index']).shape)
        
        Gain = self.tfmodel.get_tensor(output_details[0]['index'])
        Bias = self.tfmodel.get_tensor(output_details[1]['index'])
        

        # Bias=Ypredicted_N[-1]
        # Gain=Ypredicted_N[1]
        
        model = casadi.Opti("conic")
        Uvar = model.variable(1, self.Xtrain.shape[1] + self.Xtrain.shape[1] * self.Xtrain.shape[1]);
        stateVar = model.variable(self.Xtrain.shape[1], H);
        absE_var = model.variable(1, H);
        
        model.subject_to(absE_var >= 0)
        
        uvar_dn = Uvar * self.stdu.reshape([1, -1]) + self.meanu.reshape([1, -1])
        model.subject_to(uvar_dn >= lb)        
        model.subject_to(uvar_dn <= ub)
        
        c = np.array([0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0])
        model.subject_to(uvar_dn[self.Xtrain.shape[1]:] == c[self.Xtrain.shape[1]:].reshape([1, -1]))
        model.subject_to(uvar_dn[0] == np.sum(X0))
        
        N = self.Xtrain.shape[1]
    
        # in questo modo scrivo il controllore
        if(isAR):
            for h in range(H - 1):
                if(h == 0):
                    model.subject_to(stateVar[:, h + 1] == Bias[0, (N * h):(N * h + N)] + Gain[0,:, 0:N * (N + 1)] @ Uvar[0,:].T)
                else:
                    model.subject_to(stateVar[:, h + 1] == (Bias[0, (N * h):(N * h + N)] + (Gain[0,:, N * (N + 2) * (h - 1) + N * (N + 1):N * (N + 2) * (h) + N * (N + 1)] @ casadi.horzcat(Uvar, stateVar[:, h].T).T)))
        else:
            Ypredicted = (Bias.T + Gain[0,:,:] @ Uvar[0,:].T)
            for h in range(H):
                # model.subject_to(stateVar[:,h+1]==Bias[0,(3*h):(3*h+3)]+Gain[0,(3*h):(3*h+3),:]@Uvar[0,:].T)
                model.subject_to(stateVar[:, h] == Ypredicted[(N * h):N * (h + 1)])
        
        obj = 0
        for h in range(H):
            model.subject_to(absE_var[0, h] >= (stateVar[0, h] * self.stdy[h * N] + self.meany[h * N] - tgt))
            model.subject_to(absE_var[0, h] >= -(stateVar[0, h] * self.stdy[h * N] + self.meany[h * N] - tgt))
            # obj+=(stateVar[0,h]*self.stdy[h*N]+self.meany[h*N]-tgt)**2
            obj += absE_var[0, h]
        
        ru = 0;
        if(Sold is not None):
            for ui in range(1, P.shape[0]):
                ru += (uvar_dn[ui] - Sold[ui]) ** 2
        
        model.minimize(obj + 0.1*ru + 0.3*casadi.sumsqr(uvar_dn[1:3]))
        
        optionsIPOPT = {'print_time':False, 'ipopt':{'print_level':0}}
        optionsOSQP = {'print_time':False, 'osqp':{'verbose':False}}
        #model.solver('ipopt',optionsIPOPT)
        model.solver('osqp', optionsOSQP)
        model.solve()
        return model.value(Uvar), model.value(stateVar[:, 1])


if __name__ == "__main__":
    
    signal.signal(signal.SIGINT, handler)
    
    
    curpath = os.path.realpath(__file__)
    ctrl = optCtrlNN3("%s/../learnt_model/gcp_model/model_3tier.tflite" % (os.path.dirname(curpath)),
                     "%s/../learnt_model/gcp_model/open_loop_3tier_H5.mat" % (os.path.dirname(curpath)))
    
    isAR = True
    isCpu = True
    dt = 10 ** (-1)
    H = 5
    N = 3
    rep = 1
    drep = 0
    sTime = 10000
    TF = sTime * rep * dt;
    Time = np.linspace(0, TF, int(np.ceil(TF / dt)) + 1)
    XSNN = np.zeros([N, len(Time)])
    XSSIM = np.zeros([N, XSNN.shape[1]])
    XSSIM2 = np.zeros([N, XSNN.shape[1]])
    XSSIMPid = np.zeros([N, XSNN.shape[1]])
    # XSSIM[:,0]=np.random.randint(low=1,high=100,size=[1,N])
    XSNN[:, 0] = XSSIM[:, 0]
    XSSIM2[:, 0] = XSSIM[:, 0]
    optSNN = np.zeros([N, XSNN.shape[1]])
    optSMD = np.zeros([N, XSNN.shape[1]])
    optSPID = np.zeros([N, XSNN.shape[1]])
    P = np.matrix([[0, 1., 0], [0, 0, 1.], [1., 0, 0]])
    S = np.matrix([-1, -1, -1]).T
    MU = np.matrix([1, 10, 10]).T
    Us = np.zeros([N, XSNN.shape[1]])
    sIdx = []
    keys = ["think", "e1_bl", "e1_ex", "t1_hw", "e2_bl", "e2_ex", "t2_hw"]
    
    alfa = [];
    ek = 0
        
    # alfa=np.round(np.random.rand(),4)
    # tgt=alfa[-1]*0.441336*np.sum(XSSIM[:,0])
    tgtStory = [0]
    # init_cstr=["X%d_0" % (i) for i in range(P.shape[0])];
    cp = -1
    
    Ie = 0
    Sold = None
    r=None
    tgt=None
    step=0
    
    plant = jvm_sys("../",isCpu)
    #plant=dockersys()
    plant.startSys()
    #plant.startClient(np.random.randint(low=10, high=100))
    plant.startClient(40,sim=True)
    
    #memcached client
    r=Client("localhost:11211")
    
    try:
        
            while(r.get("sim")==None):
                print("waiting sim to start")
                time.sleep(0.2)
                
            while drep<=rep and step<(XSNN.shape[1]-1):
                if "step" in r.get("sim").decode('UTF-8'):
                    pop=float(r.get("sim").decode('UTF-8').split("_")[1]);
                    print("drep=",drep,"pop",pop)
                    r.set("sim","-1")
                    #time.sleep(3)                            
                    drep+=1
                    
                    #Sold = None       
                    #alfa.append(genAfa())
                    alfa.append(1)
                    #XSSIM[:, step] = [np.random.randint(low=10, high=100), 0, 0]
                    XSSIM[:, step] = plant.getstate(r)[0]
                    #XSSIM[:, step] = [100, 0, 0]
                    print(alfa[-1], XSSIM[:, step])
                    # print(XSSIM[:, step])
                    XSSIM2[:, step] = XSSIM[:, step]
                    XSSIMPid[:, step] = XSSIM[:, step]
                    S[0] = np.sum(XSSIM[:, step])
                    tgt = np.round(alfa[-1] * 0.884 * pop, 5)
                    sIdx.append({'alfa':alfa[-1], 'x0':XSSIM[:, step].tolist(), "tgt":tgt,"idx":step})
                    optSPid = [np.sum(XSSIM[:, step]), 1, 1]
                    cp += 1
                    #ek = 0
                    #Ie = 0
                       
                    # if(r is not None):
                    #     killClient()
                    #     time.sleep(10)
                    #
                    #     killSys()
                    #     #time.sleep(10)
                    #
                    #     pruneContainer()
                    
                    
                    # redis_cnt=client.containers.get("monitor-cnt")
                    # tier1=client.containers.get("tier1-cnt")
                    # tier2=client.containers.get("tier2-cnt")
                    
                    # redis_cnt=sys[0]
                    # tier2=sys[1]
                    # tier1=sys[2]
                    
                    # redis_cnt.update(cpuset_cpus="0-4")
                    # tier1.update(cpuset_cpus="5-31")
                    # tier2.update(cpuset_cpus="5-31")
                    
                    # if(isCpu):
                    #     resetU()
                    #r.mset({"t1_hw":np.sum(XSSIM[:, step]),"t2_hw":np.sum(XSSIM[:, step])})
                    # startClient(np.sum(XSSIM[:, step]))
                    # time.sleep(3)
                    # if(step>0):
                    #     r.set("t1_hw",optSNN[1, step-1])
                    #     r.set("t2_hw",optSNN[2, step-1])
                    
                    # r.set("t1_hw",str(110))
                    # r.set("t2_hw",str(110))
                    
                #print(r.get("sim").decode('UTF-8'))
                
                XSSIM[:, step] = plant.getstate(r)[0]
                #tgt = np.round(alfa[-1] * 0.884 * np.sum(XSSIM[:, step]), 5)
                
                if(step > 0):
                    Ie += (tgt - XSSIM[0, step])
                
                #stime = time.time()
                optU_N, XNN = ctrl.buildOpt(XSSIM[:, [step]].T, tgt + 0.05 * Ie, MU, S, P, Sold, H, isAR)
                #ftime = time.time() - stime
                
                optU = optU_N * ctrl.stdu + ctrl.meanu
                Sold = optU_N
                
                # if(not isCpu):
                #     r.set("t1_hw",str(optU[1]))
                #     r.set("t2_hw",str(optU[2]))
                # #r.mset({"t1_hw":str(np.round(optU[1],4)),"t2_hw":str(np.round(optU[2],4))})
                # else:
                #optU=[0,9.57555318,7.32977541]
                r.set("t1_hw",str(optU[1]))
                r.set("t2_hw",str(optU[2]))
                plant.setU(optU[1],"tier1")
                plant.setU(optU[2],"tier2")
                # print(optU)
                
                print(XSSIM[:, step],tgt,np.sum(XSSIM[:, step]),step,optU[1:N])
                            
                optSNN[:, step] = optU[0:N]
                tgtStory += [tgt]
                
                time.sleep(0.1)
                
                # optSPID[:,step]=optSPid
                # optSPid=mitigateBottleneck(optSPid, Xsim3, tgt)
                
                step+=1
             
            # print("NN Reference error %f%% \nODE Reference error %f%% \n"%(np.abs(XSNN[0,-1]-tgt)*100/tgt,np.abs(XSODE[0,-1]-tgt)*100/tgt))
            plt.close('all')
            
            Path( './figure' ).mkdir( parents=True, exist_ok=True )   
            
            xsim_cavg = []
            xsim_cavg2 = []
            xsim_cavg3 = []
            optS_avg1 = []
            optS_avg2 = []
            e = []
            e2 = []
            e3 = []
            print("nrep",len(sIdx))
            for i in range(len(sIdx)):
                stepTime=None
                iIdx=None
                fIdx=None
                
                iIdx=sIdx[i]["idx"]
                
                if(i<len(sIdx)-1):    
                    fIdx=sIdx[i+1]["idx"]
                else:
                    fIdx=min(XSSIM.shape[1]-1,len(tgtStory)-1) 
                        
                stepTime=fIdx-iIdx
                    
                xsim_cavg += np.divide(np.cumsum(XSSIM[:, iIdx:fIdx], axis=1), np.arange(1, stepTime + 1)).T[:, 0].tolist()
                optS_avg1 += np.divide(np.cumsum(optSNN[[1], iIdx:fIdx], axis=1), np.arange(1, stepTime + 1)).T[:, 0].tolist()
                optS_avg2 += np.divide(np.cumsum(optSNN[[2], iIdx:fIdx], axis=1), np.arange(1, stepTime + 1)).T[:, 0].tolist()
                # xsim_cavg2 += np.divide(np.cumsum(XSSIM2[:, i * sTime:(i + 1) * sTime], axis=1), np.arange(1, sTime + 1)).T[:, 0].tolist()
                # xsim_cavg3 += np.divide(np.cumsum(XSSIMPid[:, i * sTime:(i + 1) * sTime], axis=1), np.arange(1, sTime + 1)).T[:, 0].tolist()
                print(len(tgtStory),fIdx)
                e.append(np.abs(xsim_cavg[-1] - tgtStory[fIdx]) / tgtStory[fIdx])
                # e2.append(np.abs(xsim_cavg2[-1] - tgtStory[i * sTime + 1]) / tgtStory[i * sTime + 1])
                # e3.append(np.abs(xsim_cavg3[-1] - tgtStory[i * sTime + 1]) / tgtStory[i * sTime + 1])
                
                sIdx[i]["e"] = e[-1] * 100;
        
            f=plt.figure()
            plt.title("Mean Relaive Long-run Tracking Error (%)")
            plt.boxplot([np.array(e)*100,np.array(e2)*100,np.array(e3)*100])
            plt.xticks([1,2,3],['NN','MD','PID'])
            
            f = plt.figure()
            plt.title("Mean Relaive Long-run Tracking Error (%)")
            plt.boxplot([np.array(e) * 100])
            plt.xticks([1], ['NN'])
            plt.savefig("./figure/boxerror.png")
            
            sumPop = []
            tgts = []
            for ipop in sIdx:
                sumPop.append(np.sum(ipop["x0"]))
                tgts.append(np.sum(ipop["tgt"]))
            
            plt.figure()
            plt.title("error vs total pop")
            plt.scatter(sumPop, np.array(e) * 100)
            plt.savefig("./figure/evspop.png")
            
            plt.figure()
            plt.title("error vs alfa")
            plt.scatter(alfa, np.array(e) * 100) 
            plt.savefig("./figure/evsalfa.png")
            
            plt.figure()
            plt.title("error vs tgt")
            plt.scatter(tgts, np.array(e) * 100) 
            plt.savefig("./figure/evstgt.png")
            
            print(np.array(e) * 100)
            print(np.array(e2)*100)
            print(np.array(e3)*100)
            print(sIdx)
                
            for k in range(0, 1):
                plt.figure()
                plt.plot(Time[0:len(tgtStory)], XSSIM.T[0:len(tgtStory), k], label="SIM_NNctrl")
                # plt.plot(Time,XSSIM2.T[:,k],label="SIM_MDctrl",linestyle ='-.')
                # plt.axhline(y = tgt, color = 'r', linestyle = '--')
                plt.plot(Time[0:len(tgtStory)], np.array(tgtStory), '--', color='r')
            plt.legend()
            plt.savefig("./figure/queue_sim.png")
            
            plt.figure()
            plt.plot(xsim_cavg, label="SIM_NNctrl")
            # plt.plot(xsim_cavg2,label="SIM_MDctrl",linestyle ='-.')
            plt.plot(np.array(tgtStory), '--', color='r')
            plt.legend()
            plt.savefig("./figure/queue_avg.png")
            
            plt.figure()
            plt.stem(alfa)
            
            plt.figure()
            plt.title("Control Signals NN")
            for i in range(1, N):
                plt.plot(optSNN[i,0:min(optSPID.shape[1],len(tgtStory))-1].T, label="Tier_%d" % (i))
            plt.legend()
            plt.savefig("./figure/control.png")
            
            plt.figure()
            plt.title("Control Signals NN AVG")
            plt.plot(optS_avg1)
            plt.plot(optS_avg2)
            plt.savefig("./figure/control_avg.png")
            
            # plt.figure()
            # plt.title("Control Singals Model Driven")
            # plt.plot(optSMD[1:,:].T)
            # plt.figure()
            # plt.title("Control Singals PID")
            # plt.plot(optSPID[1:,:].T)
            
            print(np.mean(optSPID[1:,0:min(optSPID.shape[1],len(tgtStory))-1], axis=1))
            print(np.mean(optSMD[1:,0:min(optSPID.shape[1],len(tgtStory))-1], axis=1))
            print(np.mean(optSNN[1:,0:min(optSPID.shape[1],len(tgtStory))-1], axis=1))         
    
            plt.show()
    
    finally:
        plant.stopClient()
        plant.stopSystem()
        #pass
        # killClient()
        # time.sleep(5)
        # killSys()
        #killDockerCmp()
