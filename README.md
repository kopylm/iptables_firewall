# Iptables Firewall
The application is designed to change host INPUT iptable according to the rules in config file.

## Overview
**main.py** - iptables Firewall app <br />
**logger_config.py** - logger object configuration <br />
**requirements.txt** - required packages <br />
**rules.json** - iptables rules configuration that need to be applied for a host <br />
**nodes.json** - list of mocked nodes with metadata (Consul) <br />

## Installation for testing
1. Use the [Docker](https://docs.docker.com/reference/cli/docker/image/build/) to create a docker image.
From application root dir run:
```bash
docker build .
```
2. Run [docker container](https://docs.docker.com/reference/cli/docker/container/run/) with ___--privileged___ to have 
access to iptables inside container. If you want use mocked host ip address also need to add ___-e___ with any ip address 
from **services.json**
```bash
docker run --privileged -e MOCKED_HOST_IP='10.10.0.17' IMAGE[:TAG]
```
