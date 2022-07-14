from pymemcache.client.base import Client
import time


client = Client('monitor')
for i in range(0,15):
    st=time.time()
    client.set('some_key', 'some_value')
    result = client.get('some_key')
    print(time.time()-st)