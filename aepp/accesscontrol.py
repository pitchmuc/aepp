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
from .configs import ConnectObject
from typing import Union

class AccessControl:
    """
    Access Control API endpoints.
    Complete documentation is available:
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/access-control.yaml
    """

    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict =aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ) -> None:
        """
        Instantiate the access controle API wrapper.
        Arguments:
            config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
            loggingObject : OPTIONAL : logging object to log messages.
        kwargs :
            header options
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
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.endpoint = (
            aepp.config.endpoints["global"] + aepp.config.endpoints["access"]
        )

    def getReferences(self) -> dict:
        """
        List all available permission names and resource types.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getReferences")
        path = "/acl/reference"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def postEffectivePolicies(self, listElements: list = None):
        """
        List all effective policies for a user on given resources within a sandbox.
        Arguments:
            listElements : REQUIRED : List of resource urls. Example url : /resource-types/{resourceName} or /permissions/{highLevelPermissionName}
        """
        if type(listElements) != list:
            raise TypeError("listElements should be a list of elements")
        if self.loggingEnabled:
            self.logger.debug(f"Starting postEffectivePolicies")
        path = "/acl/effective-policies"
        res = self.connector.postData(
            self.endpoint + path, data=listElements, headers=self.header
        )
        return res
