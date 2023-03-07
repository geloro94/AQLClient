from flask import Flask, request, jsonify, Response
import json
import requests
from requests.auth import HTTPBasicAuth

EHR_BASE = "http://localhost:8180/ehrbase/rest/openehr/v1"
EHR_USER = "admin"
EHR_PASSWORD = "SuperAwesomePassword123"
AD_HOC_QUERY_EXECUTION_ENDPOINT = EHR_BASE + "/query/aql"


def del_none(dictionary):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.

    This alters the input so you may wish to ``copy`` the dict first.
    """
    for key, value in list(dictionary.items()):
        if value is None:
            del dictionary[key]
        elif value is []:
            del dictionary[key]
        elif isinstance(value, dict):
            del_none(value)
    return dictionary


def del_keys(dictionary, keys):
    for k in keys:
        dictionary.pop(k, None)
    return dictionary


class AQLQuery:
    DO_NOT_SERIALIZE = ["DO_NOT_SERIALIZE"]

    def __init__(self):
        self.q = ""
        self.fetch = None
        self.offset = None

    def to_json(self):
        return json.dumps(self, default=lambda o: del_none(
            del_keys(o.__dict__, self.DO_NOT_SERIALIZE)),
                          sort_keys=True, indent=4)


def post_query(query: AQLQuery):
    return requests.post(url=AD_HOC_QUERY_EXECUTION_ENDPOINT, data=query.to_json(),
                         auth=HTTPBasicAuth(EHR_USER, EHR_PASSWORD),
                         headers={'Content-type': 'application/json'}).content


def get_uids(response):
    response_data = json.loads(response)
    print(response_data)
    uids = []
    rows = [row for row in response_data["rows"]]
    for row in rows:
        for element in row:
            uids.append(element)
    return set(uids)


api = Flask(__name__)


def get_CNF_result(inclusion):
    result = set()
    intersection = inclusion.split("INTERSECT")
    for intersection_part in intersection:
        union = intersection_part.split("UNION")
        if len(union) > 1:
            for union_part in union:
                aql_query = AQLQuery()
                aql_query.q = union_part
                result = result.union(get_uids(post_query(aql_query)))
        else:
            aql_query = AQLQuery()
            aql_query.q = intersection_part
            if result:
                result = result.intersection(get_uids(post_query(aql_query)))
            else:
                result = get_uids(post_query(aql_query))
    return result


def get_DNF_result(exclusion):
    result = set()
    union = exclusion.split("UNION")
    for union_part in union:
        intersection = union_part.split("INTERSECT")
        if len(intersection) > 1:
            for intersection_part in intersection:
                aql_query = AQLQuery()
                aql_query.q = intersection_part
                result = result.intersection(get_uids((post_query(aql_query))))
        else:
            aql_query = AQLQuery()
            aql_query.q = union_part
            if result:
                result = result.union(get_uids((post_query(aql_query))))
            else:
                result = get_uids(post_query(aql_query))
    return result


def run_query(query):
    if "MINUS" in query:
        inclusion, exclusion = query.split("MINUS")
        return str(len(get_CNF_result(inclusion).difference(get_DNF_result(exclusion))))

    else:
        return str(len(get_CNF_result(query)))


@api.route("/query/execute", methods=["POST"])
def parse_translate():
    query_input: str = request.data.decode("iso-8859-1")
    print(query_input)
    print(f"\nFound {run_query(query_input)} Patients matching criteria")
    return Response(run_query(query_input), mimetype="text/plain")


if __name__ == '__main__':
    api.run()
