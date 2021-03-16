import boto3
import json
import requests
import time
import logging
from os import getenv
from schema import Schema, And, SchemaError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.ERROR)
CSRF_TOKEN = None
MIN_TTL_HOURS = 1


def lambda_handler(event, context):

    env = {
        "ttl_seconds": getenv("TTL_SECONDS"),
        "default_only": getenv("DEFAULT_ONLY", "true"),
        "apiId": getenv("API_ID"),
        "secret": getenv("SECRET"),
    }
    key_rotate(boto3.client("appsync"), env)


def key_rotate(appsync_client, env):
    global CSRF_TOKEN

    if env["ttl_seconds"] is None:
        raise Exception(f"TTL_SECONDS not set, cannot continue")
    try:
        ttl_seconds = int(env["ttl_seconds"])
    except:
        raise Exception(f"TTL_SECONDS not an integer.")
    if ttl_seconds < (60 * 60 * MIN_TTL_HOURS):
        raise Exception(f"TTL_SECONDS less than {MIN_TTL_HOURS} hours.")

    if str.upper(env["default_only"]) == "TRUE":
        default_only = True
    elif str.upper(env["default_only"]) == "FALSE":
        default_only = False
    else:
        raise Exception(f"DEFAULT_ONLY set, but not one of TRUE/FALSE.")

    client = boto3.client("secretsmanager")
    try:
        secrets = json.loads(
            client.get_secret_value(SecretId=env["secret"])["SecretString"]
        )
    except:
        raise Exception(f"Secret string not set.")

    secret_schema = Schema(
        {
            "BASE_URL": str,
            "BPM_USER": str,
            "BPM_PW": str,
            "BAW_CONTAINERS": And(
                [str], lambda l: len(l) > 0, error="BAW_CONTAINERS not a list or empty."
            ),
        }
    )
    try:
        secret_schema.validate(secrets)
    except SchemaError as error:
        raise Exception(f"Secret fails validation: ", error)

    as_response = appsync_client.create_api_key(
        apiId=env["apiId"],
        description="Autogenerated by appsync-key-rotation 🧙‍♂️",
        expires=int(time.time()) + ttl_seconds,
    )
    key_id = as_response["apiKey"]["id"]

    as_uri = appsync_client.get_graphql_api(apiId=env["apiId"])["graphqlApi"]["uris"][
        "GRAPHQL"
    ]

    if not as_uri.lower().startswith("https://"):
        raise Exception(f"GraphQL URI looks broken! - {as_uri}")

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
                    "data": {
                        "pairs": [
                            {"name": "GRAPHQL_API_KEY", "value": key_id},
                            {"name": "GRAPHQL_ENDPOINT", "value": as_uri},
                        ]
                    },
                },
                {"name": "targetContainers", "data": secrets["BAW_CONTAINERS"],},
                {"name": "defaultOnly", "data": env["default_only"]},
            ]
        },
    )
    if r.status_code != 201:
        raise Exception(r.text)
