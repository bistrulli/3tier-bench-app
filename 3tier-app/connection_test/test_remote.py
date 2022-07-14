from pymemcache.client.base import Client
import time
import numpy as np
from scipy.io import savemat


client = Client('monitor')

sampleT=[]

nsample=1000
for i in range(0,nsample):
    st=time.time()
    client.set('state', "%d"%(np.random.randint(low=0,high=1000)))
    result = client.get('state')
    sampleT.append(time.time()-st)
    print((i*100.0/nsample))

savemat("gketime.mat", {"data":sampleT})


