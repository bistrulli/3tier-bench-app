import docker
import redis

r = redis.Redis()
r.mset({"t1_hw":"1",
        "t2_hw":"1"})
r.close()

client = docker.from_env()

client.containers.run(image="bistrulli/client:0.1",
                      command="java -Xmx4G -jar client-0.0.1-SNAPSHOT-jar-with-dependencies.jar --initPop 20 --queues '[\"think\", \"e1_bl\", \"e1_ex\", \"t1_hw\", \"e2_bl\", \"e2_ex\", \"t2_hw\"]' --jedisHost monitor",
                      auto_remove=True,
                      detach=False,
                      hostname="client",
                      network="3tier-app_default")

