import os
import requests
from urllib3 import disable_warnings, exceptions
from urllib3.exceptions import HTTPError
from requests.auth import HTTPBasicAuth


def get_metric(target, uuid, key):
    url = "https://" + target + "/suite-api/api/resources/" + uuid + "/stats/latest"
    headers = {
        'Content-Type': "application/json",
        'Accept': "application/json"
    }
    disable_warnings(exceptions.InsecureRequestWarning)
    try:
        response = requests.get(url,
                                auth=HTTPBasicAuth(username=os.environ['USER'], password=os.environ['PASSWORD']),
                                verify=False,
                                headers=headers)
        try:
            for statkey in response.json()["values"][0]["stat-list"]["stat"]:
                if statkey["statKey"]["key"] is not None and statkey["statKey"]["key"] == key:
                    return statkey["data"][0]
        except AttributeError as ar:
            print("There is no attribute: stat", ar.args)
    except HTTPError as err:
        print("Request failed: ", err.args)

