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
from .configs import ConnectObject
from copy import deepcopy
from typing import Union
import json

class Edge:
    """
    Server Side Edge data collection and rendering.
    This implementation is using the Edge Server Side API: https://experienceleague.adobe.com/en/docs/experience-platform/edge-network-server-api/overview
    It allows you to send data via the Edge using python applications 
    """
    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(self,
                 dataStreamId : str = None,
                 server: str="server.adobedc.net",
                 config: Union[dict,ConnectObject] = None,
                 version: int = 2,
                 )->None:
        """
            This will instantiate the Edge class
            Arguments:
                dataStreamId : REQUIRED : The datastream ID to be used.
                server : OPTIONAL : If you have setup a CNAME
                config : OPTIONAL : For Authenticated calls. ConnectObject or a dictionary with key similar to the aepp.config.config_object
                version : OPTIONAL : If you want to change the version from v2 to v1 (client side)
        """
        self.versionEdge = version
        self.server = server
        self.endpoint = f"https://{server}/ee/v{self.versionEdge}/interact"
        paramName = "dataStreamId"
        if self.versionEdge == 1:
            paramName = "configId"
        self.params = {paramName:dataStreamId}
        origin = 'edge'
        if config is None:
            self.authenticated = False
        else:
            self.authenticated = True
        if type(config) == dict: ## Supporting either default setup or passing a ConnectObject
            config = config
        elif type(config) == ConnectObject:
            header = config.getConfigHeader()
            config = config.getConfigObject()
        else:
            header = {
                "Content-Type": "application/json"
            }
            origin ="edge-no-auth"

        self.connector = connector.AdobeRequest(
            config=config,
            header=header,
            loggingEnabled=self.loggingEnabled,
            logger=self.logger,
            origin=origin
        )
        if self.authenticated:
            self.token = self.connector.token


    def __str__(self):
        data = {
            "server":self.server,
            "endpoint":self.endpoint,
            "dataStreamId" : self.params['dataStreamId'],
            "authenticated" : self.authenticated,
            "version": self.versionEdge
        }
        if self.authenticated:
            data['token'] = self.token
        return json.dumps(data,indent=2)

    def __str__(self):
        data = {
            "server":self.server,
            "endpoint":self.endpoint,
            "dataStreamId" : self.params['dataStreamId'],
            "authenticated" : self.authenticated,
            "version": self.versionEdge
        }
        if self.authenticated:
            data['token'] = self.token
        return json.dumps(data,indent=2)    

    def interact(self,payload:dict=None,xdm:dict=None,data:dict=None,scopes:list=None,surfaces:list=None,params:dict=None)->dict:
        """
        Send an interact calls. It usually return a response that can be used on the application.
        Arguments:
            payload : OPTIONAL : In case you want to pass the whole payload yourself
            xdm : OPTIONAL : In case you want to pass only XDM data
            data : OPTIONAL : In case you want to pass the data object (can be passed with xdm)
            scopes : OPTIONAL : In case you want to pass Target scopes/mbox in the request. List of strings.
            surfaces : OPTIONAL : In case you want to pass AJO surfaces in the request. List of strings.
            params: OPTIONAL : If you want to pass additional query parameter. It takes a dictionary.
        """
        if payload is None and xdm is None and data is None:
            raise ValueError("an argument should be used to send data")
        privateParams = {**self.params}
        if params is not None:
            for key, value in params.items():
                privateParams[key] = value
        if payload is not None:
            dataPayload = payload
        else:
            dataPayload = {'event':{}}
            if self.versionEdge == 1:
               dataPayload = {'events':[]} 
        if xdm is not None:
            if "event" in dataPayload.keys():
                dataPayload['event']['xdm'] = xdm
            elif "events" in dataPayload.keys():
                dataPayload['events'].append({"xdm":xdm})
            if data is not None:
                if "event" in dataPayload.keys():
                    dataPayload['event']['data'] = data
                elif "events" in dataPayload.keys():
                    dataPayload['events'][0]['data'] = data
            if scopes is not None:
                if type(scopes) == str:
                    scopes = [scopes]
                if "event" in dataPayload.keys():
                    dataPayload['query'] = {
                        "personalization" : {
                            "decisionScopes":scopes,
                            "schemas":[
                                "https://ns.adobe.com/personalization/html-content-item",
                                "https://ns.adobe.com/personalization/json-content-item",
                                "https://ns.adobe.com/personalization/redirect-item",
                                "https://ns.adobe.com/personalization/dom-action"
                            ]
                        },
                    }
                elif "events" in dataPayload.keys():
                    dataPayload['events'][0]['query'] = {
                        "personalization" : {
                            "decisionScopes":scopes,
                            "schemas":[
                                "https://ns.adobe.com/personalization/html-content-item",
                                "https://ns.adobe.com/personalization/json-content-item",
                                "https://ns.adobe.com/personalization/redirect-item",
                                "https://ns.adobe.com/personalization/dom-action"
                            ]
                        },
                    }
            if surfaces is not None:
                if type(surfaces) == str:
                    surfaces = [surfaces]
                if 'query' in dataPayload.get('event').keys():
                    dataPayload['query']['personalization']['surfaces'] = surfaces
                elif 'query' in dataPayload.get('events',[{}])[0].keys():
                    dataPayload['events'][0]['query']['personalization']['surfaces'] = surfaces
                else:
                    if "event" in dataPayload.keys():
                        dataPayload['query'] = {
                            "personalization" : {
                                "surfaces":surfaces
                            }
                        }
                    elif "events" in dataPayload.keys():
                        dataPayload['events'][0]['query'] = {
                            "personalization" : {
                                "surfaces":surfaces
                            }
                        }
        elif data is not None:
            if "event" in dataPayload.keys():
                dataPayload['event']['data'] = data
            elif "events" in dataPayload.keys():
                dataPayload['events'][0]['data'] = data
        res = self.connector.postData(self.endpoint,params=privateParams,data=dataPayload)
        return res
    
    def collect(self,payloads:list=None,xdms:list=None,data:list=None)->dict:
        """
        In case you want to send multiple requests in one go. These are not returning response that can be used by the application.
        They are just sending data to AEP.
        You can send requests from different users. 
        Arguments:
            payloads : OPTIONAL : A list of payload to be send via Edge.
            xdms : OPTIONAL : A list of xdm to be sent via Edge
            data : OPTIONAL : A list of data to attach to the xdms calls (note that the list of xdms and data should be in the same order)
        """
        if payloads is None and xdms is None and data is None:
            raise ValueError("an argument should be used to send data")
        if payloads is not None:
            res = self.connector.postData(self.endpoint,params=self.params,data=payloads)
            return res
        elif xdms is not None:
            dataPayloads = [
                {
                    "event":{
                        "xdm" : deepcopy(xdm)
                }
                }
                for xdm in xdms
            ]
            if data is not None:
                for index,d in enumerate(data):
                    if d is not None:
                        dataPayloads[index]['event']['data'] = data
            res = self.connector.postData(self.endpoint,params=self.params,data=dataPayloads)
            return res
        elif data is not None:
            dataPayloads = [
                {
                    "event":{
                        "xdm" : deepcopy(xdm)
                }
                }
                for d in data
            ]
            res = self.connector.postData(self.endpoint,params=self.params,data=dataPayloads)
            return res

class IdentityMapHelper:
    """
    This class will help you create an Identity Map object
    """

    def __init__(self,namespace:str=None,identity:str=None,primary:bool=True,state:str='ambiguous')->None:
        """
        Instantiate the Identity Map Helper
        Arguments:
            namespace : OPTIONAL : User namespace
            identity : OPTIONAL : User Value for that namespace
            primary : OPTIONAL : Default True.
            state : OPTIONAL : Default ambiguous. possible options: 'authenticated'
        """
        self.data = {}
        if namespace is not None and identity is not None:
            self.data[namespace] = [
                {
                    "id":identity,
                    "primary":primary,
                    "authenticatedState":state
                }
            ]
    
    def __str__(self):
        return json.dumps(self.data,indent=2)
    
    def __repr__(self):
        return json.dumps(self.data,indent=2)
        
    def addIdentity(self,namespace:str=None,identity:str=None,primary:bool=False,state:str="ambigous")->None:
        """
        Add an identity to the identityMap.
        Arguments:
            namespace : REQUIRED : User namespace
            identity : REQUIRED : User Value for that namespace
            primary : OPTIONAL : Default False.
            state : OPTIONAL : Default "ambigous", possible state: "authenticated"
        """
        if namespace is None:
            raise ValueError("No namespace specified")
        if identity is None:
            raise ValueError("No identity specified")
        if namespace not in self.data.keys():
            self.data[namespace]=[
                {
                    "id":identity,
                    "primary":primary,
                    "authenticatedState":state
                }
            ]
        else:
            self.data[namespace].append({
                    "id":identity,
                    "primary":primary,
                    "authenticatedState":"ambiguous"
                })
    
    def removePrimaryFlag(self,namespace:str=None,identity:str=None)->None:
        """
        remove the primary flag from the identity map.
        Arguments:
            namespace : OPTIONAL : The namespace to remove the identity primary flag
            identity : OPTIONAL : The identity to remove the identity flag.
        If nothing is provided, it will loop through all identities and remove the flag
        """
        if namespace is not None:
            identities = self.data[namespace]
            if identity is not None:
                for myId in identities:
                    if myId['id'] == identity:
                        myId['primary'] = False
            else:
                for myId in identities:
                    if myId['primary']:
                            myId['primary'] = False
        elif identity is not None:
            for namespace in self.data.keys():
                for myId in self.data[namespace]:
                    if myId['id'] == identity:
                        myId['primary'] = False
        else:
            for myId in self.data[namespace]:
                if myId['primary']:
                    myId['primary'] = False
    
    def setPrimaryFlag(self,namespace:str=None,identity:str=None)->None:
        """
        Set an identity as primary identity.
        Arguments:
            namespace : OPTIONAL : If you want to specify the namespace to set the primary identity.
                        If no identity are provided and multiple identities are available, the first one is picked up to be primary.
            identity : OPTIONAL : the identity to be used as primary.
        """
        if namespace is None and identity is None:
            raise ValueError("You must specify a namespace or/and an identity")
        if namespace is not None:
            identities = self.data[namespace]
            if identity is not None:
                for myId in identities:
                    if myId['id'] == identity:
                        myId['primary'] = True
            else:
                identities[0]['primary'] = True
        elif identity is not None:
            for namespace in self.data.keys():
                for myId in self.data[namespace]:
                    if myId['id'] == identity:
                        myId['primary'] = True

    def to_dict(self)->dict:
        """
        Return the identity map constructed in dictionary format.
        """
        return self.data


    def to_json(self,indent:int=2)->json.dumps:
        """
        Return the identity map constructed in JSON format
        """
        return json.dumps(self.data,indent=indent)
