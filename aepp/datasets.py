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
from copy import deepcopy
import logging
from typing import Union
from .configs import ConnectObject


class DataSets:
    """
    Class that provides methods to manage labels of datasets.
    A complete documentation ca be found here:
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/dataset-service.yaml
    """

    ## logging capability
    loggingEnabled = False
    logger = None

    REFERENCE_LABELS_CREATION = {
        "labels": [["C1", "C2"]],
        "optionalLabels": [
            {
                "option": {
                    "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
                    "contentType": "application/vnd.adobe.xed-full+json;version=1",
                    "schemaPath": "/properties/repositoryCreatedBy",
                },
                "labels": [["S1", "S2"]],
            }
        ],
    }

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ):
        """
        Instantiate the DataSet class.
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
            logger=self.logger,
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
            aepp.config.endpoints["global"] + aepp.config.endpoints["dataset"]
        )

    def getLabelSchemaTests(self, dataSetId: str = None) -> dict:
        """
        Return the labels assigned to a dataSet
        Argument:
            dataSetId : REQUIRED : the dataSet ID to retrieve the labels
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getLabels")
        path = f"/datasets/{dataSetId}/labels"
        res = self.connector.getData(self.endpoint + path)
        return res

    def headLabels(self, dataSetId: str = None) -> dict:
        """
        Return the head assigned to a dataSet
        Argument:
            dataSetId : REQUIRED : the dataSet ID to retrieve the head data
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting headLabels")
        path = f"/datasets/{dataSetId}/labels"
        res = self.connector.headData(self.endpoint + path)
        return res

    def deleteLabels(self, dataSetId: str = None, ifMatch: str = None) -> dict:
        """
        Delete the labels of a dataset.
        Arguments:
            dataSetId : REQUIRED : The dataset ID to delete the labels for.
            ifMatch : REQUIRED : the value is from the header etag of the headLabels. (use the headLabels method)
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        if ifMatch is None:
            raise ValueError("Require the ifMatch parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteLabels")
        path = f"/datasets/{dataSetId}/labels"
        privateHeader = deepcopy(self.header)
        privateHeader["If-Match"] = ifMatch
        res = self.connector.deleteData(self.endpoint + path, headers=privateHeader)
        return res

    def createLabels(self, dataSetId: str = None, data: dict = None) -> dict:
        """
        Assign labels to a dataset.
        Arguments:
            dataSetId : REQUIRED : The dataset ID to delete the labels for.
            data : REQUIRED : Dictionary setting the labels to be added.
                more info https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Datasets/postDatasetLabels
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        if data is None or type(data) != dict:
            raise ValueError("Require a dictionary to pass labels")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createLabels")
        path = f"/datasets/{dataSetId}/labels"
        res = self.connector.postData(self.endpoint + path, data=data)
        return res

    def updateLabels(
        self, dataSetId: str = None, data: dict = None, ifMatch: str = None
    ) -> dict:
        """
        Update the labels (PUT method)
            dataSetId : REQUIRED : The dataset ID to delete the labels for.
            data : REQUIRED : Dictionary setting the labels to be added.
                more info https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Datasets/postDatasetLabels
            ifMatch : REQUIRED : the value is from the header etag of the headLabels.(use the headLabels method)
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        if data is None or type(data) != dict:
            raise ValueError("Require a dictionary to pass labels")
        if ifMatch is None:
            raise ValueError("Require the ifMatch parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateLabels")
        path = f"/datasets/{dataSetId}/labels"
        privateHeader = deepcopy(self.header)
        privateHeader["If-Match"] = ifMatch
        res = self.connector.putData(
            self.endpoint + path, data=data, headers=privateHeader
        )
        return res
