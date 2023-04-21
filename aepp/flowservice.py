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
from dataclasses import dataclass
from typing import Union
from .configs import ConnectObject

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
            auth : REQUIRED : dictionary that contains "specName" and "params"
                specName : string that names of the the type of authentication to be used with the base connection.
                params : dict that contains credentials and values necessary to authenticate and create a connection.
            connectionSpec : REQUIRED : dictionary containing the "id" and "verison" key.
                id : The specific connection specification ID associated with source
                version : Specifies the version of the connection specification ID. Omitting this value will default to the most recent version
        Possible kwargs:
            responseType : by default json, but you can request 'raw' that return the requests response object.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createConnection")
        path = "/connections"
        if data is not None:
            if (
                "name" not in data.keys()
                or "auth" not in data.keys()
                or "connectionSpec" not in data.keys()
            ):
                raise Exception(
                    "Require some keys to be present : name, auth, connectionSpec"
                )
            obj = data
            res = self.connector.postData(self.endpoint + path, data=obj,format=kwargs.get('responseType','json'))
            return res
        elif data is None:
            if "specName" not in auth.keys() or "params" not in auth.keys():
                raise Exception(
                    "Require some keys to be present in auth dict : specName, params"
                )
            if "id" not in connectionSpec.keys():
                raise Exception(
                    "Require some keys to be present in connectionSpec dict : id"
                )
            if name is None:
                raise Exception("Require a name to be present")
            obj = {"name": name, "auth": auth, "connectionSpec": connectionSpec}
            res = self.connector.postData(self.endpoint + path, data=obj,format=kwargs.get('responseType','json'))
            return res

    def createStreamingConnection(
        self,
        name: str = None,
        sourceId: str = None,
        dataType: str = "xdm",
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
        Arguments:
            name : REQUIRED : Name of the Connection.
            sourceId : REQUIRED : The ID of the streaming connection you want to create (random string possible).
            dataType : REQUIRED : The type of data to ingest (default xdm)
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
        limit: int = 10,
        n_results: int = 100,
        prop: str = None,
        filterMappingSetIds: list = None,
        filterSourceIds: list = None,
        filterTargetIds: list = None,
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
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFlows")
        params: dict = {"limit": limit, "count": kwargs.get("count", False)}
        if property is not None:
            params["property"] = prop
        if kwargs.get("continuationToken", False) != False:
            params["continuationToken"] = kwargs.get("continuationToken")
        path: str = "/flows"
        res: dict = self.connector.getData(self.endpoint + path, params=params)
        token: str = res.get("_links", {}).get("next", {}).get("href", "")
        items = res["items"]
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
        schedule_frequency: str = "minute",
        schedule_interval: int = 15,
        transformation_mapping_id: str = None,
        transformation_name: str = None,
        transformation_version: int = 0,
        obj: dict = None,
        version: str = "1.0"
    ) -> dict:
        """
        Create a flow with the API.
        Arguments:
            obj : REQUIRED : body to create the flow service.
                Details can be seen at https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Flows/postFlow
                requires following keys : name, flowSpec, sourceConnectionIds, targetConnectionIds, transformations, scheduleParams.
        """
        if obj is None:
            if any(param is None for param in [name, source_connection_id, target_connection_id]):
                raise KeyError("Require either obj or all of 'name', 'source_connection_id', 'target_connection_id'")
            if schedule_frequency not in ("minute", "hour"):
                raise ValueError("schedule frequency has to be either minute or hour")
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
            if schedule_start_time is not None:
                obj["scheduleParams"]["startTime"] = schedule_start_time
            if schedule_frequency is not None:
                obj["scheduleParams"]["frequency"] = schedule_frequency
            if schedule_interval is not None:
                obj["scheduleParams"]["interval"] = str(schedule_interval)
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

    def createFlowDataLakeToDataLandingZone(
        self,
        name: str,
        source_connection_id: str,
        target_connection_id: str,
        schedule_start_time: str,
        schedule_frequency: str = "hour",
        schedule_interval: int = 3,
        transformation_mapping_id: str = None,
        transformation_name: str = None,
        transformation_version: int = 0,
        version: str = "1.0",
        flow_spec_name: str = "Data Landing Zone",
        source_spec_name: str = "activation-datalake",
        target_spec_name: str = "Data Landing Zone"
    ) -> dict:
        """
        Create a Data Flow to move data from Data Lake to the Data Landing Zone.
        Arguments:
            name : REQUIRED : The name of the Data Flow.
            source_connection_id : REQUIRED : The ID of the source connection tied to Data Lake.
            target_connection_id : REQUIRED : The ID of the target connection tied to Data Landing Zone.
            schedule_start_time : REQUIRED : The time from which the Data Flow should start running.
            schedule_frequency : OPTIONAL : The granularity of the Data Flow. Currently only "hour" supported.
            schedule_interval : OPTIONAL : The interval on which the Data Flow runs. Either 3, 6, 9, 12 or 24. Default to 3.
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
        Return the Flow specification ID corresponding to some conditions..
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
        self, limit: int = 10, n_results: int = 100, prop: str = None, **kwargs
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
            params["property"] = prop
        if kwargs.get("continuationToken", False):
            params["continuationToken"] = kwargs.get("continuationToken")
        res: dict = self.connector.getData(self.endpoint + path, params=params)
        items: list = res.get("items",[])
        nextPage = res["_links"].get("next", {}).get("href", "")
        while nextPage != "" and len(items) < float(n_results):
            token: str = res["_links"]["next"].get("href", "")
            continuationToken: str = token.split("=")[1]
            params["continuationToken"] = continuationToken
            res = self.connector.getData(self.endpoint + path, params=params)
            items += res.get('items')
            nextPage = res["_links"].get("next", {}).get("href", "")
        return items

    def createRun(self, flowId: str = None, status: str = "active") -> dict:
        """
        Generate a run based on the flowId.
        Arguments:
            flowId : REQUIRED : the flow ID to run
            stats : OPTIONAL : Status of the flow
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
        description: str = "",
        spec_name: str = "Streaming Connection"
    ) -> dict:
        """
        Create a source connection based on streaming connection created.
        Arguments:
            connectionId : REQUIRED : The Streaming connection ID.
            name : REQUIRED : Name of the Connection.
            format : REQUIRED : format of the data sent (default : delimited)
            description : REQUIRED : Description of of the Connection Source.
            spec_name : OPTIONAL : The name of the source specification corresponding to Streaming.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createSourceConnectionStreaming")
        spec_id = self.getConnectionSpecIdFromName(spec_name)
        obj = {
            "name": name,
            "providerId": "521eee4d-8cbe-4906-bb48-fb6bd4450033",
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
        kwargs will be added as query parameterss
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
        return self.getLandingZoneCredential(dlz_type=dlz_type)["SASUri"]

    def getLandingZoneSASToken(
        self,
        dlz_type: str = "user_drop_zone"
    ) -> str:
        """
        Returns the SAS token of the DLZ container corresponding to this type.
        Arguments:
            dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"
        """
        return self.getLandingZoneCredential(dlz_type=dlz_type)["SASToken"]

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

    def exploreLandingZone(self,fileType:str='delimited')->list:
        """
        Return the structure of your landing zones
        Arguments:
            fileType : OPTIONAL : The type of the file to see.
        """
        path ="/connectionSpecs/26f526f2-58f4-4712-961d-e41bf1ccc0e8/explore"
        params = {"objectType":"root"}
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
    





class FlowManager:
    """
    A class that abstract the different information retrieved by the Flow ID in order to provide all relationships inside that Flow.
    It takes a flow id and dig to all relationship inside that flow.
    """

    def __init__(self,
                flowId:str=None,
                config: dict = aepp.config.config_object,
                header=aepp.config.header)->None:
        """
        Instantiate a Flow Manager Instance based on the flow ID.
        Arguments:
            flowId : REQUIRED : A flow ID
        """
        from aepp import schema, catalog,dataprep,flowservice
        self.schemaAPI = schema.Schema()
        self.catalogAPI = catalog.Catalog()
        self.mapperAPI = dataprep.DataPrep()
        self.flowAPI = flowservice.FlowService()
        self.flowData = self.flowAPI.getFlow(flowId)
        self.__setAttributes__(self.flowData)
        self.flowMapping = None
        self.flowSpec = {'id' : self.flowData.get('flowSpec',{}).get('id')}
        self.flowSourceConnection = {'id' : self.flowData.get('sourceConnectionIds',[None])[0]}
        self.flowTargetConnection = {'id' : self.flowData.get('targetConnectionIds',[None])[0]}
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
        ## Target Connection part
        if self.flowTargetConnection['id'] is not None:
            targetConnData = self.flowAPI.getTargetConnection(self.flowTargetConnection['id'])
            self.flowTargetConnection['name'] = targetConnData.get('name')
            self.flowTargetConnection['data'] = targetConnData.get('data')
            self.flowTargetConnection['params'] = targetConnData.get('params')
            self.flowTargetConnection['connectionSpec'] = targetConnData.get('connectionSpec')
            if self.flowTargetConnection['connectionSpec'].get('id') is not None:
                connSpec = self.flowAPI.getConnectionSpec(self.flowSourceConnection['connectionSpec'].get('id'))
                self.flowTargetConnection['connectionSpec']['name'] = connSpec.get('name')
        ## Catalog part
        if 'dataSetId' in self.flowTargetConnection['params'].keys():
            datasetInfo = self.catalogAPI.getDataSet(self.flowTargetConnection['params']['dataSetId'])
            self.flowTargetConnection['params']['datasetName'] = datasetInfo[list(datasetInfo.keys())[0]].get('name')
        ## Schema part
        if 'schema' in self.flowTargetConnection['data'].keys():
            schemaInfo = self.schemaAPI.getSchema(self.flowTargetConnection['data']['schema']['id'],full=False)
            self.flowTargetConnection['data']['schema']['name'] = schemaInfo.get('title')
        ## Mapping
        if self.flowMapping is not None:
            mappingInfo = self.mapperAPI.getMappingSet(self.flowMapping['id'])
            self.flowMapping['createdDate'] = time.ctime(mappingInfo.get('createdDate')/1000)
            self.flowMapping['createdDateTS'] = mappingInfo.get('createdDate')
            self.flowMapping['updatedAtTS'] = mappingInfo.get('updatedAt',None)
            if self.flowMapping['updatedAtTS'] is None:
                self.flowMapping['updatedAt'] = None
            else:
                self.flowMapping['updatedAt'] = time.ctime(mappingInfo.get('updatedAt',0)/1000)
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


    def __repr__(self)->str:
        data = {
                "id" : self.id,
                "name": self.name,
                "version":self.version,
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
                "flowSpecs": self.flowSpec,
                "sourceConnection": self.flowSourceConnection,
                "targetConnection": self.flowTargetConnection,
            }
        if self.flowMapping is not None:
            data['mapping'] = self.flowMapping
        return json.dumps(data,indent=2)

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
    
    def getRuns(self,limit:int=10,n_results=100)->list:
        """
        Returns the last run of the flow.
        Arguments:
            limit : OPTIONAL : Amount of item per requests
            n_results : OPTIONAL : Total amount of item to return
        """
        runs = self.flowAPI.getRuns(limit,n_results,prop=f"flowId=={self.id}")
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
            'params': {'mappingId': operation['params']['mappingId'],
            'mappingVersion': operation['params']['mappingVersion']}}}
            ]
        else:
            raise Exception('Could not find a mapping transformation in the flow')
        res = self.updateFlow(self.id,self.etag,patchOperation)
        self.flowData = res
        self.__setAttributes__(res)
        return res
