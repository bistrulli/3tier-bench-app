import yaml
import threading
import subprocess
import re


def get_vpaout(vpa_name):
    p=subprocess.Popen(["kubectl","get","vpa",vpa_name,"--output","yaml"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,error = p.communicate()
    yaml_out=yaml.safe_load(out.decode('UTF-8'))
    
    temp=re.findall(r'\d+', yaml_out["status"]["recommendation"]["containerRecommendations"][0]["target"]["cpu"])
    return  list(map(float, temp))[0]


if __name__ == "__main__":
   tier1Vpa_cpu=get_vpaout("tier1-vpa")
   print(tier1Vpa_cpu)
    





