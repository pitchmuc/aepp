#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

# Internal Library
import aepp
from aepp import connector
import time
from concurrent import futures
import logging
from typing import Union
from copy import deepcopy
from .configs import ConnectObject


class Segmentation:
    """
    A class containing methods to use on segmentation.
    A complete documentation can be found here:
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/segmentation.yaml
    """

    ## logging capability
    loggingEnabled = False
    logger = None
    PLATFORM_AUDIENCE_DICT = {
                    "name": "People who ordered in the last 30 days",
                    "profileInstanceId": "ups",
                    "description": "This audience is generated to see people who ordered in the last 30 days.",
                    "type": "SegmentDefinition",
                    "expression": {
                        "type": "PQL",
                        "format": "pql/text",
                        "value": "workAddress.country = \"US\""
                    },
                    "schema": {
                        "name": "_xdm.context.profile"
                    },
                    "labels": [
                        "core/C1"
                    ],
                    "ttlInDays": 60
                }
    EXTERNAL_AUDIENCE_DICT = {
                    "audienceId": "test-external-audience-id",
                    "name": "externalSegment1",
                    "namespace": "aam",
                    "description": "This audience is generated to see people who ordered in the last 30 days.",
                    "type": "ExternalSegment",
                    "lifecycle": "published",
                    "datasetId": "6254cf3c97f8e31b639fb14d",
                    "labels": [
                        "core/C1"
                    ],
                    "audienceMeta": {
                        "segmentStatus": "ACTIVE",
                        "AAMFolderId": "325813-testnew"
                    },
                    "linkedAudienceRef": {
                        "flowId": "4685ea90-d2b6-11ec-9d64-0242ac120002"
                    }
                }  

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ) -> None:
        """
        Instanciate the segmentation API methods class-
        Arguments:
            loggingObject : OPTIONAL : logging object to log messages.
            config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
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
            aepp.config.endpoints["global"] + aepp.config.endpoints["segmentation"]
        )
        self.SCHEDULE_TEMPLATE = {
            "name": "profile-default",
            "type": "batch_segmentation-OR-export",
            "properties": {"segments": ["*"]},
            "schedule": "0 0 1 * * ?",
            "state": "inactive",
        }

    def getResource(self,endpoint:str=None, params:dict=None, **kwargs)->dict:
        """
        Abstract GET requests with header from the the connection.
        Arguments:
            endpoint : REQUIRED : the endpoint to use
            params : OPTIONAL : the parameters to use in the GET requests
        possible kwargs:
            all kwargs are passed to the header
        """
        if endpoint is None:
            raise ValueError("Endpoint is required")
        if type(params) != dict:
            raise TypeError("params should be a dictionary")
        parameters = {**params}
        myPrivateHeader = deepcopy(self.header)
        if kwargs is None:
            for key in kwargs:
                myPrivateHeader[key] = kwargs[key]
        res = self.connector.getData(endpoint, headers=myPrivateHeader,params=parameters)
        return res


    def getSegments(self, onlyRealTime: bool = False, **kwargs) -> list:
        """
        Return segment definitions in your experience platfom instance.
        Arguments:
            onlyRealTime : OPTIONAL : If you wish to retrieve only real time compatible segment. (default False)
        Possible arguments:
            - limit : number of segment returned per page
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSegments")
        params = {"limit": kwargs.get("limit", 100)}
        if onlyRealTime:
            params["evaluationInfo.continuous.enabled"] = True
        path = "/segment/definitions"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        if "segments" in res.keys():
            data = res["segments"]
        else:
            data = []
        total_pages = res["page"]["totalPages"]
        if total_pages > 1:
            nb_request = total_pages
            max_workers = min((total_pages, 5))
            list_parameters = [
                {"page": str(x), **params} for x in range(1, total_pages + 1)
            ]
            urls = [self.endpoint + path for x in range(1, total_pages + 1)]
            with futures.ThreadPoolExecutor(max_workers) as executor:
                res = executor.map(
                    lambda x, y: self.connector.getData(x, params=y),
                    urls,
                    list_parameters,
                )
            res = list(res)
            append_data = [
                val for sublist in [data["segments"] for data in res] for val in sublist
            ]  # flatten list of list
            data = data + append_data
        return data

    def getSegment(self, segment_id: str = None) -> dict:
        """
        Return a specific segment definition.
        Argument:
            segment_id : REQUIRED : Segment ID of the segment to be retrieved.
        """
        if segment_id is None:
            raise Exception("Expecting a segment ID to fetch the segment definition.")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSegment")
        path = f"/segment/definitions/{segment_id}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def createSegment(self, segment_data: dict = None) -> dict:
        """
        Create a segment based on the information provided by the dictionary passed.
        Argument :
            segment_data : REQUIRED : Dictionary of the segment definition.
                require in the segment_data: name, description, expression, schema, ttlInDays
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createSegment")
        path = "/segment/definitions"
        if segment_data is None or type(segment_data) != dict:
            raise Exception(
                "Expecting data as dictionary format to update the segment."
            )
        checks = "name,description,expression,schema,ttlInDays".split(
            ","
        )  # mandatory elements in segment definition
        if len(set(checks) & set(segment_data.keys())) != len(checks):
            raise Exception(
                "Segment data doesn't hold one or several mandatory fields:\n\
                name, description, expression, schema, ttlInDays"
            )
        res = self.connector.postData(
            self.endpoint + path, data=segment_data, headers=self.header
        )
        return res

    def deleteSegment(self, segment_id: str = None) -> dict:
        """
        Delete a specific segment definition.
        Argument:
            segment_id : REQUIRED : Segment ID of the segment to be deleted.
        """
        if segment_id is None:
            raise Exception("Expecting a segment ID to delete the segment.")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteSegment")
        path = f"/segment/definitions/{segment_id}"
        res = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res

    def updateSegment(self, segment_id: str = None, segment_data: dict = None) -> dict:
        """
        Update the segment characteristics from the definition pass to that method.
        Arguments:
            segment_id : REQUIRED : id of the segment to be udpated.
            segment_data : REQUIRED : Dictionary of the segment definition.
                require in the segment_data: name, description, expression, schema, ttlInDays
        """
        if segment_id is None:
            raise Exception("Expecting a segment ID to update the segment.")
        elif segment_data is None or type(segment_data) != dict:
            raise Exception(
                "Expecting data as dictionary format to update the segment."
            )
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateSegment")
        path = f"/segment/definitions/{segment_id}"
        checks = "name,description,expression,schema,ttlInDays".split(
            ","
        )  # mandatory elements in segment definition
        if len(set(checks) & set(segment_data.keys())) != len(checks):
            raise Exception(
                "Segment data doesn't hold one or several mandatory fields:\n\
                name, description, expression, schema, ttlInDays"
            )
        update = self.connector.postData(
            self.endpoint + path, headers=self.header, data=segment_data
        )
        return update
    
    def getMultipleSegments(self,segmentIds:list=None)->dict:
        """
        Retrieve multiple segments from a list of segment IDs.
        Arguments:
            segmentIds: REQUIRED : list of segment IDs
        """
        if segmentIds is None:
            raise Exception("Require a list of segment Ids")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMultipleSegments with this list: {segmentIds}")
        path = "/segment/definitions/bulk-get"
        res = self.connector.postData(self.endpoint + path,data=segmentIds)
        results = res.get('results')
        return results

    def convertSegmentDef(self,name:str=None,expression:dict=None,description:str=None,schemaClass:str="_xdm.context.profile",ttl:int=30,**kwargs)->dict:
        """
        This endpoint converts a segment definition from pql/text to pql/json or from pql/json to pql/text.
        Arguments:
            name : REQUIRED : The name of the segment. It should be unique.
            expression : REQUIRED : the expriession regarding the transformation.
                A dictionary such as
                {
                    "type" : "PQL" (or "ARL"),
                    "format" : "pql/text" (or "pql/json")
                    "value" : "your PQL expression"
                }
            description : OPTIONAL : the description to be used
            schemaClass : OPTIONAL :  the class ID to be used. (ex: default : "_xdm.context.profile")
            ttl : OPTIONAL : Time to live per day (default 30)
        possible kwargs:
            additional kwargs will be used as parameter of the body
        """
        if name is None:
            raise Exception("Require a name")
        if expression is None and type(expression)!=dict:
            raise Exception("Require a dictionary as expression")
        if self.loggingEnabled:
            self.logger.debug(f"Starting convertSegmentDef")
        path = "/segment/conversion"
        data = {**kwargs}
        data['name'] = name
        data['imsOrgId'] = self.connector.config['org_id']
        data['description'] = description
        data['expression'] = expression
        data['schema'] = {
            "name" : schemaClass
        }
        data['ttlInDays'] = ttl
        res = self.connector.postData(self.endpoint + path,data=data)
        return res

    def getExportJobs(self, limit: int = 1000, status: str = None) -> list:
        """
        Retrieve a list of all export jobs.
        Arguments:
            limit : OPTIONAL : number of jobs to be returned (default 100)
            status : OPTIONAL : status of the job (NEW, SUCCEEDED, FAILED)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getExportJobs")
        path = "/export/jobs"
        params = {"limit": limit}
        if status is not None and status in ["NEW", "SUCEEDED", "FAILED"]:
            params["status"] = status
        lastPage = False
        data = []
        while lastPage != True:
            res = self.connector.getData(
                self.endpoint + path, params=params, headers=self.header
            )
            data += res["records"]
            nextPage = res.get("link", {}).get("next", "")
            if nextPage == "":
                lastPage = True
            else:
                offset = nextPage.split("offset=")[1].split("&")[0]
                params["offset"] = offset
        return data

    def createExport(self, export_request: dict = None) -> dict:
        """
        Create an exportJob
        Arguments:
            export_request : REQUIRED : number of jobs to be returned (default 100)
            information on the structure of the request here: https://experienceleague.adobe.com/docs/experience-platform/segmentation/api/export-jobs.html?lang=en#get
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createExport")
        path = "/export/jobs"
        if export_request is None:
            raise Exception("Expected export data to specify segment to export.")
        res = self.connector.postData(
            self.endpoint + path, data=export_request, headers=self.header
        )
        return res

    def getExport(self, export_id: str = None) -> dict:
        """
        Retrieve a specific export Job.
        Arguments:
            export_id : REQUIRED : Export Job to be retrieved.
        """
        if export_id is None:
            raise Exception("Expected a export_id")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getExport")
        path = f"/export/jobs/{export_id}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def deleteExport(self, export_id: str = None) -> dict:
        """
        Cancel or delete an export Job.
        Arguments:
            export_id : REQUIRED : Export Job to be deleted.
        """
        if export_id is None:
            raise Exception("Expected a export_id")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteExport")
        path = f"/export/jobs/{export_id}"
        res = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res

    def searchNamespaces(
        self,
        query: str = None,
        schema: str = "_xdm.context.segmentdefinition",
        **kwargs,
    ) -> dict:
        """
        Return a list of search count results, queried across all namespaces.
        Arguments:
            query : REQUIRED : the search query.
            schema : OPTIONAL : The schema class value associated with the search objects. (default _xdm.context.segmentdefinition)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting searchNamespaces")
        path = "/search/namespaces"
        if query is None:
            raise Exception("Expected a query to search for.")
        params = {"schema.name": schema, "s": query}
        self.header["x-ups-search-version"] = "1.0"
        res = self.connector.getData(
            self.endpoint + path, headers=self.header, params=params
        )
        del self.header["x-ups-search-version"]
        return res

    def searchEntities(
        self,
        query: str = None,
        namespace: str = "ECID",
        entityId: str = None,
        schema: str = "_xdm.context.segmentdefinition",
        **kwargs,
    ) -> dict:
        """
        Return the list of objects that are contained  within a namespace.
        Arguments:
            query : REQUIRED : the search query based on Lucene query syntax (ex: name:test) (https://learn.microsoft.com/en-us/azure/search/query-lucene-syntax)
            schema : OPTIONAL : The schema class value associated with the search objects.(defaul _xdm.context.segmentdefinition)
            namespace : OPTIONAL : The namespace you want to search within (default ECID)
            entityId : OPTIONAL : The ID of the folder you want to search for external segments in
        possible kwargs:
            limit : maximum number of result per page. Max 50.
            page : page to be retrieved (start at 0)
            page_limit : maximum number of pages retrieved.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting searchEntity")
        path = "/search/entities"
        if query is None:
            raise Exception("Expected a query to search for.")
        limit = kwargs.get("limit", 50)
        page = kwargs.get("page", 0)
        page_limit = kwargs.get("page_limit", 0)
        self.header["x-ups-search-version"] = "1.0"
        params = {
            "schemaClass": schema,
            "namespace": namespace,
            "s": query,
            "entityId": entityId,
            "limit": limit,
            "page": page,
        }
        res = self.connector.getData(
            self.endpoint + path, headers=self.header, params=params
        )
        data = res["entities"]
        curr_page = res["page"]["pageOffset"]
        total_pages = res["page"]["totalPages"]
        while curr_page <= page_limit - 1 or curr_page == total_pages:
            res = self.connector.getData(
                self.endpoint + path, headers=self.header, params=params
            )
            data += res["entities"]
            curr_page = res["page"]["pageOffset"]
            total_pages = res["page"]["totalPages"]
        del self.header["x-ups-search-version"]
        return data

    def getSchedules(
        self, limit: int = 100, n_results: Union[int, str] = "inf"
    ) -> list:
        """
        Return the list of scheduled segments.
        Arguments:
            limit : OPTIONAL : number of result per request (100 max)
            n_results : OPTIONAL : Total of number of result to retrieve.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchedules")
        path = "/config/schedules"
        params = {"start": 0}
        lastPage = False
        data = []
        while lastPage != True:
            res = self.connector.getData(
                self.endpoint + path, params=params, headers=self.header
            )
            data += res.get("children", [])
            nextPage = res.get("_links", {}).get("href", "")
            if nextPage == "" or len(data) > float(n_results):
                lastPage = True
            else:
                params["start"] += 1
        return data

    def createSchedule(self, schedule_data: dict = None) -> dict:
        """
        Schedule a segment to run.
        Arguments:
            schedule_data : REQUIRED : Definition of the schedule.
            Should contains name, type, properties, schedule.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createSchedule")
        path = "/config/schedules"
        if schedule_data is None or type(schedule_data) != dict:
            raise Exception(
                "Expected a dictionary data for setting the segment schedule."
            )
        min_requirements = "name,type,properties,schedule".split(",")
        if len(set(min_requirements) & set(schedule_data.keys())) != len(
            min_requirements
        ):
            raise Exception(
                "Missing one minimal requirements : name, type, properties, schedule"
            )
        res = self.connector.postData(
            self.endpoint + path, data=schedule_data, headers=self.header
        )
        return res

    def getSchedule(self, scheduleId: str = None) -> dict:
        """
        Get a specific schedule definition.
        Argument:
            scheduleId : REQUIRED : Segment ID to be retrieved.
        """
        if scheduleId is None:
            raise Exception("Expected a schedule_id")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchedule")
        path = f"/config/schedules/{scheduleId}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def deleteSchedule(self, scheduleId: str = None) -> dict:
        """
        Delete a specific schedule definition.
        Argument:
            scheduleId : REQUIRED : Segment ID to be deleted.
        """
        if scheduleId is None:
            raise Exception("Expected a schedule_id")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteSchedule")
        path = f"/config/schedules/{scheduleId}"
        res = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res

    def updateSchedule(self, scheduleId: str = None, operations: list = None) -> dict:
        """
        Update a schedule with the operation provided.
        Arguments:
            scheduleId : REQUIRED : the schedule ID to update
            operations : REQUIRED : List of operations to realize
                [
                    {
                    "op": "add",
                    "path": "/state",
                    "value": "active"
                    }
                ]
        """
        if scheduleId is None:
            raise ValueError("Require a schedule ID")
        if operations is None or type(operations) != list:
            raise ValueError("Require a list of operation to run")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateSchedule")
        path = f"/config/schedules/{scheduleId}"
        res = self.connector.patchData(self.endpoint + path, data=operations)
        return res

    def getJobs(
        self,
        name: str = None,
        status: str = None,
        limit: int = 100,
        n_results: Union[str, int] = "inf",
        **kwargs,
    ) -> list:
        """
        Returns the list of segment jobs.
        Arguments:
            name : OPTIONAL : Name of the snapshot
            status : OPTIONAL : Status of the job (PROCESSING,SUCCEEDED)
            limit : OPTIONAL : Amount of jobs to be retrieved per request (100 max)
            n_results : OPTIONAL : How many total jobs do you want to retrieve.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getJobs")
        path = "/segment/jobs"
        params = {"snapshot.name": name, "status": status, "limit": limit, "start": 0}
        lastPage = False
        data = []
        while lastPage != True:
            res = self.connector.getData(
                self.endpoint + path, params=params, headers=self.header
            )
            data += res.get("children", [])
            nextPage = res.get("_links", {}).get("href", "")
            if nextPage == "" or len(data) > float(n_results):
                lastPage = True
            else:
                params["start"] += 1
        return data

    def createJob(self, segmentIds: list = None) -> dict:
        """
        Create a new job for a segment.
        Argument:
            segmentIds : REQUIRED : a list of segmentIds.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createJob")
        path = "/segment/jobs"
        if segmentIds is None or type(segmentIds) != list:
            raise Exception("Expecting a list of segment ID to run.")
        jobData = [{"segmentId": segId} for segId in segmentIds]
        res = self.connector.postData(
            self.endpoint + path, data=jobData, headers=self.header
        )
        return res

    def getJob(self, job_id: str = None) -> dict:
        """
        Retrieve a Segment job by ID.
        Argument:
            job_id: REQUIRED : The job ID to retrieve.
        """
        if job_id is None:
            raise ValueError("Require a job ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getJob")
        path = f"/segment/jobs/{job_id}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def deleteJob(self, job_id: str = None) -> dict:
        """
        deleteJob a Segment job by ID.
        Argument:
            job_id: REQUIRED : The job ID to delete.
        """
        if job_id is None:
            raise ValueError("Require a job ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getJob")
        path = f"/segment/jobs/{job_id}"
        res = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res

    def createPreview(
        self, pql: str = None, model: str = "_xdm.context.profile"
    ) -> dict:
        """
        Given a PQL expression genereate a preview of how much data there would be.
        Arguments:
            pql : REQUIRED : The PQL statement that would be your segment definition
            model : OPTIONAL : XDM class the statement is based on. Default : _xdm.context.profile
        """
        if pql is None:
            ValueError("Require a PQL statement for creation")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createPreview")
        path = "/preview"
        obj = {
            "predicateExpression": pql,
            "predicateType": "pql/text",
            "predicateModel": model,
            "graphType": "pdg",
        }
        res = self.connector.postData(self.endpoint + path, data=obj)
        return res

    def getPreview(self, previewId: str = None) -> dict:
        """
        Retrieve the preview once it has been created by the createPreview method.
        Arguments:
            previewId : REQUIRED : The preview ID to used.
        """
        if previewId is None:
            raise Exception("require a preview ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPreview")
        path = f"/preview/{previewId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def deletePreview(self, previewId: str = None) -> dict:
        """
        Delete the preview based on its ID.
        Arguments:
            previewId : REQUIRED : The preview ID to deleted.
        """
        if previewId is None:
            raise Exception("require a preview ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deletePreview")
        path = f"/preview/{previewId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def getEstimate(self, previewId: str = None) -> dict:
        """
        Based on the preview ID generated by createPreview, you can look at statistical information of a segment.
        Arguments:
            previewId : REQUIRED : The preview ID to used for estimation
        """
        if previewId is None:
            raise Exception("require a preview ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getEstimate")
        path = f"/estimate/{previewId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def estimateExpression(
        self, pql: str = None, model: str = "_xdm.context.profile", wait: int = 60
    ) -> dict:
        """
        This method is a combination of the createPreview and getEstimate method so you don't have to build a pipeline for it.
        It automatically fetch the estimate based on the PQL statement passed. Run a loop every minute to fetch the result.
        Arguments:
            pql : REQUIRED : The PQL statement that would be your segment definition
            model : OPTIONAL : XDM class the statement is based on. Default : _xdm.context.profile
            wait : OPTIONAL : How many seconds to wait between 2 call to getEstimate when result are not ready. (default 60)
        """
        if pql is None:
            raise ValueError("Require a PQL expression")
        if self.loggingEnabled:
            self.logger.debug(f"Starting estimateExpression")
        preview = self.createPreview(pql=pql, model=model)
        try:
            previewId = preview["previewId"]
        except:
            print(preview)
            raise KeyError("Couldn't retrieve the previewId from the response")
        estimate = self.getEstimate(previewId)
        while estimate["state"] != "RESULT_READY" or estimate["state"] != "ERROR":
            time.sleep(60)
            estimate = self.getEstimate(previewId)
        return estimate
    

    def getAudiences(self,
        limit:int=100,
        metrics:bool=True,
        name:str=None,
        sort:str=None,
        prop:str=None,
        description:str=None,
        **kwargs)->list:
        """
        Get the audiences list.
        Arguments:
            name : OPTIONAL : Filter audiences that contains that string in the name, case unsensitive.
            limit : OPTIONAL : The number of audiences to be returned by pages (default: 100)
            sort : OPTIONAL : If you want to sort by a specific attribute (ex: "updateTime:desc")
            prop : If you want to test a specific property of the result to filter the data.
                    Ex: "audienceId==mytestAudienceId"
            description : OPTIONAL : Filter audiences that contains that string in the description, case unsensitive.
            with metrics : OPTIONAL : If metrics should be returned as well. Default true.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getAudiences")
        params = {"limit":limit,"withMetrics":metrics}
        path = "/audiences"
        if name is not None:
            params['name'] = name
        if sort is not None:
            params['sort'] = sort
        if prop is not None:
            params['property'] = prop
        if description is not None:
            params['description'] = description
        if kwargs.get('start',0) is not None:
            params['start'] = kwargs.get('start')
        res = self.connector.getData(self.endpoint+path, params=params)
        data = res.get('children',[])
        nextStart = res.get('_pages',{}).get('next',0)
        while nextStart != 0:
            params['start'] = nextStart
            res = self.connector.getData(self.endpoint+path, params=params)
            data += res.get('children',[])
            nextStart = res.get('_pages',{}).get('next',0)
        return data
    
    def getAudience(self,audienceId:str=None)->dict:
        """
        Retrieve a specific audience id.
        Arguments:
            audienceId : REQUIRED : The audience ID to retrieve.
        """
        if audienceId is None:
            raise ValueError("Require an audience ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getAudience for audienceId: {audienceId}")
        path = f"/audiences/{audienceId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def deleteAudience(self,audienceId:str=None)->str:
        """
        Delete an audience based on its ID.
        Argument:
            audienceId : REQUIRED : The audience ID to delete
        """
        if audienceId is None:
            raise ValueError("Require an audience ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteAudience for audienceId: {audienceId}")
        path = f"/audiences/{audienceId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res
    
    def createAudience(self,audienceObj:dict=None)->dict:
        """
        Create an audience basde on the dictionary passed as argument.
        Argument:
            audienceObj : REQUIRED : Can be either one of the Platform Audience or External Audience
                See constants EXTERNAL_AUDIENCE_DICT & PLATFORM_AUDIENCE_DICT  
        """
        if audienceObj is None or type(audienceObj) != dict:
            raise ValueError("Require an audience Object as dictionary")
        path = "/audiences"
        if self.loggingEnabled:
            self.logger.debug(f"Starting createAudience")
        res = self.connector.postData(self.endpoint + path, data=audienceObj)
        return res

    def patchAudience(self,audienceId:str=None,operations:list=None)->dict:
        """
        PATCH an existing audience with some operation described in parameter.
        Arguments:
            audienceId : REQUIRED : The audience ID to patch
            operations : REQUIRED : A list of operation to apply.
                            Example: 
                            [
                                {
                                    "op": "add",
                                    "path": "/expression",
                                    "value": {
                                    "type": "PQL",
                                    "format": "pql/text",
                                    "value": "workAddress.country= \"US\""
                                    }
                                }
                            ]
        """
        if audienceId is None:
            raise ValueError("Require an audience ID")
        if operations is None or type(operations) != list:
            raise ValueError("Require a list of operations")
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchAudience for audienceId: {audienceId}")
        path = f"/audiences/{audienceId}"
        res = self.connector.patchData(self.endpoint + path,data=operations)
        return res
    
    def putAudience(self,audienceId:str=None,audienceObj: dict = None)-> dict:
        """
        Replace an existing definition with a new one, with the PUT method.
        Arguments:
            audienceId : REQUIRED : the audience ID to replace
            audienceObj : REQUIRED : the new definition to use
                see EXTERNAL_AUDIENCE_DICT & PLATFORM_AUDIENCE_DICT  
        """
        if audienceId is None:
            raise ValueError("Require an audience ID")
        if audienceObj is None or type(audienceObj) != dict:
            raise ValueError("Require a new definition")
        if self.loggingEnabled:
            self.logger.debug(f"Starting putAudience for audienceId: {audienceId}")
        path = f"/audiences/{audienceId}"
        res = self.connector.putData(self.endpoint + path,data=audienceObj)
        return res
    


