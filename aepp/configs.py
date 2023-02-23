import json
import os
from pathlib import Path
from typing import Optional
import json

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
    **kwargs,
) -> None:
    """
    This function will create a 'config_admin.json' file where you can store your access data.
    Arguments:
        destination : OPTIONAL : if you wish to save the file at a specific location.
        sandbox : OPTIONAL : You can directly set your sandbox name in this parameter.
        verbose : OPTIONAL : set to true, gives you a print stateent where is the location.
    """
    json_data: dict = {
        "org_id": "<orgID>",
        "client_id": "<client_id>",
        "tech_id": "<something>@techacct.adobe.com",
        "secret": "<YourSecret>",
        "pathToKey": "<path/to/your/privatekey.key>",
        "sandbox-name": sandbox,
        "environment": environment
    }
    if ".json" not in destination:
        destination: str = f"{destination}.json"
    with open(destination, "w") as cf:
        cf.write(json.dumps(json_data, indent=4))
    if verbose:
        print(
            f" file created at this location : {os.getcwd()}{os.sep}config_analytics.json"
        )


def importConfigFile(path: str=None,connectInstance:bool=False) -> None:
    """Reads the file denoted by the supplied `path` and retrieves the configuration information
    from it.

    Arguments:
        path: REQUIRED : path to the configuration file. Can be either a fully-qualified or relative.
        connectInstance : OPTIONAL : If you want to return an instance of the ConnectObject class

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
    with open(config_file_path, "r") as file:
        provided_config = json.load(file)
        provided_keys = provided_config.keys()
        if "api_key" in provided_keys:
            ## old naming for client_id
            client_id = provided_config["api_key"]
        elif "client_id" in provided_keys:
            client_id = provided_config["client_id"]
        else:
            raise RuntimeError(
                f"Either an `api_key` or a `client_id` should be provided."
            )
        myInstance = configure(
            org_id=provided_config["org_id"],
            tech_id=provided_config["tech_id"],
            secret=provided_config["secret"],
            path_to_key=provided_config["pathToKey"],
            client_id=client_id,
            sandbox=provided_config.get("sandbox-name", "prod"),
            connectInstance=connectInstance,
            environment=provided_config.get("environment", "prod")
        )
        if connectInstance:
            return myInstance


def configure(
    org_id: str = None,
    tech_id: str = None,
    secret: str = None,
    client_id: str = None,
    path_to_key: str = None,
    private_key: str = None,
    sandbox: str = "prod",
    connectInstance: bool = False,
    environment: str = "prod"
):
    """Performs programmatic configuration of the API using provided values.
    Arguments:
        org_id : REQUIRED : Organization ID
        tech_id : REQUIRED : Technical Account ID
        secret : REQUIRED : secret generated for your connection
        client_id : REQUIRED : The client_id (old api_key) provided by the JWT connection.
        path_to_key : REQUIRED : If you have a file containing your private key value.
        private_key : REQUIRED : If you do not use a file but pass a variable directly.
        sandbox : OPTIONAL : If not provided, default to prod
        connectInstance : OPTIONAL : If you want to return an instance of the ConnectObject class
        environment : OPTIONAL : If not provided, default to prod
    """
    if not org_id:
        raise ValueError("`org_id` must be specified in the configuration.")
    if not client_id:
        raise ValueError("`client_id` must be specified in the configuration.")
    if not tech_id:
        raise ValueError("`tech_id` must be specified in the configuration.")
    if not secret:
        raise ValueError("`secret` must be specified in the configuration.")
    if not path_to_key and not private_key:
        raise ValueError(
            "`pathToKey` or `private_key` must be specified in the configuration."
        )
    config_object["org_id"] = org_id
    header["x-gw-ims-org-id"] = org_id
    config_object["client_id"] = client_id
    header["x-api-key"] = client_id
    config_object["tech_id"] = tech_id
    config_object["secret"] = secret
    config_object["pathToKey"] = path_to_key
    config_object["private_key"] = private_key
    config_object["sandbox"] = sandbox
    header["x-sandbox-name"] = sandbox

    # ensure we refer to the right environment endpoints
    config_object["environment"] = environment
    if environment == "prod":
        endpoints["global"] = "https://platform.adobe.io"
        config_object["imsEndpoint"] = "https://ims-na1.adobelogin.com"
    else:
        endpoints["global"] = f"https://platform-{environment}.adobe.io"
        config_object["imsEndpoint"] = "https://ims-na1-stg1.adobelogin.com"
    endpoints["streaming"]["inlet"] = f"{endpoints['global']}/data/core/edge"
    config_object["tokenEndpoint"] = f"{config_object['imsEndpoint']}/ims/exchange/jwt"

    # ensure the reset of the state by overwriting possible values from previous import.
    config_object["date_limit"] = 0
    config_object["token"] = ""
    if connectInstance:
        myInstance = ConnectObject(
            org_id=org_id,
            tech_id=tech_id,
            secret=secret,
            client_id=client_id,
            path_to_key = path_to_key,
            private_key = private_key,
            sandbox=sandbox
        )
        return myInstance


def get_private_key_from_config(config: dict) -> str:
    """
    Returns the private key directly or read a file to return the private key.
    """
    private_key = config.get("private_key")
    if private_key is not None:
        return private_key
    private_key_path = find_path(config["pathToKey"])
    if private_key_path is None:
        raise FileNotFoundError(
            f'Unable to find the private key under path `{config["pathToKey"]}`.'
        )
    with open(Path(private_key_path), "r") as f:
        private_key = f.read()
    return private_key


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
            path_to_key: str = None,
            private_key: str = None,
            sandbox: str = "prod",
            **kwargs)->None:
        """
        Take a config object and save the configuration directly in the instance of the class.
        """
        self.header = {"Accept": "application/json",
          "Content-Type": "application/json",
          "Authorization": "",
          "x-api-key": client_id,
          "x-gw-ims-org-id": org_id,
          "x-sandbox-name": sandbox
          }
        self.org_id = org_id
        self.tech_id = tech_id
        self.client_id = client_id
        self.secret = secret
        self.pathToKey = path_to_key
        self.privateKey = private_key
        self.sandbox = sandbox
        self.token = ""
        self.__configObject__ = {
            "org_id": self.org_id,
            "client_id": self.client_id,
            "tech_id": self.tech_id,
            "pathToKey": self.pathToKey,
            "secret": self.secret,
            "date_limit" : 0,
            "sandbox": self.sandbox,
            "token": "",
            "tokenEndpoint" : "https://ims-na1.adobelogin.com/ims/exchange/jwt"
        }
    
    def connect(self)->None:
        """
        Generate a token and provide a connector instance in that class.
        """
        self.connector = connector.AdobeRequest(self.__configObject__,self.header)
        self.token = self.connector.token
    
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