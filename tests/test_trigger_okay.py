import pytest
import boto3
from moto import mock_secretsmanager
import requests_mock
import json
import os
import time

from lambdas.lambda_function import key_rotate

secrets = {
    "BASE_URL": "https://example.com",
    "BPM_USER": "",
    "BPM_PW": "",
    "BAW_CONTAINERS": ["TEST"],
}


@pytest.fixture(scope="function")
def sm():
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"
    with mock_secretsmanager():
        client = boto3.client("secretsmanager")
        yield client


@mock_secretsmanager
def test_trigger_okay(sm):
    sm.create_secret(Name="secret", SecretString=json.dumps(secrets))
    env = {
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
        key_rotate(MockAppsync(), env)
        # If no exception raised, we're good, test passed


class MockAppsync:
    def create_api_key(self, apiId, description, expires):
        return {"apiKey": {"id": "grevergrv"}}

    def get_graphql_api(self, apiId):
        return {"graphqlApi": {"uris": {"GRAPHQL": "https://blah"}}}

    def get_paginator(self, function_name):
        if function_name == "list_api_keys":
            return MockListAPIKeys()
        else:
            raise Exception(f"Function {function_name} not defined for mock client")

    def delete_api_key(self, apiId, id):
        assert id == "123456"


class MockListAPIKeys:
    """"Mocks the list API keys paginator from the boto3 appsync client"""
    def paginate(self, apiId):
        """returns an iterator of pages, each containing a list of api keys"""
        return [
            {
                "apiKeys": [
                    {"expires": time.time() - 100, "id": "123456"},
                    {"expires": time.time() + 100, "id": "000000"},
                ]
            }
        ]
