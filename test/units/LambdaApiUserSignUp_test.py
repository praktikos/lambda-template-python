# -*- coding: utf-8 -*-

import json

import boto3
import requests

from api.rdb.config import is_test, is_production
from api.rdb.utils.apigateway import get_api_url
from api.rdb.utils.service_framework import STATUS_OK, STATUS_BAD_REQUEST
from ..utilities import invoke, get_lambda_test_data, get_lambda_fullpath


# noinspection PyUnusedLocal
def test(empty_database, create_and_delete_user, create_login_session):
    from ..conftest import _ID_TOKEN
    if is_test():
        fullpath = get_lambda_fullpath("LambdaApiUserSignUp")
        event = get_lambda_test_data(fullpath)
        # Read user TESTER1
        payload = {"httpMethod": "GET", "queryStringParameters": event['body']}
        # noinspection PyTypeChecker
        response1 = invoke(fullpath, payload)
        assert response1['statusCode'] == STATUS_OK
        assert len(response1['body'])
        response_data = json.loads(response1['body'])
        assert response_data['Username']
        username = response_data['Username']
        assert 'UserAttributes' in response_data
        # TODO: iterate through UserAttributes list and verify given_name and family_name
        # assert any(event['username'] in s['username'] for s in data)
        # assert event['body']['given_name'] == response_data['given_name']
        # assert event['body']['family_name'] == response_data['family_name']
        assert 'UserCreateDate' in response_data
        assert 'UserLastModifiedDate' in response_data
        assert 'Enabled' in response_data
        assert 'UserStatus' in response_data

        # Update user TESTER1
        event = get_lambda_test_data(fullpath, authorization_token=_ID_TOKEN)
        event['body'].pop('password', None)
        event['body'].pop('newpassword', None)
        event['body']['authorization_token'] = _ID_TOKEN
        event['body']['username'] = username
        payload = {"httpMethod": "POST", "body": event['body']}
        response2 = invoke(fullpath, payload)
        assert response2['statusCode'] == STATUS_OK
        assert len(response2['body'])
        response_data = json.loads(response2['body'])
        assert response_data['Username']
        assert 'UserCreateDate' in response_data
        assert 'UserLastModifiedDate' in response_data
        assert 'Enabled' in response_data
        assert 'UserStatus' in response_data

        # Get errors
        event['body']['username'] = "02347y23ijrkiuvc97dyvl4kjnvohv937fv3oijvn3o8uh91287dy"
        payload = {"httpMethod": "GET", "queryStringParameters": event['body']}
        response4 = invoke(fullpath, payload)
        assert response4['statusCode'] == STATUS_BAD_REQUEST
        response_data = json.loads(response4['body'])
        assert response_data['Message'] == 'User does not exist.'
        # assert response_data['Code'] == 'UserNotFoundException'

        # event['body'].pop('username', None)
        # event['body']['xyzzy'] = "x@praktikos.com"
        # payload = {"httpMethod": "GET", "queryStringParameters": event['body']}
        # response5 = invoke(fullpath, payload)
        # assert response5['statusCode'] == STATUS_BAD_REQUEST
        # response_data = json.loads(response5['body'])
        # assert response_data['Message'] == 'Param ["username"] is not valid'

    elif is_production():
        fullpath = get_lambda_fullpath("LambdaApiUserSignUp")
        event = get_lambda_test_data(fullpath)
        url = get_api_url(boto3.client("apigateway"), 'API', '/v1', '/user/signup')
        response6 = requests.get(url, params=event['body'])
        assert response6.status_code == STATUS_OK

        response_data = response6.json()
        event['body']['username'] = response_data['Username']
        event['body']['password'] = event['body']['newpassword']
        event['body'].pop('email', None)
        event['body'].pop('newpassword', None)
        event['body'].pop('aws_access_key_id', None)
        event['body'].pop('aws_secret_access_key', None)
        event['body'].pop('aws_account_id', None)

        response7 = requests.post(url, headers=event['headers'], data=json.dumps(event['body']))
        assert response7.status_code == STATUS_OK
