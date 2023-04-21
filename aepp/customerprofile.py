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
from copy import deepcopy
import pandas as pd
import logging
from typing import Union
from .configs import ConnectObject


class Profile:
    """
    A class containing the different methods exposed on Customer Profile API.
    The API documentation is available:
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/real-time-customer-profile.yaml
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
            This will instantiate the profile class
            Arguments:
                config : OPTIONAL : config object in the config module.
                header : OPTIONAL : header object  in the config module.
                loggingObject : OPTIONAL : logging object to log messages.
        kwargs:
            kwargsvaluewillupdatetheheader
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
        self.header["Accept"] = "application/vnd.adobe.xdm+json"
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
            aepp.config.endpoints["global"] + aepp.config.endpoints["segmentation"]
        )

    def getEntity(
        self,
        schema_name: str = "_xdm.context.profile",
        entityId: str = None,
        entityIdNS: str = None,
        mergePoliciyId: str = None,
        **kwargs,
    ) -> dict:
        """
        Returns an entity by ID or Namespace.
        Arguments:
            schema_name : REQUIRED : class name of the schema to be retrieved. default : _xdm.context.profile
            entityId : OPTIONAL : identity ID
            entityIdNS : OPTIONAL : Identity Namespace code. Required if entityId is used (except for native identity)
            mergePoliciyId : OPTIONAL : Id of the merge policy.
        Possible kwargs:
            fields : path of the elements to be retrieved, separated by comma. Ex : "person.name.firstName,person.name.lastName"
            relatedSchema_name : If schema.name is "_xdm.context.experienceevent", this value must specify the schema for the profile entity that the time series events are related to.
            relatedEntityId : ID of the entity that the ExperienceEvents are associated with. Used when looking up ExperienceEvents. For Native XID lookup, use relatedEntityId=<XID> and leave relatedEntityIdNS absent;
            For ID:NS lookup, use both relatedEntityId and relatedEntityIdNS fields.
            relatedEntityIdNS : Identity Namespace code of the related entity ID of ExperienceEvent. Used when looking up ExperienceEvents. If this field is used, entityId cannot be empty.
            startTime : Start time of Time range filter for ExperienceEvents. Should be at millisecond granularity. Included. Default: From beginning.
            endTime : End time of Time range filter for ExperienceEvents. Should be at millisecond granularity. Excluded. Default: To the end.
            limit : Number of records to return from the result. Only for time-series objects. Default: 1000
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getEntity")
        path = "/access/entities"
        params = {
            "schema.name": schema_name,
            "entityId": entityId,
            "entityIdNS": entityIdNS,
            "mergePoliciyId": mergePoliciyId,
        }
        if schema_name == "_xdm.context.experienceevent":
            params["relatedSchema.name"] = kwargs.get(
                "relatedSchema_name", "_xdm.context.profile"
            )
            params["relatedEntityId"] = kwargs.get("relatedEntityId", entityId)
            params["relatedEntityIdNS"] = kwargs.get("relatedEntityIdNS", None)
            params["limit"] = kwargs.get("limit", 1000)
            params["startTime"] = kwargs.get("startTime", None)
            params["endTime"] = kwargs.get("endTime", None)
        params["fields"] = kwargs.get("fields", None)
        res = self.connector.getData(
            self.endpoint + path, params=params, headers=self.header
        )
        return res

    def getEntities(self, request_data: dict = None) -> dict:
        """
        Get a number of different identities from ID or namespaces.
        Argument:
            request_data : Required : A dictionary that contains fields for the search.
            Example
            {
                "schema": {
                    "name": "_xdm.context.profile"
                },
                "relatedSchema": {
                    "name": "_xdm.context.profile"
                },
                "fields": [
                    "person.name.firstName"
                ],
                "identities": [
                    {
                    "entityId": "69935279872410346619186588147492736556",
                    "entityIdNS": {
                        "code": "CRMID"
                        }
                    },
                    ,
                {
                    "entityId":"89149270342662559642753730269986316900",
                    "entityIdNS":{
                        "code":"ECID"
                        }
                    ],
                "timeFilter": {
                    "startTime": 1539838505,
                    "endTime": 1539838510
                },
                "limit": 10,
                "orderby": "-timestamp",
                "withCA": True
            }
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getEntities")
        path = "/access/entities"
        if request_data is None or type(request_data) != dict:
            raise Exception("Expected a dictionary to fetch entities")
        res = self.connector.postData(
            self.endpoint + path, data=request_data, headers=self.header
        )
        return res

    def deleteEntity(
        self, schema_name: str = None, entityId: str = None, entityIdNS: str = None
    ) -> str:
        """
        Delete a specific entity
        Arguments:
            schema_name : REQUIRED : Name of the associated XDM schema.
            entityId : REQUIRED : entity ID
            entityIdNS : OPTIONAL : entity ID Namespace
        """
        path = "/access/entities"
        params = {}
        if schema_name is None:
            raise Exception("Expected a schema name")
        else:
            params["schema.name"] = schema_name
        if entityId is not None:
            params["entityId"] = entityId
        if entityIdNS is not None:
            params["entityIdNS"] = entityIdNS
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteEntity")
        res = self.connector.deleteData(
            self.endpoint + path, params=params, headers=self.header
        )
        return res
    
    def createExportJob(self,
            exportDefinition:dict=None,
            fields:list=None,
            mergePolicyId:str=None,
            additionalFields:dict=None,
            datasetId:str=None,
            schemaName:str="_xdm.context.profile",
            segmentPerBatch:bool=False,
            )->dict:
        """
        Create an export of the profile information of the user.
        You can pass directly the payload or you can pass different arguments to create that export job.
        Documentation: https://experienceleague.adobe.com/docs/experience-platform/profile/api/export-jobs.html?lang=en
        Arguments: 
            exportDefinition : OPTIONAL : The complete definition of the export
        If not provided, use the following parameters:
            fields : OPTIONAL : Limits the data fields to be included in the export to only those provided in this parameter. 
                    Omitting this value will result in all fields being included in the exported data.
            mergePolicyId : OPTIONAL : MergePolicyId to use for data combination.
            additionalFields : OPTIONAL : Controls the time-series event fields exported for child or associated objects by providing one or more of the following settings:
            datasetId : OPTIONAL : the datasetId to be used for the export.
            schemaName : OPTIONAL : Schema associated with the dataset.
            segmentPerBatch : OPTIONAL : A Boolean value that, if not provided, defaults to false. A value of false exports all segment IDs into a single batch ID. A value of true exports one segment ID into one batch ID.
        """
        if exportDefinition is not None and type(exportDefinition) == dict:
            data = exportDefinition
        elif fields is not None and mergePolicyId is not None and datasetId is not None and schemaName is not None:
            data = {}
            data['fields'] = ','.join(fields)
            data['mergePolicy'] = {
                "id": mergePolicyId,
                "version": 1
            }
            data['destination'] = {
                "datasetId": datasetId,
                "segmentPerBatch": segmentPerBatch
            }
            data['schema'] = {
                "name": schemaName,
            }
            if additionalFields is not None:
                data['additionalFields'] = additionalFields
        else:
            raise ValueError("Require the definition or arguments to be used")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createExportJob")
        path = f"/export/jobs"
        res = self.connector.postData(self.endpoint + path, data=data)
        return res

    def getExportJobs(self,limit:int=100)->dict:
        """
        Returns all export jobs
        Arguments:
            limit : OPTIONAL : Number of jobs to return
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getExportJobs")
        path = "/export/jobs/"
        params = {"limit":limit}
        res = self.connector.getData(self.endpoint+path,params=params)
        return res
    
    def getExportJob(self, exportId:str=None)->dict:
        """
        Returns an export job status
        Arguments:
            exportId : OPTIONAL : The id of the export job you want to access.
        """
        if exportId is None:
            raise ValueError("Require an export ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getExportJob with ID: {exportId}")
        path = f"/export/jobs/{exportId}"
        res = self.connector.getData(self.endpoint+path)
        return res

    def deleteExportJob(self, exportId:str=None)->dict:
        """
        Delete an export job
        Arguments:
            exportId : OPTIONAL : The id of the export job you want to delete.
        """
        if exportId is None:
            raise ValueError("Require an export ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteExportJob with ID: {exportId}")
        path = f"/export/jobs/{exportId}"
        res = self.connector.deleteData(self.endpoint+path)
        return res



    def getMergePolicies(self, limit: int = 100) -> dict:
        """
        Returns the list of merge policies hosted in this instance.
        Arguments:
            limit : OPTIONAL : amount of merge policies returned by pages.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMergePolicies")
        path = "/config/mergePolicies"
        params = {"limit": limit}
        res = self.connector.getData(
            self.endpoint + path, params=params, headers=self.header
        )
        data = res["children"]
        nextPage = res["_links"]["next"].get("href", "")
        while nextPage != "":
            path = "/config/mergePolicies?" + nextPage.split("?")[1]
            res = self.connector.getData(
                self.endpoint + path, params=params, headers=self.header
            )
            data += res["children"]
            nextPage = res["_links"]["next"].get("href", "")
        return data

    def getMergePolicy(self, policy_id: str = None) -> dict:
        """
        Return a specific merge policy.
        Arguments:
            policy_id : REQUIRED : id of the the policy id to be returned.
        """
        if policy_id is None:
            raise Exception("Missing the policy id")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMergePolicy")
        path = f"/config/mergePolicies/{policy_id}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def createMergePolicy(self, policy: dict = None) -> dict:
        """
        Arguments:
            policy: REQUIRED : The dictionary defining the policy
        Refer to the documentation : https://experienceleague.adobe.com/docs/experience-platform/profile/api/merge-policies.html
        Example of JSON:
        {
            "name": "real-time-customer-profile-default",
            "imsOrgId": "1BD6382559DF0C130A49422D@AdobeOrg",
            "schema": {
                "name": "_xdm.context.profile"
            },
            "default": False,
            "identityGraph": {
                "type": "pdg"
            },
            "attributeMerge": {
                "type": "timestampOrdered",
                "order": [
                "string"
                ]
            },
            "updateEpoch": 1234567890
        }
        """
        path = "/config/mergePolicies"
        if policy is None:
            raise ValueError("Require a dictionary")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createMergePolicy")
        res = self.connector.postData(
            self.endpoint + path, data=policy, headers=self.header
        )
        return res

    def updateMergePolicy(self, mergePolicyId: str = None, policy: dict = None) -> dict:
        """
        Update a merge policy by replacing its definition. (PUT method)
        Arguments:
            mergePolicyId : REQUIRED : The merge Policy Id
            policy : REQUIRED : a dictionary giving the definition of the merge policy
            Refer to the documentation : https://experienceleague.adobe.com/docs/experience-platform/profile/api/merge-policies.html
        Example of JSON:
        {
            "name": "real-time-customer-profile-default",
            "imsOrgId": "1BD6382559DF0C130A49422D@AdobeOrg",
            "schema": {
                "name": "_xdm.context.profile"
            },
            "default": False,
            "identityGraph": {
                "type": "pdg"
            },
            "attributeMerge": {
                "type": "timestampOrdered",
                "order": [
                "string"
                ]
            },
            "updateEpoch": 1234567890
        }
        attributeMerge can be "dataSetPrecedence" or "timestampOrdered". Please provide a list of dataSetId on "order" when using the first option.
        """
        if mergePolicyId is None:
            raise ValueError("Require a mergePolicyId")
        if policy is None or type(policy) != dict:
            raise ValueError("Require a dictionary to update the merge policy")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateMergePolicy")
        path = f"/config/mergePolicies/{mergePolicyId}"
        res = self.connector.putData(
            self.endpoint + path, data=policy, headers=self.header
        )
        return res

    def patchMergePolicy(
        self, mergePolicyId: str = None, operations: list = None
    ) -> str:
        """
        Update a merge policy by replacing its definition.
        Arguments:
            mergePolicyId : REQUIRED : The merge Policy Id
            operations : REQUIRED : a list of operations to realize on the merge policy
            Refer to the documentation : https://experienceleague.adobe.com/docs/experience-platform/profile/api/merge-policies.html
        Example of operation:
        [
            {
                "op": "add",
                "path": "/identityGraph.type",
                "value": "pdg"
            }
        ]
        """
        if mergePolicyId is None:
            raise ValueError("Require a mergePolicyId")
        if operations is None or type(operations) != list:
            raise ValueError("Require a dictionary to update the merge policy")
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchMergePolicy")
        path = f"/config/mergePolicies/{mergePolicyId}"
        res = self.connector.patchData(
            self.endpoint + path, data=operations, headers=self.header
        )
        return res

    def deleteMergePolicy(self, mergePolicyId: str = None) -> str:
        """
        Delete a merge policy by its ID.
        Arguments:
            mergePolicyId : REQUIRED : The merge Policy to be deleted
        """
        if mergePolicyId is None:
            raise ValueError("Require a mergePolicyId")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteMergePolicy")
        path = f"/config/mergePolicies/{mergePolicyId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def getPreviewStatus(self) -> dict:
        """
        View the details for the last successful sample job that was run for the IMS Organization.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPreviewStatus")
        path = "/previewsamplestatus"
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = "application/json"
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        return res

    def getPreviewDataSet(self, date: str = None, output: str = "raw") -> dict:
        """
        View a report showing the distribution of profiles by dataset.
        Arguments:
            date : OPTIONAL : Format: YYYY-MM-DD.
                If multiple reports were run on the date, the most recent report for that date will be returned.
                If a report does not exist for the specified date, a 404 error will be returned.
                If no date is specified, the most recent report will be returned.
                Example: date=2024-12-31
            output : OPTIONAL : if you want to have a dataframe returns. Use "df", default "raw"
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPreviewDataSet")
        path = "/previewsamplestatus/report/dataset"
        params = {}
        if date is not None:
            params["date"] = date
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = "application/json"
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        if output == "df":
            df = pd.DataFrame(res["data"])
            return df
        return res

    def getPreviewDataSetOverlap(self, date: str = None, output: str = "raw") -> dict:
        """
        Method to find the overlap of identities with datasets.
        Arguments:
            date : OPTIONAL : Format: YYYY-MM-DD.
                If multiple reports were run on the date, the most recent report for that date will be returned.
                If a report does not exist for the specified date, a 404 error will be returned.
                If no date is specified, the most recent report will be returned.
                Example: date=2024-12-31
            output : OPTIONAL : if you want to have a dataframe returns. Use "df", default "raw"
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPreviewDataSetOverlap")
        path = "/previewsamplestatus/report/dataset/overlap"
        params = {}
        if date is not None:
            params["date"] = date
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = "application/json"
        privateHeader["x-model-name"] = "_xdm.context.profile"
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        if output == "df":
            df = pd.DataFrame(res["data"])
            return df
        return res

    def getPreviewNamespace(self, date: str = None, output: str = "raw") -> dict:
        """
        View a report showing the distribution of profiles by namespace.
        Arguments:
            date : OPTIONAL : Format: YYYY-MM-DD.
                If multiple reports were run on the date, the most recent report for that date will be returned.
                If a report does not exist for the specified date, a 404 error will be returned.
                If no date is specified, the most recent report will be returned.
                Example: date=2024-12-31
            output : OPTIONAL : if you want to have a dataframe returns. Use "df", default "raw"
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPreviewNamespace")
        path = "/previewsamplestatus/report/namespace"
        params = {}
        if date is not None:
            params["date"] = date
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = "application/json"
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        if output == "df":
            df = pd.DataFrame(res["data"])
            return df
        return res

    def createDeleteSystemJob(self, dataSetId: str = None, batchId: str = None) -> dict:
        """
        Delete all the data for a batch or a dataSet based on their ids.
        Note: you cannot delete batch from record type dataset. You can overwrite them to correct the issue.
        Only Time Series and record type datasets can be deleted.
        Arguments:
            dataSetId : REQUIRED : dataSetId to be deleted
            batchId : REQUIRED : batchId to be deleted.
        More info: https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Profile_System_Jobs/createDeleteRequest
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createDeleteSystemJob")
        path = "/system/jobs"
        if dataSetId is not None:
            obj = {"dataSetId": dataSetId}
            res = self.connector.postData(self.endpoint + path, data=obj)
            return res
        elif batchId is not None:
            obj = {"batchId": batchId}
            res = self.connector.postData(self.endpoint + path, data=obj)
            return res
        else:
            raise ValueError("Require a dataSetId or a batchId")

    def getDeleteSystemJobs(
        self, page: int = 0, limit: int = 100, n_results: int = 100
    ) -> dict:
        """
        Retrieve a list of all delete requests (Profile System Jobs) created by your organization.
        Arguments:
            page : OPTIONAL : Return a specific page of results, as per the create time of the request. For example, page=0
            limit : OPTIONAL : Limit response to a specific number of objects. Must be a positive number. For example, limit=10
            n_results : OPTIONAL : Number of total result to retrieve.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDeleteSystemJobs")
        path = "/system/jobs"
        params = {"page": page, "limit": limit}
        res = self.connector.getData(self.endpoint + path, params=params)
        data = res["children"]
        count = len(data)
        nextPage = res["_page"].get("next", "")
        while nextPage != "" and count < n_results:
            page += 1
            params = {"page": page, "limit": limit}
            res = self.connector.getData(
                self.endpoint + path, params=params, headers=self.header
            )
            count += len(res["children"])
            data += res["children"]
            nextPage = res["_page"].get("next", "")
        return data

    def getDeleteSystemJob(self, jobId: str = None) -> dict:
        """
        Get a specific delete system job by its ID.
        Arguments:
            jobId : REQUIRED : Job ID to be retrieved.
        """
        if jobId is None:
            raise ValueError("Require a system Job ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDeleteSystemJob")
        path = f"/system/jobs/{jobId}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def deleteDeleteSystemJob(self, jobId: str = None) -> dict:
        """
        Delete a specific delete system job by its ID.
        Arguments:
            jobId : REQUIRED : Job ID to be deleted.
        """
        if jobId is None:
            raise ValueError("Require a system Job ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteDeleteSystemJob")
        path = f"/system/jobs/{jobId}"
        res = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res

    def getComputedAttributes(self) -> list:
        """
        Retrieve the list of computed attributes set up in your organization.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getComputedAttributes")
        path = "/config/computedAttributes"
        res = self.connector.getData(self.endpoint + path)
        data = res["children"]
        nextPage = res["_page"].get("next", "")
        # while nextPage != "":
        #     res = self.connector.getData(self.endpoint+path,
        #                     params=params, headers=self.header)
        #     data += res['children']
        #     nextPage = res['_page'].get('next','')
        return res

    def getComputedAttribute(self, attributeId: str = None) -> dict:
        """
        Returns a single computed attribute.
        Arguments:
            attributeId : REQUIRED : The computed attribute ID.
        """
        if attributeId is None:
            raise ValueError("Require a computed attribute ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getComputedAttribute")
        path = f"/config/computedAttributes/{attributeId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def deleteComputedAttribute(self, attributeId: str = None) -> dict:
        """
        Delete a specific computed attribute.
        Arguments:
            attributeId : REQUIRED : The computed attribute ID to be deleted.
        """
        if attributeId is None:
            raise ValueError("Require a computed attribute ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteComputedAttributes")
        path = f"/config/computedAttributes/{attributeId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def getDestinations(self) -> dict:
        """
        Retrieve a list of edge projection destinations. The latest definitions are returned.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDestinations")
        path = "/config/destinations"
        res = self.connector.getData(self.endpoint + path)
        return res

    def createDestination(self, destinationConfig: dict = None) -> dict:
        """
        Create a new edge projection destination. Assume that there is time between creation and propagation of this information to the edge.
        Arguments:
            destinationConfig : REQUIRED : the destination configuration
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createDestination")
        privateHeader = deepcopy(self.header)
        privateHeader[
            "Content-Type"
        ] = "application/vnd.adobe.platform.projectionDestination+json; version=1"
        if destinationConfig is None:
            raise ValueError("Require a destination configuration object")
        path = "/config/destinations"
        res = self.connector.postData(
            self.endpoint + path, data=destinationConfig, headers=privateHeader
        )
        return res

    def getDestination(self, destinationId: str = None) -> dict:
        """
        Get a specific destination based on its ID.
        Arguments:
            destinationId : REQUIRED : The destination ID to be retrieved
        """
        if destinationId is None:
            raise ValueError("Require a destination ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDestination")
        path = f"/config/destinations/{destinationId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def deleteDestination(self, destinationId: str = None) -> dict:
        """
        Delete a specific destination based on its ID.
        Arguments:
            destinationId : REQUIRED : The destination ID to be deleted
        """
        if destinationId is None:
            raise ValueError("Require a destination ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteDestination")
        path = f"/config/destinations/{destinationId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def updateDestination(
        self, destinationId: str = None, destinationConfig: dict = None
    ) -> dict:
        """
        Update a specific destination based on its ID. (PUT request)
        Arguments:
            destinationId : REQUIRED : The destination ID to be updated
            destinationConfig : REQUIRED : the destination config object to replace the old one.
        """
        if destinationId is None:
            raise ValueError("Require a destination ID")
        if destinationConfig is None:
            raise ValueError("Require a dictionation for updating the destination")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateDestination")
        privateHeader = deepcopy(self.header)
        privateHeader[
            "Content-Type"
        ] = "application/vnd.adobe.platform.projectionDestination+json"
        path = f"/config/destinations/{destinationId}"
        res = self.connector.putData(
            self.endpoint + path, data=destinationConfig, headers=privateHeader
        )
        return res

    def getProjections(self, schemaName: str = None, name: str = None) -> dict:
        """
        Retrieve a list of edge projection configurations. The latest definitions are returned.
        Arguments:
            schemaName : OPTIONAL : The name of the schema class associated with the projection configuration you want to access.
                example : _xdm.context.profile
            name : OPTIONAL : The name of the projection configuration you want to access.
                if name is specified, schemaName is also required.
        """
        path = "/config/projections"
        params = {}
        if name is not None and schemaName is None:
            raise AttributeError(
                "You must specify a schema name when setting a projection name"
            )
        if self.loggingEnabled:
            self.logger.debug(f"Starting getProjections")
        if schemaName is not None:
            params["schemaName"] = schemaName
        if name is not None:
            params["name"] = name
        res = self.connector.getData(
            self.endpoint + path, params=params, headers=self.headers
        )
        return res

    def getProjection(self, projectionId: str = None) -> dict:
        """
        Retrieve a single projection based on its ID.
        Arguments:
            projectionId : REQUIRED : the projection ID to be retrieved.
        """
        if projectionId is None:
            raise ValueError("Require a projection ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getProjection")
        path = f"/config/projections/{projectionId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def deleteProjection(self, projectionId: str = None) -> dict:
        """
        Delete a single projection based on its ID.
        Arguments:
            projectionId : REQUIRED : the projection ID to be deleted.
        """
        if projectionId is None:
            raise ValueError("Require a projection ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteProjection")
        path = f"/config/projections/{projectionId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def createProjection(
        self, schemaName: str = None, projectionConfig: dict = None
    ) -> dict:
        """
        Create a projection
        Arguments:
            schemaName : REQUIRED : XDM schema namess
            projectionConfig : REQUIRED : the object definiing the projection
        """
        if schemaName is None:
            raise ValueError("Require a schema name specified")
        if projectionConfig is None:
            raise ValueError("Require a projection configuration")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createProjection")
        path = "/config/projections"
        params = {"schemaName": schemaName}
        privateHeader = deepcopy(self.header)
        privateHeader[
            "Content-Type"
        ] = "application/vnd.adobe.platform.projectionConfig+json; version=1"
        res = self.connector.postData(
            self.endpoint + path,
            params=params,
            data=projectionConfig,
            privateHeader=privateHeader,
        )
        return res

    def updateProjection(
        self, projectionId: str = None, projectionConfig: dict = None
    ) -> dict:
        """
        Update a projection based on its ID.(PUT request)
        Arguments:
            projectionId : REQUIRED : The ID of the projection to be updated.
            projectionConfig : REQUIRED : the object definiing the projection
        """
        if projectionId is None:
            raise ValueError("Require a projectionId")
        if projectionConfig is None:
            raise ValueError("Require a projection Configuration object")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateProjection")
        privateHeader = deepcopy(self.header)
        privateHeader[
            "Content-Type"
        ] = "application/vnd.adobe.platform.projectionConfig+json"
        path = f"/config/projections/{projectionId}"
        res = self.connector.putData(
            self.endpoint + path, data=projectionConfig, headers=privateHeader
        )
        return res
