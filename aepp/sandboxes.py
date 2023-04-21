#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

import aepp
from aepp import connector
import logging
from typing import Union
from .configs import ConnectObject


class Sandboxes:
    """
    A collection of methods to realize actions on the sandboxes.
    It comes from the sandbox API:
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/sandbox-api.yaml
    """

    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ):
        """
        Instantiate the sandbox class.
        Arguments:
            config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
            loggingObject : OPTIONAL : logging object to log messages.
        Additional kwargs will update the header.
        """
        if loggingObject is not None and sorted(
            ["level", "stream", "format", "filename", "file"]
        ) == sorted(list(loggingObject.keys())):
            self.loggingEnabled = True
            self.logger = logging.getLogger(f"{__name__}")
            self.logger.setLevel(loggingObject["level"])
            if type(loggingObject["format"]) == str:
                formatter = logging.Formatter(loggingObject["format"])
            elif type(loggingObject["format"]) == logging.Formatter:
                formatter = loggingObject["format"]
            if loggingObject["file"]:
                fileHandler = logging.FileHandler(loggingObject["filename"])
                fileHandler.setFormatter(formatter)
                self.logger.addHandler(fileHandler)
            if loggingObject["stream"]:
                streamHandler = logging.StreamHandler()
                streamHandler.setFormatter(formatter)
                self.logger.addHandler(streamHandler)
        if type(config) == dict: ## Supporting either default setup or passing a ConnectObject
            config = config
        elif type(config) == ConnectObject:
            header = config.getConfigHeader()
            config = config.getConfigObject()
        self.connector = connector.AdobeRequest(
            config=config,
            header=header,
            loggingEnabled=self.loggingEnabled,
            loggingObject=self.logger,
        )
        self.header = self.connector.header
        self.header.update(**kwargs)
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.endpoint = (
            aepp.config.endpoints["global"] + aepp.config.endpoints["sandboxes"]
        )

    def getSandboxes(self) -> list:
        """
        Return the list of all the sandboxes
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSandboxes")
        path = self.endpoint + "/sandboxes"
        res = self.connector.getData(path)
        data = res["sandboxes"]
        return data

    def getSandboxTypes(self) -> list:
        """
        Return the list of all the sandboxes types.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSandboxTyoes")
        path = self.endpoint + "/sandboxTypes"
        res = self.connector.getData(path)
        data = res["sandboxTypes"]
        return data

    def createSandbox(
        self, name: str = None, title: str = None, type_sandbox: str = "development"
    ) -> dict:
        """
        Create a new sandbox in your AEP instance.
        Arguments:
            name : REQUIRED : name of your sandbox
            title : REQUIRED : display name of your sandbox
            type_sandbox : OPTIONAL : type of your sandbox. default : development.
        """
        if name is None or title is None:
            raise Exception("name and title cannot be empty")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createSandbox")
        path = self.endpoint + "/sandboxes"
        data = {"name": name, "title": title, "type": type_sandbox}
        res = self.connector.postData(path, data=data)
        return res

    def getSandbox(self, name: str) -> dict:
        """
        retrieve a Sandbox information by name
        Argument:
            name : REQUIRED : name of Sandbox
        """
        if name is None:
            raise Exception("Expected a name as parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSandbox")
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.getData(path)
        return res

    def getSandboxId(self, name: str) -> str:
        """
        Retrieve the ID of a sandbox by name.
        Argument:
            name : REQUIRED : name of Sandbox
        """
        return self.getSandbox(name)["id"]

    def deleteSandbox(self, name: str) -> dict:
        """
        Delete a sandbox by its name.
        Arguments:
            name : REQUIRED : sandbox to be deleted.
        """
        if name is None:
            raise Exception("Expected a name as parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteSandbox")
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.deleteData(path)
        return res

    def resetSandbox(self, name: str) -> dict:
        """
        Reset a sandbox by its name. Sandbox will be empty.
        Arguments:
            name : REQUIRED : sandbox name to be deleted.
        """
        if name is None:
            raise Exception("Expected a sandbox name as parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting resetSandbox")
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.putData(path, data={'action':'reset'})
        return res

    def updateSandbox(self, name: str, action: dict = None) -> dict:
        """
        Update the Sandbox with the action provided.
        Arguments:
            name : REQUIRED : sandbox name to be updated.
            action : REQUIRED : dictionary defining the action to realize on that sandbox.
        """
        if name is None:
            raise Exception("Expected a sandbox name as parameter")
        if action is None or type(action) != dict:
            raise Exception("Expected a dictionary to pass the action")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateSandboxes")
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.patchData(path, data=action)
        return res
