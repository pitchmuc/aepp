# Internal Library
import aepp
from aepp import connector
from copy import deepcopy
import pandas as pd


class Profile:

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        """
        This will instantiate the profile class 
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
    kwargs:
        kwargsvaluewillupdatetheheader
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header['Accept'] = "application/vnd.adobe.xdm+json"
        self.header.update(**kwargs)
        # same endpoint than segmentation
        self.endpoint = aepp.config.endpoints['global']+aepp.config.endpoints["segmentation"]

    def getEntity(self, schema_name: str = "_xdm.context.profile", entityId: str = None, entityIdNS: str = None, mergePoliciyId: str = None, **kwargs)->dict:
        """
        Returns an entity by ID or Namespace.
        Arguments:
            schema_name : REQUIRED : class name of the schema to be retrieved. default : _xdm.context.profile
            entityId : OPTIONAL : idenitity ID
            entityIdNS : OPTIONAL : Identity Namespace code. Required if entityId is used.
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
        path = "/access/entities"
        params = {"schema.name":  schema_name, "entityId": entityId,
                  "entityIdNS": entityIdNS, "mergePoliciyId": mergePoliciyId}
        if schema_name == "_xdm.context.experienceevent":
            params["relatedSchema.name"] = kwargs.get(
                "relatedSchema_name", "_xdm.context.profile")
            params["relatedEntityId"] = kwargs.get(
                "relatedEntityId", entityId)
            params["relatedEntityIdNS"] = kwargs.get(
                "relatedEntityIdNS", None)
            params["limit"] = kwargs.get("limit", 1000)
            params["startTime"] = kwargs.get("startTime", None)
            params["endTime"] = kwargs.get("endTime", None)
        params["fields"] = kwargs.get("fields", None)
        res = self.connector.getData(self.endpoint+path,
                            params=params, headers=self.header)
        return res

    def getEntities(self, request_data: dict = None)->dict:
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
        path = "/access/entities"
        if request_data is None or type(request_data) != dict:
            raise Exception("Expected a dictionary to fetch entities")
        res = self.connector.postData(self.endpoint + path,
                             data=request_data, headers=self.header)
        return res

    def deleteEntity(self, schema_name: str = None, entityId: str = None, entityIdNS: str = None)->str:
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
        res = self.connector.deleteData(self.endpoint+path,
                            params=params, headers=self.header)

    def getMergePolicies(self, limit: int = 100)->dict:
        """
        Returns the list of merge policies hosted in this instance.
        Arguments:
            limit : OPTIONAL : amount of merge policies returned by pages.
        """
        path = "/config/mergePolicies"
        params = {"limit": limit}
        res = self.connector.getData(self.endpoint+path,
                            params=params, headers=self.header)
        data = res['children']
        nextPage = res['_links']['next'].get('href','')
        while nextPage != "":
            path = "/config/mergePolicies?" + nextPage.split('?')[1]
            res = self.connector.getData(self.endpoint+path,
                            params=params, headers=self.header)
            data += res['children']
            nextPage = res['_links']['next'].get('href','')
        return data

    def getMergePolicy(self, policy_id: str = None)->dict:
        """
        Return a specific merge policy.
        Arguments:
            policy_id : REQUIRED : id of the the policy id to be returned.
        """
        if policy_id is None:
            raise Exception("Missing the policy id")
        path = f"/config/mergePolicies/{policy_id}"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res
    
    def createMergePolicy(self,policy:dict=None)->dict:
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
        res = self.connector.postData(self.endpoint+path,data=policy,headers=self.header)
        return res
    
    def updateMergePolicy(self,mergePolicyId:str=None,policy:dict=None)->dict:
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
        """
        if mergePolicyId is None:
            raise ValueError("Require a mergePolicyId")
        if policy is None or type(policy) != dict:
            raise ValueError("Require a dictionary to update the merge policy")
        path = f"/config/mergePolicies/{mergePolicyId}"
        res = self.connector.putData(self.endpoint+path,data=policy,headers=self.header)
        return res
    
    def patchMergePolicy(self,mergePolicyId:str=None,operations:list=None)->str:
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
        path = f"/config/mergePolicies/{mergePolicyId}"
        res = self.connector.patchData(self.endpoint+path,data=operations,headers=self.header)
        return res

    def deleteMergePolicy(self,mergePolicyId:str=None)->str:
        """
        Delete a merge policy by its ID.
        Arguments:
            mergePolicyId : REQUIRED : The merge Policy to be deleted
        """
        if mergePolicyId is None:
            raise ValueError("Require a mergePolicyId")
        path = f"/config/mergePolicies/{mergePolicyId}"
        res = self.connector.deleteData(self.endpoint+path)
        return res

    def getPreviewStatus(self)->dict:
        """
        View the details for the last successful sample job that was run for the IMS Organization.
        """
        path = "/previewsamplestatus"
        privateHeader = deepcopy(self.header)
        privateHeader['Accept'] = 'application/json'
        res = self.connector.getData(self.endpoint + path,headers=privateHeader)
        return res
    
    def getPreviewDataSet(self,date:str=None,output:str="raw")->dict:
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
        path = "/previewsamplestatus/report/dataset"
        params={}
        if date is not None:
            params['date'] = date
        privateHeader = deepcopy(self.header)
        privateHeader['Accept'] = 'application/json'
        res = self.connector.getData(self.endpoint + path,headers=privateHeader)
        if output == "df":
            df = pd.DataFrame(res['data'])
            return df
        return res
    
    def getPreviewNamespace(self,date:str=None)->dict:
        """
        View a report showing the distribution of profiles by namespace.
        Arguments:
            date : OPTIONAL : Format: YYYY-MM-DD. 
                If multiple reports were run on the date, the most recent report for that date will be returned. 
                If a report does not exist for the specified date, a 404 error will be returned. 
                If no date is specified, the most recent report will be returned. 
                Example: date=2024-12-31
        """
        path = "/previewsamplestatus/report/namespace"
        params={}
        if date is not None:
            params['date'] = date
        privateHeader = deepcopy(self.header)
        privateHeader['Accept'] = 'application/json'
        res = self.connector.getData(self.endpoint + path,headers=privateHeader)
        return res
    
    def createDeleteSystemJob(self,dataSetId:str=None,batchId:str=None)->dict:
        """
        Delete all the data for a batch or a dataSet based on their ids.
        Note: you cannot delete batch from record type dataset. You can overwrite them to correct the issue.
        Only Time Series and record type datasets can be deleted.
        Arguments:
            dataSetId : REQUIRED : dataSetId to be deleted
            batchId : REQUIRED : batchId to be deleted.
        More info: https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Profile_System_Jobs/createDeleteRequest
        """
        path = "/system/jobs"
        if dataSetId is not None:
            obj = {
                "dataSetId": dataSetId
            }
            res = self.connector.postData(self.endpoint+path,data=obj)
            return res
        elif batchId is not None:
            obj = {
                "batchId": batchId
            }
            res = self.connector.postData(self.endpoint+path,data=obj)
            return res
        else:
            raise ValueError("Require a dataSetId or a batchId")
    
    def getDeleteSystemJobs(self,page:int=0,limit:int=100,n_results:int=100)->dict:
        """
        Retrieve a list of all delete requests (Profile System Jobs) created by your organization.
        Arguments:
            page : OPTIONAL : Return a specific page of results, as per the create time of the request. For example, page=0
            limit : OPTIONAL : Limit response to a specific number of objects. Must be a positive number. For example, limit=10
            n_results : OPTIONAL : Number of total result to retrieve.
        """
        path = "/system/jobs"
        params = {"page":page,"limit":limit}
        res = self.connector.getData(self.endpoint+path,params=params)
        data = res['children']
        count = len(data)
        nextPage = res['_page'].get('next','')
        while nextPage != "" and count < n_results:
            page += 1 
            params = {"page":page,"limit":limit}
            res = self.connector.getData(self.endpoint+path,
                            params=params, headers=self.header)
            count += len(res['children'])
            data += res['children']
            nextPage = res['_page'].get('next','')
        return data
    
    def getDeleteSystemJob(self,jobId:str=None)->dict:
        """
        Get a specific delete system job by its ID.
        Arguments:
            jobId : REQUIRED : Job ID to be retrieved.
        """
        if jobId is None:
            raise ValueError("Require a system Job ID")
        path = f"/system/jobs/{jobId}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res
    
    def deleteDeleteSystemJob(self,jobId:str=None)->dict:
        """
        Delete a specific delete system job by its ID.
        Arguments:
            jobId : REQUIRED : Job ID to be deleted.
        """
        if jobId is None:
            raise ValueError("Require a system Job ID")
        path = f"/system/jobs/{jobId}"
        res = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res

    def getComputedAttributes(self)->list:
        """
        Retrieve the list of computed attributes set up in your organization.
        """
        path = "/config/computedAttributes"
        res = self.connector.getData(self.endpoint + path)
        data = res['children']
        nextPage = res['_page'].get('next','')
        # while nextPage != "":
        #     res = self.connector.getData(self.endpoint+path,
        #                     params=params, headers=self.header)
        #     data += res['children']
        #     nextPage = res['_page'].get('next','')
        return data
    
    def getComputedAttribute(self,attributeId:str=None)->dict:
        """
        Returns a single computed attribute.
        Arguments:
            attributeId : REQUIRED : The computed attribute ID.
        """
        if attributeId is None:
            raise ValueError("Require a computed attribute ID")
        path = f"/config/computedAttributes/{attributeId}"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def deleteComputedAttribute(self,attributeId:str=None)->dict:
        """
        Delete a specific computed attribute.
        Arguments:
            attributeId : REQUIRED : The computed attribute ID to be deleted.
        """
        if attributeId is None:
            raise ValueError("Require a computed attribute ID")
        path = f"/config/computedAttributes/{attributeId}"
        res = self.connector.deleteData(self.endpoint+path)
        return res

    def getDestinations(self)->dict:
        """
        Retrieve a list of edge projection destinations. The latest definitions are returned.
        """
        path = "/config/destinations"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def createDestination(self,destinationConfig:dict=None)->dict:
        """
        Create a new edge projection destination. Assume that there is time between creation and propagation of this information to the edge.
        Arguments:
            destinationConfig : REQUIRED : the destination configuration
        """
        privateHeader = deepcopy(self.header)
        privateHeader['Content-Type'] = 'application/vnd.adobe.platform.projectionDestination+json; version=1'
        if destinationConfig is None:
            raise ValueError("Require a destination configuration object")
        path = "/config/destinations"
        res = self.connector.postData(self.endpoint + path, data=destinationConfig,headers=privateHeader)
        return res

    def getDestination(self,destinationId:str=None)->dict:
        """
        Get a specific destination based on its ID.
        Arguments:
            destinationId : REQUIRED : The destination ID to be retrieved 
        """
        if destinationId is None:
            raise ValueError("Require a destination ID")
        path = f"/config/destinations/{destinationId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def deleteDestination(self, destinationId:str=None)->dict:
        """
        Delete a specific destination based on its ID.
        Arguments:
            destinationId : REQUIRED : The destination ID to be deleted 
        """
        if destinationId is None:
            raise ValueError("Require a destination ID")
        path = f"/config/destinations/{destinationId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res
    
    def updateDestination(self,destinationId:str=None,destinationConfig:dict=None)->dict:
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
        privateHeader = deepcopy(self.header)
        privateHeader['Content-Type'] = 'application/vnd.adobe.platform.projectionDestination+json'
        path = f"/config/destinations/{destinationId}"
        res = self.connector.putData(self.endpoint + path,data=destinationConfig,headers=privateHeader)
        return res

    
    def getProjections(self,schemaName:str=None,name:str=None)->dict:
        """
        Retrieve a list of edge projection configurations. The latest definitions are returned.
        Arguments:
            schemaName : OPTIONAL : The name of the schema class associated with the projection configuration you want to access.
                example : _xdm.context.profile
            name : OPTIONAL : The name of the projection configuration you want to access.
                if name is specified, schemaName is also required.
        """
        path = "/config/projections"
        params={}
        if name is not None and schemaName is None:
            raise AttributeError("You must specify a schema name when setting a projection name")
        if schemaName is not None:
            params['schemaName'] = schemaName
        if name is not None:
            params['name'] = name
        res = self.connector.getData(self.endpoint+path,params=params,headers=self.headers)
        return res

    def getProjection(self,projectionId:str=None)->dict:
        """
        Retrieve a single projection based on its ID.
        Arguments:
            projectionId : REQUIRED : the projection ID to be retrieved.
        """
        if projectionId is None:
            raise ValueError("Require a projection ID")
        path = f"/config/projections/{projectionId}"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def deleteProjection(self,projectionId:str=None)->dict:
        """
        Delete a single projection based on its ID.
        Arguments:
            projectionId : REQUIRED : the projection ID to be deleted.
        """
        if projectionId is None:
            raise ValueError("Require a projection ID")
        path = f"/config/projections/{projectionId}"
        res = self.connector.deleteData(self.endpoint+path)
        return res
    
    def createProjection(self,schemaName:str=None,projectionConfig:dict=None)->dict:
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
        path = "/config/projections"
        params = {'schemaName' : schemaName}
        privateHeader = deepcopy(self.header)
        privateHeader['Content-Type'] = 'application/vnd.adobe.platform.projectionConfig+json; version=1'
        res = self.connector.postData(self.endpoint + path, params=params, data=projectionConfig, privateHeader=privateHeader)
        return res
    
    def updateProjection(self,projectionId:str=None,projectionConfig:dict=None)->dict:
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
        privateHeader = deepcopy(self.header)
        privateHeader['Content-Type'] = 'application/vnd.adobe.platform.projectionConfig+json'
        path = f"/config/projections/{projectionId}"
        res = self.connector.putData(self.endpoint+path,data=projectionConfig,headers=privateHeader)
        return res

