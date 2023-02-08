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

    loggingEnabled = False

    def __init__(
        self,
        config_object: dict = config.config_object,
        header: dict = config.header,
        verbose: bool = False,
        loggingEnabled: bool = False,
        logger: object = None,
        retry: int = 0,
        **kwargs,
    ) -> None:
        """
        Set the connector to be used for handling request to AAM
        Arguments:
            config_object : OPTIONAL : Require the importConfig file to have been used.
            header : OPTIONAL : Header that you are already using.
            verbose : OPTIONAL : display comment while running
            loggingEnabled : OPTIONAL : if the logging is enable for that instance.
            logger : OPTIONAL : instance of the logger created
            retry : OPTIONAL : When GET request fails, if set to an int, it will retry this number of time
        """
        if config_object["org_id"] == "":
            raise Exception(
                "You have to upload the configuration file with importConfigFile or configure method."
            )
        self.config = deepcopy(config_object)
        self.header = deepcopy(header)
        self.loggingEnabled = loggingEnabled
        self.logger = logger
        self.retry = retry
        if self.config["token"] == "" or time.time() > self.config["date_limit"]:
            if "aepScope" in kwargs.keys() and "privacyScope" in kwargs.keys():
                token_with_expiry = self.get_token_and_expiry_for_config(
                    config=self.config,
                    verbose=verbose,
                    aepScope=kwargs.get("aepScope"),
                    privacyScope=kwargs.get("privacyScope"),
                )
                self.token = token_with_expiry["token"]
                self.config["token"] = self.token
                self.config["date_limit"] = (
                    time.time() + token_with_expiry["expiry"] / 1000 - 500
                )
                self.header.update({"Authorization": f"Bearer {self.token}"})
            else:
                token_with_expiry = self.get_token_and_expiry_for_config(
                    config=self.config,
                    verbose=verbose,
                    aepScope=kwargs.get("aepScope"),
                    privacyScope=kwargs.get("privacyScope"),
                )
                self.token = token_with_expiry["token"]
                self.config["token"] = self.token
                self.config["date_limit"] = (
                    time.time() + token_with_expiry["expiry"] / 1000 - 500
                )
                self.header.update({"Authorization": f"Bearer {self.token}"})

    def _find_path(self, path: str) -> Optional[Path]:
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

    def get_token_and_expiry_for_config(
        self, config: dict, verbose: bool = False, save: bool = False, **kwargs
    ) -> Dict[str, str]:
        """
        Retrieve the token by using the information provided by the user during the import importConfigFile function.
        ArgumentS :
            verbose : OPTIONAL : Default False. If set to True, print information.
            save : OPTIONAL : Default False. If set to True, save the toke in the .
        """
        private_key = configs.get_private_key_from_config(config)
        header_jwt = {
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded",
        }
        now_plus_24h = int(time.time()) + 24 * 60 * 60
        jwt_payload = {
            "exp": now_plus_24h,
            "iss": config["org_id"],
            "sub": config["tech_id"],
            f"{self.config['imsEndpoint']}/s/ent_dataservices_sdk": True,
            "aud": f'{self.config["imsEndpoint"]}/c/{config["client_id"]}',
        }
        # privacy topic
        if kwargs.get("privacyScope", False):
            jwt_payload[f"{self.config['imsEndpoint']}/s/ent_gdpr_sdk"] = True
        if kwargs.get("aepScope", True) == False:
            del jwt_payload[f"{self.config['imsEndpoint']}/s/ent_dataservices_sdk"]
        encoded_jwt = self._get_jwt(payload=jwt_payload, private_key=private_key)

        payload = {
            "client_id": config["client_id"],
            "client_secret": config["secret"],
            "jwt_token": encoded_jwt,
        }
        response = requests.post(
            config["tokenEndpoint"], headers=header_jwt, data=payload
        )
        json_response = response.json()
        try:
            self.token = json_response["access_token"]
            self.config["token"] = self.token
        except KeyError:
            print("Issue retrieving token")
            print(json_response)
        expiry = json_response["expires_in"] - 500
        if save:
            with open("token.txt", "w") as f:
                f.write(self.token)
            print(f"token has been saved here: {os.getcwd()}{os.sep}token.txt")
        if self.loggingEnabled:
            self.logger.debug(f"token retrieved: {self.token}")
        if verbose:
            print("token valid till : " + time.ctime(time.time() + expiry / 1000))
        if self.loggingEnabled:
            self.logger.debug(
                f"token valid till : {time.ctime(time.time() + expiry / 1000)}"
            )
        return {"token": self.token, "expiry": expiry}

    def _get_jwt(self, payload: dict, private_key: str) -> str:
        """
        Ensure that jwt enconding return the same type (str) as versions < 2.0.0 returned bytes and >2.0.0 return strings.
        """
        token: Union[str, bytes] = jwt.encode(payload, private_key, algorithm="RS256")
        if isinstance(token, bytes):
            return token.decode("utf-8")
        return token

    def _checkingDate(self) -> None:
        """
        Checking if the token is still valid
        """
        now = time.time()
        if now > self.config["date_limit"]:
            if self.loggingEnabled:
                self.logger.warning("token expired. Trying to retrieve a new token")
            token_with_expiry = self.get_token_and_expiry_for_config(config=self.config)
            self.token = token_with_expiry["token"]
            self.config["token"] = self.token
            if self.loggingEnabled:
                self.logger.info("new token retrieved : {self.token}")
            self.header.update({"Authorization": f"Bearer {self.token}"})
            self.config["date_limit"] = (
                time.time() + token_with_expiry["expiry"] / 1000 - 500
            )

    def updateSandbox(self, sandbox: str) -> None:
        """
        Update the sandbox used for the request
        Arguments:
            sandbox : REQUIRED : the sandbox to use for the requests
        """
        if not sandbox:
            raise Exception("require a sandbox")
        self.header["x-sandbox-name"] = sandbox

    def getData(
        self,
        endpoint: str,
        params: dict = None,
        data: dict = None,
        headers: dict = None,
        *args,
        **kwargs,
    ):
        """
        Abstraction for getting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if self.loggingEnabled:
            self.logger.debug(
                f"Start GET request to {endpoint} with header: {json.dumps(headers)}"
            )
        if params is None and data is None:
            res = requests.get(endpoint, headers=headers)
        elif params is not None and data is None:
            if self.loggingEnabled:
                self.logger.debug(f"params: {json.dumps(params)}")
            res = requests.get(endpoint, headers=headers, params=params)
        elif params is None and data is not None:
            if self.loggingEnabled:
                self.logger.debug(f"data: {json.dumps(data)}")
            res = requests.get(endpoint, headers=headers, data=data)
        elif params is not None and data is not None:
            if self.loggingEnabled:
                self.logger.debug(f"params: {json.dumps(params)}")
                self.logger.debug(f"data: {json.dumps(data)}")
            res = requests.get(endpoint, headers=headers, params=params, data=data)
        if self.loggingEnabled:
            self.logger.debug(f"endpoint used: {res.request.url}")
            self.logger.debug(f"params used: {params}")
        try:
            if kwargs.get("format", "json") == "json":
                res_json = res.json()
            if kwargs.get("format", "json") == "txt":
                res_json = res.text
            elif kwargs.get("format", "json") == "raw":
                res_json = res
            else:
                res_json = res.json()
        except:
            if kwargs.get("verbose", False):
                print(res.text)
            if self.loggingEnabled:
                self.logger.warning(f"error: {res.text}")
            res_json = {"error": "Request Error - could not generate json"}
            if self.retry > 0:
                if self.loggingEnabled:
                    self.logger.info(f"starting retry: {self.retry} to do")
                for each in range(self.retry):
                    if "error" in res_json.keys():
                        time.sleep(5)
                        res_json = self.getData(
                            endpoint, params, data, headers, **kwargs
                        )
        try:  ## sometimes list is being returned
            if type(res_json) == dict:
                if "errorMessage" in res_json.keys():
                    if self.loggingEnabled:
                        self.logger.error(
                            f"GET method failed: {res.status_code}, {res['errorMessage']}"
                        )
                    print(f"status code : {res.status_code}")
                    print(f"error message : {res['errorMessage']}")
        except:
            pass
        return res_json

    def headData(
        self, endpoint: str, params: dict = None, headers: dict = None, *args, **kwargs
    ):
        """
        Abstraction for the head method.
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if self.loggingEnabled:
            self.logger.debug(
                f"Start GET request to {endpoint} with header: {json.dumps(headers)}"
            )
        if params is None:
            res = requests.head(endpoint, headers=headers)
        if params is not None:
            res = requests.head(endpoint, headers=headers, params=params)
        try:
            res_header = res.headers()
        except:
            if kwargs.get("verbose", False):
                print("error generating the JSON response")
                print(f"status: {res.status_code}")
                print(res.text)
            if res.status_code != 200:
                res_header = res.headers()
            else:
                res_header = {}
        return res_header

    def postData(
        self,
        endpoint: str,
        params: dict = None,
        data: dict = None,
        bytesData: bytes = None,
        headers: dict = None,
        *args,
        **kwargs,
    ):
        """
        Abstraction for posting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if self.loggingEnabled:
            self.logger.debug(
                f"Start POST request to {endpoint} with header: {json.dumps(headers)}"
            )
        if params is None and data is None:
            res = requests.post(endpoint, headers=headers)
        elif params is not None and data is None:
            if self.loggingEnabled:
                self.logger.debug(f"params: {json.dumps(params)}")
            res = requests.post(endpoint, headers=headers, params=params)
        elif params is None and data is not None:
            if self.loggingEnabled:
                self.logger.debug(f"data: {json.dumps(data)}")
            res = requests.post(endpoint, headers=headers, data=json.dumps(data))
        elif params is not None and data is not None:
            if self.loggingEnabled:
                self.logger.debug(f"params: {json.dumps(params)}")
                self.logger.debug(f"data: {json.dumps(data)}")
            res = requests.post(
                endpoint, headers=headers, params=params, data=json.dumps(data)
            )
        elif bytesData is not None:
            if self.loggingEnabled:
                self.logger.debug(f"bytes data used")
            res = requests.post(
                endpoint, headers=headers, params=params, data=bytesData
            )
        try:
            formatUse = kwargs.get("format", "json")
            if self.loggingEnabled:
                self.logger.debug(f"format used: {formatUse}")
            if formatUse == "json":
                res_json = res.json()
            elif formatUse == "txt":
                res_json = res.text
            elif formatUse == "raw":
                res_json = res
            else:
                res_json = res.json()
        except:
            if kwargs.get("verbose", False):
                print("error generating the JSON response")
                print(f"status: {res.status_code}")
                print(res.text)
            if res.status_code != 200:
                try:
                    res_json = res.json()
                except:
                    res_json = {"error": "Request Error - could not generate JSON"}
            else:
                res_json = {}
        try:  ## sometimes list is being returned
            if "errorMessage" in res_json.keys():
                print(f"status code : {res.status_code}")
        except:
            pass
        return res_json

    def patchData(
        self,
        endpoint: str,
        params: dict = None,
        data=None,
        headers: dict = None,
        *args,
        **kwargs,
    ):
        """
        Abstraction for deleting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if self.loggingEnabled:
            self.logger.debug(
                f"Start PATCH request to {endpoint} with header: {json.dumps(headers)}"
            )
        if params is not None and data is None:
            if self.loggingEnabled:
                self.logger.debug(f"params: {json.dumps(params)}")
            res = requests.patch(endpoint, headers=headers, params=params)
        elif params is None and data is not None:
            if self.loggingEnabled:
                self.logger.debug(f"data: {json.dumps(data)}")
            res = requests.patch(endpoint, headers=headers, data=json.dumps(data))
        elif params is not None and data is not None:
            if self.loggingEnabled:
                self.logger.debug(f"params: {json.dumps(params)}")
                self.logger.debug(f"data: {json.dumps(data)}")
            res = requests.patch(
                endpoint, headers=headers, params=params, data=json.dumps(data)
            )
        try:
            res_json = res.json()
        except:
            if kwargs.get("verbose", False):
                print("error generating the JSON response")
                print(f"status: {res.status_code}")
                print(res.text)
            if self.loggingEnabled:
                self.logger.error(
                    f"error with the response {res.status_code}: {res.text}"
                )
            if res.status_code != 200:
                try:
                    res_json = res.json()
                except:
                    res_json = {"error": "Request Error - could not generate JSON"}
            else:
                res_json = {}
        return res_json

    def putData(
        self,
        endpoint: str,
        params: dict = None,
        data=None,
        headers: dict = None,
        *args,
        **kwargs,
    ):
        """
        Abstraction for deleting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if self.loggingEnabled:
            self.logger.debug(
                f"Start PUT request to {endpoint} with header: {json.dumps(headers)}"
            )
        if params is not None and data is None:
            if self.loggingEnabled:
                self.logger.debug(f"params: {json.dumps(params)}")
            res = requests.put(endpoint, headers=headers, params=params)
        elif params is None and data is not None:
            if self.loggingEnabled:
                self.logger.debug(f"data: {json.dumps(data)}")
            res = requests.put(endpoint, headers=headers, data=json.dumps(data))
        elif params is not None and data is not None:
            if self.loggingEnabled:
                self.logger.debug(f"params: {json.dumps(params)}")
                self.logger.debug(f"data: {json.dumps(data)}")
            res = requests.put(
                endpoint, headers=headers, params=params, data=json.dumps(data)
            )
        try:
            res_json = res.json()
        except:
            if kwargs.get("verbose", False):
                print("error generating the JSON response")
                print(f"status: {res.status_code}")
                print(res.text)
            if self.loggingEnabled:
                self.logger.error(
                    f"error with the response {res.status_code}: {res.text}"
                )
            if res.status_code != 200:
                res_json = {"error": res.text}
            else:
                res_json = {}
        return res_json

    def deleteData(
        self, endpoint: str, params: dict = None, headers: dict = None, *args, **kwargs
    ):
        """
        Abstraction for deleting data
        """
        self._checkingDate()
        if headers is None:
            headers = self.header
        if self.loggingEnabled:
            self.logger.debug(
                f"Start PUT request to {endpoint} with header: {json.dumps(headers)}"
            )
        if params is None:
            res = requests.delete(endpoint, headers=headers)
        elif params is not None:
            res = requests.delete(endpoint, headers=headers, params=params)
        try:
            status_code = res.status_code
            if status_code >= 400:
                if self.loggingEnabled:
                    self.logger.error(
                        f"error with the response {res.status_code}: {res.text}"
                    )
                return res.json()
        except:
            if kwargs.get("verbose", False):
                print(res.text)
            status_code = res.status_code
        return status_code
