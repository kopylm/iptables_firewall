# Iptables Firewall Rules Script
The application is designed to automate the management of Node iptables firewall rules based on Consul catalog data or catalog file. <br />
The script is designed to be deployed in a Kubernetes cluster using a DaemonSet and a CronJob inside container to run periodically on each node,  <br />
ensuring the firewall rules are always up-to-date.

## Requirements

- Python 3.6 or later
- `python-iptables` library
- Consul with the catalog data available

## Overview
**main.py** - iptables Firewall app <br />
**logger_config.py** - logger object configuration <br />
**requirements.txt** - required packages <br />
**rules.json** - iptables rules configuration that need to be applied for a host <br />
**nodes.json** - list of mocked nodes with metadata (Consul) <br />

## Local testing
1. Use the [Docker](https://docs.docker.com/reference/cli/docker/image/build/) to create a docker image.
From application root dir run:
```bash
docker build -t iptables-firewall .
```
2. Run [docker container](https://docs.docker.com/reference/cli/docker/container/run/) with ___--privileged___ to have 
access to iptables inside container. If you want use mocked host ip address also need to add ___-e___ with any ip address 
from **services.json**
```bash
docker run --privileged -e MOCKED_HOST_IP='10.10.0.17' iptables-firewall
```
### Alternative way to test
1. Build docker image:
```bash
docker build -t iptables-firewall .
```
2. Exec inside container:
```bash
docker run --privileged -ti c142e7addff9 bash 
```
3. Add env var of the node that you want to test:
```bash
export MOCKED_HOST_IP=10.10.17
```
4. Run script:
```bash
python main.py 
```

## Kubernetes installation 
1. Build and Push Docker Image:
```bash
docker build -t docker-registry/iptables-firewall:latest .
docker push docker-registry/iptables-firewall:latest
```
2. Apply the DaemonSet to your Kubernetes cluster:
```bash
kubectl apply -f iptables-daemonset.yaml
```
3. Check the Logs:
```bash
kubectl logs <pod-name>
```
