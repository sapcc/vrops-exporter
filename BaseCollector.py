from abc import ABC, abstractmethod
import requests, json
import time

class BaseCollector(ABC):
    def __init__(self):
        print("waiting")
        time.sleep(60)
        self.get_vcenters()
        self.get_datacenters()
        self.get_clusters()
        self.get_hosts()
        self.get_vms()
        self.get_iteration()

    @abstractmethod
    def collect(self):
        pass

    def get_vcenters(self):
        request = requests.get(url = "http://localhost:8000/vcenters")
        self.vcenters = request.json()

    def get_datacenters(self):
        request = requests.get(url = "http://localhost:8000/datacenters")
        self.datacenters = request.json()

    def get_clusters(self):
        request = requests.get(url = "http://localhost:8000/clusters")
        self.clusters = request.json()

    def get_hosts(self):
        request = requests.get(url = "http://localhost:8000/hosts")
        self.hosts = request.json()

    def get_vms(self):
        request = requests.get(url = "http://localhost:8000/vms")
        self.vms = request.json()

    def get_iteration(self):
        request = requests.get(url = "http://localhost:8000/iteration")
        self.iteration = request.json()
