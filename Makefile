SHELL       := /bin/sh
IMAGE       := keppel.eu-de-1.cloud.sap/ccloud/vrops-exporter
VERSION     := 0.2

### Executables
DOCKER := docker

### Docker Targets 

.PHONY: build
build: 
	$(DOCKER) build -t $(IMAGE):$(VERSION) --no-cache --rm .
	#$(DOCKER) build -t $(IMAGE):$(VERSION)  .

.PHONY: push 
push: 
	$(DOCKER) push $(IMAGE):$(VERSION)
	#$(DOCKER) push $(IMAGE):latest
