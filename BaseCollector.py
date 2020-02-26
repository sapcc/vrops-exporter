from abc import ABC, abstractmethod
import requests, json
import time

class BaseCollector(ABC):

    @abstractmethod
    def collect(self):
        pass

    def get_vcenters(self):
        request = requests.get(url = "http://localhost:8000/vcenters")
        self.vcenters = request.json()
        return self.vcenters

    def get_datacenters(self):
        request = requests.get(url = "http://localhost:8000/datacenters")
        self.datacenters = request.json()
        return self.datacenters

    def get_clusters(self):
        request = requests.get(url = "http://localhost:8000/clusters")
        self.clusters = request.json()
        return self.clusters

    def get_hosts(self):
        request = requests.get(url = "http://localhost:8000/hosts")
        self.hosts = request.json()
        return self.hosts

    def get_vms(self):
        request = requests.get(url = "http://localhost:8000/vms")
        self.vms = request.json()
        return self.vms

    def get_iteration(self):
        request = requests.get(url = "http://localhost:8000/iteration")
        self.iteration = request.json()
        return self.iteration

    # def get_token(self):
        # request = requests.get(url="http://localhost:8000/token")
        # self.token = request.json()
        # return self.token

    def get_target(self):
        request = requests.get(url="http://localhost:8000/target")
        self.target = request.json()
        return self.target

    def get_targets(self):
        request = requests.get(url="http://localhost:8000/vrops_list")
        self.target = request.json()
        return self.target
