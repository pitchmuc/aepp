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
import time,json
import logging
import deprecation
from dataclasses import dataclass
from typing import Union
from .configs import ConnectObject
import datetime

@dataclass
class _Data:
    def __init__(self):
        self.flowId = {}
        self.flowSpecId = {}


class FlowService:
    """
    The Flow Service manage the ingestion part of the data in AEP.
    For more information, relate to the API Documentation, you can directly refer to the official documentation:
        https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/flow-service.yaml
        https://experienceleague.adobe.com/docs/experience-platform/sources/home.html
        https://experienceleague.adobe.com/docs/experience-platform/destinations/home.html
    """

    PATCH_REFERENCE = [
        {
            "op": "Add",
            "path": "/auth/params",
            "value": {
                "description": "A new description to provide further context on a specified connection or flow."
            },
        }
    ]

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
        initialize the Flow Service instance.
        Arguments:
            config : OPTIONAL : config object in the config module.
            header : OPTIONAL : header object  in the config module.
            loggingObject : OPTIONAL : A dictionary presenting the configuration of the logging service.
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
        self.endpoint = aepp.config.endpoints["global"] + aepp.config.endpoints["flow"]
        self.endpoint_gloal = aepp.config.endpoints["global"]
        self.data = _Data()

    def __str__(self):
        return json.dumps({'class':'FlowService','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)
    
    def __repr__(self):
        return json.dumps({'class':'FlowService','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)

    def getResource(
        self,
        endpoint: str = None,
        params: dict = None,
        format: str = "json",
        save: bool = False,
        **kwargs,
    ) -> dict:
        """
        Template for requesting data with a GET method.
        Arguments:
            endpoint : REQUIRED : The URL to GET
            params: OPTIONAL : dictionary of the params to fetch
            format : OPTIONAL : Type of response returned. Possible values:
                json : default
                txt : text file
                raw : a response object from the requests module
        """
        if endpoint is None:
            raise ValueError("Require an endpoint")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getResource")
        res = self.connector.getData(endpoint, params=params, format=format)
        if save:
            if format == "json":
                aepp.saveFile(
                    module="catalog",
                    file=res,
                    filename=f"resource_{int(time.time())}",
                    type_file="json",
                    encoding=kwargs.get("encoding", "utf-8"),
                )
            elif format == "txt":
                aepp.saveFile(
                    module="catalog",
                    file=res,
                    filename=f"resource_{int(time.time())}",
                    type_file="txt",
                    encoding=kwargs.get("encoding", "utf-8"),
                )
            else:
                print(
                    "element is an object. Output is unclear. No save made.\nPlease save this element manually"
                )
        return res

    def getConnections(
        self, limit: int = 20, n_results: int = 100, count: bool = False, **kwargs
    ) -> list:
        """
        Returns the list of connections available.
        Arguments:
            limit : OPTIONAL : number of result returned per request (default 20)
            n_results : OPTIONAL : number of total result returned (default 100, set to "inf" for retrieving everything)
            count : OPTIONAL : if set to True, just returns the number of connections
        kwargs will be added as query parameters
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getConnections")
        params = {"limit": limit}
        if count:
            params["count"] = count
        for kwarg in kwargs:
            params[kwarg] = kwargs[kwarg]
        path = "/connections"
        res = self.connector.getData(self.endpoint + path, params=params)
        try:
            data = res["items"]
            continuationToken = res.get("_links", {}).get("next", {}).get("href", "")
            while continuationToken != "" and len(data) < float(n_results):
                res = self.connector.getData(
                    self.endpoint + continuationToken, params=params
                )
                data += res["items"]
                continuationToken = (
                    res.get("_links", {}).get("next", {}).get("href", "")
                )
            return data
        except:
            return res

    def createConnection(
        self,
        data: dict = None,
        name: str = None,
        auth: dict = None,
        connectionSpec: dict = None,
        **kwargs,
    ) -> dict:
        """
        Create a connection based on either the data being passed or the information passed.
        Arguments:
            data : REQUIRED : dictionary containing the different elements required for the creation of the connection.

            In case you didn't pass a data parameter, you can pass different information.
            name : REQUIRED : name of the connection.
            connectionSpec : REQUIRED : dictionary containing the "id" and "verison" key.
                id : The specific connection specification ID associated with source
                version : Specifies the version of the connection specification ID. Omitting this value will default to the most recent version
            auth : OPTIONAL : dictionary that contains "specName" and "params"
                specName : string that names of the the type of authentication to be used with the base connection.
                params : dict that contains credentials and values necessary to authenticate and create a connection.
            Possible kwargs:
            responseType : by default json, but you can request 'raw' that return the requests response object.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createConnection")
        path = "/connections"
        if data is not None:
            if (
                "name" not in data.keys()
                or "connectionSpec" not in data.keys()
            ):
                raise Exception(
                    "Require some keys to be present : name, auth, connectionSpec"
                )
            obj = data
            res = self.connector.postData(self.endpoint + path, data=obj,format=kwargs.get('responseType','json'))
            return res
        elif data is None:
            if "id" not in connectionSpec.keys():
                raise Exception(
                    "Require some keys to be present in connectionSpec dict : id"
                )
            if name is None:
                raise Exception("Require a name to be present")
            obj = {"name": name, "connectionSpec": connectionSpec}
            if auth is not None:
                obj["auth"] = auth
            res = self.connector.postData(self.endpoint + path, data=obj,format=kwargs.get('responseType','json'))
            return res

    def createConnectionStreaming(
        self,
        name: str = None,
        sourceId: str = None,
        dataType: str = "xdm",
        authenticationRequired:bool=False,
        paramName: str = None,
        description: str = "provided by aepp",
        **kwargs,
    ) -> dict:
        """
        Create a Streaming connection based on the following connectionSpec :
        "connectionSpec": {
                "id": "bc7b00d6-623a-4dfc-9fdb-f1240aeadaeb",
                "version": "1.0",
            },
            with provider ID : 521eee4d-8cbe-4906-bb48-fb6bd4450033
        It requires a mapping file to be provided in the flow.
        Arguments:
            name : REQUIRED : Name of the Connection.
            sourceId : REQUIRED : The ID of the streaming connection you want to create (random string possible).
            dataType : REQUIRED : The type of data to ingest (default "xdm") possible value: "raw".
            paramName : REQUIRED : The name of the streaming connection you want to create.
            description : OPTIONAL : if you want to add a description
        kwargs possibility:
            specName : if you want to modify the specification Name.(Default : "Streaming Connection")
            responseType : by default json, but you can request 'raw' that return the requests response object.
        """
        if name is None:
            raise ValueError("Require a name for the connection")
        if sourceId is None:
            raise Exception("Require an ID for the connection")
        if dataType is None:
            raise Exception("Require a dataType specified")
        if paramName is None:
            raise ValueError("Require a name for the Streaming Connection")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createStreamingConnection")
        obj = {
            "name": name,
            "providerId": "521eee4d-8cbe-4906-bb48-fb6bd4450033",
            "description": description,
            "connectionSpec": {
                "id": "bc7b00d6-623a-4dfc-9fdb-f1240aeadaeb",
                "version": "1.0",
            },
            "auth": {
                "specName": kwargs.get("specName", "Streaming Connection"),
                "params": {
                    "sourceId": sourceId,
                    "dataType": dataType,
                    "name": paramName,
                },
            },
        }
        if authenticationRequired:
            obj['auth']['params']['authenticationRequired'] = True
        res = self.createConnection(data=obj,responseType=kwargs.get('responseType','json'))
        return res

    def getConnection(self, connectionId: str = None) -> dict:
        """
        Returns a specific connection object.
        Argument:
            connectionId : REQUIRED : The ID of the connection you wish to retrieve.
        """
        if connectionId is None:
            raise Exception("Require a connectionId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getConnection")
        path = f"/connections/{connectionId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def connectionTest(self, connectionId: str = None) -> dict:
        """
        Test a specific connection ID.
        Argument:
            connectionId : REQUIRED : The ID of the connection you wish to test.
        """
        if connectionId is None:
            raise Exception("Require a connectionId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting connectionTest")
        path: str = f"/connections/{connectionId}/test"
        res: dict = self.connector.getData(self.endpoint + path)
        return res

    def deleteConnection(self, connectionId: str = None) -> dict:
        """
        Delete a specific connection ID.
        Argument:
            connectionId : REQUIRED : The ID of the connection you wish to delete.
        """
        if connectionId is None:
            raise Exception("Require a connectionId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteConnection")
        path: str = f"/connections/{connectionId}"
        res: dict = self.connector.deleteData(self.endpoint + path)
        return res

    def getConnectionSpecs(self) -> list:
        """
        Returns the list of connectionSpecs in that instance.
        If that doesn't work, return the response.
        """
        path: str = "/connectionSpecs"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getConnectionSpecs")
        res: dict = self.connector.getData(self.endpoint + path)
        try:
            data: list = res["items"]
            return data
        except:
            return res

    def getConnectionSpecsMap(self) -> dict:
        """
        Returns a mapping of connection spec name to connection spec ID.
        If that doesn't work, return the response.
        """
        specs_info = self.getConnectionSpecs()
        return {spec["name"]: spec["id"] for spec in specs_info if "id" in spec and "name" in spec}

    def getConnectionSpec(self, specId: str = None) -> dict:
        """
        Returns the detail for a specific connection.
        Arguments:
            specId : REQUIRED : The specification ID of a connection
        """
        if specId is None:
            raise Exception("Require a specId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getConnectionSpec")
        path: str = f"/connectionSpecs/{specId}"
        res: dict = self.connector.getData(self.endpoint + path)
        return res.get('items',[{}])[0]

    def getConnectionSpecIdFromName(self, name: str = None) -> int:
        """
        Returns the connection spec ID corresponding to a connection spec name.
        Arguments:
            name : REQUIRED : The specification name of a connection
        """
        if name is None:
            raise Exception("Require a name to be present")
        spec_name_to_id = self.getConnectionSpecsMap()
        if name not in spec_name_to_id:
            raise Exception(f"Connection spec name '{name}' not found")
        return spec_name_to_id[name]

    def getFlows(
        self,
        limit: int = 100,
        n_results: int = 100,
        prop: str = None,
        filterMappingSetIds: list = None,
        filterSourceIds: list = None,
        filterTargetIds: list = None,
        onlyDestinations: bool = False,
        onlySources:bool = False,
        **kwargs,
    ) -> list:
        """
        Returns the flows set between Source and Target connection.
        Arguments:
            limit : OPTIONAL : number of results returned
            n_results : OPTIONAL : total number of results returned (default 100, set to "inf" for retrieving everything)
            prop : OPTIONAL : comma separated list of top-level object properties to be returned in the response.
                Used to cut down the amount of data returned in the response body.
                For example, prop=id==3416976c-a9ca-4bba-901a-1f08f66978ff,6a8d82bc-1caf-45d1-908d-cadabc9d63a6,3c9b37f8-13a6-43d8-bad3-b863b941fedd.
            filterMappingSetId : OPTIONAL : returns only the flow that possess the mappingSetId passed in a list.
            filterSourceIds : OPTIONAL : returns only the flow that possess the sourceConnectionIds passed in a list.
            filterTargetIds : OPTIONAL : returns only the flow that possess the targetConnectionIds passed in a list.
            onlyDestinations : OPTIONAL : Filter to only destinations flows (max 100)
            onlySources : OPTIONAL : Filter to only source flows (max 100)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFlows")
        params: dict = {"limit": limit, "count": kwargs.get("count", False)}
        if property is not None:
            params["property"] = prop
        if kwargs.get("continuationToken", False) != False:
            params["continuationToken"] = kwargs.get("continuationToken")
        path: str = "/flows"
        if onlyDestinations:
            params['property'] = "inheritedAttributes.properties.isDestinationFlow==true"
        if onlySources:
            params['property'] = "inheritedAttributes.properties.isSourceFlow==true"
        res: dict = self.connector.getData(self.endpoint + path, params=params)
        token: str = res.get("_links", {}).get("next", {}).get("href", "")
        items = res.get("items",[])
        while token != "" and len(items) < float(n_results):
            continuationToken = token.split("=")[1]
            params["continuationToken"] = continuationToken
            res = self.connector.getData(self.endpoint + path, params=params)
            token = res["_links"].get("next", {}).get("href", "")
            items += res["items"]
        self.data.flowId = {item["name"]: item["id"] for item in items}
        self.data.flowSpecId = {item["name"]: item.get("flowSpec",{}).get('id') for item in items}
        if filterMappingSetIds is not None:
            filteredItems = []
            for mappingsetId in filterMappingSetIds:
                for item in items:
                    if "transformations" in item.keys():
                        for element in item["transformations"]:
                            if element["params"].get("mappingId", "") == mappingsetId:
                                filteredItems.append(item)
            items = filteredItems
        if filterSourceIds is not None:
            filteredItems = []
            for sourceId in filterSourceIds:
                for item in items:
                    if sourceId in item["sourceConnectionIds"]:
                        filteredItems.append(item)
            items = filteredItems
        if filterTargetIds is not None:
            filteredItems = []
            for targetId in filterTargetIds:
                for item in items:
                    if targetId in item["targetConnectionIds"]:
                        filteredItems.append(item)
            items = filteredItems
        return items

    def getFlow(self, flowId: str = None) -> dict:
        """
        Returns the details of a specific flow.
        Arguments:
            flowId : REQUIRED : the flow ID to be returned
        """
        if flowId is None:
            raise Exception("Require a flowId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFlow")
        path: str = f"/flows/{flowId}"
        res: dict = self.connector.getData(self.endpoint + path)
        return res.get('items',[{}])[0]

    def deleteFlow(self, flowId: str = None) -> dict:
        """
        Delete a specific flow by its ID.
        Arguments:
            flowId : REQUIRED : the flow ID to be returned
        """
        if flowId is None:
            raise Exception("Require a flowId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteFlow")
        path: str = f"/flows/{flowId}"
        res: dict = self.connector.deleteData(self.endpoint + path)
        return res

    def createFlow(
        self,
        flow_spec_id: str,
        name: str = None,
        source_connection_id: str = None,
        target_connection_id: str = None,
        schedule_start_time: str = None,
        schedule_end_time: str = None,
        schedule_frequency: str = "minute",
        schedule_interval: int = 15,
        transformation_mapping_id: str = None,
        transformation_name: str = None,
        transformation_version: int = 0,
        output_folder_name: str = "%DESTINATION%_%DATASET_ID%_%DATETIME(YYYYMMdd_HHmmss)%",
        obj: dict = None,
        version: str = "1.0",
        **kwargs
    ) -> dict:
        """
        Create a flow with the API.
        Arguments:
            flow_spec_id : REQUIRED : flow spec ID If you decide to use specific parameterization
            name : REQUIRED : Name of the flow 
            obj : REQUIRED : body to create the flow service.
                Details can be seen at https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Flows/postFlow
                requires following keys : name, sourceConnectionIds, targetConnectionIds.
        """
        if obj is None:
            if any(param is None for param in [name, source_connection_id, target_connection_id]):
                raise KeyError("Require either obj or all of 'name', 'source_connection_id', 'target_connection_id'")
            obj = {
                "name": name,
                "flowSpec": {
                    "id": flow_spec_id,
                    "version": version
                },
                "sourceConnectionIds": [
                    source_connection_id
                ],
                "targetConnectionIds": [
                    target_connection_id
                ],
                "transformations": [],
                "scheduleParams": {}
            }
            if schedule_frequency == "once":
                obj["scheduleParams"] = {
                    "timeUnit": "day",
                    "interval": 0,
                    "exportMode": "DAILY_FULL_EXPORT"
                }
            elif schedule_frequency not in ("minute", "hour"): 
                if kwargs.get("schedule_timeUnit",None) is not None:
                    obj["scheduleParams"]["timeUnit"] = kwargs.get("schedule_timeUnit",None)
                if schedule_end_time is not None:
                    obj["scheduleParams"]["endTime"] = schedule_end_time
                if schedule_frequency is not None:
                    obj["scheduleParams"]["frequency"] = schedule_frequency
                if schedule_interval is not None:
                    obj["scheduleParams"]["interval"] = str(schedule_interval)
                if kwargs.get("export_mode", None) is not None: ## infer dataset export
                    obj["scheduleParams"]["exportMode"] = kwargs.get("export_mode",None)
            else:
                raise ValueError("schedule frequency has to be either once, minute or hour")

            if schedule_start_time is not None:
                obj["scheduleParams"]["startTime"] = schedule_start_time
            obj["scheduleParams"]["foldernameTemplate"] = output_folder_name
            if transformation_mapping_id is not None:
                obj["transformations"] = [
                    {
                        "name": transformation_name,
                        "params": {
                            "mappingId": transformation_mapping_id,
                            "mappingVersion": transformation_version
                        }
                    }
                ]
        else:
            if "name" not in obj.keys():
                raise KeyError("missing 'name' parameter in the dictionary")
            if "flowSpec" not in obj.keys():
                raise KeyError("missing 'flowSpec' parameter in the dictionary")
            if "sourceConnectionIds" not in obj.keys():
                raise KeyError("missing 'sourceConnectionIds' parameter in the dictionary")
            if "targetConnectionIds" not in obj.keys():
                raise KeyError("missing 'targetConnectionIds' parameter in the dictionary")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createFlow")
        path: str = "/flows"
        res: dict = self.connector.postData(self.endpoint + path, data=obj)
        return res
    
    def createFlowStreaming(self,
                            name: str = None,
                            description: str = "power by aepp",
                            source_connection_id: str = None,
                            target_connection_id: str = None,
                            transformation : bool = False,
                            transformation_mapping_id: str = None,
                            transformation_name: str = None,
                            transformation_version: int = 0,
                            )-> dict:
        """
        Create a streaming flow with or without transformation
            name : REQUIRED : The name of the Data Flow.
            description : OPTIONAL : description of the Flow
            source_connection_id : REQUIRED : The ID of the source connection tied to Data Lake.
            target_connection_id : REQUIRED : The ID of the target connection tied to Data Landing Zone.
            transformation : OPTIONAL : if it is using transformation step. If Optional, set to True.
            transformation_mapping_id : OPTIONAL : If a transformation is required, its mapping ID.
            transformation_name : OPTIONAL : If a transformation is required, its name.
            transformation_version : OPTIONAL : If a transformation is required, its version.
        """
        if transformation:
            flowSpecId = 'c1a19761-d2c7-4702-b9fa-fe91f0613e81'
        else:
            flowSpecId = 'd8a6f005-7eaf-4153-983e-e8574508b877'
        return self.createFlow(
            flow_spec_id=flowSpecId,
            name=name,
            description=description,
            source_connection_id=source_connection_id,
            target_connection_id=target_connection_id,
            transformation_mapping_id=transformation_mapping_id,
            transformation_name=transformation_name,
            transformation_version=transformation_version,
        )

    def createFlowDataLakeToDataLandingZone(
        self,
        name: str,
        source_connection_id: str,
        target_connection_id: str,
        schedule_start_time: str,
        schedule_end_time:str=None,
        export_mode: str=None,
        schedule_frequency: str = "hour",
        schedule_timeUnit:str = None,
        schedule_interval: int = 3,
        transformation_mapping_id: str = None,
        transformation_name: str = None,
        transformation_version: int = 0,
        version: str = "1.0",
        description: str = "power by aepp"
    ) -> dict:
        """
        Create a Data Flow to move data from Data Lake to the Data Landing Zone.
        Arguments:
            name : REQUIRED : The name of the Data Flow.
            source_connection_id : REQUIRED : The ID of the source connection tied to Data Lake.
            target_connection_id : REQUIRED : The ID of the target connection tied to Data Landing Zone.
            schedule_start_time : REQUIRED : The time from which the Data Flow should start running. Unix in seconds.
            schedule_end_time : OPTIONAL : The time from which the data flow should not run anymore. Unix in seconds.
            export_mode : OPTIONAL : Type of export you want for dataset. "DAILY_FULL_EXPORT" or "FIRST_FULL_THEN_INCREMENTAL"
            schedule_frequency : OPTIONAL : The granularity of the Data Flow. Currently only "hour" supported.
            schedule_interval : OPTIONAL : The interval on which the Data Flow runs. Either 3, 6, 9, 12 or 24. Default to 3.
            transformation_mapping_id : OPTIONAL : If a transformation is required, its mapping ID.
            transformation_name : OPTIONAL : If a transformation is required, its name.
            transformation_version : OPTIONAL : If a transformation is required, its version.
            version : OPTIONAL : The version of the Data Flow.
            description : OPTIONAL : description of the Flow
        """
        return self.createFlow(
            flow_spec_id="cd2fc47e-e838-4f38-a581-8fff2f99b63a",
            name=name,
            description=description,
            source_connection_id=source_connection_id,
            target_connection_id=target_connection_id,
            schedule_start_time=schedule_start_time,
            schedule_end_time=schedule_end_time,
            export_mode=export_mode,
            schedule_frequency=schedule_frequency,
            schedule_timeUnit=schedule_timeUnit,
            schedule_interval=schedule_interval,
            transformation_mapping_id=transformation_mapping_id,
            transformation_name=transformation_name,
            transformation_version=transformation_version,
            version=version
        )

    def createFlowDataLandingZoneToDataLake(
        self,
        name: str,
        source_connection_id: str,
        target_connection_id: str,
        schedule_start_time: str,
        schedule_frequency: str = "minute",
        schedule_interval: int = 15,
        transformation_mapping_id: str = None,
        transformation_name: str = None,
        transformation_version: int = 0,
        version: str = "1.0",
        flow_spec_name: str = "CloudStorageToAEP",
        source_spec_name: str = "landing-zone",
        target_spec_name: str = "datalake"
    ) -> dict:
        """
        Create a Data Flow to move data from Data Lake to the Data Landing Zone.
        Arguments:
            name : REQUIRED : The name of the Data Flow.
            source_connection_id : REQUIRED : The ID of the source connection tied to Data Lake.
            target_connection_id : REQUIRED : The ID of the target connection tied to Data Landing Zone.
            schedule_start_time : REQUIRED : The time from which the Data Flow should start running.
            schedule_frequency : OPTIONAL : The granularity of the Data Flow. Can be "hour" or "minute". Default to "minute".
            schedule_interval : OPTIONAL : The interval on which the Data Flow runs. Default to 15
            transformation_mapping_id : OPTIONAL : If a transformation is required, its mapping ID.
            transformation_name : OPTIONAL : If a transformation is required, its name.
            transformation_version : OPTIONAL : If a transformation is required, its version.
            version : OPTIONAL : The version of the Data Flow.
            flow_spec_name : OPTIONAL : The name of the Data Flow specification. Same for all customers.
        """
        flow_spec_id = self.getFlowSpecIdFromNames(flow_spec_name, source_spec_name, target_spec_name)
        return self.createFlow(
            flow_spec_id=flow_spec_id,
            name=name,
            source_connection_id=source_connection_id,
            target_connection_id=target_connection_id,
            schedule_start_time=schedule_start_time,
            schedule_frequency=schedule_frequency,
            schedule_interval=schedule_interval,
            transformation_mapping_id=transformation_mapping_id,
            transformation_name=transformation_name,
            transformation_version=transformation_version,
            version=version
        )

    def updateFlow(
        self, flowId: str = None, etag: str = None, updateObj: list = None
    ) -> dict:
        """
        update the flow based on the operation provided.
        Arguments:
            flowId : REQUIRED : the ID of the flow to Patch.
            etag : REQUIRED : ETAG value for patching the Flow.
            updateObj : REQUIRED : List of operation to realize on the flow.

            Follow the following structure:
            [
                {
                    "op": "Add",
                    "path": "/auth/params",
                    "value": {
                    "description": "A new description to provide further context on a specified connection or flow."
                    }
                }
            ]
        """
        if flowId is None:
            raise Exception("Require a flow ID to be present")
        if etag is None:
            raise Exception("Require etag to be present")
        if updateObj is None:
            raise Exception("Require a list with data to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateFlow")
        privateHeader = deepcopy(self.header)
        privateHeader["if-match"] = etag
        path: str = f"/flows/{flowId}"
        res: dict = self.connector.patchData(
            self.endpoint + path, headers=privateHeader, data=updateObj
        )
        return res

    def getFlowSpecs(self, prop: str = None) -> list:
        """
        Returns the flow specifications.
        Arguments:
            prop : OPTIONAL : A comma separated list of top-level object properties to be returned in the response.
                Used to cut down the amount of data returned in the response body.
                For example, prop=id==3416976c-a9ca-4bba-901a-1f08f66978ff,6a8d82bc-1caf-45d1-908d-cadabc9d63a6,3c9b37f8-13a6-43d8-bad3-b863b941fedd.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFlowSpecs")
        path: str = "/flowSpecs"
        params = {}
        if prop is not None:
            params["property"] = prop
        res: dict = self.connector.getData(self.endpoint + path, params=params)
        items: list = res["items"]
        return items

    def getFlowSpecIdFromNames(
        self,
        flow_spec_name: str,
        source_spec_name: str = None,
        target_spec_name: str = None
    ) -> str:
        """
        Return the Flow specification ID corresponding to some conditions.
        Arguments:
            flow_spec_name : REQUIRED : The flow specification name to look for
            source_spec_name : OPTIONAL : Additional filter to only return a flow with a source specification ID.
            target_spec_name : OPTIONAL : Additional filter to only return a flow with a target specification ID.
        """
        flows = self.getFlowSpecs(f"name=={flow_spec_name}")
        if source_spec_name is not None:
            source_spec_id = self.getConnectionSpecIdFromName(source_spec_name)
            flows = [flow for flow in flows if source_spec_id in flow["sourceConnectionSpecIds"]]
        if target_spec_name is not None:
            target_spec_id = self.getConnectionSpecIdFromName(target_spec_name)
            flows = [flow for flow in flows if target_spec_id in flow["targetConnectionSpecIds"]]
        if len(flows) != 1:
            raise Exception(f"Expected a single flow specification mapping to flow name '{flow_spec_name}', "
                            f"source spec name '{source_spec_name}' and target spec name '{target_spec_name}'"
                            f"but got {len(flows)}")
        flow_spec_id = flows[0]["id"]
        return flow_spec_id

    def getFlowSpec(self, flowSpecId) -> dict:
        """
        Return the detail of a specific flow ID Spec
        Arguments:
            flowSpecId : REQUIRED : The flow ID spec to be checked
        """
        if flowSpecId is None:
            raise Exception("Require a flowSpecId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFlowSpec")
        path: str = f"/flowSpecs/{flowSpecId}"
        res: dict = self.connector.getData(self.endpoint + path)
        return res.get('items',[{}])[0]

    def getRuns(
        self, limit: int = 10, n_results: int = 100, prop: Union[str,list] = None, **kwargs
    ) -> list:
        """
        Returns the list of runs. Runs are instances of a flow execution.
        Arguments:
            limit : OPTIONAL : number of results returned per request
            n_results : OPTIONAL : total number of results returned (default 100, set to "inf" for retrieving everything)
            prop : OPTIONAL : comma separated list of top-level object properties to be returned in the response.
                Used to cut down the amount of data returned in the response body.
                For example, prop=id==3416976c-a9ca-4bba-901a-1f08f66978ff,6a8d82bc-1caf-45d1-908d-cadabc9d63a6,3c9b37f8-13a6-43d8-bad3-b863b941fedd.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getRuns")
        path = "/runs"
        params = {"limit": limit, "count": kwargs.get("count", False)}
        if prop is not None:
            if type(prop) == str:
                params["property"] = prop
            elif type(prop) == list:
                params["property"] = prop
        if kwargs.get("continuationToken", False):
            params["continuationToken"] = kwargs.get("continuationToken")
        res: dict = self.connector.getData(self.endpoint + path, params=params)
        items: list = res.get("items",[])
        nextPage = res.get("_links",{}).get("next", {}).get("href", "")
        while nextPage != "" and len(items) < float(n_results):
            token: str = res["_links"]["next"].get("href", "")
            continuationToken: str = token.split("=")[1]
            params["continuationToken"] = continuationToken
            res = self.connector.getData(self.endpoint + path, params=params)
            items += res.get('items')
            nextPage = res.get("_links").get("next", {}).get("href", "")
        return items

    def createRun(self, flowId: str = None, status: str = "active") -> dict:
        """
        Generate a run based on the flowId.
        Arguments:
            flowId : REQUIRED : the flow ID to run
            status : OPTIONAL : Status of the flow
        """
        path = "/runs"
        if flowId is None:
            raise Exception("Require a flowId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createRun")
        obj = {"flowId": flowId, "status": status}
        res: dict = self.connector.postData(self.endpoint + path, data=obj)
        return res

    def getRun(self, runId: str = None) -> dict:
        """
        Return a specific runId.
        Arguments:
            runId : REQUIRED : the run ID to return
        """
        if runId is None:
            raise Exception("Require a runId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getRun")
        path: str = f"/runs/{runId}"
        res: dict = self.connector.getData(self.endpoint + path)
        return res

    def getSourceConnections(self, n_results: int = 100, **kwargs) -> list:
        """
        Return the list of source connections
        Arguments:
            n_results : OPTIONAL : total number of results returned (default 100, set to "inf" for retrieving everything)
        kwargs will be added as query parameterss
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSourceConnections")
        params = {**kwargs}
        path: str = f"/sourceConnections"
        res: dict = self.connector.getData(self.endpoint + path, params=params)
        data: list = res["items"]
        nextPage = res["_links"].get("next", {}).get("href", "")
        while nextPage != "" and len(data) < float(n_results):
            continuationToken = nextPage.split("=")[1]
            params["continuationToken"] = continuationToken
            res: dict = self.connector.getData(self.endpoint + path, params=params)
            data += res["items"]
            nextPage = res["_links"].get("next", {}).get("href", "")
        return data

    def getSourceConnection(self, sourceConnectionId: str = None) -> dict:
        """
        Return detail of the sourceConnection ID
        Arguments:
            sourceConnectionId : REQUIRED : The source connection ID to be retrieved
        """
        if sourceConnectionId is None:
            raise Exception("Require a sourceConnectionId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSourceConnection")
        path: str = f"/sourceConnections/{sourceConnectionId}"
        res: dict = self.connector.getData(self.endpoint + path)
        return res.get('items',[{}])[0]

    def deleteSourceConnection(self, sourceConnectionId: str = None) -> dict:
        """
        Delete a sourceConnection ID
        Arguments:
            sourceConnectionId : REQUIRED : The source connection ID to be deleted
        """
        if sourceConnectionId is None:
            raise Exception("Require a sourceConnectionId to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteSourceConnection")
        path: str = f"/sourceConnections/{sourceConnectionId}"
        res: dict = self.connector.deleteData(self.endpoint + path)
        return res

    def createSourceConnection(self, data: dict = None) -> dict:
        """
        Create a sourceConnection based on the dictionary passed.
        Arguments:
            obj : REQUIRED : the data to be passed for creation of the Source Connection.
                Details can be seen at https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Source_connections/postSourceConnection
                requires following keys : name, baseConnectionId, data, params, connectionSpec.
        """
        if data is None:
            raise Exception("Require a dictionary with data to be present")
        if "name" not in data.keys():
            raise KeyError("Require a 'name' key in the dictionary passed")
        if "connectionSpec" not in data.keys():
            raise KeyError("Require a 'connectionSpec' key in the dictionary passed")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createSourceConnection")
        path: str = f"/sourceConnections"
        res: dict = self.connector.postData(self.endpoint + path, data=data)
        return res

    def createSourceConnectionStreaming(
        self,
        connectionId: str = None,
        name: str = None,
        format: str = "delimited",
        description: str = "Streaming Source powered by aepp",
        providerId:str = "521eee4d-8cbe-4906-bb48-fb6bd4450033",
        spec_name: str = "Streaming Connection"
    ) -> dict:
        """
        Create a source connection based on streaming connection created.
        Arguments:
            connectionId : REQUIRED : The Streaming connection ID.
            name : REQUIRED : Name of the Connection.
            format : REQUIRED : format of the data sent (default : delimited)
            description : REQUIRED : Description of of the Connection Source.
            providerId : OPTIONAL : By default using the 521eee4d-8cbe-4906-bb48-fb6bd4450033 provider ID from 'Streaming Connection' connection Specification. 
            spec_name : OPTIONAL : The name of the source specification corresponding used to get the providerId, if you decide to change from the default provider ID specified by default.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createSourceConnectionStreaming")
        if providerId is None:
            if spec_name is None:
                raise ValueError("spec_name is required if you did not want the default provider ID")
            spec_id = self.getConnectionSpecIdFromName(spec_name)
        obj = {
            "name": name,
            "providerId": providerId,
            "description": description,
            "baseConnectionId": connectionId,
            "connectionSpec": {
                "id": spec_id,
                "version": "1.0",
            },
            "data": {"format": format},
        }
        res = self.createSourceConnection(data=obj)
        return res
    
    def createSourceConnectionDataLandingZone(
        self,
        name: str = None,
        format: str = "delimited",
        path: str = None,
        type: str = "file",
        recursive: bool = False,
        spec_name: str = "landing-zone"
    ) -> dict:
        """
        Create a new data landing zone connection.
        Arguments:
            name : REQUIRED : A name for the connection
            format : REQUIRED : The type of data type loaded. Default "delimited". Can be "json" or "parquet" 
            path : REQUIRED : The path to the data you want to ingest. Can be a single file or folder.
            type : OPTIONAL : Use "file" if path refers to individual file, otherwise "folder".
            recursive : OPTIONAL : Whether to look for files recursively under the path or not.
            spec_name : OPTIONAL : The name of the source specification corresponding to Data Landing Zone.
        """
        if name is None:
            raise ValueError("Require a name for the connection")
        spec_id = self.getConnectionSpecIdFromName(spec_name)
        obj = {
            "name": name,
            "data": {
                "format": format
            },
            "params": {
                "path": path,
                "type": type,
                "recursive": recursive
            },
            "connectionSpec": {
                "id": spec_id,
                "version": "1.0"
            }
        }
        res = self.createSourceConnection(obj)
        return res

    def createSourceConnectionDataLake(
        self,
        name: str = None,
        format: str = "delimited",
        dataset_ids: list = [],
        spec_name: str = "activation-datalake"
    ) -> dict:
        """
        Create a new data lake connection.
        Arguments:
            name : REQUIRED : A name for the connection
            format : REQUIRED : The type of data type loaded. Default "delimited". Can be "json" or "parquet"
            dataset_ids : REQUIRED : A list of dataset IDs acting as a source of data.
            spec_name : OPTIONAL : The name of the source specification corresponding to Data Lake.
        """
        if name is None:
            raise ValueError("Require a name for the connection")
        if len(dataset_ids) == 0:
            raise ValueError("Expected at least 1 dataset ID to be passed")
        spec_id = self.getConnectionSpecIdFromName(spec_name)
        obj = {
            "name": name,
            "data": {
                "format": format
            },
            "connectionSpec": {
                "id": spec_id,
                "version": "1.0"
            },
            "params": {
                "datasets": [{
                    "dataSetId": dataset_id,
                } for dataset_id in dataset_ids]
            }
        }
        res = self.createSourceConnection(obj)
        return res

    def updateSourceConnection(
        self, sourceConnectionId: str = None, etag: str = None, updateObj: list = None
    ) -> dict:
        """
        Update a source connection based on the ID provided with the object provided.
        Arguments:
            sourceConnectionId : REQUIRED : The source connection ID to be updated
            etag: REQUIRED : A header containing the etag value of the connection or flow to be updated.
            updateObj : REQUIRED : The operation call used to define the action needed to update the connection. Operations include add, replace, and remove.
        """
        if sourceConnectionId is None:
            raise Exception("Require a sourceConnection to be present")
        if etag is None:
            raise Exception("Require etag to be present")
        if updateObj is None:
            raise Exception("Require a list with data to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateSourceConnection")
        privateHeader = deepcopy(self.header)
        privateHeader["if-match"] = etag
        path: str = f"/sourceConnections/{sourceConnectionId}"
        res: dict = self.connector.patchData(
            self.endpoint + path, headers=privateHeader, data=updateObj
        )
        return res

    def getTargetConnections(self, n_results: int = 100, **kwargs) -> dict:
        """
        Return the target connections
        Arguments:
            n_results : OPTIONAL : total number of results returned (default 100, set to "inf" for retrieving everything)
        kwargs will be added as query parameters
        """
        params = {**kwargs}
        path: str = f"/targetConnections"
        res: dict = self.connector.getData(self.endpoint + path, params=params)
        data: list = res["items"]
        nextPage = res["_links"].get("next", {}).get("href", "")
        while nextPage != "" and len(data) < float(n_results):
            continuationToken = nextPage.split("=")[1]
            params["continuationToken"] = continuationToken
            res: dict = self.connector.getData(self.endpoint + path, params=params)
            data += res["items"]
            nextPage = res["_links"].get("next", {}).get("href", "")
        return data

    def getTargetConnection(self, targetConnectionId: str = None) -> dict:
        """
        Retrieve a specific Target connection detail.
        Arguments:
            targetConnectionId : REQUIRED : The target connection ID is a unique identifier used to create a flow.
        """
        if targetConnectionId is None:
            raise Exception("Require a target connection ID to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getTargetConnection")
        path: str = f"/targetConnections/{targetConnectionId}"
        res: dict = self.connector.getData(self.endpoint + path)
        return res.get('items',[None])[0]

    def deleteTargetConnection(self, targetConnectionId: str = None) -> dict:
        """
        Delete a specific Target connection detail
        Arguments:
             targetConnectionId : REQUIRED : The target connection ID to be deleted
        """
        if targetConnectionId is None:
            raise Exception("Require a target connection ID to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteTargetConnection")
        path: str = f"/targetConnections/{targetConnectionId}"
        res: dict = self.connector.deleteData(self.endpoint + path)
        return res

    def createTargetConnection(
        self,
        name: str = None,
        connectionSpecId: str = None,
        datasetId: str = None,
        format: str = "parquet_xdm",
        version: str = "1.0",
        description: str = "",
        data: dict = None,
    ) -> dict:
        """
        Create a new target connection
        Arguments:
                name : REQUIRED : The name of the target connection
                connectionSpecId : REQUIRED : The connectionSpecId to use.
                datasetId : REQUIRED : The dataset ID that is the target
                version : REQUIRED : version to be used (1.0 by default)
                format : REQUIRED : Data format to be used (parquet_xdm by default)
                description : OPTIONAL : description of your target connection
                data : OPTIONAL : If you pass the complete dictionary for creation
        Details can be seen at https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Target_connections/postTargetConnection
        requires following keys : name, data, params, connectionSpec.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createTargetConnection")
        path: str = f"/targetConnections"
        if data is not None and type(data) == dict:
            obj = data
            res: dict = self.connector.postData(self.endpoint + path, data=obj)
        else:
            if name is None:
                raise ValueError("Require a name to be passed")
            if connectionSpecId is None:
                raise ValueError("Require a connectionSpec Id to be passed")
            if datasetId is None:
                raise ValueError("Require a datasetId to be passed")
            obj = {
                "name": name,
                "description": description,
                "connectionSpec": {"id": connectionSpecId, "version": version},
                "data": {"format": format},
                "params": {"dataSetId": datasetId},
            }
            res: dict = self.connector.postData(self.endpoint + path, data=obj)
        return res

    def createTargetConnectionDataLandingZone(
        self,
        name: str = None,
        format: str = "delimited",
        path: str = None,
        type: str = "file",
        version: str = "1.0",
        description: str = "",
        spec_name: str = "Data Landing Zone"
    ) -> dict:
        """
        Create a target connection to the Data Landing Zone
        Arguments:
                name : REQUIRED : The name of the target connection
                format : REQUIRED : Data format to be used
                path : REQUIRED : The path to the data you want to ingest. Can be a single file or folder.
                type : OPTIONAL : Use "file" if path refers to individual file, otherwise "folder".
                version : REQUIRED : version of your target destination
                description : OPTIONAL : description of your target destination.
                spec_name : OPTIONAL : The name of the target specification corresponding to Data Lake.
        """
        if name is None:
            raise ValueError("Require a name for the connection")
        spec_id = self.getConnectionSpecIdFromName(spec_name)
        obj = {
            "name": name,
            "description": description,
            "data": {
                "format": format
            },
            "params": {
                "path": path,
                "type": type
            },
            "connectionSpec": {
                "id": spec_id,
                "version": version
            }
        }
        if self.loggingEnabled:
            self.logger.debug(f"Starting createTargetConnectionDataLandingZone")
        res = self.createTargetConnection(data=obj)
        return res
    
    def createTargetConnectionDatasetToDataLandingZone(
        self,
        name: str = None,
        baseConnectionId: str = None,
        path: str = None,
        datasetFileType: str = "JSON",
        compression:str= "GZIP",
        version: str = "1.0",
        description: str = "power by aepp"
    ) -> dict:
        """
        Create a target connection to the Data Landing Zone
        Arguments:
                name : REQUIRED : The name of the target connection
                baseConnectionId : REQUIRED : The base connection ID you have used which define the dataset to export.
                path : REQUIRED : The path to the data you want to ingest. Can be a single file or folder.
                datasetFileType : OPTIONAL : Default JSON compressed data, other possible value "PARQUET".
                compression : OPTIONAL : If you wish to compress the file (default: GZIP, other value : NONE). JSON file cannot be sent uncompressed.
                version : REQUIRED : version of your target destination
                description : OPTIONAL : description of your target destination.
        """
        if name is None:
            raise ValueError("Require a name for the connection")
        if baseConnectionId is None:
            raise Exception("Require a base connection ID")
        obj = {
            "name": name,
            "description" : description,
            "baseConnectionId": baseConnectionId,
            "params": {
                "mode": "Server-to-server",
                "path": path,
                "compression": compression,
                "datasetFileType": datasetFileType
            },
            "connectionSpec": {
                "id": "10440537-2a7b-4583-ac39-ed38d4b848e8",
                "version": version
            }
        }
        if self.loggingEnabled:
            self.logger.debug(f"Starting createTargetConnectionDatasetToDataLandingZone")
        res = self.createTargetConnection(data=obj)
        return res


    def createTargetConnectionDataLake(
        self,
        name: str = None,
        datasetId: str = None,
        schemaId: str = None,
        format: str = "delimited",
        version: str = "1.0",
        description: str = "",
        spec_name: str = "datalake"
    ) -> dict:
        """
        Create a target connection to the AEP Data Lake.
        Arguments:
            name : REQUIRED : The name of your target Destination
            datasetId : REQUIRED : the dataset ID of your target destination.
            schemaId : REQUIRED : The schema ID of your dataSet. (NOT meta:altId)
            format : REQUIRED : format of your data inserted
            version : REQUIRED : version of your target destination
            description : OPTIONAL : description of your target destination.
            spec_name : OPTIONAL : The name of the target specification corresponding to Data Lake.
        """
        if name is None:
            raise ValueError("Require a name for the connection")
        spec_id = self.getConnectionSpecIdFromName(spec_name)
        targetObj = {
            "name": name,
            "description": description,
            "data": {
                "format": format,
                "schema": {
                    "id": schemaId,
                    "version": "application/vnd.adobe.xed-full+json;version=1.0",
                },
            },
            "params": {"dataSetId": datasetId},
            "connectionSpec": {
                "id": spec_id,
                "version": version,
            },
        }
        if self.loggingEnabled:
            self.logger.debug(f"Starting createTargetConnectionDataLake")
        res = self.createTargetConnection(data=targetObj)
        return res

    def updateTargetConnection(
        self, targetConnectionId: str = None, etag: str = None, updateObj: list = None
    ) -> dict:
        """
        Update a target connection based on the ID provided with the object provided.
        Arguments:
            targetConnectionId : REQUIRED : The target connection ID to be updated
            etag: REQUIRED : A header containing the etag value of the connection or flow to be updated.
            updateObj : REQUIRED : The operation call used to define the action needed to update the connection. Operations include add, replace, and remove.
        """
        if targetConnectionId is None:
            raise Exception("Require a sourceConnection to be present")
        if etag is None:
            raise Exception("Require etag to be present")
        if updateObj is None:
            raise Exception("Require a dictionary with data to be present")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateTargetConnection")
        privateHeader = deepcopy(self.header)
        privateHeader["if-match"] = etag
        path: str = f"/targetConnections/{targetConnectionId}"
        res: dict = self.connector.patchData(
            self.endpoint + path, headers=privateHeader, data=updateObj
        )
        return res
    
    def updatePolicy(self,flowId:str=None, policies:Union[list,str]=None, operation:str="Replace")->dict:
        """
        By passing the policy IDs as a list, we update the Policies apply to this Flow.
        Arguments:
            flowId : REQUIRED : The Flow ID to be updated
            policies : REQUIRED : The list of policies Id to add to the Flow
                example of value: "/dulepolicy/marketingActions/06621fe3q-44t3-3zu4t-90c2-y653rt3hk4o499"
            operation : OPTIONAL : By default "replace" the current policies. It can be an "add" operation.
        """
        if flowId is None:
            raise ValueError("Require a Flow ID")
        if policies is None:
            raise ValueError("Require a list of policy ID")
        if type(policies) == str:
            policies = [policies]
        if type(policies) != list:
            raise TypeError("The policiy ID were not passed via a string or a list of string")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updatePolicy")
        op = [
            {
                "op" : operation,
                "path":"/policy",
                "value":{
                    "enforcementRefs":policies
                }

            }
        ]
        res = self.updateFlow(flowId=flowId, operation=op)
        return res
    
    def getLandingZoneContainer(
        self,
        dlz_type: str = "user_drop_zone"
    ) -> dict:
        """
        Returns a dictionary of the available Data Landing Zone container information.
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getLandingZoneContainer")
        path = f"/data/foundation/connectors/landingzone"
        params = {"type": dlz_type}
        res = self.connector.getData(self.endpoint_gloal + path, params=params)
        return res

    @deprecation.deprecated(deprecated_in="0.3.4", details="Use getLandingZoneStorageName instead")
    def getLandingZoneContainerName(
        self,
        dlz_type: str = "user_drop_zone"
    ) -> str:
        """
        Returns the name of the DLZ container corresponding to this type.
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        return self.getLandingZoneContainer(dlz_type=dlz_type)["containerName"]

    def getLandingZoneStorageName(
        self,
        dlz_type: str = "user_drop_zone"
    ) -> str:
        """
        Returns the name of the DLZ storage corresponding to this type.
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        response = self.getLandingZoneContainer(dlz_type=dlz_type)
        if self._isAzureLandingZone(response):
            return response["containerName"]
        else:
            return response["dlzPath"]["dlzFolder"]

    @deprecation.deprecated(deprecated_in="0.3.4", details="Use getLandingZoneStorageTTL instead")
    def getLandingZoneContainerTTL(
        self,
        dlz_type: str = "user_drop_zone"
    ) -> int:
        """
        Returns the TTL in days of the DLZ container corresponding to this type.
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        return int(self.getLandingZoneContainer(dlz_type=dlz_type)["containerTTL"])

    def getLandingZoneStorageTTL(
            self,
            dlz_type: str = "user_drop_zone"
    ) -> int:
        """
        Returns the TTL in days of the DLZ storage corresponding to this type.
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        response = self.getLandingZoneContainer(dlz_type=dlz_type)
        if self._isAzureLandingZone(response):
            return int(response["containerTTL"])
        else:
            return int(response["dataTTL"]['timeQuantity'])

    def _isAzureLandingZone(self, landingZoneResponse) -> bool:
        """
        Inspects landingZoneResponse structure, if "dlzProvider" - is present and value is not 'Amazon S3' flags it as Azure;
        Arguments:
            landingZoneResponse : REQUIRED : response object of landingzone or landingzone/credentials invocation
        """
        return not ('dlzProvider' in landingZoneResponse and landingZoneResponse['dlzProvider'] == 'Amazon S3')

    def getLandingZoneCredential(
        self,
        dlz_type: str = "user_drop_zone"
    ) -> dict:
        """
        Returns a dictionary with the credential to be used in order to create a new zone
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getLandingZoneCredential")
        path = f"/data/foundation/connectors/landingzone/credentials"
        params = {"type": dlz_type}
        res = self.connector.getData(self.endpoint_gloal + path,params=params)
        return res

    def getLandingZoneSASUri(
        self,
        dlz_type: str = "user_drop_zone"
    ) -> str:
        """
        Returns the SAS URI of the DLZ container corresponding to this type.
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        response = self.getLandingZoneCredential(dlz_type=dlz_type)
        if self._isAzureLandingZone(response):
            return response["SASUri"]
        else:
            raise Exception("Not Azure Landing Zone, consider using getLandingZoneCredential instead")

    def getLandingZoneSASToken(
        self,
        dlz_type: str = "user_drop_zone"
    ) -> str:
        """
        Returns the SAS token of the DLZ container corresponding to this type.
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        response = self.getLandingZoneCredential(dlz_type=dlz_type)
        if self._isAzureLandingZone(response):
            return response["SASToken"]
        else:
            raise Exception("Not Azure Landing Zone, consider using getLandingZoneCredential instead")

    @deprecation.deprecated(deprecated_in="0.3.4", details="Use getLandingZoneNamespace instead")
    def getLandingZoneStorageAccountName(
        self,
        dlz_type: str = "user_drop_zone"
    ) -> str:
        """
        Returns the storage account name of the DLZ container corresponding to this type.
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        return self.getLandingZoneCredential(dlz_type=dlz_type)["storageAccountName"]

    def getLandingZoneNamespace(
            self,
            dlz_type: str = "user_drop_zone"
    ) -> str:
        """
        Returns either:
          'storage account name' of the DLZ storage if provisioned on Azure
           or
          's3 bucket name' of the DLZ storage if provisioned on Amazon
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        response = self.getLandingZoneCredential(dlz_type=dlz_type)
        if self._isAzureLandingZone(response):
            return response["storageAccountName"]
        else:
            return response["dlzPath"]["bucketName"]

    def exploreLandingZone(self,objectType:str='root',fileType:str=None,object:str=None)->list:
        """
        Return the structure of your landing zones
        Arguments:
            objectType : OPTIONAL : The type of the object you want to access.(root (default), folder, file)
            fileType : OPTIONAL : The type of the file to see. (delimited, json, parquet )
            object : OPTIONAL : To be used to defined the path when you are using the "folder" or "file" attribute on objectType
        """
        path ="/connectionSpecs/26f526f2-58f4-4712-961d-e41bf1ccc0e8/explore"
        params = {"objectType":objectType}
        if objectType == "folder":
            params['object'] = object
        if fileType is not None:
            params['fileType'] = fileType
        res = self.connector.getData(self.endpoint + path,params=params)
        return res

    def getLandingZoneContent(self,fileType:str="delimited",file:str=None,determineProperties:bool=True,preview:bool=True)->list:
        """
        Return the structure of your landing zones
        Arguments:
            fileType : OPTIONAL : The type of the file to see.
                Possible option : "delimited", "json" or "parquet"
            file : OPTIONAL : the path to the specific file.
            determineProperties : OPTIONAL : replace other parameter to auto-detect file properties.
            preview : OPTIONAL : If you wish to see a preview of the file.
        """
        path ="/connectionSpecs/26f526f2-58f4-4712-961d-e41bf1ccc0e8/explore"
        params = {"objectType":"file","preview":preview,}
        if determineProperties:
            params['determineProperties'] = True
        if determineProperties == False and fileType is not None:
            params['FILE_TYPE'] = fileType
        if file:
            params['object'] = file
        res = self.connector.getData(self.endpoint + path,params=params)
        return res

    def postFlowAction(self,flowId:str,action:str)->dict:
        """
        Define a flow action to realize.
        Arguments:
            flowId : REQUIRED : The flow ID to pass the action
            action : REQUIRED : The type of action to pass
        """
        if flowId is None:
            raise Exception("Requires a flowId to be present")
        if action is None:
            raise Exception("Requires an action to be present")
        path = "/flows/" + flowId + "/action?op=" + action
        privateHeader = deepcopy(self.header)
        privateHeader.pop("Content-Type")
        res = self.connector.postData(endpoint=self.endpoint + path, headers=privateHeader)
        return res
    
    def getExportableDatasets(self,connectionSpec:str=None,)->list:
        """
        Retrieve the exportable dataset 
        Arguments:
            connectionSpec : REQUIRED : The connection Spec used for the flow 
        """
        path = f"/connectionSpecs/{connectionSpec}/configs"
        params = {"outputType":"activationDatasets","outputField":"datasets","limit":100,"start":0}
        res = self.connector.getData(self.endpoint+path,params=params)
        items = res.get('items',[])
        hasnext = res.get('pageInfo',{}).get('hasNext',False)
        while hasnext:
            params["start"] += 100
            res = self.connector.getData(self.endpoint+path,params=params)
            items += res.get('items',[])
            hasnext = res.get('pageInfo',{}).get('hasNext',False)
        return items
    
    def getExportableDatasetsDLZ(self)->list:
        """
        Return the exportable dataset to Data Landing Zone
        """
        results = self.getExportableDatasets('10440537-2a7b-4583-ac39-ed38d4b848e8')
        return results


    def createBaseConnectionS3Target(self,name:str=None,s3AccessKey:str=None,s3SecretKey:str=None)->dict:
        """
        Create a base connection for S3 storage as Target.
        Arguments:
            name : REQUIRED : Name of the connectionBase
            s3AccessKey : REQUIRED : The S3 Access Key to access the storage
            s3SecretKey : REQUIRED : The S3 Secret Key to access the storage
        """
        if name is None or s3AccessKey is None or s3SecretKey is None:
            raise Exception("The required parameters are not filled")
        data = {"name": name,
        "auth": {
                "specName": "Access Key",
                "params": {
                "s3SecretKey": s3SecretKey,
                "s3AccessKey": s3AccessKey
                }
            },
            "connectionSpec": {
                "id": "4fce964d-3f37-408f-9778-e597338a21ee",
                "version": "1.0"
            }
        }
        res = self.createConnection(data)
        return res

    def createBaseConnectionBlobTarget(self,name:str=None,connectionString:str=None)->dict:
        """
        Create a base connection for Blob Storage as Target. 
        Use the connection string auth passed by Azure Blob Storage.
        Arguments:
            name : REQUIRED : Name of your base connection
            connectionString : REQUIRED : Connection string used to authenticate to Blob Storage
        """
        if name is None or connectionString is None:
            raise Exception("Required parameters are not filled")
        data = {
            "name": name,
            "auth": {
                "specName": "ConnectionString",
                "params": {
                "connectionString": connectionString
                }
            },
            "connectionSpec": {
                "id": "6d6b59bf-fb58-4107-9064-4d246c0e5bb2",
                "version": "1.0"
            }
        }
        res = self.createConnection(data)
        return res
    
    def createBaseConnectionDLZTarget(self,name:str=None)->dict:
        """
        Create a Connection for Data Landing Zone as Target 
        Arguments:
            name : REQUIRED : The name of your Data Landing Zone
        """
        if name is None:
            Exception("Require a name for the connection")
        data = {
            "name": name,
            "connectionSpec": {
                "id": "10440537-2a7b-4583-ac39-ed38d4b848e8",
                "version": "1.0"
            }
        }
        res = self.createConnection(data)
        return res
    
    def exportDatasetToDLZ(self,
                           datasetIds:list=None,
                           path:str="/aepp",
                           fileType:str="JSON",
                           compression:str="GZIP",
                           exportMode:str="FIRST_FULL_THEN_INCREMENTAL",
                           scheduleStart:str=None,
                           scheduleEnd:str=None,
                           scheduleUnit:str="day",
                           scheduleInterval:str="1",
                           baseConnection:str="base-dataset-export-dlz",
                           sourceConnection:str="source-dataset-export-dlz",
                           targetConnection:str="target-dataset-export-dlz",
                           flowname:str="flow-dataset-export-dlz",
                           )->dict:
        """
        Create a Flow to export a specific dataset to your data landing zone.
        Taking care of creating a base, source, target and the related specification in DLZ.
        Arguments:
            datasetIds : REQUIRED : The list of datasetId that needs to be exported.
            path : REQUIRED : The path that will be used in DLZ to export the data (default:aepp)
            fileType : REQUIRED : can be JSON (default),PARQUET or DELIMITED (CSV)
            compression : REQUIRED : JSON are automatically compressed. Only PARQUET can not be compressed.
            exportMode: REQUIRED : Can be "FIRST_FULL_THEN_INCREMENTAL" (default) or "DAILY_FULL_EXPORT"
            scheduleStart : REQUIRED : The UNIX seconds when to start the flow runs
            scheduleEnd : OPTIONAL : The UNIX seconds when to end the flow runs
            scheduleUnit : OPTIONAL : The unit used to define intervals to send new files, by default "day", "hour" supported
            scheduleInterval : OPTIONAL : Interval between 2 export.
            baseConnection : OPTIONAL : Base Connection name, by default "base-dataset-export-dlz" + date
            sourceConnection : OPTIONAL : Source Connection name, by default "source-dataset-export-dlz" + date
            targetConnection : OPTIONAL : Target Connection name, by default "target-dataset-export-dlz" + date
            flowname : OPTIONAL : Name of your flow, by default "flow-dataset-export-dlz" + date
        """
        date = datetime.datetime.now().date().isoformat()
        if baseConnection == "base-dataset-export-dlz":
            baseConnection = f"{baseConnection} {date}"
        if sourceConnection == "source-dataset-export-dlz":
            sourceConnection = f"{sourceConnection} {date}"
        if targetConnection == "target-dataset-export-dlz":
            targetConnection = f"{targetConnection} {date}"
        if flowname == "flow-dataset-export-dlz":
            flowname = f"{flowname} {date}"
        if type(datasetIds) == str:
            if ',' in datasetIds:
                datasetIds = datasetIds.split(',')
            else:
                datasetIds = list(datasetIds)
        exportableDatasets = self.getExportableDatasetsDLZ()
        for dsId in datasetIds:
            if dsId not in [ds['id'] for ds in exportableDatasets]:
                raise Exception(f"{dsId} cannot be found on the list of exportable datasets for DLZ")
        if fileType == "JSON":
            compression = "GZIP"
        baseConn = self.createBaseConnectionDLZTarget(baseConnection)
        sourceConn = self.createSourceConnectionDataLake(sourceConnection,dataset_ids=datasetIds)
        targetConn = self.createTargetConnectionDatasetToDataLandingZone(targetConn,baseConnectionId=baseConn['id'],path=path,datasetFileType=fileType,compression=compression)
        flow = self.createFlowDataLakeToDataLandingZone(flowname,
                                                        source_connection_id=sourceConn['id'],
                                                        target_connection_id=targetConn['id'],
                                                        export_mode=exportMode,
                                                        schedule_start_time=scheduleStart,
                                                        schedule_end_time=scheduleEnd,
                                                        schedule_timeUnit=scheduleUnit,
                                                        schedule_interval = scheduleInterval
                                                        )
        return flow


class FlowManager:
    """
    A class that abstract the different information retrieved by the Flow ID in order to provide all relationships inside that Flow.
    It takes a flow id and dig to all relationship inside that flow.
    """

    def __init__(self,
                flowId:str=None,
                config: Union[dict,aepp.ConnectObject] = aepp.config.config_object
                )->None:
        """
        Instantiate a Flow Manager Instance based on the flow ID.
        Arguments:
            flowId : REQUIRED : A flow ID
            config : OPTIONAL : The configuration to the sandbox and API
        """
        from aepp import schema, catalog,dataprep,flowservice
        self.schemaAPI = schema.Schema(config=config)
        self.catalogAPI = catalog.Catalog(config=config)
        self.mapperAPI = dataprep.DataPrep(config=config)
        self.flowAPI = flowservice.FlowService(config=config)
        self.flowData = self.flowAPI.getFlow(flowId)
        self.__setAttributes__(self.flowData)
        self.flowMapping = None
        self.frequency = None
        self.datasetId = None
        self.flowSpec = {'id' : self.flowData.get('flowSpec',{}).get('id')}
        self.flowSourceConnection = {'id' : self.flowData.get('sourceConnectionIds',[None])[0]}
        self.flowTargetConnection = {'id' : self.flowData.get('targetConnectionIds',[None])[0]}
        self.connectionInfo = {'id':self.flowData.get('sourceConnectionIds',[""])[0]}
        for trans in self.flowData.get('transformations',[{}]):
            if trans.get('name') == 'Mapping':
                self.flowMapping = {'id':trans.get('params',{}).get('mappingId')}
        ## Flow Spec part
        if self.flowSpec['id'] is not None:
            flowSpecData = self.flowAPI.getFlowSpec(self.flowSpec['id'])
            self.flowSpec['name'] = flowSpecData['name']
            self.flowSpec['frequency'] = flowSpecData.get('attributes',{}).get('frequency')
        ## Source Connection part
        if self.flowSourceConnection['id'] is not None:
            sourceConnData = self.flowAPI.getSourceConnection(self.flowSourceConnection['id'])
            self.flowSourceConnection['data'] = sourceConnData.get('data')
            self.flowSourceConnection['params'] = sourceConnData.get('params')
            self.flowSourceConnection['connectionSpec'] = sourceConnData.get('connectionSpec')
            if self.flowSourceConnection['connectionSpec'].get('id') is not None:
                connSpec = self.flowAPI.getConnectionSpec(self.flowSourceConnection['connectionSpec'].get('id'))
                self.flowSourceConnection['connectionSpec']['name'] = connSpec.get('name')
                self.connectionInfo['name'] = connSpec.get('name')
            if connSpec.get('sourceSpec',{}).get('attributes',{}).get('uiAttributes',{}).get('isSource',False):
                self.connectionType = 'source'
            elif  connSpec.get('attributes',{}).get('isDestination',False):
                self.connectionType = 'destination'
            frequency = connSpec.get('sourceSpec',{}).get('attributes',{}).get('uiAttributes',{}).get('frequency',{}).get('key')
            if frequency is not None:
                self.frequency = frequency
        ## Target Connection part
        if self.flowTargetConnection['id'] is not None:
            targetConnData = self.flowAPI.getTargetConnection(self.flowTargetConnection['id'])
            self.flowTargetConnection['name']:str = targetConnData.get('name')
            self.flowTargetConnection['data']:dict = targetConnData.get('data',{})
            self.flowTargetConnection['params']:dict = targetConnData.get('params',{})
            for key, value in self.flowTargetConnection['params'].items():
                if key == 'datasetId':
                    self.datasetId = value
            self.flowTargetConnection['connectionSpec']:dict = targetConnData.get('connectionSpec',{})
            if self.flowTargetConnection['connectionSpec'].get('id',None) is not None:
                connSpec = self.flowAPI.getConnectionSpec(self.flowSourceConnection['connectionSpec'].get('id'))
                self.flowTargetConnection['connectionSpec']['name'] = connSpec.get('name')
        ## Catalog part
        if 'dataSetId' in self.flowTargetConnection.get('params',{}).keys():
            datasetInfo = self.catalogAPI.getDataSet(self.flowTargetConnection['params']['dataSetId'])
            if 'status' in datasetInfo.keys():
                if datasetInfo['status'] == 404:
                    self.flowTargetConnection['params']['datasetName'] = 'DELETED'
            else:
                self.flowTargetConnection['params']['datasetName'] = datasetInfo[list(datasetInfo.keys())[0]].get('name')
                self.datasetId = self.flowTargetConnection['params']['dataSetId']
        ## Schema part
        if 'schema' in self.flowTargetConnection.get('data',{}).keys():
            if self.flowTargetConnection.get('data',{}).get('schema',None) is not None:
                ## handling inconsistency in the response
                schemaId = self.flowTargetConnection['data']['schema'].get('id',self.flowTargetConnection['data']['schema'].get('schemaId',None))
                if schemaId is not None:
                    schemaInfo = self.schemaAPI.getSchema(schemaId,full=False)
                    self.flowTargetConnection['data']['schema']['name'] = schemaInfo.get('title')
        ## Mapping
        if self.flowMapping is not None:
            mappingInfo = self.mapperAPI.getMappingSet(self.flowMapping['id'])
            if 'createdDate' in mappingInfo.keys():
                self.flowMapping['createdDate'] = time.ctime(mappingInfo.get('createdDate',1000)/1000)
                self.flowMapping['createdDateTS'] = mappingInfo.get('createdDate')
                self.flowMapping['updatedAtTS'] = mappingInfo.get('updatedAt',None)
                self.flowMapping['updatedAt'] = time.ctime(mappingInfo.get('updatedAt',0)/1000)
            else:
                self.flowMapping['createdDate'] = None
                self.flowMapping['createdDateTS'] = None
                self.flowMapping['updatedAtTS'] = None
                self.flowMapping['updatedAt'] = None
            self.getMapping = lambda : self.mapperAPI.getMappingSet(self.flowMapping['id'])

    def __setAttributes__(self,flowData:dict)->None:
        """
        Set the attributes
        """
        self.id = flowData.get('id')
        self.etag = flowData.get('etag')
        self.sandbox = flowData.get('sandboxName')
        self.name = flowData.get('name')
        self.version = flowData.get('version')
        self.state = flowData.get('state')
        self.createdAt = flowData.get('createdAt')
        self.lastRunStartedUTC = flowData.get('lastRunDetails',{}).get('startedAtUTC')

    def __repr__(self)->str:
        data = {
                "id" : self.id,
                "name": self.name,
                "version":self.version,
                "connectionName" : self.connectionInfo.get('name','unknown'),
                "frequency" : self.frequency,
                "flowSpecs": self.flowSpec,
                "sourceConnection": self.flowSourceConnection,
                "targetConnection": self.flowTargetConnection,
            }
        if self.flowMapping is not None:
            data['mapping'] = self.flowMapping
        return json.dumps(data,indent=2)

    def __str__(self)->str:
        data = {
                "id" : self.id,
                "name": self.name,
                "version":self.version,
                "connectionName" : self.connectionInfo.get('name','unknown'),
                "frequency" : self.frequency,
                "flowSpecs": self.flowSpec,
                "sourceConnection": self.flowSourceConnection,
                "targetConnection": self.flowTargetConnection,
            }
        if self.flowMapping is not None:
            data['mapping'] = self.flowMapping
        return json.dumps(data,indent=2)

    def summary(self):
        data = {
                "id" : self.id,
                "name": self.name,
                "version":self.version,
                "connectionName" : self.connectionInfo.get('name','unknown'),
                "frequency" : self.frequency,
                "flowSpecs": self.flowSpec,
                "sourceConnection": self.flowSourceConnection,
                "targetConnection": self.flowTargetConnection,
            }
        if self.flowMapping is not None:
            data['mapping'] = self.flowMapping
        return data

    def getFlowSpec(self)->dict:
        """
        Return a dictionary of the flow Spec.
        """
        if self.flowSpec['id'] is not None:
            flowSpecData = self.flowAPI.getFlowSpec(self.flowSpec['id'])
            return flowSpecData

    def getSourceConnection(self)->dict:
        """
        Return a dictionary of the connection information
        """
        if self.flowSourceConnection['id'] is not None:
            sourceConnData = self.flowAPI.getSourceConnection(self.flowSourceConnection['id'])
            return sourceConnData

    def getConnectionSpec(self)->dict:
        """
        return a dictionary of the source connection spec information
        """
        if self.flowSourceConnection['connectionSpec'].get('id') is not None:
            connSpec = self.flowAPI.getConnectionSpec(self.flowSourceConnection['connectionSpec'].get('id'))
            return connSpec

    def getTargetConnection(self)->dict:
        """
        return a dictionary of the target connection
        """
        if self.flowTargetConnection['id'] is not None:
            targetConnData = self.flowAPI.getTargetConnection(self.flowTargetConnection['id'])
            return targetConnData

    def getTargetConnectionSpec(self)->dict:
        """
        return a dictionary of the target connection spec
        """
        if self.flowTargetConnection['connectionSpec'].get('id') is not None:
            connSpec = self.flowAPI.getConnectionSpec(self.flowSourceConnection['connectionSpec'].get('id'))
            return connSpec

    def getRuns(self,limit:int=10,n_results=100,prop:str=None)->list:
        """
        Returns the last run of the flow.
        Arguments:
            limit : OPTIONAL : Amount of item per requests
            n_results : OPTIONAL : Total amount of item to return
            prop : OPTIONAL : Property to filter the flow
        """
        props = [f"flowId=={self.id}"]
        if prop is not None:
            props.append(prop)
        runs = self.flowAPI.getRuns(limit,n_results,prop=props)
        return runs

    def updateFlow(self, operations:list=None)->dict:
        """
        Update the flow with the operation provided.
        Argument:
            operations : REQUIRED : The operation to set on the PATCH method
                Example :
            [
                {
                    "op": "Add",
                    "path": "/auth/params",
                    "value": {
                    "description": "A new description to provide further context on a specified connection or flow."
                    }
                }
            ]
        """
        if operations is None:
            raise ValueError("No operations has been passed")
        res = self.flowAPI.updateFlow(self.id,self.etag,operations)
        self.flowData = res
        self.__setAttributes__(res)
        return res

    def updateFlowMapping(self,mappingId:str)->dict:
        """
        Update the flow with the latest version of the mapping Id provided.
        Arguments:
            mappingId : REQUIRED : The mapping Id to be used for update.
        """
        transformations = deepcopy(self.flowData.get('transformations',{}))
        myMapping = self.mapperAPI.getMappingSet(mappingId)
        myVersion = myMapping.get('version',0)
        operation = {}
        myIndex = None
        for index, transformation in enumerate(transformations):
            if transformation.get('name') == 'Mapping':
                myIndex=index
                operation['mappingId'] = mappingId
                operation['mappingVersion'] = myVersion
        if myIndex is not None:
            patchOperation = [{'op': 'replace',
            'path': f'/transformations/{myIndex}',
            'value': {'name': 'Mapping',
            'params': {'mappingId': operation['mappingId'],
            'mappingVersion': operation['mappingVersion']}}}
            ]
        else:
            raise Exception('Could not find a mapping transformation in the flow')
        res = self.updateFlow(patchOperation)
        self.flowData = res
        self.__setAttributes__(res)
        return res
