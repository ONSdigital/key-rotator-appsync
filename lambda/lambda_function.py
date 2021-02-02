import boto3
import json
import requests
import time
import logging
from os import getenv

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.ERROR)
CSRF_TOKEN = None
MIN_TTL_HOURS = 1


def lambda_handler(event, context):
    global CSRF_TOKEN
    containers = getenv("BAW_CONTAINERS")
    if containers is None:
        raise Exception(f"BAW_CONTAINERS not set, cannot continue")
    try:
        containers = json.loads(containers)
    except:
        raise Exception(f"BAW_CONTAINERS not valid JSON. Should be JSON array of strings.")
    if not isinstance(containers, list):
        raise Exception(f"BAW_CONTAINERS not a list. Should be JSON array of strings.")
    if len(containers) < 1:
        raise Exception(f"BAW_CONTAINERS is an empty list. Lambda configuration incomplete?")

    ttl_seconds = getenv("TTL_SECONDS")
    if ttl_seconds is None:
        raise Exception(f"TTL_SECONDS not set, cannot continue")
    try:
        ttl_seconds = int(ttl_seconds)
    except:
        raise Exception(f"TTL_SECONDS not an integer.")
    if ttl_seconds < (60*60*MIN_TTL_HOURS):
        raise Exception(f"TTL_SECONDS less than {MIN_TTL_HOURS} hours.")

    default_only = getenv("DEFAULT_ONLY", "true")
    if str.upper(default_only) == "TRUE":
        default_only = True
    elif str.upper(default_only) == "FALSE":
        default_only = False
    else:
        raise Exception(f"DEFAULT_ONLY set, but not one of TRUE/FALSE.")

    client = boto3.client("appsync")
    as_response = client.create_api_key(
        apiId=getenv("API_ID"),
        description="Autogenerated by appsync-key-rotation 🧙‍♂️",
        expires=int(time.time()) + ttl_seconds,
    )
    key_id = as_response["apiKey"]["id"]

    as_uri = client.get_graphql_api(
        apiId=getenv("API_ID")
    )['graphqlApi']['uris']["GRAPHQL"]

    if not as_uri.lower().startswith("https://"):
        raise Exception(f"GraphQL URI looks broken! - {as_uri}")

    client = boto3.client("secretsmanager")
    secrets = json.loads(
        client.get_secret_value(SecretId=getenv("SECRET"))["SecretString"]
    )

    csrf_resp = requests.post(
        f'{secrets["BASE_URL"]}/bpm/system/login',
        auth=(secrets["BPM_USER"], secrets["BPM_PW"]),
        json={"requested_lifetime": 7200},
    )
    if csrf_resp.status_code != 201:
        raise Exception(
            f"ERROR {csrf_resp.status_code}: Cannot get CSRF token: {csrf_resp.text}"
        )
    CSRF_TOKEN = csrf_resp.json()
    r = requests.post(
        f"{secrets['BASE_URL']}/bpm/processes?model=UpdateEnvironmentVar&container=SPPEU",
        headers={"BPMCSRFToken": CSRF_TOKEN["csrf_token"]},
        auth=(secrets["BPM_USER"], secrets["BPM_PW"]),
        json={
            "input": [
                {
                    "name": "envVarPairs",
                    "data": {"pairs": [{"name": "GRAPHQL_API_KEY", "value": key_id},
                            {"name": "GRAPHQL_ENDPOINT", "value": as_uri}]},
                },
                {
                    "name": "targetContainers",
                    "data": containers,
                },
                {"name": "defaultOnly", "data": default_only},
            ]
        },
    )
    if r.status_code != 201:
        raise Exception(r.text)
