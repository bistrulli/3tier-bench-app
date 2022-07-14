from pymemcache.client.base import Client
import time
import numpy as np
from scipy.io import savemat
import traceback

client = Client('localhost')

sampleT = []

try:

    nsample = int(10 ** 5)
    for i in range(0, nsample):
        st = time.time()
        state="%d" % (np.random.randint(low=0, high=1000))
        client.set('state',state)
        result = client.get('state')
        sampleT.append(time.time() - st)
        if(result!=state):
            raise ValueError(result,"is not",state)
        print((i * 100.0 / nsample))
    
    savemat("gketime_local.mat", {"data":sampleT})
except(e):
    traceback.print_exc()
finally:
    client.close()
    



