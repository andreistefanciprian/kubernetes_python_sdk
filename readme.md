## Description

K8s python client that lists all pods in Pending state and deletes the pods that have a particular error in Events.

## Run code with python from outside the cluster

```
# make sure you use the load_kube_config() method to authenticate to k8s cluster when running this script localy (from outside cluster)

# create python3 virtual env
python3 -m venv venv

# activate python env
source venv/bin/activate

# install pip packages
pip install -r requirements.txt

# run script
python main.py

# generate Pending pods
bash generate_pending_pods.sh
```

## Run app in k8s env

```
# make sure you use the config.load_kube_config() method to authenticate to k8s cluster when running this script from inside the cluster

# build container image
docker build -f Dockerfile -t andreistefanciprian/k8s-python-client:latest .
docker image push andreistefanciprian/k8s-python-client

# build k8s resources
kubectl apply -f deployment.yaml

# check app logs
kubectl logs -l app=k8s-py-client -f

# generate Pending pods
while True; do bash generate_pending_pods.sh; sleep 120; done
```