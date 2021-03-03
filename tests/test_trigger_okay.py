import pytest
import boto3
from moto import mock_secretsmanager
import requests_mock
import json
import os

from lambdas.lambda_function import key_rotate

secrets = {"BASE_URL": "https://example.com", "BPM_USER": "", "BPM_PW": ""}

@pytest.fixture(scope="function")
def sm():
    with mock_secretsmanager():
        client = boto3.client("secretsmanager")
        yield client


@mock_secretsmanager
def test_trigger_okay(sm):
    sm.create_secret(Name="secret", SecretString=json.dumps(secrets))
    env = {
        "containers": '["BS"]',
        "ttl_seconds": "600000",
        "default_only": "FALSE",
        "apiId": "fake",
        "secret": "secret",
    }
    with requests_mock.Mocker() as mock:
        mock.post(
            f"{secrets['BASE_URL']}/bpm/system/login",
            json={"csrf_token": "FAKETOKEN"},
            status_code=201,
        )
        mock.post(
            f"{secrets['BASE_URL']}/bpm/processes?model=UpdateEnvironmentVar&container=SPPEU",
            status_code=201,
        )
        key_rotate(mock_appsync, env)
        # If no exception raised, we're good, test passed


class mock_appsync:
    def create_api_key(apiId, description, expires):
        return {"apiKey": {"id": "grevergrv"}}

    def get_graphql_api(apiId):
        return {"graphqlApi": {"uris": {"GRAPHQL": "https://blah"}}}
