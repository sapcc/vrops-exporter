# vrops-exporter
Prometheus exporter to scrape metrics from vRealize Operations Manager

## Setup test environment

##### 1. Fork this repository

Forking a repository allows you to freely experiment with changes without affecting the original project.

##### 2. Clone your copied repository

```
git clone https://github.com/nmap/nmap.git
``` 

##### 3. Docker

```
docker run -it -p PORT:PORT -v $PATH_TO_YOUR_WORKDIR/:/vropsexporter $YOUR_DOCKER_HUB
```
##### 4. Establish a connection to your infrastructure 

##### 5. Provide a json configfile for testing
 
```json
 [
      {
           "labels": {
               "job": "vrops",
               "metrics_label": "vrops",
               "server_name": "VROPS_DNS_NAME" 
           }
      }
 ]
```

## How to develop a collector

```
├── BaseCollector.py
├── Dockerfile
├── InventoryBuilder.py
├── LICENSE
├── Makefile
├── README.md
├── collectors
│   ├── HostSystemCollector.py
│   ├── SampleCollector.py
│   ├── __init__.py
│   └── statkey.yaml
├── exporter.py
├── requirements.txt
├── resources
│   ├── Cluster.py
│   ├── Datacenter.py
│   ├── Host.py
│   ├── Vcenter.py
│   ├── VirtualMachine.py
│   └── __init__.py
├── tests
│   ├── TestCollectors.py
│   ├── TestLaunchExporter.py
│   ├── __init__.py
│   ├── metrics.yaml
│   └── test.json
└── tools
    ├── Resources.py
    ├── YamlRead.py
    └── __init__.py
```

##### 1. Create a new `collector.py` file in 

##### 2. 


## Running the exporter

The container is defaulting to /vrops-exporter path. Use vrops-exporter.py with one of the two ways of specifying the necessary credentials. They could also be mixed of course.

1. CLI

```
Usage: pyhton3 exporter.py [options]
```
Options:

short | long | description
--- | --- | ---
  -h | --help |           show this help message and exit
  -u USER | --user=USER | specify user to log in
  -p PASSWORD | --password=PASSWORD | specify password to log in
  -o PORT | --port=PORT | specify exporter port
  -a CONFIGFILE | --atlas | specify atlas configfile 
  -d | --debug    |       enable debug


2. Enviroment variables

```
USER
PASSWORD
PORT
```

## Service discovery way of querying
Query with: ``http://localhost:CONTAINERPORT``


## Testing
Test module is called using ENV variables. Specifying these on the fly would look like this:

```
DEBUG=0 USER=foo PASSWORD=bar python3 tests/TestCollectors.py
```

Please note, that USER and PW don't do anything at all currently, they are just being passed because VropsCollector.py is checking that these are present.

## Resources
![Class Diagram](https://yuml.me/032071b0.png)
