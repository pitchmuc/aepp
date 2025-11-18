#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

import json
import os
from pathlib import Path
from typing import Optional
import json,time

# Non standard libraries
from .config import config_object, header, endpoints
from aepp import connector

def find_path(path: str) -> Optional[Path]:
    """Checks if the file denoted by the specified `path` exists and returns the Path object
    for the file.

    If the file under the `path` does not exist and the path denotes an absolute path, tries
    to find the file by converting the absolute path to a relative path.

    If the file does not exist with either the absolute and the relative path, returns `None`.
    """
    if Path(path).exists():
        return Path(path)
    elif path.startswith("/") and Path("." + path).exists():
        return Path("." + path)
    elif path.startswith("\\") and Path("." + path).exists():
        return Path("." + path)
    else:
        return None


def createConfigFile(
    destination: str = "config_aep_template.json",
    sandbox: str = "prod",
    environment: str = "prod",
    verbose: object = False,
    auth_type: str = "oauthV2",
    **kwargs,
) -> None:
    """
    This function will create a 'config_admin.json' file where you can store your access data.
    Arguments:
        destination : OPTIONAL : if you wish to save the file at a specific location.
        sandbox : OPTIONAL : You can directly set your sandbox name in this parameter.
        verbose : OPTIONAL : set to true, gives you a print stateent where is the location.
        auth_type : OPTIONAL : type of authentication, either "oauthV2" or "oauthV1". Default is oauthV2
    """
    json_data: dict = {
        "org_id": "<orgID>",
        "client_id": "<client_id>",
        "secret": "<YourSecret>",
        "sandbox-name": sandbox,
        "environment": environment
    }
    if auth_type == "oauthV2":
        json_data["scopes"] = "<scopes>"
    elif auth_type == "oauthV1":
        json_data["auth_code"] = "<auth_code>"
    else:
        raise ValueError("unsupported authentication type, currently only oauthV2 and oauthV1 are supported")
    if ".json" not in destination:
        destination: str = f"{destination}.json"
    with open(destination, "w") as cf:
        cf.write(json.dumps(json_data, indent=4))
    if verbose:
        print(
            f" file created at this location : {os.getcwd()}{os.sep}{destination}.json"
        )


def importConfigFile(
    path: str = None,
    connectInstance: bool = False,
    auth_type: str = None,
    sandbox:str = None,
    **kwargs
):
    """Reads the file denoted by the supplied `path` and retrieves the configuration information
    from it.

    Arguments:
        path: REQUIRED : path to the configuration file. Can be either a fully-qualified or relative.
        connectInstance : OPTIONAL : If you want to return an instance of the ConnectObject class
        auth_type : OPTIONAL : type of authentication, either "oauthV2" (default) or "oauthV1". Detected based on keys present in config file.
        sandbox : OPTIONAL : The sandbox to connect it.

    Example of path value.
    "config.json"
    "./config.json"
    "/my-folder/config.json"
    """
    if path is None:
        raise ValueError("require a path to a configuration file to be provided")
     
    config_file_path: Optional[Path] = find_path(path)
    if config_file_path is None:
        raise FileNotFoundError(
            f"Unable to find the configuration file under path `{path}`."
        )
    
    def get_case_insensitive_key(d, key):
        key_lower = key.lower()
        for k, v in d.items():
            if k.lower() == key_lower:
                return v
        return None

    with open(config_file_path, "r") as file:
        provided_config = json.load(file)
        provided_keys = [k.lower() for k in provided_config.keys()]
        
        client_id = get_case_insensitive_key(provided_config, "api_key") or get_case_insensitive_key(provided_config, "client_id")
        if client_id is None:
            raise RuntimeError(
                f"Either an `api_key` or a `client_id` should be provided."
            )
        if auth_type is None:
            if 'scopes' in provided_keys:
                auth_type = 'oauthV2'
            elif 'auth_code' in provided_keys:
                auth_type = 'oauthV1'
        
        args = {
            "org_id": get_case_insensitive_key(provided_config, "org_id"),
            "client_id": client_id,
            "secret": get_case_insensitive_key(provided_config, "secret") or get_case_insensitive_key(provided_config, "client_secret") or get_case_insensitive_key(provided_config, "client_secrets")[0],
            "sandbox": get_case_insensitive_key(provided_config, "sandbox-name") or "prod",
            "environment": get_case_insensitive_key(provided_config, "environment") or "prod",
            "connectInstance": connectInstance
        }
        
        if sandbox is not None:  # overriding sandbox from parameter
            args["sandbox"] = sandbox
        if auth_type == "oauthV2":
            scopes = get_case_insensitive_key(provided_config, "scopes")
            if type(scopes) == list:
                args["scopes"] = ",".join(scopes)
            else:
                args["scopes"] = scopes.replace(' ', '')
        elif auth_type == "oauthV1":
            args["auth_code"] = get_case_insensitive_key(provided_config, "auth_code")
        else:
            raise ValueError("unsupported authentication type, currently only oauth are supported")
        if kwargs.get('accesstoken','') != "":
            args["accesstoken"] = kwargs["accesstoken"]
        if kwargs.get('region','') != "":
            args["region"] = kwargs["region"]
        myInstance = configure(**args)
    if connectInstance:
        return myInstance


def configure(
    org_id: str = None,
    tech_id: str = None,
    secret: str = None,
    client_id: str = None,
    sandbox: str = "prod",
    connectInstance: bool = False,
    environment: str = "prod",
    scopes: str = None,
    auth_code:str=None,
    **kwargs
):
    """Performs programmatic configuration of the API using provided values.
    Arguments:
        org_id : REQUIRED : Organization ID
        tech_id : OPTIONAL : Technical Account ID
        secret : REQUIRED : secret generated for your connection
        client_id : REQUIRED : The client_id (old api_key)
        sandbox : OPTIONAL : If not provided, default to prod
        connectInstance : OPTIONAL : If you want to return an instance of the ConnectObject class
        environment : OPTIONAL : If not provided, default to prod
        scopes : OPTIONAL : The scope define in your project for your API connection. Oauth V2, for clients and customers.
        auth_code : OPTIONAL : If an authorization code is used directly instead of generating via OauthV2. Oauth V1 only, for adobe internal services.
    """
    if not org_id:
        raise ValueError("`org_id` must be specified in the configuration.")
    if not client_id:
        raise ValueError("`client_id` must be specified in the configuration.")
    if not secret and kwargs.get('accesstoken','') =="":
        raise ValueError("`secret` must be specified in the configuration.")
    if ((scopes is not None and auth_code is not None) or (scopes is None and auth_code is None)) and environment != "support":
        raise ValueError("either `scopes` needs to be specified or an `auth_code`")
    config_object["org_id"] = org_id
    header["x-gw-ims-org-id"] = org_id
    config_object["client_id"] = client_id
    header["x-api-key"] = client_id
    config_object["tech_id"] = tech_id
    config_object["secret"] = secret
    config_object["scopes"] = scopes
    config_object["auth_code"] = auth_code
    config_object["sandbox"] = sandbox
    header["x-sandbox-name"] = sandbox
    if kwargs.get('accesstoken','') != "":
        config_object["token"] = kwargs.get('accesstoken')
        config_object["date_limit"] = kwargs.get('accesstoken')
    # ensure we refer to the right environment endpoints
    config_object["environment"] = environment
    if environment == "prod":
        endpoints["global"] = "https://platform.adobe.io"
        config_object["imsEndpoint"] = "https://ims-na1.adobelogin.com"
    elif environment == "support":
        endpoints["global"] = kwargs.get('endpoint')
        config_object["imsEndpoint"] = "https://ims-na1.adobelogin.com"
    else:
        endpoints["global"] = f"https://platform-{environment}.adobe.io"
        config_object["imsEndpoint"] = "https://ims-na1-stg1.adobelogin.com"
    endpoints["streaming"]["inlet"] = f"{endpoints['global']}/data/core/edge"
    config_object["oauthTokenEndpointV1"] = f"{config_object['imsEndpoint']}/ims/token/v1"
    config_object["oauthTokenEndpointV2"] = f"{config_object['imsEndpoint']}/ims/token/v3"
    # ensure the reset of the state by overwriting possible values from previous import.
    now_plus_1h = int(time.time()) + 60 * 60
    config_object["token"] = kwargs.get('accesstoken','')
    config_object["date_limit"] = 0
    if config_object["token"] != "":
        config_object["date_limit"] = now_plus_1h
    if connectInstance:
        myInstance = ConnectObject(
            org_id=org_id,
            tech_id=tech_id,
            secret=secret,
            client_id=client_id,
            sandbox=sandbox,
            scopes=scopes,
            auth_code=auth_code,
            accesstoken=kwargs.get('accesstoken',''),
            date_limit=config_object["date_limit"],
            environment=environment,
            endpoint = kwargs.get('endpoint','')
        )
        return myInstance


def generateLoggingObject(level:str="WARNING",filename:str="aepp.log") -> dict:
    """
    Generates a dictionary for the logging object with basic configuration.
    You can find the information for the different possible values on the logging documentation.
        https://docs.python.org/3/library/logging.html
    Arguments:
        level : OPTIONAL : Level of the logger to display information (NOTSET, DEBUG,INFO,WARNING,EROR,CRITICAL)
            default WARNING
        filename : OPTIONAL : name of the file for debugging. default aepp.log
    Output:
        level : Level of the logger to display information (NOTSET, DEBUG,INFO,WARNING,EROR,CRITICAL)
        stream : If the logger should display print statements
        file : If the logger should write the messages to a file
        filename : name of the file where log are written
        format : format of the logs
    """
    myObject = {
        "level": level,
        "stream": True,
        "file": False,
        "format": "%(asctime)s::%(name)s::%(funcName)s::%(levelname)s::%(message)s::%(lineno)d",
        "filename": filename,
    }
    return myObject

class ConnectObject:
    """
    A connect Object class that keep tracks of the configuration loaded during the importConfigFile operation or during configure operation.
    
    """

    def __init__(self,
            org_id: str = None,
            tech_id: str = None,
            secret: str = None,
            client_id: str = None,
            scopes:str=None,
            sandbox: str = "prod",
            environment: str = "prod",
            accesstoken: str = "",
            date_limit:int = 0,
            auth_code:str=None,
            **kwargs)->None:
        """
        Take a config object and save the configuration directly in the instance of the class.
        """
        self.header = {"Accept": "application/json",
          "Content-Type": "application/json",
          "Authorization": "Bearer "+accesstoken,
          "x-api-key": client_id,
          "x-gw-ims-org-id": org_id,
          "x-sandbox-name": sandbox
          }
        ## setting environment prod vs non-prod for token generation
        if environment == "prod":
            self.globalEndpoint = "https://platform.adobe.io"
            self.imsEndpoint = "https://ims-na1.adobelogin.com"
        elif environment == "support":
            self.globalEndpoint = kwargs.get("endpoint","https://platform.adobe.io")
            self.imsEndpoint = "https://ims-na1.adobelogin.com"

        else:
            self.globalEndpoint = f"https://platform-{environment}.adobe.io"
            self.imsEndpoint = "https://ims-na1-stg1.adobelogin.com"
        self.streamInletEndpoint = f"{self.globalEndpoint}/data/core/edge"
        self.oauthEndpointV1 = f"{self.imsEndpoint}/ims/token/v1"
        self.oauthEndpointV2 = f"{self.imsEndpoint}/ims/token/v3"
        self.org_id = org_id
        self.tech_id = tech_id
        self.client_id = client_id
        self.secret = secret
        self.sandbox = sandbox
        self.scopes = scopes
        self.token = accesstoken
        self.date_limit = date_limit
        self.__configObject__ = {
            "org_id": self.org_id,
            "client_id": self.client_id,
            "tech_id": self.tech_id,
            "secret": self.secret,
            "date_limit" : date_limit,
            "sandbox": self.sandbox,
            "token": accesstoken,
            "imsEndpoint" : self.imsEndpoint,
            "oauthTokenEndpointV1" : self.oauthEndpointV1,
            "oauthTokenEndpointV2" : self.oauthEndpointV2,
            "scopes": self.scopes,
            "environment":environment
        }

    def __str__(self):
        return json.dumps({'class':'ConnectObject','sandbox':self.sandbox, 'token':self.token,'clientId':self.client_id,'orgId':self.org_id},indent=2)
    
    def __repr__(self):
        return json.dumps({'class':'ConnectObject','sandbox':self.sandbox, 'token':self.token,'clientId':self.client_id,'orgId':self.org_id},indent=2)

    def connect(self)->None:
        """
        Generate a token and provide a connector instance in that class.
        """
        self.connector = connector.AdobeRequest(self.__configObject__,self.header)
        self.token = self.connector.token
        self.header['Authorization'] = 'bearer '+self.token
        self.getData = self.connector.getData
        self.postData = self.connector.postData
        self.putData = self.connector.putData
        self.deleteData = self.connector.deleteData
        self.patchData = self.connector.patchData
    
    def getConfigObject(self)->dict:
        """
        Return the config object expected.
        """
        return self.__configObject__
    
    def getConfigHeader(self)->dict:
        """
        Return the default header
        """
        return self.header
    
    def setConfigHeader(self,header:dict=None)->dict:
        """
        Set the header used by default.
        Return the header set
        """
        if header is None:
            raise ValueError("Require a dictionary")
        self.header = header
        return self.header

    def setSandbox(self,sandbox:str=None)->dict:
        """
        Update the sandbox used.
        Return the whole config object.
        """
        if sandbox is None:
            return None
        self.sandbox = sandbox
        self.header["x-sandbox-name"] = sandbox
        self.__configObject__["sandbox"] = sandbox
        return self.getConfigObject()
