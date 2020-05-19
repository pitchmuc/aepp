import time
import json
from collections import defaultdict
from concurrent import futures
from copy import deepcopy
from typing import Union, IO
from datetime import datetime
# Non standard libraries
import pandas as pd
import requests
import jwt
from pathlib import Path
# Internal Library
from aepp import config
from aepp import adobeio_auth

__version__ = "0.0.2"


def createConfigFile(verbose: object = False)->None:
    """
    This function will create a 'config_admin.json' file where you can store your access data. 
    """
    json_data = {
        'org_id': '<orgID>',
        'api_key': "<APIkey>",
        'tech_id': "<something>@techacct.adobe.com",
        'secret': "<YourSecret>",
        'pathToKey': '<path/to/your/privatekey.key>',
    }
    with open('config_admin.json', 'w') as cf:
        cf.write(json.dumps(json_data, indent=4))
    if verbose:
        print(' file created at this location : ' +
              config._cwd + '/config_admin.json')


def importConfigFile(file: str)-> None:
    """
    This function will read the 'config_admin.json' to retrieve the information to be used by this module. 
    """
    with open(Path(file), 'r') as file:
        f = json.load(file)
        config._org_id = f['org_id']
        config._header["x-gw-ims-org-id"] = config._org_id
        config._api_key = f['api_key']
        config._header["X-Api-Key"] = config._api_key
        config._tech_id = f['tech_id']
        config._secret = f['secret']
        config._pathToKey = f['pathToKey']


@adobeio_auth._checkToken
def _getData(endpoint: str, params: dict = None, data: dict = None, headers: dict = None, *args, **kwargs):
    """
    Abstraction for getting data
    """
    if headers is None:
        headers = config._header
    if params == None and data == None:
        res = requests.get(endpoint, headers=headers)
    elif params != None and data == None:
        res = requests.get(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = requests.get(endpoint, headers=headers, data=data)
    elif params != None and data != None:
        res = requests.get(endpoint, headers=headers,
                           params=params, data=data)
    try:
        res_json = res.json()
    except:
        res_json = {'error': 'Request Error'}
    return res_json


@adobeio_auth._checkToken
def _postData(endpoint: str, params: dict = None, data: dict = None, headers: dict = None, * args, **kwargs):
    """
    Abstraction for posting data
    """
    if headers is None:
        headers = config._header
    if params == None and data == None:
        res = requests.post(endpoint, headers=headers)
    elif params != None and data == None:
        res = requests.post(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = requests.post(endpoint, headers=headers,
                            data=json.dumps(data))
    elif params != None and data != None:
        res = requests.post(endpoint, headers=headers,
                            params=params, data=json.dumps(data))
    try:
        res_json = res.json()
    except:
        res_json = {'error': 'Request Error'}
    return res_json


@adobeio_auth._checkToken
def _patchData(endpoint: str, params: dict = None, data: dict = None, headers: dict = None, *args, **kwargs):
    """
    Abstraction for patching data
    """
    if headers is None:
        headers = config._header
    if params == None and data == None:
        res = requests.patch(endpoint, headers=headers)
    elif params != None and data == None:
        res = requests.patch(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = requests.patch(endpoint, headers=headers,
                             data=json.dumps(data))
    elif params != None and data != None:
        res = requests.patch(endpoint, headers=headers,
                             params=params, data=json.dumps(data))
    try:
        res_json = res.json()
    except:
        res_json = {'error': 'Request Error'}
    return res_json


@adobeio_auth._checkToken
def _deleteData(endpoint: str, params: dict = None, data=None, headers: dict = None, *args, **kwargs):
    """
    Abstraction for deleting data
    """
    if headers is None:
        headers = config._header
    if params == None and data == None:
        res = requests.delete(endpoint, headers=headers)
    elif params != None and data == None:
        res = requests.delete(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = requests.delete(endpoint, headers=headers,
                              data=json.dumps(data))
    elif params != None and data != None:
        res = requests.delete(endpoint, headers=headers,
                              params=params, data=json.dumps(data=data))
    try:
        status_code = res.status_code
    except:
        status_code = {'error': 'Request Error'}
    return status_code


@adobeio_auth._checkToken
def _putData(endpoint: str, params: dict = None, data=None, headers: dict = None, *args, **kwargs):
    """
    Abstraction for deleting data
    """
    if headers is None:
        headers = config._header
    if params != None and data == None:
        res = requests.put(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = requests.put(endpoint, headers=headers,
                           data=json.dumps(data))
    elif params != None and data != None:
        res = requests.put(endpoint, headers=headers,
                           params=params, data=json.dumps(data=data))
    try:
        status_code = res.json()
    except:
        status_code = {'error': 'Request Error'}
    return status_code
