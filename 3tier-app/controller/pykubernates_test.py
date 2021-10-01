import numpy as np
import matplotlib.pyplot as plt
import time
import tflite_runtime.interpreter as tflite
import os
import scipy.io
from tqdm import tqdm
import casadi
import redis
import subprocess
import signal
from kubernetes import client, config
import yaml

def readDploymen(depFile):
    dep = yaml.safe_load(depFile)
    return dep

def update_deployment(api, deployment):
    # Update container image
    #deployment.spec.template.spec.containers[0].image = "nginx:1.16.0"
    
    # Update container cpu limit
    deployment.spec.template.spec.containers[0].resources.resources.limits.cpu="1000m"
    

    # patch the deployment
    resp = api.patch_namespaced_deployment(
        name="DEPLOYMENT_NAME", namespace="default", body=deployment
    )

    print("\n[INFO] deployment's container image updated.\n")
    print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
    print(
        "%s\t\t%s\t%s\t\t%s\n"
        % (
            resp.metadata.namespace,
            resp.metadata.name,
            resp.metadata.generation,
            resp.spec.template.spec.containers[0].image,
        )
    )


# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

v1 = client.CoreV1Api()
# print("Listing pods with their IPs:")
# ret = v1.list_pod_for_all_namespaces(watch=False)
# for i in ret.items:
#     print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
tier1_dep=readDploymen(open("../tier1/deploy.yaml"))
print(tier1_dep)