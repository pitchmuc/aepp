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
import logging
from typing import Union
from .configs import ConnectObject
import json
from copy import deepcopy
import datetime


class Sandboxes:
    """
    A collection of methods to realize actions on the sandboxes.
    It comes from the sandbox API:
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/sandbox-api.yaml
    """

    ## logging capability
    loggingEnabled = False
    logger = None
    ARTIFACS_TYPE = ["REGISTRY_SCHEMA","MAPPING_SET","CATALOG_DATASET","JOURNEY","PROFILE_SEGMENT"]

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ):
        """
        Instantiate the sandbox class.
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
            loggingObject=self.logger,
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
        self.org_id = self.connector.config["org_id"]
        self.endpoint = aepp.config.endpoints["global"] + aepp.config.endpoints["sandboxes"]
        self.endpointPackage = aepp.config.endpoints["global"] + aepp.config.endpoints["sandboxTooling"]

    def __str__(self):
        return json.dumps({'class':'Sandboxes','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)
    
    def __repr__(self):
        return json.dumps({'class':'Sandboxes','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)

    def getSandboxes(self) -> list:
        """
        Return the list of all the sandboxes
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSandboxes")
        path = self.endpoint + "/sandboxes"
        res = self.connector.getData(path)
        data = res["sandboxes"]
        return data

    def getSandboxTypes(self) -> list:
        """
        Return the list of all the sandboxes types.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSandboxTyoes")
        path = self.endpoint + "/sandboxTypes"
        res = self.connector.getData(path)
        data = res["sandboxTypes"]
        return data

    def createSandbox(
        self, name: str = None, title: str = None, type_sandbox: str = "development"
    ) -> dict:
        """
        Create a new sandbox in your AEP instance.
        Arguments:
            name : REQUIRED : name of your sandbox
            title : REQUIRED : display name of your sandbox
            type_sandbox : OPTIONAL : type of your sandbox. default : development.
        """
        if name is None or title is None:
            raise Exception("name and title cannot be empty")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createSandbox")
        path = self.endpoint + "/sandboxes"
        data = {"name": name, "title": title, "type": type_sandbox}
        res = self.connector.postData(path, data=data)
        return res

    def getSandbox(self, name: str) -> dict:
        """
        retrieve a Sandbox information by name
        Argument:
            name : REQUIRED : name of Sandbox
        """
        if name is None:
            raise Exception("Expected a name as parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSandbox")
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.getData(path)
        return res

    def getSandboxId(self, name: str) -> str:
        """
        Retrieve the ID of a sandbox by name.
        Argument:
            name : REQUIRED : name of Sandbox
        """
        return self.getSandbox(name)["id"]

    def deleteSandbox(self, name: str) -> dict:
        """
        Delete a sandbox by its name.
        Arguments:
            name : REQUIRED : sandbox to be deleted.
        """
        if name is None:
            raise Exception("Expected a name as parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteSandbox")
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.deleteData(path)
        return res

    def resetSandbox(self, name: str) -> dict:
        """
        Reset a sandbox by its name. Sandbox will be empty.
        Arguments:
            name : REQUIRED : sandbox name to be deleted.
        """
        if name is None:
            raise Exception("Expected a sandbox name as parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting resetSandbox")
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.putData(path, data={'action':'reset'})
        return res

    def updateSandbox(self, name: str, action: dict = None) -> dict:
        """
        Update the Sandbox with the action provided.
        Arguments:
            name : REQUIRED : sandbox name to be updated.
            action : REQUIRED : dictionary defining the action to realize on that sandbox.
        """
        if name is None:
            raise Exception("Expected a sandbox name as parameter")
        if action is None or type(action) != dict:
            raise Exception("Expected a dictionary to pass the action")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateSandboxes")
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.patchData(path, data=action)
        return res

    def getPackages(self,prop:Union[str,list]=None,limit:int=20,**kwargs)->list:
        """
        Returns the list of packages available.
        Arguments:
            prop : OPTIONAL : A list of options to filter the different packages.
                Ex: ["status==DRAFT,PUBLISHED","createdDate>=2023-05-11T18:29:59.999Z","createdDate<=2023-05-16T18:29:59.999Z"]
            limit : OPTIONAL : The number of package to return per request
        Possible kwargs:
            see https://experienceleague.adobe.com/docs/experience-platform/sandbox/sandbox-tooling-api/appendix.html?lang=en
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPackages")
        params = {"start":0, "orderby":"-createdDate","limit":limit}
        if prop is not None:
            if type(prop) == list:
                params['property'] = "&property=".join(prop)
            elif type(prop) == str:
                params['property'] = prop
        path = "/packages/"
        res = self.connector.getData(self.endpointPackage+path,params=params)
        data = res.get('data',[])
        hasNext = res.get('hasNext',False)
        while hasNext:
            params["start"] += limit
            res = self.connector.getData(self.endpointPackage+path,params=params)
            data += res.get('data',[])
            hasNext = res.get('hasNext',False)
        return data
    
    def getPackage(self,packageId:str=None)->dict:
        """
        Retrieve a single package.
        Arguments:
            packageId : REQUIRED : The package Id to be retrieved
        """
        if packageId is None:
            raise ValueError("Requires a package ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPackage")
        path = f"/packages/{packageId}"
        res = self.connector.getData(self.endpointPackage+path)
        return res
    
    def getPublicPackages(self,requestType:str="public",prop:Union[str,list]=None,limit:int=20)->list:
        """
        Returns the public packages available.
        Arguments:
            requestType : OPTIONAL : Eithe "private" or "public"
            prop : OPTIONAL : A list of options to filter the different packages.
                Ex: ["status==DRAFT,PUBLISHED","createdDate>=2023-05-11T18:29:59.999Z","createdDate<=2023-05-16T18:29:59.999Z"]
            limit : OPTIONAL : The number of package to return per request
        Possible kwargs:
            see https://experienceleague.adobe.com/docs/experience-platform/sandbox/sandbox-tooling-api/appendix.html?lang=en
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPublicPackages")
        params = {"start":0, "orderby":"-createdDate","limit":limit,"requestType":requestType}
        if prop is not None:
            params['property'] = prop
        path = "/transfer/list"
        res = self.connector.getData(self.endpointPackage+path,params=params)
        data = res.get('data',[])
        hasNext = res.get('hasNext',False)
        while hasNext:
            params["start"] += limit
            res = self.connector.getData(self.endpointPackage+path,params=params)
            data += res.get('data',[])
            hasNext = res.get('hasNext',False)
        return data
    
    def deletePackage(self,packageId:str=None)->dict:
        """
        Delete a specific package.
        Argument:
            packageId : REQUIRED : The package ID to be deleted
        """
        if packageId is None:
            raise ValueError("Requires a package ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deletePackage")
        privateHeader = deepcopy(self.header)
        del privateHeader["x-sandbox-name"]
        path = f"/packages/{packageId}/"
        res = self.connector.deleteData(self.endpointPackage+path,headers=privateHeader)
        return res
    
    def createPackage(self,
                      name:str=None,
                      description:str=None,
                      fullPackage:bool=False,
                      artifacts:list=None,
                      expiry:int=90,
                      **kwargs)->dict:
        """
        Create a package.
        Arguments:
            name : REQUIRED : Name of the package.
            description : OPTIONAL : Description of the package
            fullPackage : OPTIONAL : If you want to copy the whole sandbox. (default False)
            artifacts : OPTIONAL : If you set fullPackage to False, then you need to provide a list of dictionary of items.
                example : [
                    {"id":"27115daa-c92b-4f17-a077-d65ffeb0c525","title": "my segment title", "type" : "PROFILE_SEGMENT"},
                    {"id":"d8d8ed6d-696a-40bd-b4fe-ca053ec94e29","title": "my journey title", "type" : "JOURNEY"}
                ]
                For more types, refers to ARTIFACS_TYPE 
            expiry : OPTIONAL : The expiry of that package in days (default 90 days)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createPackage")
        delta90days = datetime.timedelta(days=expiry)
        now = datetime.datetime.now()
        now90days = now + delta90days
        now90daysZ_str= f"{now90days.isoformat(timespec='seconds')}Z"
        if description is not None:
            desc = description
        else:
            desc = "power by aepp"
        if fullPackage:
            data = {
                "name": name,
                "description": desc,
                "packageType": "FULL",
                "sourceSandbox": {
                    "name": self.sandbox,
                    "imsOrgId": self.org_id
                },
                "expiry": now90daysZ_str,
                "artifacts": []
            }
        else:
            data = {
                "name": name,
                "description": desc,
                "packageType": "PARTIAL",
                "sourceSandbox": {
                    "name": self.sandbox,
                    "imsOrgId": self.org_id
                },
                "expiry": now90daysZ_str,
                "artifacts": deepcopy(artifacts)
            }
        path = "/packages"
        res = self.connector.postData(self.endpointPackage+path,data=data)
        return res
    
    def updatePackage(self,packageId:str=None,
                      operation:str=None,
                      name:str=None,
                      description:str=None,
                      artifacts:list=None,)->dict:
        """
        Update a package ID.
        Arguments:
            packageId : REQUIRED : The package ID to be updated
            operation : OPTIONAL : Type of update, either "UPDATE", "DELETE","ADD"
            name : OPTIONAL : In case you selected UPDATE and want to change the name of the package.
            description : OPTIONAL : In case you selected UPDATE and want to change the description of the package.
            artifacts : OPTIONAL : In case you used DELETE or ADD, provide a list of dictionary of items.
                example : [
                    {"id":"27115daa-c92b-4f17-a077-d65ffeb0c525","title": "my segment title", "type" : "PROFILE_SEGMENT"},
                    {"id":"d8d8ed6d-696a-40bd-b4fe-ca053ec94e29","title": "my journey title", "type" : "JOURNEY"}
                ]
            
        """
        if packageId is None:
            raise ValueError("Requires a package ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createPackage")
        action = operation
        if operation == "UPDATE":
            decription = description if description is not None else "power by aepp"
            data = {
                "id" : packageId,
                "action" : action,
                "name" : name,
                "description" : decription,
                "sourceSandbox" : {
                    "name": self.sandbox,
                    "imsOrgId": self.org_id
                }
            }
        elif operation == "DELETE" or operation == "ADD":
            data = {
                "id" : packageId,
                "action" : action,
                "artifacts": deepcopy(artifacts)
            }
        path = "/packages"
        res = self.connector.putData(self.endpointPackage+path,data=data)
        return res
    
    def publishPackage(self,packageId:str=None):
        """
        Publish a package. Requires step before importing the package.
        Argument:
            package ID : REQUIRED : The package to be published
        """
        if packageId is None:
            raise ValueError("Require a package ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting publishPackage")
        path = f"/packages/{packageId}/export"
        privateHeader = deepcopy(self.header)
        del privateHeader["x-sandbox-name"]
        res = self.connector.getData(self.endpointPackage+path,headers=privateHeader)
        return res
    
    def importPackageCheck(self,packageId:str=None,targetSandbox:str=None)->dict:
        """
        Try to import a specific package in a sandbox, returns the conflicts.
        Argument:
            packageId : REQUIRED : The package ID to be imported
            targetSandbox : REQUIRED : The Target sandbox to be used.
        """
        if packageId is None:
            raise ValueError("Require a package ID")
        if targetSandbox is None:
            raise ValueError("Require a target sandbox name")
        if self.loggingEnabled:
            self.logger.debug(f"Starting importPackageCheck")
        params = {"targetSandbox":targetSandbox}
        path = f"/packages/{packageId}/import"
        res = self.connector.getData(self.endpointPackage+path,params=params)
        return res
    
    def importPackage(self,packageId:str=None,targetSandbox:str=None,alternatives:dict=None)->dict:
        """
        This will import the different artifacts into the targetSandbox.
        You can provide a map of artifacts that are already in the targeted sandbox and should be avoided to be imported.
        Arguments:
            packageId : REQUIRED : The package ID to be imported
            targetSandbox : REQUIRED : The Target sandbox to be used
            alternatives : OPTIONAL : A dictionary, a map, of artifacts existing in your package that already exists in the targeted sandboxes.
                example of alternative dictionary: 
                    {"artifactIdInPackage": {
                        "id": "targetSandboxArtifactId"
                        "type" : "REGISTRY_SCHEMA" (refer to ARTIFACS_TYPE for more types)
                        }
                    }
        """
        if packageId is None:
            raise ValueError("Requires a package ID to be specified")
        if targetSandbox is None:
            raise ValueError("Requires a target sandbox to be specified")
        if self.loggingEnabled:
            self.logger.debug(f"Starting importPackage")
        path = f"/packages/{packageId}/import"
        params = {"targetSandbox":targetSandbox}
        package = self.getPackage(packageId)
        data = {
            "id" : packageId,
            "name" : package["name"],
            "description" : package["description"],
            "destinationSandbox":{
                "name" : targetSandbox,
                "imsOrgId":self.org_id
            }
        }
        if alternatives is not None:
            data["alternatives"] = alternatives
        res = self.connector.postData(self.endpointPackage+path,params=params)
        return res
    
    def getPackageDependencies(self,packageId:str=None)->list:
        """
        List all of the dependencies for the package specified
        Arguments:
            packageId : REQUIRED : the package ID to evaluate
        """
        if packageId is None:
            raise ValueError("Requires a package ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPackageDependencies")
        path = f"/packages/{packageId}/children"
        res = self.connector.postData(self.endpointPackage+path)
        return res

    def getImportExportJobs(self,importsOnly:bool=False,exportsOnly:bool=False)->dict:
        """
        Returns all of the jobs done or prepared
        Arguments:
            importsOnly : OPTIONAL : Boolean if you want to return the import jobs only (default False)
            exportsOnly : OPTIONAL : Boolean if you want to return the export jobs only (default False)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getImportExportJobs")
        params = {}
        if importsOnly:
            params['property'] = "requestType==IMPORT"
        elif exportsOnly:
            params['property'] = "requestType==EXPORT"
        path = f"/packages/jobs"
        res = self.connector.getData(self.endpointPackage+path,params=params)
        return res
    
    def checkPermissions(self,packageId:str=None,targetSandbox:str=None)->dict:
        """
        Check the type of access the client ID has.
        Arguments:
            packageId : REQUIRED : The package you want to copy over.
            targetSandbox : REQUIRED : The Target sandbox to be used
        """
        if packageId is None:
            raise ValueError("A Package ID is required")
        if targetSandbox is None:
            raise ValueError("TargetSandbox parameter is required")
        if self.loggingEnabled:
            self.logger.debug(f"Starting checkPermissions")
        params = {"targetSandbox":targetSandbox}
        path = f"/packages/preflight/{packageId}"
        res = self.connector.getData(self.endpointPackage+path,params=params)
    
    def createShareRequest(self,imsTargets:list=None,imsSourceId:str=None,imsSourceName:str=None)->dict:
        """
        Send a request to a target partner organization for sharing approval by making a POST request to the /handshake/bulkCreate endpoint. 
        This is required before you can share private packages.
        Arguments:
            imsTargets : REQUIRED : List of IMS ORG ID that should be targeted
            imsSourceId : REQUIRED : The IMS Org ID that create the package
            imsSourceName : REQUIRED : The IMS Org Name that create the package
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createShareRequest with Source: {imsSourceName}")
        if imsTargets is None:
            raise ValueError("Require a list of target IMS org ID")
        if imsSourceId is None or imsSourceName is None:
            raise Exception("Require IMS ORG ID and Name from the source")
        path = "/handshake/bulkCreate"
        data = {
            "targetIMSOrgIds":imsTargets,
            "sourceIMSDetails":{
                "id":imsSourceId,
                "name":imsSourceName
            }
        }
        res = self.connector.postData(self.endpointPackage+path,data=data)
        return res
    
    def approvingShareRequest(self,linkind_id:str=None,ims_name:str=None,ims_id:str=None,region:str="nld2")->dict:
        """
        Approve share requests from target partner organizations by making a POST request to the /handshake/action endpoint. 
        After approval, source partner organizations can share private packages.
        Use the information received by createShareRequest
        Arguments:
            linkind_id : REQUIRED : The Linkind_id received when created share request.
            ims_name : REQUIRED : The Org name that receiving the data
            ims_id : OPTIONAL : The Org ID that is used to receiving the data
            region : OPTIONAL : The region used for the receiving organization (default NLD2, possible values: VA7,AUS5,CAN2 or IND2 )
        """
        if linkind_id is None:
            raise ValueError("Linkind_id is not provided")
        if ims_id is None:
            ims_id = self.connector.config['org_id']
        path =  f"/handshake/action"
        {
            "linkingID":linkind_id,
            "status":"APPROVED",
            "reason":"Done",
            "targetIMSOrgDetails":{
                "id":ims_id,
                "name":ims_name,
                "region":region
            }
        }
        res = self.connector.postData(self.endpointPackage+path)
        return res
    
    def getShareRequests(self,requestType:str="INCOMING")->list:
        """
        returns a list of all outgoing and incoming share requests.
        Arguments:
            requestType : REQUIRED : Either "INCOMING" or "OUTGOING"
        """
        path = f"/handshake/list"
        params = {"property":"status==APPROVED","requestType":requestType}
        res = self.connector.getData(self.endpointPackage+path,params=params)
        return res
    
    def transferPackage(self,packageId:str=None,imsTargets:list=None)->list:
        """
        Transfer the package to the target IMS ID.
        Arguments:
            packageId : REQUIRED : The package ID to transfer
            imsTargetId : REQUIRED : The list of IMS ORG ID to the transfer the package
        """
        if packageId is None:
            raise ValueError("A Package ID is required")
        path = f"/transfer/"
        list_org_ids = [{"imsOrgId":t_id} for t_id in imsTargets]
        data = {
        "packageId": packageId,
        "targets": list_org_ids
        }
        res = self.connector.postData(self.endpointPackage+path,data=data)
        return res
    
    def getTransfer(self,transferId:str=None)->dict:
        """
        Fetch the details of a share request by transferId.
        Argument:
            transferId : REQUIRED : The transfer ID to be fetched.
        """
        if transferId is None:
            raise ValueError("transferId is required")
        path = f"/transfer/{transferId}"
        res = self.connector.getData(self.endpointPackage+path)
        return res
    
    def getTransfers(self,status:str="COMPLETED",requestType:str=None)->list:
        """
        Return the list of the transfert based on the filter.
        Arguments:
            status : REQUIRED : The status used to filter : COMPLETED, PENDING, IN_PROGRESS, FAILED.
            requestType : OPTIONAL : The type of request, accepts either PUBLIC or PRIVATE
        """
        path = "/transfer/list"
        params = {"start":0,"limit":50}
        if requestType is not None:
            params['requestType'] = requestType
        res = self.connector.getData(self.endpoint+path,params=params)
        data = res.get('data',[])
        next_page = res.get('hasNextPage',False)
        while next_page:
            params["start"] += 51
            res = self.connector.getData(self.endpoint+path,params=params)
            data += res.get('data',[])
            next_page = res.get('hasNextPage',False)
        return data
        
    def importPublicPackage(self,ims_sourceId:str=None,packageId:str=None)->dict:
        """
        Import a package from the public repository.
        Arguments:
            ims_sourceId : REQUIRED : The IMS Org ID used to create the package
            packageId : REQUIRED : The package ID to import
        """
        if ims_sourceId is None:
            raise Exception('Require the ims ORG ID used as source')
        if packageId is None:
            raise Exception('Require the package ID')
        path = f"/transfer/pullRequest"
        data = {
            "imsOrgId": ims_sourceId,
            "packageId": packageId,
        }
        res = self.connector.postData(self.endpointPackage+path,data=data)
        return res
    
    def publishPackage(self,packageId:str=None,packageVisibility:str="PUBLIC")->dict:
        """
        Change a package from private to public.
        By default, a package is created with private availability.
        Argument:
            packageId : REQUIRED : The package ID to make public
            packageVisibility : OPTIONAL : By default "PUBLIC", you can also use "PRIVATE" to reverse.
        """
        if packageId is None:
            raise ValueError("Expect a package ID")
        path = "/packages"
        data ={
            "id":packageId,
            "action":"UPDATE",
            "packageVisibility":packageVisibility
        }
        res = self.connector.putData(self.endpointPackage+path,data=data)
        return res
    


