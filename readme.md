## Description

Trying to build a k8s python client that lists all pods in Pending state and deletes the pods that have a particular error in Events.

## Run code

```
# create python3 virtual env
python3 -m venv venv

# activate python env
source venv/bin/activate

# install pip packages
pip install -r requirements.txt

# build container image
docker build -f Dockerfile -t andreistefanciprian/k8s-python-client:latest .
docker image push andreistefanciprian/k8s-python-client
```