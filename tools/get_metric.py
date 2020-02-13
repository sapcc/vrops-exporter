import requests
from urllib3 import disable_warnings, exceptions
from urllib3.exceptions import HTTPError


def get_metric(target, token, uuid, key):
    url = "https://" + target + "/suite-api/api/resources/" + uuid + "/stats/latest"
    headers = {
        'Content-Type': "application/json",
        'Accept': "application/json",
        'Authorization': "vRealizeOpsToken " + token
    }
    disable_warnings(exceptions.InsecureRequestWarning)
    try:
        response = requests.get(url,
                                verify=False,
                                headers=headers)
        try:
            for statkey in response.json()["values"][0]["stat-list"]["stat"]:
                if statkey["statKey"]["key"] is not None and statkey["statKey"]["key"] == key:
                    return statkey["data"][0]
        except AttributeError:
            raise AttributeError("There is no attribute stat")
    except HTTPError:
        raise HTTPError("Request failed for statkey: " + key + " and target: " + target)
