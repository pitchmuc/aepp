#  Copyright 2026 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

import aepp
from dataclasses import dataclass
from aepp import connector
from aepp.configs import ConnectObject
import json, re, logging
from urllib.parse import urlparse, parse_qs


class AJO:
    """
    AJO class from the AEP API. This class helps you on getting information on the Adobe Journey Optimizer
    The full documentation can be found here: https://developer.adobe.com/journey-optimizer-apis/ 
    Arguments:
        config : OPTIONAL : ConnectObject or a dictionary with key similar to the aepp.config.config_object
        header : OPTIONAL : header object  in the config module (DO NOT MODIFY)
        loggingObject : OPTIONAL : If you want to set logging capability for your actions.
    kwargs:
        kwargs value will update the header
    """
    loggingEnabled = False
    logger = None

    def __init__(self,
                config: dict | ConnectObject = aepp.config.config_object,
                header: dict = aepp.config.header,
                loggingObject: dict = None,
                **kwargs):
        if loggingObject is not None and sorted(["level","stream","format","filename","file"]) == sorted(list(loggingObject.keys())):
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
            logger=self.logger)
        self.header = self.connector.header
        self.header.update(**kwargs)
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.endpoint = aepp.config.endpoints['global']+aepp.config.endpoints["ajo"]
    

    def getJourneys(self, filter:str=None,fields:str=None,sort:str=None)->list:
        """
        Returns a list of journeys based on the provided filters.
        If no filters are used, get all the journeys in the sandbox.
        Arguments:
            filter : OPTIONAL : Search filters in URL-encoded format. Supports &-separated fields with basic operators '=', '>', '<', '>=', '<='.
                    Example: filter=url_encoded(status=draft,live&metadata.lastModifiedAt>2024-12-25)
            fields : OPTIONAL : Comma-separated list of fields to include in the response. Allows selective field retrieval for performance optimization.
                    Example: fields=name,status,metadata,createdBy
            sort : OPTIONAL : Sort criteria in format 'field=direction'. Multiple sorts can be comma-separated. Direction can be 'asc' or 'desc'.
                    Example: sort=url_encoded(name=asc,metadata.createdAt=desc)
        """
        params = {'pageSize':100,'page':0}
        if filter is not None:
            params["filter"] = filter
        if fields is not None:
            params["fields"] = fields
        if sort is not None:
            params["sort"] = sort
        path = '/journey'
        response = self.connector.getData(self.endpoint+path, params=params)
        data = response.get('results',[])
        pages = response.get('pages',1)
        while params['page']<pages-1:
            params['page']+=1
            response = self.connector.getData(self.endpoint+path, params=params)
            data+= response.get('results',[])
            pages = response.get('pages',1)
        return data
    
    def getJourney(self, journeyId:str, include:str=None)->dict:
        """
        Returns the details of a specific journey.
        Arguments:
            journeyId : REQUIRED : The unique identifier of the journey to retrieve.
            include : OPTIONAL : Comma-separated list of additional data to include in the response (e.g., "campaigns", "surfaces", "rulesets"). Enriches the journey model with related information.
                    Example: include=campaigns,rulesets
        """
        params = {}
        if include is not None:
            params["include"] = include
        path = f'/journey/{journeyId}'
        response = self.connector.getData(self.endpoint+path, params=params)
        return response
    

    def getCappings(self)->list:
        """
        Return the list of all endpoint capping configurations defined for the given IMS organization and sandbox.
        """
        endpoint = 'https://platform.adobe.io/journey/orchestration/list/endpointConfigs'
        response = self.connector.postData(endpoint)
        return response.get('results',[])

    def getCapping(self,uid:str=None) -> dict:
        """
        Return the endpoint capping configuration for a given endpoint, IMS organization and sandbox.
        Arguments:
            uid : REQUIRED : The unique identifier of the endpoint capping configuration to retrieve.
        """
        if uid is None:
            raise ValueError("uid is required to get a specific capping configuration")
        
        endpoint = f'https://platform.adobe.io/journey/orchestration/endpointConfigs/{uid}'
        response = self.connector.getData(endpoint)
        return response.get('result',response)
    
    def deleteCapping(self,uid:str=None) -> bool:
        """
        Delete the endpoint capping configuration for a given endpoint, IMS organization and sandbox.
        In case the configuration has been deployed, it must be undeployed before being deleted. Otherwise an error response with HTTP Status Code 500 is returned :
        Arguments:
            uid : REQUIRED : The unique identifier of the endpoint capping configuration to delete.
        """
        if uid is None:
            raise ValueError("uid is required to delete a specific capping configuration")
        endpoint = f'https://platform.adobe.io/journey/orchestration/endpointConfigs/{uid}'
        response = self.connector.deleteData(endpoint)
        return response
    
    def createCapping(self,data:dict=None,
                      url:str=None,
                      methods:list[str]=None,
                      action:str=None,
                      maxHttpConnections:int=None,
                      maxCallsCount:int=None,
                      periodInMs:int=None)->dict:
        """
        Create a capping configuration on a given endpoint identified by its URL. The endpoint can be used in one or more actions and data sources.
        Arguments: 
            data : OPTIONAL : the full endpoint capping configuration in a dictionary format. If not provided, the configuration will be built based on the other arguments.
            url : OPTIONAL : if data is not provided : The URL of the endpoint to cap (e.g., "https://api.example.org/data/2.5/weather").
            methods : OPTIONAL : the methods called on this endpoint, as defined in the actions or data sources. Ex ["GET", "POST"]
            action : OPTIONAL : if the capping will be applied on the endpoint when executing a Custom Action
            maxHttpConnections : OPTIONAL :  max count of simultaneous connections to the endpoint (max value is 400). If not provided, there will be no limitation of the number of connections to the endpoint.
            maxCallsCount : OPTIONAL : max count of calls to the endpoint in the defined period. If not provided, there will be no limitation of the number of calls to the endpoint.
            periodInMs : OPTIONAL : the period for the maxCallsCount limitation, in milliseconds (has to be greater than 0)
        """
        endpoint = "https://platform.adobe.io/journey/orchestration/endpointConfigs"
        if data is not None and type(data) == dict:
            payload = data
            if 'url' not in payload.keys():
                raise ValueError("url is required in the data to create a capping configuration")
            if 'methods' not in payload.keys():
                raise ValueError("methods is required in the data to create a capping configuration")
            res = self.connector.postData(endpoint, data=payload)
            return res
        else:
            data = {
                "url": url,
                "methods": methods,
                "orgId": self.connector.config["org_id"],
            }
            if action is not None:
                data["action"] = action
            elif maxHttpConnections is not None:
                data["dataSource"] = {"maxHttpConnections": maxHttpConnections,"rating":{}}
                if maxCallsCount is not None:
                    data["dataSource"]['rating']["maxCallsCount"] = maxCallsCount
                if periodInMs is not None:
                    data["dataSource"]['rating']["periodInMs"] = periodInMs
            res = self.connector.postData(endpoint, data=data)
            return res
    
    def updateCapping(self,uid:str=None,
                      data:dict=None,
                      url:str=None,
                      methods:list[str]=None,
                      action:str=None,
                      maxHttpConnections:int=None,
                      maxCallsCount:int=None,
                      periodInMs:int=None)->dict:
        """
        Create a capping configuration on a given endpoint identified by its URL. The endpoint can be used in one or more actions and data sources.
        Arguments: 
            uid : REQUIRED : The unique identifier of the endpoint capping configuration to update.
            data : OPTIONAL : the full endpoint capping configuration in a dictionary format. If not provided, the configuration will be built based on the other arguments.
            url : OPTIONAL : if data is not provided : The URL of the endpoint to cap (e.g., "https://api.example.org/data/2.5/weather").
            methods : OPTIONAL : the methods called on this endpoint, as defined in the actions or data sources. Ex ["GET", "POST"]
            action : OPTIONAL : if the capping will be applied on the endpoint when executing a Custom Action
            maxHttpConnections : OPTIONAL :  max count of simultaneous connections to the endpoint (max value is 400). If not provided, there will be no limitation of the number of connections to the endpoint.
            maxCallsCount : OPTIONAL : max count of calls to the endpoint in the defined period. If not provided, there will be no limitation of the number of calls to the endpoint.
            periodInMs : OPTIONAL : the period for the maxCallsCount limitation, in milliseconds (has to be greater than 0)
        """
        if uid is None:
            raise ValueError("uid is required to update a specific capping configuration")
        endpoint = f"https://platform.adobe.io/journey/orchestration/endpointConfigs/{uid}"
        if data is not None and type(data) == dict:
            payload = data
            if 'url' not in payload.keys():
                raise ValueError("url is required in the data to create a capping configuration")
            if 'methods' not in payload.keys():
                raise ValueError("methods is required in the data to create a capping configuration")
        else:
            data = {
                "url": url,
                "methods": methods,
                "orgId": self.connector.config["org_id"],
            }
            if action is not None:
                data["action"] = action
            elif maxHttpConnections is not None:
                data["dataSource"] = {"maxHttpConnections": maxHttpConnections,"rating":{}}
                if maxCallsCount is not None:
                    data["dataSource"]['rating']["maxCallsCount"] = maxCallsCount
                if periodInMs is not None:
                    data["dataSource"]['rating']["periodInMs"] = periodInMs
        res = self.connector.putData(endpoint, data=data)
        return res

    def deployCapping(self,uid:str=None) -> dict:
        """
        Deploy the endpoint capping configuration for a given endpoint, IMS organization and sandbox.
        Arguments:
            uid : REQUIRED : The unique identifier of the endpoint capping configuration to deploy.
        """
        if uid is None:
            raise ValueError("uid is required to deploy a specific capping configuration")
        endpoint = f'https://platform.adobe.io/journey/orchestration/endpointConfigs/{uid}/deploy'
        response = self.connector.postData(endpoint)
        return response
    
    def undeployCapping(self,uid:str=None) -> dict:
        """
        Undeploy the endpoint capping configuration for a given endpoint, IMS organization and sandbox.
        Arguments:
            uid : REQUIRED : The unique identifier of the endpoint capping configuration to undeploy.
        """
        if uid is None:
            raise ValueError("uid is required to undeploy a specific capping configuration")
        endpoint = f'https://platform.adobe.io/journey/orchestration/endpointConfigs/{uid}/undeploy'
        response = self.connector.postData(endpoint)
        return response
    
    def getThrottlings(self)->list:
        """
        Return the list of all endpoint throttling configurations defined for the given IMS organization and sandbox.
        """
        endpoint = 'https://platform.adobe.io/journey/orchestration/list/throttlingConfigs'
        response = self.connector.postData(endpoint)
        return response
    
    def getThrottling(self,uid:str=None) -> dict:
        """
        Return the endpoint throttling configuration for a given endpoint, IMS organization and sandbox.
        Arguments:
            uid : REQUIRED : The unique identifier of the endpoint throttling configuration to retrieve.
        """
        if uid is None:
            raise ValueError("uid is required to get a specific throttling configuration")
        endpoint = f'https://platform.adobe.io/journey/orchestration/throttlingConfigs/{uid}'
        response = self.connector.getData(endpoint)
        return response
    
    def deleteThrottling(self,uid:str=None) -> dict:
        """
        Delete the endpoint throttling configuration for a given endpoint, IMS organization and sandbox.
        Arguments:
            uid : REQUIRED : The unique identifier of the endpoint throttling configuration to delete.
        """
        if uid is None:
            raise ValueError("uid is required to delete a specific throttling configuration")
        endpoint = f'https://platform.adobe.io/journey/orchestration/throttlingConfigs/{uid}'
        response = self.connector.deleteData(endpoint)
        return response
    
    def checkThrottling(self,uid:str=None) -> dict:
        """
        Check if an throttling configuration can be deployed.
        Arguments:
            uid : REQUIRED : The unique identifier of the endpoint throttling configuration to check.
        """
        if uid is None:
            raise ValueError("uid is required to check a specific throttling configuration")
        endpoint = f'https://platform.adobe.io/journey/orchestration/throttlingConfigs/{uid}/canDeploy'
        response = self.connector.getData(endpoint)
        return response
    
    def deployThrottling(self,uid:str=None) -> dict:
        """
        Deploy the endpoint throttling configuration for a given endpoint, IMS organization and sandbox.
        Arguments:
            uid : REQUIRED : The unique identifier of the endpoint throttling configuration to deploy.
        """
        if uid is None:
            raise ValueError("uid is required to deploy a specific throttling configuration")
        endpoint = f'https://platform.adobe.io/journey/orchestration/throttlingConfigs/{uid}/deploy'
        response = self.connector.postData(endpoint)
        return response
    def undeployThrottling(self,uid:str=None) -> dict:
        """
        Undeploy the endpoint throttling configuration for a given endpoint, IMS organization and sandbox.
        Arguments:
            uid : REQUIRED : The unique identifier of the endpoint throttling configuration to undeploy.
        """
        if uid is None:
            raise ValueError("uid is required to undeploy a specific throttling configuration")
        endpoint = f'https://platform.adobe.io/journey/orchestration/throttlingConfigs/{uid}/undeploy'
        response = self.connector.postData(endpoint)
        return response
    
    def createThrottling(self,data:dict=None,
                         name:str=None,
                         description:str="",
                         urlPattern:str=None,
                         methods:list=None,
                         maxThroughput:int=None) -> dict:
        """
        Create a new endpoint throttling configuration for a given endpoint, IMS organization and sandbox.
        Arguments:
            data : OPTIONAL : the full endpoint throttling configuration in a dictionary format. If not provided, the configuration will be built based on the other arguments.
            name : OPTIONAL : The name of the throttling configuration. Required if data argument is not provided.
            description : OPTIONAL : The description of the throttling configuration. Required if data argument is not provided.
            urlPattern : OPTIONAL : The URL pattern of the endpoint to throttle (e.g., "https://api.example.org/data/2.5/*"). Required if data argument is not provided.
            methods : OPTIONAL : The methods to throttle on this endpoint, as defined in the actions. Ex ["POST", "PUT"],
            maxThroughput : OPTIONAL : The maximum throughput for the endpoint, in calls per second. Required if data argument is not provided.
        """
        endpoint = "https://platform.adobe.io/journey/orchestration/throttlingConfigs"
        if data is not None and type(data) == dict:
            if 'urlPattern' not in data.keys():
                raise ValueError("urlPattern is required in the data to create a throttling configuration")
            if 'methods' not in data.keys():
                raise ValueError("methods is required in the data to create a throttling configuration")
            if 'maxThroughput' not in data.keys():
                raise ValueError("maxThroughput is required in the data to create a throttling configuration")
        else:
            if name is None:
                raise ValueError("name is required to create a throttling configuration if data argument is not provided")
            if urlPattern is None:
                raise ValueError("urlPattern is required to create a throttling configuration if data argument is not provided")
            if methods is None:
                raise ValueError("methods is required to create a throttling configuration if data argument is not provided")
            if maxThroughput is None:
                raise ValueError("maxThroughput is required to create a throttling configuration if data argument is not provided")
            data = {
            "name": name,
            "description": description,
            "urlPattern": urlPattern,
            "methods": methods,
            "maxThroughput": maxThroughput
            }
        res = self.connector.postData(endpoint, data=data)
        return res
    
    def updateThrottling(self,uid:str=None,
                         data:dict=None,
                         name:str=None,
                         description:str="",
                         urlPattern:str=None,
                         methods:list=None,
                         maxThroughput:int=None) -> dict:
        """
        Update an existing endpoint throttling configuration for a given endpoint, IMS organization and sandbox.
        Arguments:
            data : OPTIONAL : the full endpoint throttling configuration in a dictionary format. If not provided, the configuration will be built based on the other arguments.
            name : OPTIONAL : The name of the throttling configuration. Required if data argument is not provided.
            description : OPTIONAL : The description of the throttling configuration. Required if data argument is not provided.
            urlPattern : OPTIONAL : The URL pattern of the endpoint to throttle (e.g., "https://api.example.org/data/2.5/*"). Required if data argument is not provided.
            methods : OPTIONAL : The methods to throttle on this endpoint, as defined in the actions. Ex ["POST", "PUT"],
            maxThroughput : OPTIONAL : The maximum throughput for the endpoint, in calls per second. Required if data argument is not provided.
        """
        if uid is None:
            raise ValueError("uid is required to update a specific throttling configuration")
        endpoint = f"https://platform.adobe.io/journey/orchestration/throttlingConfigs/{uid}"
        if data is not None and type(data) == dict:
            if 'urlPattern' not in data.keys():
                raise ValueError("urlPattern is required in the data to update a throttling configuration")
            if 'methods' not in data.keys():
                raise ValueError("methods is required in the data to update a throttling configuration")
            if 'maxThroughput' not in data.keys():
                raise ValueError("maxThroughput is required in the data to update a throttling configuration")
        else:
            if name is None:
                raise ValueError("name is required to update a throttling configuration if data argument is not provided")
            if urlPattern is None:
                raise ValueError("urlPattern is required to update a throttling configuration if data argument is not provided")
            if methods is None:
                raise ValueError("methods is required to update a throttling configuration if data argument is not provided")
            if maxThroughput is None:
                raise ValueError("maxThroughput is required to update a throttling configuration if data argument is not provided")
            data = {
            "name": name,
            "description": description,
            "urlPattern": urlPattern,
            "methods": methods,
            "maxThroughput": maxThroughput
            }
        res = self.connector.putData(endpoint, data=data)
        return res
    
    def getSurfaces(self,count:int=50,orderBy:str="surfaceName",channel:str="inapp",prop:str=None,surfaceType:str=None)->list:
        """
        Return the list of all surfaces defined for the given IMS organization and sandbox.
        Arguments:
            count : OPTIONAL : The maximum number of surfaces to return. Default value is 50.
            orderBy : OPTIONAL : The field to order the surfaces by. Default value is "surfaceName".
            channel : OPTIONAL : The channel of the surfaces to return. Default value is "inapp".
            prop : OPTIONAL : The property of the surface to filter on (e.g. "surfaceName==ajo;created_at>2021-09-28".
            surfaceType : OPTIONAL : The type of the surface to filter on enum: ["appConfigurationId" "channelConfigurationId" "surfaceId" "brandingPresetId"]
        """
        params = {
            "page":0,
            "count": count,
            "orderby": orderBy,
            "channel": channel
        }
        if prop is not None:
            params["property"] = prop
        if surfaceType is not None and surfaceType in ["appConfigurationId","channelConfigurationId","surfaceId","brandingPresetId"]:
            params["type"] = surfaceType
        endpoint = 'https://platform.adobe.io/journey/campaigns/service/metadata/surfaces'
        response = self.connector.postData(endpoint, params=params)
        data = response.get('data',[])
        pages = response.get('_page',{}).get('totalPages',1)
        while params['page']<pages-1:
            params['page']+=1
            response = self.connector.postData(endpoint, params=params)
            data += response.get('data',[])
            pages = response.get('_page',{}).get('totalPages',1)
        return data
    
    def getSurfaceDetail(self,channel:str=None,surfaceId:str=None)->dict:
        """
        Return the details of a surface for the given IMS organization and sandbox.
        Arguments:
            channel : REQUIRED : The channel of the surface to return.
            surfaceId : REQUIRED : The unique identifier of the surface to return.
        """
        if channel is None:
            raise ValueError("channel is required to get surface details")
        if surfaceId is None:
            raise ValueError("surfaceId is required to get surface details")
        endpoint = f'https://platform.adobe.io/journey/campaigns/service/metadata/surfaces/{channel}/{surfaceId}'
        response = self.connector.getData(endpoint)
        return response
    
    def getWorkflow(self,workflowId:str=None)->dict:
        """
        Return the details of a workflow for the given IMS organization and sandbox.
        Arguments:
            workflowId : REQUIRED : The unique identifier of the workflow to return.
        """
        if workflowId is None:
            raise ValueError("workflowId is required to get workflow details")
        endpoint = f'https://platform.adobe.io/journey/campaigns/service/workflows/{workflowId}'
        response = self.connector.getData(endpoint)
        return response
    
    def getCampaigns(self, prop:str=None, full:bool=False,actions:bool=True,orderBy:str="name")->list:
        """
        Return the list of all campaigns defined for the given IMS organization and sandbox.
        Arguments:
            prop : OPTIONAL : The property of the campaign to filter on (e.g. "campaignClass!=inline;name=like="my campaign name").
            full : OPTIONAL : Whether to return the full details of the campaigns or only the summary. Default value is False (summary only).
            actions : OPTIONAL : Whether to return the actions associated with the campaigns. Default value is True.
            orderBy : OPTIONAL : The field by which to order the campaigns. Default value is "name".
        """
        params = {"page":0,"count":50}
        if orderBy is not None:
            params["orderby"] = orderBy
        if prop is not None:
            params["property"] = prop
        if full:
            params["full"] = True
        if actions is not None:
            params["actions"] = actions
        endpoint = 'https://platform.adobe.io/journey/campaigns/service/campaigns'
        response = self.connector.postData(endpoint, params=params)
        data = response.get('data',[])
        pages = response.get('_page',{}).get('totalPages',1)
        while params.get('page',0)<pages-1:
            params['page'] += 1
            response = self.connector.postData(endpoint, params=params)
            data += response.get('data',[])
            pages = response.get('_page',{}).get('totalPages',1)
        return data
    
    def getCampaignVersions(self,campaignId:str=None,prop:str=None,full:bool=False,actions:bool=True)->list:
        """
        Return the list of all versions for a campaign for the given IMS organization and sandbox.
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to return the versions for.
        """
        params = {"page":0,"count":50}
        if prop is not None:
            params["property"] = prop
        if full:
            params["full"] = True
        if actions is not None:
            params["actions"] = actions
        if campaignId is None:
            raise ValueError("campaignId is required to get campaign versions")
        endpoint = f'https://platform.adobe.io/journey/campaigns/service/campaigns/{campaignId}/versions'
        response = self.connector.getData(endpoint, params=params)
        data = response.get('data',[])
        pages = response.get('_page',{}).get('totalPages',1)
        while params.get('page',0)<pages-1:
            params['page'] += 1
            response = self.connector.getData(endpoint, params=params)
            data += response.get('data',[])
            pages = response.get('_page',{}).get('totalPages',1)
        return data
    
    def getCampaignMessage(self,campaignId:str=None,messageId:str=None)->dict:
        """
        Return the details of a message for a campaign for the given IMS organization and sandbox.
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to return.
            messageId : REQUIRED : The unique identifier of the message to return.
        """
        if campaignId is None:
            raise ValueError("campaignId is required to get campaign message details")
        if messageId is None:
            raise ValueError("messageId is required to get campaign message details")
        endpoint = f'https://platform.adobe.io/journey/campaigns/service/campaigns/{campaignId}/messages/{messageId}'
        response = self.connector.getData(endpoint)
        return response
    
    def getCampaignMessageVariant(self,campaignId:str=None,messageId:str=None,channel:str=None,variantId:str=None)->dict:
        """
        Return the details of a message variant for a campaign for the given channel and variant
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to return.
            messageId : REQUIRED : The unique identifier of the message to return.
            channel : REQUIRED : The channel of the message to return.
            variantId : REQUIRED : The unique identifier of the variant to return.
        """
        if campaignId is None:
            raise ValueError("campaignId is required to get campaign message variant details")
        if messageId is None:
            raise ValueError("messageId is required to get campaign message variant details")
        if channel is None:
            raise ValueError("channel is required to get campaign message variant details")
        if variantId is None:
            raise ValueError("variantId is required to get campaign message variant details")
        endpoint = f'https://platform.adobe.io/journey/campaigns/service/campaigns/{campaignId}/messages/{messageId}/variants/{variantId}'
        response = self.connector.getData(endpoint)
        return response
    
    def getCampaignDetails(self,campaignId:str=None)->dict:
        """
        Return the details of a campaign for the given IMS organization and sandbox.
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to return.
        """
        if campaignId is None:
            raise ValueError("campaignId is required to get campaign details")
        endpoint = f'https://platform.adobe.io/journey/campaigns/service/campaigns/{campaignId}'
        response = self.connector.getData(endpoint)
        return response
    
    def getCampaignPublishingValidation(self,campaignId:str=None,orderBy:str=None,prop:str=None)->dict:
        """
        Return the publishing validation result of a campaign for the given IMS organization and sandbox.
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to return.
            orderBy : OPTIONAL : The field by which to order the validation results.
            prop : OPTIONAL : The property to filter on for the validation results (e.g. "status==error").
        """
        if campaignId is None:
            raise ValueError("campaignId is required to get campaign publishing validation")
        params = {"count":50,"page":0}
        if orderBy:
            params["orderby"] = orderBy
        if prop:
            params["property"] = prop
        endpoint = f'https://platform.adobe.io/journey/campaigns/service/campaigns/{campaignId}/publish/validation'
        response = self.connector.getData(endpoint, params=params)
        pages = response.get('_page',{}).get('totalPages',1)
        while params.get('page',0)<pages-1:
            params['page'] += 1
            response = self.connector.getData(endpoint, params=params)
            data += response.get('data',[])
            pages = response.get('_page',{}).get('totalPages',1)
        return response
    
    def getCampaignPackageDetails(self,campaignId:str=None,packageId:str=None)->dict:
        """
        Return the details of a campaign package for the given IMS organization and sandbox.
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to return the package details for.
            packageId : REQUIRED : The unique identifier of the package to return.
        """
        if campaignId is None:
            raise ValueError("campaignId is required to get campaign package details")
        if packageId is None:
            raise ValueError("packageId is required to get campaign package details")
        endpoint = f'https://platform.adobe.io/journey/campaigns/service/campaigns/{campaignId}/packages/{packageId}'
        response = self.connector.getData(endpoint)
        return response
    
    def getMessageExecutionStatus(self,executionId:str=None)->dict:
        """
        Return the execution status of a message for the given IMS organization and sandbox.
        Arguments:
            executionId : REQUIRED : The unique identifier of the message execution to return the status for.
        """
        if executionId is None:
            raise ValueError("executionId is required to get message execution status")
        endpoint = f'https://platform.adobe.io/ajo/im/executions/audience/{executionId}'
        response = self.connector.getData(endpoint)
        return response
    
    def getScheduleExecutionStatus(self,scheduleId:str=None)->dict:
        """
        Return the execution status of a schedule.
        Arguments:
            scheduleId : REQUIRED : The unique identifier of the schedule execution to return the status for.
        """
        if scheduleId is None:
            raise ValueError("scheduleId is required to get schedule execution status")
        endpoint = f'https://platform.adobe.io/ajo/im/executions/schedules/{scheduleId}'
        response = self.connector.getData(endpoint)
        return response
    
    def deleteScheduleExecution(self,scheduleId:str=None)->dict:
        """
        Delete the execution of a schedule.
        Arguments:
            scheduleId : REQUIRED : The unique identifier of the schedule execution to delete.
        """
        if scheduleId is None:
            raise ValueError("scheduleId is required to delete schedule execution")
        endpoint = f'https://platform.adobe.io/ajo/im/executions/schedules/{scheduleId}'
        response = self.connector.deleteData(endpoint)
        return response
    
    def triggerUnitaryMessageExecution(self, data:dict=None, requestId:str=None, campaignId:str=None, recipients:list[dict]=None)->dict:
        """
        Trigger the execution of a unitary message.
        Arguments:
            data : OPTIONAL : the full message execution payload in a dictionary format. If not provided, the payload will be built based on the other arguments.
            requestId : REQUIRED : The unique identifier of the message execution to trigger.
            campaignId : REQUIRED : The unique identifier of the campaign associated with the message execution.
            recipients : REQUIRED : The list of dictionary recipients for the message execution.
                    example of dictionary for a recipient in the list:
                    {
                        "type": "aep",
                        "userId": "AEP-ProfileID-12345",
                        "namespace": "email",
                        "mergePolicyName": "Default Timebased",
                        "mergePolicySchema": "_xdm.context.profile",
                        "channelData": {
                            "emailAddress": "customer123@example.com",
                            "mobilePhoneNumber": "111-111-1111"
                            },
                        "profile": {
                            "person": {
                                "name": {
                                    "firstName": "Jane",
                                    "lastName": "Doe"
                                }
                            }
                        },
                        "context": {
                            "product": "Gaming Laptop"
                            }
                        }
        """
        if requestId is None:
            raise ValueError("requestId is required to trigger unitary message execution")
        path = f'/im/executions/unitary'
        if data is not None and type(data) == dict:
            if 'requestId' not in data.keys():
                raise ValueError("requestId is required in the data to trigger unitary message execution")
            if 'campaignId' not in data.keys():
                raise ValueError("campaignId is required in the data to trigger unitary message execution")
            if 'recipients' not in data.keys():
                raise ValueError("recipients are required in the data to trigger unitary message execution")
        elif data is None and requestId is not None and campaignId is not None and recipients is not None:
            if requestId is None:
                raise ValueError("requestId is required to trigger unitary message execution")
            if campaignId is None:
                raise ValueError("campaignId is required to trigger unitary message execution")
            if recipients is None or type(recipients) != list or len(recipients) == 0:
                raise ValueError("recipients are required to trigger unitary message execution")
            data = {
                "requestId": requestId,
                "campaignId": campaignId,
                "recipients": recipients
            }
        else:
            raise ValueError("You should provide either the data argument with the full payload or the requestId, campaignId and recipients arguments to trigger unitary message execution")
        response = self.connector.postData(self.endpoint+path, data=data)
        return response
    
    def triggerAudienceMessageExecution(self, data:dict=None, 
                                        requestId:str=None,
                                        campaignId:str=None,
                                        audienceId:str=None,
                                        context:dict=None,
                                        schedule:str=None)->dict:
        """
        Trigger the execution of an audience message. It can be also scheduled.
        Arguments:
            data : OPTIONAL : the full message execution payload in a dictionary format. If not provided, the payload will be built based on the other arguments.
            requestId : REQUIRED : The unique identifier of the message execution to trigger.
            campaignId : REQUIRED : The unique identifier of the campaign associated with the message execution.
            audienceId : REQUIRED : The unique identifier of the audience associated with the message execution.
            context : OPTIONAL : The context of the message execution in a dictionary format. It can contain any relevant information to be passed to the message execution, such as product details, event information, etc.
            schedule : REQUIRED : The schedule time for the message execution. Example: "2016-08-29T09:12:33.001Z"
        """
        path = "/im/executions/audience"
        if data is not None and type(data) == dict:
            if 'requestId' not in data.keys():
                raise ValueError("requestId is required in the data to trigger audience message execution")
            if 'campaignId' not in data.keys():
                raise ValueError("campaignId is required in the data to trigger audience message execution")
            if 'audienceId' not in data.keys():
                raise ValueError("audienceId is required in the data to trigger audience message execution")
            if 'schedule' not in data.keys():
                raise ValueError("schedule is required in the data to trigger audience message execution")
        elif data is None and requestId is not None and campaignId is not None and audienceId is not None and schedule is not None:
                data = {
                    "requestId": requestId,
                    "campaignId": campaignId,
                    "audience":{
                        "id": audienceId
                    },
                    "context": context,
                    "schedule": {
                        "executeAt": schedule
                    }
                }
        else:
            raise ValueError("You should provide either the data argument with the full payload or the requestId, campaignId, audienceId and schedule arguments to trigger audience message execution")
        res = self.connector.postData(self.endpoint+path, data=data)
        return res
    
    def triggerUnitaryHighThrouputMessage(self,data:dict=None,
                                        requestId:str=None,
                                        campaignId:str=None,
                                        recipients:list[dict]=None)->dict:
        """
        Trigger the execution of a unitary message with high throughput. This method is designed for high volume executions and does not return the execution status in real time.
        Arguments:
            data : OPTIONAL : the full message execution payload in a dictionary format. If not provided, the payload will be built based on the other arguments.
            requestId : REQUIRED : The unique identifier of the message execution to trigger.
            campaignId : REQUIRED : The unique identifier of the campaign associated with the message execution.
            recipients : REQUIRED : The list of dictionary recipients for the message execution.
                    example of dictionary for a recipient in the list:
                    {
                    "type": "external",
                    "userId": "customer123@example.com",
                    "namespace": "email",
                    "channelData": {
                        "emailAddress": "customer123@example.com",
                        "mobilePhoneNumber": "111-111-1111"
                    },
                    "profile": {
                        "person": {
                            "name": {
                            "firstName": "Jane",
                            "lastName": "Doe"
                            }
                        }
                    },
                    "context": {
                        "product": "Gaming Laptop"
                        }
                    }
            """
        path = "/im/executions/highthroughput"
        if data is not None and type(data) == dict:
            if 'requestId' not in data.keys():
                raise ValueError("requestId is required in the data to trigger unitary high throughput message execution")
            if 'campaignId' not in data.keys():
                raise ValueError("campaignId is required in the data to trigger unitary high throughput message execution")
            if 'recipients' not in data.keys():
                raise ValueError("recipients are required in the data to trigger unitary high throughput message execution")
        elif data is None and requestId is not None and campaignId is not None and recipients is not None:
            data = {
                "requestId": requestId,
                "campaignId": campaignId,
                "recipients": recipients
            }
        else:
            raise ValueError("You should provide either the data argument with the full payload or the requestId, campaignId and recipients arguments to trigger unitary high throughput message execution")
        response = self.connector.postData(self.endpoint+path, data=data)
        return response
    
    def getUnitaryServiceHealth(self)->dict:
        """
        Return the health status of the unitary message execution service.
        """
        path = '/im/health'
        response = self.connector.getData(self.endpoint+path)
        return response
    
    def triggerCampaignProofJob(self,campaignId:str=None,recipients:list[dict]=None)->dict:
        """
        Trigger a proof job for a campaign. A proof job is a test execution of a campaign that allows to validate the campaign configuration and content before deploying it.
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to trigger the proof job for.
            recipients : REQUIRED : The list of dictionary recipients for the proof job.
                    example of dictionary for a recipient in the list:
                    {
                        "userId": "test@gmail.com",
                        "namespace": "Email",
                        "channelsData": [
                            {
                            "channel": "email",
                            "subjectPrefix": "string",
                            "emailAddresses": []
                            }
                        ],
                        "profile": {},
                        "context": {}
                        }
        """
        if campaignId is None:
            raise ValueError("campaignId is required to trigger campaign proof job")
        if recipients is None or type(recipients) != list or len(recipients) == 0:
            raise ValueError("recipients are required to trigger campaign proof job")
        data = {
            "recipients": recipients
        }
        path = f'/simulations/campaigns/{campaignId}/proofs'
        response = self.connector.postData(self.endpoint+path, data=data)
        return response
    
    def getCampaignProofStatus(self,campaignId:str=None,proofId:str=None)->dict:
        """
        Return the status of a campaign proof job.
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to return the proof job status for.
            proofId : REQUIRED : The unique identifier of the proof job to return the status for.
        """
        if campaignId is None:
            raise ValueError("campaignId is required to get campaign proof job status")
        if proofId is None:
            raise ValueError("proofId is required to get campaign proof job status")
        path = f"/simulations/campaigns/{campaignId}/proofs/{proofId}"
        response = self.connector.getData(self.endpoint+path)
        return response
    
    def createCampaignPreview(self,campaignId:str=None,previewRequestItems:list[dict]=None)->dict:
        """
        Trigger a preview job for a campaign. A preview job is a test execution of a campaign that allows to validate the campaign configuration and content before deploying it. The difference with a proof job is that a preview job does not send any message to the recipients, but only simulates the execution and returns the expected results.
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to trigger the preview job for.
            previewRequestItems : REQUIRED : The list of dictionary recipients for the preview job.
                    example of dictionary for a previewRequestItem in the list:
                    {
                        "userId": "test@gmail.com",
                        "namespace": "Email",
                        "profileAttributes": {},
                        "contextAttributes": {}
                    }
        """
        if campaignId is None:
            raise ValueError("campaignId is required to trigger campaign preview job")
        if previewRequestItems is None or type(previewRequestItems) != list or len(previewRequestItems) == 0:
            raise ValueError("previewRequestItems are required to trigger campaign preview job")
        for item in previewRequestItems:
            if 'userId' not in item.keys():
                raise ValueError("userId is required for each previewRequestItem to trigger campaign preview job")
            if 'namespace' not in item.keys():
                raise ValueError("namespace is required for each previewRequestItem to trigger campaign preview job")
        data = {
            "previewRequestItems": previewRequestItems
        }
        path = f'/simulations/campaigns/{campaignId}/previews'
        response = self.connector.postData(self.endpoint+path, data=data)
        return response
    
    def validateDatasetOrchestration(self,datasetId:str=None)->dict:
        """
        validates if the Orchestrated Campaign extension can be applied on a dataset. It checks if the dataset meets the following criteria:
        Dataset must be associated with a model-based schema.
        Dataset must not be a System dataset or a Profile-enabled dataset.
        Schema behavior must be set to record. (Schemas with behavior timeseries are not supported.)
        Schema must define both a primary key and a version descriptor.
        Dataset must be of CDC (Change Data Capture) type.
        Orchestrated Campaign extension is not enabled on the dataset or in progress.
        Arguments:
            datasetId : REQUIRED : The unique identifier of the dataset to validate.
        """
        if datasetId is None:
            raise ValueError("datasetId is required to validate dataset orchestration")
        path = f'/relational/modeler/datasets/{datasetId}/extensions/validation'
        response = self.connector.getData(self.endpoint+path)
        return response
    
    def getDatasetExtensionJob(self,jobId:str=None)->dict:
        """
        Return the details of a dataset extension job. Dataset extension job is the job that applies the Orchestrated Campaign extension on a dataset that has been validated for orchestration.
        Arguments:
            jobId : REQUIRED : Job Id of the dataset enablement request
        """
        if jobId is None:
            raise ValueError("jobId is required to get dataset extension job details")
        path = f'/relational/modeler/datasets/extensions/enablement/jobs/{jobId}'
        response = self.connector.getData(self.endpoint+path)
        return response
    
    def enableDatasetOrchestration(self,datasetIds:list[str]=None)->dict:
        """
        Enable the Orchestrated Campaign extension on a dataset. This method can be called after validating the dataset for orchestration and once you are ready to apply the extension on the dataset. It will trigger a dataset extension job that will apply the Orchestrated Campaign extension on the dataset.
        Arguments:
            datasetIds : REQUIRED : list of dataset IDs
        """
        if datasetIds is None:
            raise ValueError("datasetId is required to enable dataset orchestration")
        path = f'/relational/modeler/datasets/extensions/enablement'
        data = {
            "datasetIds": datasetIds
        }
        response = self.connector.postData(self.endpoint+path,data=data)
        return response
    
    def triggerOrchestratedCampaign(self,campaignId:str=None)->dict:
        """
        Trigger the execution of an orchestrated campaign. This method is designed to trigger a campaign that has been created with the Orchestrated Campaign extension and is in DRAFT status. It will trigger the campaign execution and return the execution status in real time.
        Arguments:
            campaignId : REQUIRED : The unique identifier of the campaign to trigger.
        """
        if campaignId is None:
            raise ValueError("campaignId is required to trigger orchestrated campaign")
        path = f'/campaign-orchestration/orchestratedCampaigns/{campaignId}/trigger'
        response = self.connector.postData(self.endpoint+path)
        return response
    
    def getContentTemplates(self,prop:str=None,orderBy:str=None)->list:
        """
        Return the list of content templates available for the given IMS organization and sandbox. Content templates are used in orchestrated campaigns to define the content of the messages that will be sent to the recipients.
        Arguments:
            prop : OPTIONAL : The property of the content template to filter on (e.g. "templateName==myTemplate").
            orderBy : OPTIONAL : The property to order the content templates by (e.g. "modifiedAt").
        """
        params = {"limit":1000}
        if prop is not None:
            params["property"] = prop
        if orderBy is not None:
            params["orderby"] = orderBy
        path = f'/contentTemplates'
        response = self.connector.getData(self.endpoint+path, params=params)
        data = response.get('items',[])
        parsedUrl = urlparse(response.get('_links',{}).get('next',{}).get('href',''))
        query_params = parse_qs(parsedUrl.query) or None
        startParam = query_params.get('start', [None])[0]
        while startParam is not None:
            params['start'] = startParam
            response = self.connector.getData(self.endpoint+path, params=params)
            data += response.get('items',[])
            parsedUrl = urlparse(response.get('_links',{}).get('next',{}).get('href',''))
            query_params = parse_qs(parsedUrl.query) or None
            startParam = query_params.get('start', [None])[0]
        return data
    
    def getContentTemplate(self,templateId:str=None)->dict:
        """
        Return the details of a content template for the given IMS organization and sandbox.
        Arguments:
            templateId : REQUIRED : Content Template id
        """
        if templateId is None:
            raise ValueError("templateId is required to get content template details")
        path = f'/content/templates/{templateId}'
        response = self.connector.getData(self.endpoint+path)
        return response
    
    def deleteContentTemplate(self,templateId:str=None)->dict:
        """
        Delete a content template for the given IMS organization and sandbox.
        Arguments:
            templateId : REQUIRED : Content Template id
        """
        if templateId is None:
            raise ValueError("templateId is required to delete content template")
        path = f'/content/templates/{templateId}'
        response = self.connector.deleteData(self.endpoint+path)
        return response
    
    def createContentTemplate(self,data:dict)->dict:
        """
        Create a content template for the given IMS organization and sandbox.
        Arguments:
            data : REQUIRED : the full content template payload in a dictionary format.
                        Example of the content template payload:
                        {
                            "name": "Cyber Monday Sale - Header !!",
                            "description": "Cyber Monday Sale - Header Banner!!",
                            "templateType": "html",
                            "channels": [
                                "email"
                            ],
                            "source": {
                                "origin": "ajo",
                                "metadata": {}
                            },
                            "subType": "HTML",
                            "template": {
                                "html": "<html> Hi {{profile.person.name}} its a great day to shop !! </html>",
                                "editorContext": {}
                            }
                        }
        """
        if data is None or type(data) != dict:
            raise ValueError("data is required to create content template and should be in a dictionary format")
        path = f'/content/templates'
        response = self.connector.postData(self.endpoint+path, data=data)
        return response
    
    def putContentTemplate(self,templateId:str=None,data:dict=None)->dict:
        """
        Update a content template for the given IMS organization and sandbox.
        Arguments:
            templateId : REQUIRED : Content Template id
            data : REQUIRED : the full content template payload in a dictionary format.
                        Example of the content template payload:
                        {
                            "name": "Cyber Monday Sale - Header !!",
                            "description": "Cyber Monday Sale - Header Banner!!",
                            "templateType": "html",
                            "channels": [
                                "email"
                            ],
                            "source": {
                                "origin": "ajo",
                                "metadata": {}
                            },
                            "subType": "HTML",
                            "template": {
                                "html": "<html> Hi {{profile.person.name}} its a great day to shop !! </html>",
                                "editorContext": {}
                            }
                        }
        """
        if templateId is None:
            raise ValueError("templateId is required to update content template")
        if data is None or type(data) != dict:
            raise ValueError("data is required to update content template and should be in a dictionary format")
        path = f'/content/templates/{templateId}'
        response = self.connector.putData(self.endpoint+path, data=data)
        return response
    
    def patchContentTemplate(self,templateId:str=None,data:list[dict]=None)->dict:
        """
        Partially update a content template for the given IMS organization and sandbox.
        Arguments:
            templateId : REQUIRED : Content Template id
            data : REQUIRED : the list of operations to realize on the template fields to update in a dictionary format.
                        Example of the content template payload for a single item:
                        {
                            "op": "add",
                            "path": "string",
                            "value": {},
                            "from": "string"
                        }
        """
        if templateId is None:
            raise ValueError("templateId is required to partially update content template")
        if data is None or type(data) != list:
            raise ValueError("data is required to partially update content template and should be in a list of dictionaries format")
        path = f'/content/templates/{templateId}'
        response = self.connector.patchData(self.endpoint+path, data=data)
        return response
    
    def getContentFragments(self,prop:str=None,orderBy:str=None)->list:
        """
        Return the list of content fragments available for the given IMS organization and sandbox. Content fragments are used in orchestrated campaigns to define reusable pieces of content that can be used in the content templates.
        Arguments:
            prop : OPTIONAL : The property of the content fragment to filter on (e.g. "fragmentName==myFragment").
            orderBy : OPTIONAL : The property to order the content fragments by (e.g. "modifiedAt").
        """
        params = {"limit":1000}
        if prop is not None:
            params["property"] = prop
        if orderBy is not None:
            params["orderby"] = orderBy
        path = f'/content/fragments'
        response = self.connector.getData(self.endpoint+path, params=params)
        data = response.get('items',[])
        parsedUrl = urlparse(response.get('_links',{}).get('next',{}).get('href',''))
        query_params = parse_qs(parsedUrl.query) or None
        startParam = query_params.get('start', [None])[0]
        while startParam is not None:
            params['start'] = startParam
            response = self.connector.getData(self.endpoint+path, params=params)
            data += response.get('items',[])
            parsedUrl = urlparse(response.get('_links',{}).get('next',{}).get('href',''))
            query_params = parse_qs(parsedUrl.query) or None
            startParam = query_params.get('start', [None])[0]
        return data
    
    def getContentFragment(self,fragmentId:str=None)->dict:
        """
        Return the details of a content fragment for the given IMS organization and sandbox.
        Arguments:
            fragmentId : REQUIRED : Content Fragment id
        """
        if fragmentId is None:
            raise ValueError("fragmentId is required to get content fragment details")
        path = f'/content/fragments/{fragmentId}'
        response = self.connector.getData(self.endpoint+path)
        return response
    
    def createContentFragment(self,data:dict)->dict:
        """
        Create a content fragment for the given IMS organization and sandbox.
        Arguments:
            data : REQUIRED : the full content fragment payload in a dictionary format.
                        Example of the content fragment payload:
                        {
                            "name": "Cyber Monday Sale - Header !!",
                            "description": "Cyber Monday Sale - Header Banner!!",
                            "type": "html",
                            "source": {
                                "origin": "ajo",
                                "metadata": {}
                            },
                            "fragment": {
                                "content": "<div> Hi {{profile.person.name}} its a great day to shop !! </div>",
                                "editorContext": {}
                            },
                            "channels": [
                                "email"
                            ]
                        }
        """
        if data is None or type(data) != dict:
            raise ValueError("data is required to create content fragment and should be in a dictionary format")
        if "name" not in data.keys():
            raise ValueError("name is required in the data to create content fragment")
        if "type" not in data.keys():
            raise ValueError("type is required in the data to create content fragment")
        if "fragment" not in data.keys():
            raise ValueError("fragment is required in the data to create content fragment")
        if "channels" not in data.keys():
            raise ValueError("channels are required in the data to create content fragment")
        path = f'/content/fragments'
        response = self.connector.postData(self.endpoint+path, data=data)
        return response
    
    def publishContentFragment(self,fragmentId:str=None)->dict:
        """
        Publish a content fragment for the given IMS organization and sandbox. Publishing a content fragment makes it available for use in the content templates.
        Arguments:
            fragmentId : REQUIRED : Content Fragment id
        """
        if fragmentId is None:
            raise ValueError("fragmentId is required to publish content fragment")
        path = f'/content/fragments/publications'
        data = {
            "fragmentId": fragmentId
            }
        response = self.connector.postData(self.endpoint+path, data=data)
        return response
    
    def patchContentFragment(self,fragmentId:str=None,data:list[dict]=None)->dict:
        """
        Partially update a content fragment for the given IMS organization and sandbox.
        Arguments:
            fragmentId : REQUIRED : Content Fragment id
            data : REQUIRED : the list of operations to realize on the content fragment fields to update in a dictionary format.
                        Example of the content fragment payload for a single item:
                            {
                            "op": "add",
                            "path": "string",
                            "value": { },
                            "from": "string"
                            }
        """
        if fragmentId is None:
            raise ValueError("fragmentId is required to partially update content fragment")
        if data is None or type(data) != list:
            raise ValueError("data is required to partially update content fragment and should be in a list of dictionaries format")
        path = f'/content/fragments/{fragmentId}'
        response = self.connector.patchData(self.endpoint+path, data=data)
        return response
    
    def putContentFragment(self,fragmentId:str=None,data:dict=None)->dict:
        """
        Update a content fragment for the given IMS organization and sandbox.
        Arguments:
            fragmentId : REQUIRED : Content Fragment id
            data : REQUIRED : the full content fragment payload in a dictionary format.
                        Example of the content fragment payload:
                        {
                            "name": "Cyber Monday Sale - Header !!",
                            "description": "Cyber Monday Sale - Header Banner!!",
                            "type": "html",
                            "source": {
                                "origin": "ajo",
                                "metadata": {}
                            },
                            "fragment": {
                                "content": "<div> Hi {{profile.person.name}} its a great day to shop !! </div>",
                                "editorContext": {}
                            },
                            "channels": [
                                "email"
                            ]
                        }
        """
        if fragmentId is None:
            raise ValueError("fragmentId is required to update content fragment")
        if data is None or type(data) != dict:
            raise ValueError("data is required to update content fragment and should be in a dictionary format")
        path = f'/content/fragments/{fragmentId}'
        response = self.connector.putData(self.endpoint+path, data=data)
        return response
    
    def getContentFragmentLastPublication(self,fragmentId:str=None)->dict:
        """
        Return the details of the last publication of a content fragment for the given IMS organization and sandbox.
        Arguments:
            fragmentId : REQUIRED : Content Fragment id
        """
        if fragmentId is None:
            raise ValueError("fragmentId is required to get content fragment last publication details")
        path = f'/content/fragments/{fragmentId}/liveFragment'
        response = self.connector.getData(self.endpoint+path)
        return response
    
    def getContentFragmentPublicationStatus(self,fragmentId:str=None)->dict:
        """
        Fetch the status of last publication request for a content fragment by Id. 
        A fragment can have multiple publications. A publication can either be successful, in progress or can error out. 
        This API will be responsible for fetching the status of the last issued publication request for a fragment.
        Arguments:
            fragmentId : REQUIRED : Content Fragment id
        """
        if fragmentId is None:
            raise ValueError("fragmentId is required to get content fragment publication status")
        path = f'/content/fragments/{fragmentId}/lastPublicationStatus'
        response = self.connector.getData(self.endpoint+path)
        return response
    
    def getEmailsStatus(self,statusType:str="client",prop:str=None,orderBy:str=None)->list:
        """
        Return the status of the emails, if they are suppressed or allowed for that sandbox and AJO setup.
        Arguments:
            statusType : REQUIRED : For suppressed entities use 'client', for allowed entities use 'allowed'. It can be either "client" "allowed"
            prop : OPTIONAL : The property of the email status to filter on (e.g. "creationdate<1631739725150")
            orderBy : OPTIONAL : The property to order the email statuses by (e.g. "-creationdate").
        """
        if statusType not in ["client", "allowed"]:
            raise ValueError("statusType must be either 'client' or 'allowed'")
        params = {"limit":100}
        if prop is not None:
            params["property"] = prop
        if orderBy is not None:
            params["orderby"] = orderBy
        path = f"/config/suppression/addresses"
        res = self.connector.getData(self.endpoint+path, params=params)
        data = res.get('items',[])
        parsedUrl = urlparse(res.get('_links',{}).get('next',{}).get('href',''))
        query_params = parse_qs(parsedUrl.query) or None
        startParam = query_params.get('start', [None])[0]
        while startParam is not None:
            params['start'] = startParam
            res = self.connector.getData(self.endpoint+path, params=params)
            data += res.get('items',[])
            parsedUrl = urlparse(res.get('_links',{}).get('next',{}).get('href',''))
            query_params = parse_qs(parsedUrl.query) or None
            startParam = query_params.get('start', [None])[0]
        return data
    
    def getEmailStatus(self,email:str=None,statusType:str="client")->dict:
        """
        Return the status of a specific email, if it is suppressed or allowed for that sandbox and AJO setup.
        Arguments:
            email : REQUIRED : The email address to check the status for.
            statusType : REQUIRED : For suppressed entities use 'client', for allowed entities use 'allowed'. It can be either "client" "allowed"
        """
        if email is None:
            raise ValueError("email is required to get email status")
        if statusType not in ["client", "allowed"]:
            raise ValueError("statusType must be either 'client' or 'allowed'")
        path = f"/config/suppression/addresses/{email}"
        params = {"type": statusType}
        res = self.connector.getData(self.endpoint+path, params=params)
        return res
    
    def createEmailsStatus(self,statusType:str="client",data:list[dict]=None)->dict:
        """
        Allow or suppress a list of emails for that sandbox and AJO setup.
        Arguments:
            statusType : REQUIRED : For suppressed entities use 'client', for allowed entities use 'allowed'. It can be either "client" "allowed"
            data : REQUIRED : the list of emails to allow or suppress in a dictionary format.
                    Example of the data argument:
                    [
                        {
                            "entity": {
                            "type": "email",
                            "entityValue": "bademailaddress@domain.com"
                            },
                            "comment": "Known bad email address",
                            "user": "myusername@corp.com"
                        }
                    ]
        """
        if statusType not in ["client", "allowed"]:
            raise ValueError("statusType must be either 'client' or 'allowed'")
        if data is None or type(data) != list:
            raise ValueError("data is required to create emails status and should be in a list of dictionaries format")
        path = f"/config/suppression/addresses"
        params = {"type": statusType}
        res = self.connector.postData(self.endpoint+path, params=params, data=data)
        return res
    
    def deleteEmailStatus(self,email:str=None,statusType:str="client")->dict:
        """
        Delete the status of a specific email, if it is suppressed or allowed for that sandbox and AJO setup. This will allow the email again if it was suppressed, or remove it from the allowed list if it was allowed.
        Arguments:
            email : REQUIRED : The email address to delete the status for.
            statusType : REQUIRED : For suppressed entities use 'client', for allowed entities use 'allowed'. It can be either "client" "allowed"
        """
        if email is None:
            raise ValueError("email is required to delete email status")
        if statusType not in ["client", "allowed"]:
            raise ValueError("statusType must be either 'client' or 'allowed'")
        path = f"/config/suppression/addresses/{email}"
        params = {"type": statusType}
        res = self.connector.deleteData(self.endpoint+path, params=params)
        return res

    def getDomainsStatus(self,statusType:str="client",prop:str=None,orderBy:str=None)->list:
        """
        Return the status of the domains, if they are suppressed or allowed for that sandbox and AJO setup.
        Arguments:
            statusType : REQUIRED : For suppressed entities use 'client', for allowed entities use 'allowed'. It can be either "client" "allowed"
            prop : OPTIONAL : The property of the domain status to filter on (e.g. "creationdate<1631739725150")
            orderBy : OPTIONAL : The property to order the domain statuses by (e.g. "-creationdate").
        """
        if statusType not in ["client", "allowed"]:
            raise ValueError("statusType must be either 'client' or 'allowed'")
        params = {"limit":100}
        if prop is not None:
            params["property"] = prop
        if orderBy is not None:
            params["orderby"] = orderBy
        path = f"/config/suppression/domains"
        res = self.connector.getData(self.endpoint+path, params=params)
        data = res.get('items',[])
        parsedUrl = urlparse(res.get('_links',{}).get('next',{}).get('href',''))
        query_params = parse_qs(parsedUrl.query) or None
        startParam = query_params.get('start', [None])[0]
        while startParam is not None:
            params['start'] = startParam
            res = self.connector.getData(self.endpoint+path, params=params)
            data += res.get('items',[])
            parsedUrl = urlparse(res.get('_links',{}).get('next',{}).get('href',''))
            query_params = parse_qs(parsedUrl.query) or None
            startParam = query_params.get('start', [None])[0]
        return data
    
    def getDomainStatus(self,domain:str=None,statusType:str="client")->dict:
        """
        Return the status of a specific domain, if it is suppressed or allowed for that sandbox and AJO setup.
        Arguments:
            domain : REQUIRED : The domain to check the status for.
            statusType : REQUIRED : For suppressed entities use 'client', for allowed entities use 'allowed'. It can be either "client" "allowed"
        """
        if domain is None:
            raise ValueError("domain is required to get domain status")
        if statusType not in ["client", "allowed"]:
            raise ValueError("statusType must be either 'client' or 'allowed'")
        path = f"/config/suppression/domains/{domain}"
        params = {}
        if statusType is not None:
            if statusType not in ["client", "allowed"]:
                raise ValueError("statusType must be either 'client' or 'allowed'")
            params = {"type": statusType}
        res = self.connector.getData(self.endpoint+path, params=params)
        return res
    
    def createDomainsStatus(self,statusType:str="client",data:list[dict]=None)->dict:
        """
        Allow or suppress a list of domains for that sandbox and AJO setup.
        Arguments:
            statusType : REQUIRED : For suppressed entities use 'client', for allowed entities use 'allowed'. It can be either "client" "allowed"
            data : REQUIRED : the list of domains to allow or suppress in a dictionary format.
                    Example of the data argument:
                    [
                        {
                            "entity": {
                            "type": "domain",
                            "entityValue": "baddomain.com"
                            },
                            "comment": "Known bad domain",
                            "user": "myusername@corp.com"
                        }
                    ]
        """
        if statusType not in ["client", "allowed"]:
            raise ValueError("statusType must be either 'client' or 'allowed'")
        if data is None or type(data) != list:
            raise ValueError("data is required to create domains status and should be in a list of dictionaries format")
        path = f"/config/suppression/domains"
        params = {"type": statusType}
        res = self.connector.postData(self.endpoint+path, params=params, data=data)
        return res
    
    def deleteDomainStatus(self,domain:str=None,statusType:str="client")->dict:
        """
        Delete the status of a specific domain, if it is suppressed or allowed for that sandbox and AJO setup. This will allow the domain again if it was suppressed, or remove it from the allowed list if it was allowed.
        Arguments:
            domain : REQUIRED : The domain to delete the status for.
            statusType : REQUIRED : For suppressed entities use 'client', for allowed entities use 'allowed'. It can be either "client" "allowed"
        """
        if domain is None:
            raise ValueError("domain is required to delete domain status")
        if statusType not in ["client", "allowed"]:
            raise ValueError("statusType must be either 'client' or 'allowed'")
        path = f"/config/suppression/domains/{domain}"
        params = {"type": statusType}
        res = self.connector.deleteData(self.endpoint+path, params=params)
        return res
    
    def getUploadJobs(self,prop:str=None,orderBy:str=None)->list:
        """
        Return the list of upload jobs for that sandbox and AJO setup.
        Arguments:
            prop : OPTIONAL : The property of the upload job to filter on (e.g. "creationdate<1631739725150")
            orderBy : OPTIONAL : The property to order the upload jobs by (e.g. "-creationdate").
        """
        params = {"limit":100}
        if prop is not None:
            params["property"] = prop
        if orderBy is not None:
            params["orderby"] = orderBy
        path = f"/config/suppression/uploads"
        res = self.connector.getData(self.endpoint+path, params=params)
        data = res.get('items',[])
        parsedUrl = urlparse(res.get('_links',{}).get('next',{}).get('href',''))
        query_params = parse_qs(parsedUrl.query) or None
        startParam = query_params.get('start', [None])[0]
        while startParam is not None:
            params['start'] = startParam
            res = self.connector.getData(self.endpoint+path, params=params)
            data += res.get('items',[])
            parsedUrl = urlparse(res.get('_links',{}).get('next',{}).get('href',''))
            query_params = parse_qs(parsedUrl.query) or None
            startParam = query_params.get('start', [None])[0]
        return data
    
    def getUploadJob(self,jobId:str=None)->dict:
        """
        Return the details of an upload job for that sandbox and AJO setup.
        Arguments:
            jobId : REQUIRED : The unique identifier of the upload job.
        """
        if jobId is None:
            raise ValueError("jobId is required to get upload job details")
        path = f"/config/suppression/uploads/{jobId}"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def deleteUploadJob(self,jobId:str=None)->dict:
        """
        Delete an upload job for that sandbox and AJO setup.
        Arguments:
            jobId : REQUIRED : The unique identifier of the upload job.
        """
        if jobId is None:
            raise ValueError("jobId is required to delete upload job")
        path = f"/config/suppression/uploads/{jobId}"
        res = self.connector.deleteData(self.endpoint+path)
        return res
    
    def deleteAllSuppressionData(self)->dict:
        """
        Delete all suppression data for that sandbox and AJO setup. 
        This will allow all emails and domains again for that setup.
        """
        path = f"/config/suppression/admin/{self.connector.config['org_id']}/{self.sandbox}"
        res = self.connector.deleteData(self.endpoint+path)
        return res
    
    def uploadSuppressionData(self,statusType:str="client",filePath:str=None)->dict:
        """
        Upload a CSV file with a list of emails or domains to allow or suppress for that sandbox and AJO setup.
        Arguments:
            statusType : REQUIRED : For suppressed entities use 'client', for allowed entities use 'allowed'. It can be either "client" "allowed"
            filePath : REQUIRED : The path of the file to upload. The file should be in CSV format with a header and a column named "entityValue" that contains the email addresses or domains to allow or suppress.
        """
        if statusType not in ["client", "allowed"]:
            raise ValueError("statusType must be either 'client' or 'allowed'")
        if filePath is None:
            raise ValueError("filePath is required to upload suppression data")
        path = f"/config/suppression/uploads"
        params = {"type": statusType}
        files = {'file': open(filePath, 'rb')}
        res = self.connector.postData(self.endpoint+path, params=params, files=files)
        files['file'].close()
        return res