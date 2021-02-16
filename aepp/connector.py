## Internal modules
from aepp import config, configs

## External module
import json
import os
from typing import Dict, Optional, Union
from copy import deepcopy
import time
import requests
from pathlib import Path
import jwt

class AdobeRequest:
    """
    Handle request to Audience Manager and taking care that the request have a valid token set each time.
    """

    def __init__(self, config_object: dict = config.config_object, header: dict = config.header, verbose: bool = False, retry: int = 0,**kwargs)->None:
        """
        Set the connector to be used for handling request to AAM
        Arguments:
            config_object : OPTIONAL : Require the importConfig file to have been used.
            header : OPTIONAL : Header that you are already using.
            verbose : OPTIONAL : display comment while running
            retry : OPTIONAL : When GET request fails, if set to an int, it will retry this number of time 
        """
        if config_object['org_id'] == "":
            raise Exception(
                'You have to upload the configuration file with importConfigFile or configure method.')
        self.config = deepcopy(config_object)
        self.header = deepcopy(header)
        self.retry = retry
        if self.config['token'] == "" or time.time() > self.config['date_limit']:
            if 'aepScope' in kwargs.keys() and "privacyScope" in kwargs.keys():
                token_with_expiry = self.get_token_and_expiry_for_config(config=self.config, verbose=verbose,aepScope=kwargs.get('aepScope'),privacyScope=kwargs.get('privacyScope'))
                self.token = token_with_expiry['token']
                self.config['date_limit'] = time.time() + token_with_expiry['expiry'] / 1000 - 500
                self.header.update({'Authorization': f'Bearer {self.token}'})
            else:
                token_with_expiry = self.get_token_and_expiry_for_config(config=self.config, verbose=verbose,aepScope=kwargs.get('aepScope'),privacyScope=kwargs.get('privacyScope'))
                self.token = token_with_expiry['token']
                self.config['date_limit'] = time.time() + token_with_expiry['expiry'] / 1000 - 500
                self.header.update({'Authorization': f'Bearer {self.token}'})
    
    def _find_path(self,path: str) -> Optional[Path]:
        """Checks if the file denoted by the specified `path` exists and returns the Path object
        for the file.

        If the file under the `path` does not exist and the path denotes an absolute path, tries
        to find the file by converting the absolute path to a relative path.

        If the file does not exist with either the absolute and the relative path, returns `None`.
        """
        if Path(path).exists():
            return Path(path)
        elif path.startswith('/') and Path('.' + path).exists():
            return Path('.' + path)
        elif path.startswith('\\') and Path('.' + path).exists():
            return Path('.' + path)
        else:
            return None

    def get_token_and_expiry_for_config(self, config: dict, verbose: bool = False, save: bool = False, **kwargs) ->Dict[str, str]:
        """
        Retrieve the token by using the information provided by the user during the import importConfigFile function.
        ArgumentS :
            verbose : OPTIONAL : Default False. If set to True, print information.
            save : OPTIONAL : Default False. If set to True, save the toke in the .
        """
        private_key = configs.get_private_key_from_config(config)
        header_jwt = {
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded'
        }
        now_plus_24h = int(time.time()) + 24 * 60 * 60
        jwt_payload = {
            'exp': now_plus_24h,
            'iss': config['org_id'],
            'sub': config['tech_id'],
            "https://ims-na1.adobelogin.com/s/ent_dataservices_sdk": True,
            'aud': f'https://ims-na1.adobelogin.com/c/{config["client_id"]}'
        }
        #privacy topic
        if kwargs.get("privacyScope", False):
            jwt_payload["https://ims-na1.adobelogin.com/s/ent_gdpr_sdk"] = True
        if kwargs.get("aepScope", True)==False:
            del jwt_payload["https://ims-na1.adobelogin.com/s/ent_dataservices_sdk"]
        encoded_jwt = self._get_jwt(payload=jwt_payload, private_key=private_key)

        payload = {
            'client_id': config['client_id'],
            'client_secret': config['secret'],
            'jwt_token': encoded_jwt
        }
        response = requests.post(config['tokenEndpoint'], headers=header_jwt, data=payload)
        json_response = response.json()
        try:
            token = json_response['access_token']
        except KeyError:
            print('Issue retrieving token')
            print(json_response)
        expiry = json_response['expires_in'] -500
        if save:
            with open('token.txt', 'w') as f:
                f.write(token)
            print(f'token has been saved here: {os.getcwd()}{os.sep}token.txt')
        if verbose:
            print('token valid till : ' + time.ctime(time.time() + expiry / 1000))
        return {'token': token, 'expiry': expiry}


    def _get_jwt(self,payload: dict, private_key: str) -> str:
        """
        Ensure that jwt enconding return the same type (str) as versions < 2.0.0 returned bytes and >2.0.0 return strings. 
        """
        token: Union[str, bytes] = jwt.encode(payload, private_key, algorithm='RS256')
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token

    def _checkingDate(self)->None:
        """
        Checking if the token is still valid
        """
        now = time.time()
        if now > self.config['date_limit']:
            token_with_expiry = self.get_token_and_expiry_for_config(config=self.config)
            token = token_with_expiry['token']
            self.config['token'] = token
            self.header.update({'Authorization': f'Bearer {token}'})
            self.config['date_limit'] = time.time() + token_with_expiry['expiry'] / 1000 - 500
    
    def updateSandbox(self,sandbox:str)->None:
        """
        Update the sandbox used for the request
        Arguments:
            sandbox : REQUIRED : the sandbox to use for the requests
        """
        if not sandbox:
            raise Exception("require a sandbox")
        self.header["x-sandbox-name"] = sandbox


    def getData(self, endpoint: str, params: dict = None, data: dict = None, headers: dict = None, *args, **kwargs):
        """
        Abstraction for getting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if params == None and data == None:
            res = requests.get(
                endpoint, headers=headers)
        elif params != None and data == None:
            res = requests.get(
                endpoint, headers=headers, params=params)
        elif params == None and data != None:
            res = requests.get(
                endpoint, headers=headers, data=data)
        elif params != None and data != None:
            res = requests.get(endpoint, headers=headers,
                                            params=params, data=data)
        try:
            res_json = res.json()
        except:
            if kwargs.get('verbose',False):
                print(res.text)
            res_json = {'error': 'Request Error'}
            if self.retry > 0:
                for each in range(self.retry):
                    if 'error' in res_json.keys():
                        time.sleep(5)
                        res_json = self.getData(endpoint,params,data,headers,**kwargs)
        return res_json

    def headData(self,endpoint: str, params: dict = None, headers: dict = None,*args, **kwargs):
        """
        Abstraction for the head method.
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if params is None:
            res = requests.head(endpoint, headers=headers)
        if params is not None:
            res = requests.head(endpoint, headers=headers, params=params)
        try:
            res_json = res.json()
        except:
            if kwargs.get('verbose',False):
                print(res.text)
            res_json = {'error': 'Request Error'}
        return res_json
        

    def postData(self, endpoint: str, params: dict = None, data: dict = None, bytesData : bytes =None, headers: dict = None, * args, **kwargs):
        """
        Abstraction for posting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if params == None and data == None:
            res = requests.post(
                endpoint, headers=headers)
        elif params != None and data == None:
            res = requests.post(
                endpoint, headers=headers, params=params)
        elif params == None and data != None:
            res = requests.post(endpoint, headers=headers,
                                             data=json.dumps(data))
        elif params != None and data != None:
            res = requests.post(endpoint, headers=headers,
                                             params=params, data=json.dumps(data))
        elif bytesData != None :
            res = requests.post(endpoint, headers=headers,
                                             params=params, data=bytesData)
        try:
            res_json = res.json()
        except:
            if kwargs.get('verbose',False):
                print(res.text)
            res_json = {'error': 'Request Error'}
        return res_json

    def patchData(self, endpoint: str, params: dict = None, data=None, headers: dict = None, *args, **kwargs):
        """
        Abstraction for deleting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if params != None and data == None:
            res = requests.patch(
                endpoint, headers=headers, params=params)
        elif params == None and data != None:
            res = requests.patch(endpoint, headers=headers,
                                              data=json.dumps(data))
        elif params != None and data != None:
            res = requests.patch(endpoint, headers=headers,
                                              params=params, data=json.dumps(data=data))
        try:
            status_code = res.json()
        except:
            if kwargs.get('verbose',False):
                print(res.text)
            status_code = {'error': 'Request Error'}
        return status_code

    def putData(self, endpoint: str, params: dict = None, data=None, headers: dict = None, *args, **kwargs):
        """
        Abstraction for deleting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if params != None and data == None:
            res = requests.put(
                endpoint, headers=headers, params=params)
        elif params == None and data != None:
            res = requests.put(endpoint, headers=headers,
                                            data=json.dumps(data))
        elif params != None and data != None:
            res = requests.put(endpoint, headers=headers,
                                            params=params, data=json.dumps(data=data))
        try:
            status_code = res.json()
        except:
            if kwargs.get('verbose',False):
                print(res.text)
            status_code = {'error': 'Request Error'}
        return status_code

    def deleteData(self, endpoint: str, params: dict = None, headers: dict = None, *args, **kwargs):
        """
        Abstraction for deleting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if params == None:
            res = requests.delete(
                endpoint, headers=headers)
        elif params != None:
            res = requests.delete(
                endpoint, headers=headers, params=params)
        try:
            status_code = res.status_code
        except:
            if kwargs.get('verbose',False):
                print(res.text)
            status_code = {'error': 'Request Error'}
        return status_code
