#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

# internal library
import aepp
from aepp import connector
import logging
from copy import deepcopy
from typing import Union
from .configs import ConnectObject


class Sensei:
    """
    This module is based on the Sensei Machine Learning API from Adobe Experience Platform.
    You can find more documentation on the endpoints here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/
    """

    # logging capability
    loggingEnabled = False
    logger = None

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ) -> None:
        """
        Initialize the class with the config header used.
        Arguments:
            loggingObject : OPTIONAL : logging object to log messages.
            config : OPTIONAL : config object in the config module.
            header : OPTIONAL : header object  in the config module.
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
            logger=self.logger,
        )
        self.header = self.connector.header
        self.header[
            "Accept"
        ] = "application/vnd.adobe.platform.sensei+json;profile=mlInstanceListing.v1.json"
        self.header.update(**kwargs)
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.endpoint = (
            aepp.config.endpoints["global"] + aepp.config.endpoints["sensei"]
        )

    def getEngines(self, limit: int = 25, **kwargs) -> list:
        """
        Return the list of all engines.
        Arguments:
            limit : OPTIONAL : number of element per requests
        kwargs:
            property : filtering, example value "name==test."
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getEngines")
        path = "/engines"
        params = {"limit": limit}
        if kwargs.get("property", False) != False:
            params["property"] = kwargs.get("property", "")
        res = self.connector.getData(
            self.endpoint + path, headers=self.header, params=params
        )
        data = res["children"]
        return data

    def getEngine(self, engineId: str = None) -> dict:
        """
        return a specific engine information based on its id.
        Arguments:
            engineId : REQUIRED : the engineId to return.
        """
        if engineId is None:
            raise Exception("require an engineId parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getEngine")
        path = f"/engines/{engineId}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def getDockerRegistery(self) -> dict:
        """
        Return the docker registery information.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDockerRegistery")
        path = "/engines/dockerRegistry"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def deleteEngine(self, engineId: str = None) -> str:
        """
        Delete an engine based on the id passed.
        Arguments:
            engineId : REQUIRED : Engine ID to be deleted.
        """
        if engineId is None:
            raise Exception("require an engineId parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteEngine")
        path = f"/engines/{engineId}"
        res = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res

    def getMLinstances(self, limit: int = 25) -> list:
        """
        Return a list of all of the ml instance
        Arguments:
            limit : OPTIONAL : number of elements retrieved.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMLinstances")
        path = "/mlInstances"
        params = {"limit": limit}
        res = self.connector.getData(
            self.endpoint + path, headers=self.header, params=params
        )
        data = res["children"]
        return data

    def createMLinstances(
        self, name: str = None, engineId: str = None, description: str = None
    ):
        """
        Create a ML instance with the name and instanceId provided.
        Arguments:
            name : REQUIRED : name of the ML instance
            engineId : REQUIRED : engine attached to the ML instance
            description : OPTIONAL : description of the instance.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createMLinstances")
        path = "/mlInstances"
        privateHeader = deepcopy(self.header)
        privateHeader[
            "Content"
        ] = "application/vnd.adobe.platform.sensei+json;profile=mlInstanceListing.v1.json"
        if name is None and engineId is None:
            raise Exception("Requires a name and an egineId")
        body = {"name": name, "engineId": engineId, "description": description}
        res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, data=body
        )
        return res
