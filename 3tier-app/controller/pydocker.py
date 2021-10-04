import docker
import redis

r = redis.Redis()
r.mset({"t1_hw":"1",
        "t2_hw":"1"})
r.close()
client = docker.from_env()



