### Description

Build K8s python client that lists all pods in Pending state and deletes the pods that have a particular error in Events.

* Requirements:
    * helm
    * taskfile
    * kubectl


### Run script on local machine/laptop

```
# create python3 virtual env
python3 -m venv venv

# activate python env
source venv/bin/activate

# install pip packages
pip install -r requirements.txt

# run script
python main.py
```

### Deploy to k8s with helm

```
# build container image
task build

# deploy helm chart
task install

# verify helm release
helm list -A

# uninstall helm chart
task uninstall
```

### Test 

```
# generate Pending pods
while True; do task generate-pending-pods; sleep 300; done

# check app logs
kubectl logs -l app=k8s-py-client -f
```