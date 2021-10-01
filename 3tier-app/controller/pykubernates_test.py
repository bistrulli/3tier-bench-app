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


# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

v1 = client.CoreV1Api()
print("Listing pods with their IPs:")
ret = v1.list_pod_for_all_namespaces(namespace="default")
for i in ret.items:
    print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))