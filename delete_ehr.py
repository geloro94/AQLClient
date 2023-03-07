import json

import requests
from requests.auth import HTTPBasicAuth

from main import AQLQuery, post_query

EHR_BASE = "http://localhost:8180/ehrbase/rest"
EHR_USER = "admin"
EHR_PASSWORD = "SuperAwesomePassword123"
ADMIN_ENDPOINT = EHR_BASE + "/admin/ehr/"


def delete_ehr(ehr_id):
    return requests.delete(url=ADMIN_ENDPOINT + ehr_id, auth=HTTPBasicAuth(EHR_USER, EHR_PASSWORD))


def delete_all_ehr():
    request = AQLQuery()
    request.q = "SELECT e/ehr_id/value AS ehrid FROM EHR e"
    response = post_query(request)
    response_data = json.loads(response)
    rows = [row for row in response_data.get("rows")]
    for row in rows:
        for ehr_id in row:
            print(ehr_id)
            delete_ehr(ehr_id)


if __name__ == "__main__":
    delete_all_ehr()
