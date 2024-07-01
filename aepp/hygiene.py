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
from typing import Union
import logging
from .configs import ConnectObject



class Hygiene:
    """
    Hygiene class from the AEP API. This class helps you to create methods to delete or clean your data in AEP.
    More details here : https://experienceleague.adobe.com/en/docs/experience-platform/data-lifecycle/api/dataset-expiration
    It possess a data attribute that is containing information about your datasets. 
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
                config : Union[dict,ConnectObject]=aepp.config.config_object,
                header : dict=aepp.config.header,
                loggingObject:dict=None,
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
        self.endpoint = aepp.config.endpoints['global']+aepp.config.endpoints["hygiene"]

    def getQuotas(self,quotaType:str=None)->list:
        """
        Returns a list of quota types and their status.
        It allows you to monitor your Advanced data lifecycle management usage against your organization’s quota limits for each job type.
        Arguments:
            quotaType : OPTIONAL : If you wish to restrict to specific quota type.
                Possible values: 
                    expirationDatasetQuota (Dataset expirations)
                    deleteIdentityWorkOrderDatasetQuota (Record delete)
                    fieldUpdateWorkOrderDatasetQuota (Record updates)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getQuotas")
        path = "/quota"
        params = {}
        if quotaType is not None and quotaType in ["expirationDatasetQuota","deleteIdentityWorkOrderDatasetQuota","fieldUpdateWorkOrderDatasetQuota"]:
            params["quotaType"] = quotaType
        res = self.connector.getData(self.endpoint+path,params=params)
        return res.get('quotas',[])
    
    def getDatasetsExpirations(self,**kwargs)->list:
        """
        allows you to schedule expiration dates for datasets in Adobe Experience Platform.
        A dataset expiration is only a timed-delayed delete operation. The dataset is not protected in the interim, so it may be be deleted by other means before its expiry is reached.
        It can take up to 24h after the date specified before the dataset is deleted from AEP.
        It can take up to 7 days for all services (UIS, UPS, CJA, etc...) to reflect the deletion impact.
        Arguments:
            Possible keywords:
                author : Matches expirations whose created_by (ex: author=LIKE %john%, author=John Q. Public)
                datasetId : Matches expirations that apply to specific dataset.	(ex : datasetId=62b3925ff20f8e1b990a7434)
                datasetName : Matches expirations whose dataset name contains the provided search string. The match is case-insensitive. (ex : datasetName=Acme)
                createdDate : Matches expirations that were created in the 24-hour window starting at the stated time. (ex : createdDate=2021-12-07)
                createdFromDate : Matches expirations that were created at, or after, the indicated time. (ex : createdFromDate=2021-12-07T00:00:00Z)
                createdToDate : Matches expirations that were created at, or before, the indicated time. (ex : createdToDate=2021-12-07T23:59:59.00Z)
                completedToDate : Matches expirations that were completed during the specified interval. (ex: completedToDate=2021-11-11-06:00)
                status : A comma-separated list of statuses. When included, the response matches dataset expirations whose current status is among those listed. (ex : status=pending,cancelled)
                updatedDate : matches against a dataset expiration’s update time instead of creation time. (updatedDate=2022-01-01)
                full list : https://experienceleague.adobe.com/en/docs/experience-platform/data-lifecycle/api/dataset-expiration#appendix
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDatasetsExpirations")
        path = "/ttl"
        params = {**kwargs}
        params['page'] = kwargs.get('page',0)
        params['limit'] = kwargs.get('limit',50)
        res = self.connector.getData(self.endpoint+path,params=params)
        data = res.get('results',[])
        curr_page = 1
        lastPage = res.get('total_pages') == curr_page
        while lastPage != True:
            curr_page +=1
            params['page'] += 1
            res = self.connector.getData(self.endpoint+path,params=params)
            data = res.get('results',[])
            lastPage = res.get('total_pages') == curr_page
        return data
    
    def getDatasetExpiration(self,datasetId:str=None,ttlId:str=None)->dict:
        """
        To retrieve the specify dataset deletion.
        One of the 2 parameters is required.
        Arguments:
            datasetId : OPTIONAL : the datasetId to look for
            ttlId : OPTIONAL : The ttlId returned when setting the ttl.
        """
        if datasetId is None and ttlId is None:
            raise ValueError('datasetId or ttlId require')
        if datasetId is not None:
            path = f"/ttl/{datasetId}?include=history"
        elif ttlId is not None:
            path = f"/ttl/{ttlId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDatasetExpiration : {path}")
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def createDatasetExpiration(self,datasetId:str=None,ttlId:str=None,expiry:str=None,name:str=None,description:str="")->dict:
        """
        Create or update an expiration date for a dataset through a PUT request. 
        The PUT request uses either the datasetId or the ttlId.
        One of the 2 first parameters is required.
        Arguments:
            datasetId : OPTIONAL : the datasetId to set expiration for
            ttlId : OPTIONAL : The ID of the dataset expiration.
            expiry : REQUIRED : the expiration in date such as "2024-12-31T23:59:59Z"
            name : REQUIRED : name of the ttl setup
            description : OPTIONAL : description of the ttl setup
        """
        if datasetId is None and ttlId is None:
            raise ValueError('datasetId or ttlId require')
        if datasetId is not None:
            path = f"/ttl/{datasetId}"
        elif ttlId is not None:
            path = f"/ttl/{ttlId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting createDatasetExpiration : {path}")
        data = {
            "expiry": expiry,
            "displayName": name,
            "description": description,
        }
        res = self.connector.putData(self.endpoint+path,data=data)
        return res
    
    def deleteDatasetExpiration(self,ttlId:str=None)->dict:
        """
        You can cancel a dataset expiration by making a DELETE request.
        Arguments:
            ttlId : REQUIRED : The ttlId of the dataset expiration that you want to cancel.
        """
        if ttlId is None:
            raise ValueError("Require a ttlId")
        path = f"/ttl/{ttlId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteDatasetExpiration, ttlId: {ttlId}")
        res = self.connector.deleteData(self.endpoint+path)
        return res

    def createRecordDeleteRequest(self,datasetId:str="ALL",name:str=None,identities:list=None,description:str="")->dict:
        """
        Delete records from a specific identity.
        NOTE : You should use the maximum number of identities in one request. Max is 100 K identities in the list.
        Argument:
            datasetId : REQUIRED : default "ALL" for all dataset, otherwise a specific datasetId.
            name : REQUIRED : Name of the deletion request job
            identities : REQUIRED : list of namespace code and id to be deleted.
                example : 
                [{"namespace": {
                        "code": "email"
                        },
                    "id": "poul.anderson@example.com"
                }],
            description : OPTIONAL : Description of the job
        """
        if datasetId is None:
            raise ValueError("datasetId is required")
        if identities is None:
            raise ValueError("list of identities is required")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createRecordDeleteRequest, datasetId: {datasetId}")
        path = "/workorder"
        data = {
            "action": "delete_identity",
            "datasetId": datasetId,
            "displayName": name,
            "description": description,
            "identities":identities
        }
        res = self.connector.postData(self.endpoint+path,data=data)
        return res
    
    def getWorkOrderStatus(self,workorderId:str=None)->dict:
        """
        Return the status of a work order.
        Arguments:
            workorderId : REQUIRED : The workorderId return by the job creation 
        """
        if workorderId is None:
            raise ValueError("a workorderId is required")
        path = f"/workorder/{workorderId}/"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def updateWorkOrder(self,workorderId:str=None,name:str=None,description:str="")->dict:
        """
        Update the work order 
        Arguments:
            workorderId : REQUIRED : The workorderId return by the job creation 
            name : REQUIRED : the new name of the work order
            description : OPTIONAL : Description of the work order
        """
        if workorderId is None:
            raise ValueError("A workorderId is required")
        path = f"/workorder/{workorderId}/"
        data = {
            "displayName" : name,
            "description" : description
        }
        res = self.connector.putData(self.endpoint+path,data=data)
        return res

