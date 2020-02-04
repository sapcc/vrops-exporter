SHELL       := /bin/sh
IMAGE       := hub.global.cloud.sap/monsoon/vrops-exporter
VERSION     := 0.1

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
