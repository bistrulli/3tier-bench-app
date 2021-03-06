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

def readDploymentFromYaml(depFile):
    dep = yaml.safe_load(depFile)
    return dep

def getDeplyment(api,name,namespace=None):
    if(namespace==None):
        namespace="default"
        
    deps = api.list_namespaced_deployment(namespace=namespace)
    for i in deps.items:
        print(i)

def update_deployment(api, deployment):
    
    # Update container cpu limit
    deployment.spec.template.spec.containers[0].resources.limits.cpu="1000m"
    if(deployment.spec.template.spec.containers[0].resources==None):
        resources=client.V1ResourceRequirements(
                #requests={"cpu": "100m", "memory": "200Mi"},
                limits={"cpu": "500m"},
            )
    else:
        deployment.spec.template.spec.containers[0].resources.limits={"cpu": "100m"}
    

    # # patch the deployment
    # resp = api.patch_namespaced_deployment(
    #     name="DEPLOYMENT_NAME", namespace="default", body=deployment
    # )
    #
    # print("\n[INFO] deployment's container image updated.\n")
    # print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
    # print(
    #     "%s\t\t%s\t%s\t\t%s\n"
    #     % (
    #         resp.metadata.namespace,
    #         resp.metadata.name,
    #         resp.metadata.generation,
    #         resp.spec.template.spec.containers[0].image,
    #     )
    # )


# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

apps_api = client.AppsV1Api()
tier1=apps_api.read_namespaced_deployment(name="tier1-pod",namespace="default")

tier1.spec.template.spec.containers[0].resources.limits={"cpu": "100m"}
apps_api.patch_namespaced_deployment(name=tier1.metadata.name, namespace=tier1.metadata.namespace, body=tier1, async_req=True)

    
