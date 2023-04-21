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
import pandas as pd
from typing import Union
import re
import logging
from .configs import ConnectObject


class DataPrep:
    """
    This class instanciate the data prep capability.
    The data prep is mostly use for the mapping service and you can find some documentation on this in the following part:
        https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/data-prep.yaml
        https://experienceleague.adobe.com/docs/experience-platform/data-prep/home.html
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
    ) -> None:
        """
            This will instantiate the Mapping class
            Arguments:
                config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
                header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
                loggingObject : OPTIONAL : logging object to log messages.
        kwargs:
            kwargs value will update the header
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
        # same endpoint than segmentation
        self.endpoint = (
            aepp.config.endpoints["global"] + aepp.config.endpoints["mapping"]
        )
        self.REFERENCE_MAPPING = {"sourceType": "", "source": "", "destination": ""}

    def getXDMBatchConversions(
        self,
        dataSetId: str = None,
        prop: str = None,
        batchId: str = None,
        status: str = None,
        limit: int = 100,
    ) -> dict:
        """
        Returns all XDM conversions
        Arguments:
            dataSetId : OPTIONAL : Destination dataSet ID to filter for.
            property : OPTIONAL : Filters for dataSetId, batchId and Status.
            batchId : OPTIONAL : batchId Filter
            status : OPTIONAL : status of the batch.
            limit : OPTIONAL : number of results to return (default 100)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getXDMBatchConversions")
        path = "/xdmBatchConversions"
        params = {"limit": limit}
        if dataSetId is not None:
            params["destinationDatasetId"] = dataSetId
        if prop is not None:
            params["property"] = prop
        if batchId is not None:
            params["sourceBatchId"] = batchId
        if status is not None:
            params["status"] = status
        res = self.connector.getData(self.endpoint + path, params=params)
        return res

    def getXDMBatchConversion(self, conversionId: str = None) -> dict:
        """
        Returns XDM Conversion info.
        Arguments:
            conversionId : REQUIRED : Conversion ID to be returned
        """
        if conversionId is None:
            raise ValueError("Require a conversion ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getXDMBatchConversion")
        path = f"/xdmBatchConversions/{conversionId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def getXDMBatchConversionActivities(self, conversionId: str = None) -> dict:
        """
        Returns activities for a XDM Conversion ID.
        Arguments:
            conversionId : REQUIRED : Conversion ID for activities to be returned
        """
        if conversionId is None:
            raise ValueError("Require a conversion ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getXDMBatchConversionActivities")
        path = f"/xdmBatchConversions/{conversionId}/activities"
        res = self.connector.getData(self.endpoint + path)
        return res

    def getXDMBatchConversionRequestActivities(
        self, requestId: str = None, activityId: str = None
    ) -> dict:
        """
        Returns conversion activities for given request
        Arguments:
            requestId : REQUIRED : the request ID to look for
            activityId : REQUIRED : the activity ID to look for
        """
        if requestId is None:
            raise ValueError("Require a request ID")
        if activityId is None:
            raise ValueError("Require a activity ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getXDMBatchConversionRequestActivities")
        path = f"/xdmBatchConversions/{requestId}/activities/{activityId}"
        res = self.connector.getData(self.endpoint + path + path)
        return res

    def createXDMConversion(
        self, dataSetId: str = None, batchId: str = None, mappingId: str = None
    ) -> dict:
        """
        Create a XDM conversion request.
        Arguments:
            dataSetId : REQUIRED : destination dataSet ID
            batchId : REQUIRED : Source Batch ID
            mappingSetId : REQUIRED : Mapping ID to be used
        """
        if dataSetId is None:
            raise ValueError("Require a destination dataSet ID")
        if batchId is None:
            raise ValueError("Require a source batch ID")
        if mappingId is None:
            raise ValueError("Require a mapping ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createXDMConversion")
        path = "/xdmBatchConversions"
        params = {
            "destinationDataSetId": dataSetId,
            "sourceBatchId": batchId,
            "mappingSetId": mappingId,
        }
        res = self.connector.getData(self.endpoint + path, params=params)
        return res

    def copyMappingRules(
        self, mapping: Union[dict, list] = None, tenantId: str = None
    ) -> list:
        """
        create a copy of the mapping based on the mapping information passed.
        Argument:
            mapping : REQUIRED : either the list of mapping or the dictionary returned from the getMappingSetMapping
            tenantid : REQUIRED : in case tenant is present, replace the existing one with new one.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting copyMapping")
        if tenantId.startswith("_") == False:
            tenantId = f"_{tenantId}"
        if mapping is None:
            raise ValueError("Require a mapping object")
        if type(mapping) == list:
            new_list = [
                {
                    "sourceType": map["sourceType"],
                    "source": map["source"],
                    "destination": re.sub(
                        "^_[\w]+\.", f"{tenantId}.", map["destination"]
                    ),
                }
                for map in mapping
            ]
            return new_list
        if type(mapping) == dict:
            if "mappings" in mapping.keys():
                mappings = mapping["mappings"]
                new_list = [
                    {
                        "sourceType": map["sourceType"],
                        "source": map["source"],
                        "destination": re.sub(
                            "^_[\w]+\.", f"{tenantId}.", map["destination"]
                        ),
                    }
                    for map in mappings
                ]
                return new_list
            else:
                print("Couldn't find a mapping information to copy")
                return None

    def cleanMappingRules(self, mapping: Union[dict, list] = None
    ) -> list:
        """
        create a clean copy of the mapping based on the mapping list information passed.
        Argument:
            mapping : REQUIRED : either the list of mapping or the dictionary returned from the getMappingSetMapping
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting copyMapping")
        if mapping is None:
            raise ValueError("Require a mapping object")
        if type(mapping) == list:
            new_list = [
                {
                    "sourceType": map["sourceType"],
                    "source": map["source"],
                    "destination":  map["destination"]
                }
                for map in mapping
            ]
            return new_list
        if type(mapping) == dict:
            if "mappings" in mapping.keys():
                mappings = mapping["mappings"]
                new_list = [
                    {
                        "sourceType": map["sourceType"],
                        "source": map["source"],
                        "destination": map["destination"]
                    }
                    for map in mappings
                ]
                return new_list
            else:
                print("Couldn't find a mapping information to clean")
                return None

    def getMappingSets(
        self, name: str = None, prop: str = None, limit: int = 100
    ) -> list:
        """
        Returns all mapping sets for given IMS Org Id
        Arguments:
            name : OPTIONAL : Filtering by name
            prop : OPTIONAL : property filter. Supported fields are: xdmSchema, status.
                Example : prop="status==success"
            limit : OPTIONAL : number of result to retun. Default 100.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMappingSets")
        params = {"limit": limit}
        if name is not None:
            params["name"] = name
        if prop is not None:
            params["property"] = prop
        path = "/mappingSets"
        res = self.connector.getData(self.endpoint + path, params=params)
        data = res["data"]
        return data

    def getMappingSuggestions(
        self, dataSetId: str = None, batchId: str = None, excludeUnmapped: bool = True
    ) -> dict:
        """
        Returns non-persisted mapping set suggestion for review
        Arguments:
            dataSetId : OPTIONAL : Id of destination DataSet. Must be a DataSet with schema.
            batchId : OPTIONAL : Id of source Batch.
            excludeUnmapped : OPTIONAL : Exclude unmapped source attributes (default True)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMappingSuggestions")
        path = "/mappingSets/suggestion"
        params = {"excludeUnmapped": excludeUnmapped}
        if dataSetId is not None:
            params["datasetId"] = dataSetId
        if batchId is not None:
            params["batchId"] = batchId
        res = self.connector.getData(self.endpoint + path, params=params)
        return res

    def getMappingSet(
            self, 
            mappingSetId: str = None,
            save: bool = False,
            saveMappingRules: bool = False, 
            mappingRulesOnly: bool = False,
            **kwargs
    ) -> dict:
        """
        Get a specific mappingSet by its ID.
        Argument:
            mappingSetId : REQUIRED : mappingSet ID to be retrieved.
            save : OPTIONAL : save your mapping set defintion in a JSON file.
            saveMappingRules : OPTIONAL : save your mapping rules only in a JSON file
            mappingRulesOnly : OPTIONAL : If set to True, return only the mapping rules.
        optional kwargs:
            encoding : possible to set encoding for the file.
        """
        if mappingSetId is None:
            raise ValueError("Require a mapping ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMappingSet")
        path = f"/mappingSets/{mappingSetId}"
        res = self.connector.getData(self.endpoint + path)
        if save:
            aepp.saveFile(
                module="dataPrep",
                file=res,
                filename=f"mapping_{res['id']}",
                type_file="json",
                encoding=kwargs.get("encoding", "utf-8"),
            )
        if saveMappingRules:
            aepp.saveFile(
                module="dataPrep",
                file=self.cleanMappingRules(res),
                filename=f"mapping_rules_{res['id']}",
                type_file="json",
                encoding=kwargs.get("encoding", "utf-8"),
            )
        if mappingRulesOnly:
            mappingRules = self.cleanMappingRules(res)
            return mappingRules
        return res

    def deleteMappingSet(self, mappingSetId: str = None) -> dict:
        """
        Delete a specific mappingSet by its ID.
        Argument:
            mappingSetId : REQUIRED : mappingSet ID to be deleted.
        """
        if mappingSetId is None:
            raise ValueError("Require a mapping ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteMappingSet")
        path = f"/mappingSets/{mappingSetId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def createMappingSet(
        self,
        schemaId: str = None,
        mappingList: list = None,
        validate: bool = False,
        verbose: bool = False,
        mappingSet: dict = None,
    ) -> dict:
        """
        Create a mapping set.
        Arguments:
            schemaId : OPTIONAL : schemaId to map to.
            mappingList: OPTIONAL : List of mapping to set.
            validate : OPTIONAL : Validate the mapping.
        if you want to provide a dictionary for mapping set creation, you can pass the following params:
            mappingSet : REQUIRED : A dictionary that creates the mapping info.
                see info on https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Mappings/createMappingSetUsingPOST
            
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createMappingSet")
        path = "/mappingSets"
        params = {"validate": validate}
        if (mappingSet is None or type(mappingSet) != dict) and (
            schemaId is None and mappingList is None
        ):
            raise ValueError(
                "Require a dictionary as mapping set or some schema reference ID and a mapping list"
            )
        if mappingSet is not None:
            res = self.connector.postData(
                self.endpoint + path, params=params, data=mappingSet, verbose=verbose
            )
        elif schemaId is not None and mappingList is not None:
            obj = {
                "outputSchema": {
                    "schemaRef": {
                        "id": schemaId,
                        "contentType": "application/vnd.adobe.xed-full+json;version=1",
                    }
                },
                "mappings": mappingList,
            }
            res = self.connector.postData(
                self.endpoint + path, params=params, data=obj, verbose=verbose
            )
        return res

    def updateMappingSet(
        self, mappingSetId: str = None, mappingRules: list = None,outputSchema:dict=None,
    ) -> dict:
        """
        Update a specific Mapping set based on its Id.
        Arguments:
            mappingSetId : REQUIRED : mapping Id to be updated
            mappingRules : REQUIRED : the list of different rule to map
            outputSchema : OPTIONAL : If you wish to change the destination output schema. By default taking the same one.
        """
        if mappingSetId is None:
            raise ValueError("Require a mappingSet ID")
        if mappingRules is None:
            raise ValueError("Require a list of mappings ")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateMappingSet")
        path = f"/mappingSets/{mappingSetId}"
        if outputSchema is None:
            currMapping = self.getMappingSet(mappingSetId)
            outputSchema = {
                "schemaRef" : currMapping.get('outputSchema',{}).get('schemaRef')
            }
        data = {
            "outputSchema":outputSchema,
            "mappings":mappingRules
        }
        res = self.connector.putData(self.endpoint + path, data=data)
        return res

    def getMappingSetMappings(self, mappingSetId: str = None) -> dict:
        """
        Returns all mappings for a mapping set
        Arguments:
            mappingSetId : REQUIRED : the mappingSet ID to retrieved
        """
        if mappingSetId is None:
            raise ValueError("Require a mapping ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMappingSetMappings")
        path = f"/mappingSets/{mappingSetId}/mappings"
        res = self.connector.getData(self.endpoint + path)
        return res

    def createMappingSetMapping(
        self, mappingSetId: str = None, mapping: dict = None, verbose: bool = False
    ) -> dict:
        """
        Create mappings for a mapping set
        Arguments:
            mappingSetId : REQUIRED : the mappingSet ID to attached the mapping
            mapping : REQUIRED : a dictionary to define the new mapping.
        """
        if mappingSetId is None:
            raise ValueError("Require a mapping ID")
        if mapping is None or type(mapping) != dict:
            raise Exception("Require a dictionary as mapping")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createMappingSetMapping")
        path = f"/mappingSets/{mappingSetId}/mappings"
        res = self.connector.postData(
            self.endpoint + path, data=mapping, verbose=verbose
        )
        return res

    def getMappingSetMapping(
        self, mappingSetId: str = None, mappingId: str = None
    ) -> dict:
        """
        Get a mapping from a mapping set.
        Arguments:
            mappingSetId : REQUIRED : The mappingSet ID
            mappingId : REQUIRED : The specific Mapping
        """
        if mappingSetId is None:
            raise ValueError("Require a mappingSet ID")
        if mappingId is None:
            raise ValueError("Require a mapping ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMappingSetMapping")
        path = f"/mappingSets/{mappingSetId}/mappings/{mappingId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def deleteMappingSetMapping(
        self, mappingSetId: str = None, mappingId: str = None
    ) -> dict:
        """
        Delete a mapping in a mappingSet
        Arguments:
            mappingSetId : REQUIRED : The mappingSet ID
            mappingId : REQUIRED : The specific Mapping
        """
        if mappingSetId is None:
            raise ValueError("Require a mappingSet ID")
        if mappingId is None:
            raise ValueError("Require a mapping ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteMappingSetMapping")
        path = f"/mappingSets/{mappingSetId}/mappings/{mappingId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def updateMappingSetMapping(
        self, mappingSetId: str = None, mappingId: str = None, mapping: dict = None
    ) -> dict:
        """
        Update a mapping for a mappingSet (PUT method)
        Arguments:
            mappingSetId : REQUIRED : The mappingSet ID
            mappingId : REQUIRED : The specific Mapping
            mapping : REQUIRED : dictionary to update
        """
        if mappingSetId is None:
            raise ValueError("Require a mappingSet ID")
        if mappingId is None:
            raise ValueError("Require a mapping ID")
        if mapping is None or type(mapping) != dict:
            raise Exception("Require a dictionary as mapping")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateMappingSetMapping")
        path = f"/mappingSets/{mappingSetId}/mappings/{mappingId}"
        res = self.connector.putData(self.endpoint + path, data=mapping)
        return res

    def previewDataOutput(self, data: dict = None, mappingSet: dict = None) -> dict:
        """
        The data you want to run through as a preview, which will be transformed by the mapping sets within the body.
        Arguments:
            data : REQUIRED : A dictionary containing the data to test.
            mappingSet : REQUIRED : The mappingSet to test.

        Example:
        {
            "data": {
                "id": 1234,
                "firstName": "Jim",
                "lastName": "Seltzer"
            },
            "mappingSet": {
                "outputSchema": {
                "schemaRef": {
                    "id": "https://ns.adobe.com/stardust/schemas/89abc189258b1cb1a816d8f2b2341a6d98000ed8f4008305",
                    "contentType": "application/vnd.adobe.xed-full+json;version=1"
                }
                },
                "mappings": [
                {
                    "sourceType": "ATTRIBUTE",
                    "source": "id",
                    "destination": "_id",
                    "name": "id",
                    "description": "Identifier field"
                },
                {
                    "sourceType": "ATTRIBUTE",
                    "source": "firstName",
                    "destination": "person.name.firstName"
                },
                {
                    "sourceType": "ATTRIBUTE",
                    "source": "lastName",
                    "destination": "person.name.lastName"
                }
                ]
            }
        }
        """
        if data is None:
            raise ValueError("Require a dictionary that contains the data to be tested")
        if mappingSet is None:
            raise ValueError("Require a dictionary that contains the mapping set")
        if self.loggingEnabled:
            self.logger.debug(f"Starting previewDataOutput")
        path = "/mappingSets/preview"
        dataObject = {"data": data, "mappingSet": mappingSet}
        res = self.connector.postData(self.endpoint + path, data=dataObject)
        return res

    def getMappingSetFunctions(
        self,
    ) -> list:
        """
        Return list of mapping functions.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMappingSetFunctions")
        path = "/languages/el/functions"
        res = self.connector.getData(self.endpoint + path)
        return res

    def getMappingSetOperators(
        self,
    ) -> list:
        """
        Return list of mapping operators.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMappingSetOperators")
        path = "/languages/el/operators"
        res = self.connector.getData(self.endpoint + path)
        return res

    def validateExpression(
        self,
        expression: str = None,
        mappingSetId: str = None,
        sampleData: str = None,
        sampleDataType: str = None,
    ) -> dict:
        """
        Check if the expression that you have passed is valid.
        Arguments:
            expression : REQUIRED : the expression you are trying to validate.
            mappingSetId : OPTIONAL : MappingSetId to integrate this expression.
            sampleData : OPTIONAL : Sample Date to validate
            sampleDataType : OPTIONAL : Data Type of your Sample data.
        """
        if expression is None:
            raise ValueError("Require an expression")
        if self.loggingEnabled:
            self.logger.debug(f"Starting validateExpression")
        path = "/languages/el/validate"
        data = {"expression": expression}
        if mappingSetId is not None:
            data["mappingSetId"] = mappingSetId
        if sampleData is not None:
            data["sampleData"] = sampleData
        if sampleDataType is not None:
            data["sampleDataType"] = sampleDataType
        res = self.connector.postData(self.endpoint + path, data=data)
        return res
