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
import logging, json
from .configs import ConnectObject
from typing import Union

class AccessControl:
    """
    Access Control API endpoints.
    Complete documentation is available:
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/access-control.yaml
    """

    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict =aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ) -> None:
        """
        Instantiate the access controle API wrapper.
        Arguments:
            config : OPTIONAL : it could be the instance of the ConnectObject class (preferred) or a dictionary containing the config information. 
                    Default will take the latest configuration loaded.
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
            loggingObject : OPTIONAL : logging object to log messages.
        kwargs :
            header options
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
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.endpoint = (
            aepp.config.endpoints["global"] + aepp.config.endpoints["access"]
        )

    def __str__(self):
        return json.dumps({'class':'AccessControl','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)
    
    def __repr__(self):
        return json.dumps({'class':'AccessControl','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)

    def getPermissions(self) -> dict:
        """
        List all available permission names and resource types.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPermissions")
        path = "/acl/reference"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def getEffectivePolicies(self, listElements: list = None):
        """
        List all effective policies for a user on given resources within a sandbox.
        Arguments:
            listElements : REQUIRED : List of resource urls. Example url : /resource-types/{resourceName} or /permissions/{highLevelPermissionName}
                example: "/permissions/manage-dataset" "/resource-types/schema" "/permissions/manage-schemas"
        """
        if type(listElements) != list:
            raise TypeError("listElements should be a list of elements")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getEffectivePolicies")
        path = "/acl/effective-policies"
        res = self.connector.postData(
            self.endpoint + path, data=listElements, headers=self.header
        )
        return res
    
    def getRoles(self,)->list:
        """
        Return all existing roles in the Company.      
        """
        path = "/administration/roles"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getRoles")
        res = self.connector.getData(self.endpoint+path)
        data = res.get('items',[])
        nextPage = res.get('_links',{}).get('next',{}).get('href','')
        while nextPage != "":
            path_addition = nextPage.split('roles')[1]
            newPath = path + path_addition
            res = self.connector.getData(self.endpoint+newPath)
            data += res.get('items',[])
            nextPage = res.get('_links',{}).get('next',{}).get('href','')
            if len(res.get('items',[])) == 0:
                nextPage = ""
        return data
    
    def getRole(self,roleId:str=None)->dict:
        """
        Retrieve a specific role based on the ID.
        Arguments:
            roleId : REQUIRED : Role ID to be retrieved
        """
        if roleId is None:
            raise ValueError("A role ID is required")
        path = f"/administration/roles/{roleId}/"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getRole with id : {roleId}")
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def deleteRole(self,roleId:str=None)->dict:
        """
        Delete a role based on its ID.
        Argument:
            roleId : REQUIRED : The role ID to be deleted
        """
        if roleId is None:
            raise ValueError("A role ID is required")
        path = f"/administration/roles/{roleId}/"
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteRole with id : {roleId}")
        res = self.connector.deleteData(self.endpoint+path)
        return res
    
    def patchRole(self, roleId:str=None,roleChange:dict=None)->dict:
        """
        PATCH the role with the attribute passed.
        Attribute can have the following action "add" "replace" "remove".
        Arguments:
            roleId : REQUIRED : The role ID to be updated
            roleDict : REQUIRED : The change to the role
        """
        if roleChange is None:
            raise ValueError("a dictionary for the role change should be provided")
        if roleId is None:
            raise ValueError("A role ID is required")
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchRole with id : {roleId}")
        path = f"/administration/roles/{roleId}/"
        res = self.connector.patchData(self.endpoint+path,data=roleChange)
        return res
    
    def putRole(self,roleId:str=None,roleDict:dict=None)->dict:
        """
        PUT the role with the new definition passed.
        As a PUT method, the old definition will be replaced by the new one.
        Arguments:
            roleId : REQUIRED : The role ID to be updated
            roleDict : REQUIRED : The change to the role
        example:
        {
        "name": "Administrator Role",
        "description": "Role for administrator type of responsibilities and access.",
        "roleType": "user-defined"
        }
        """
        if roleDict is None:
            raise ValueError("a dictionary for the role change should be provided")
        if roleId is None:
            raise ValueError("A role ID is required")
        if self.loggingEnabled:
            self.logger.debug(f"Starting putRole with id : {roleId}")
        path = f"/administration/roles/{roleId}/"
        res = self.connector.putData(self.endpoint+path,data=roleDict)
        return res

    def getSubjects(self,roleId:str=None)->dict:
        """
        Get the subjects attached to the role specified in the roleId.
        Arguments:
            roleId : REQUIRED : The roleId for which the subjects should be extracted
        """
        if roleId is None:
            raise ValueError("A role ID is required")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSubjects with id : {roleId}")
        path = f"/administration/roles/{roleId}/subjects"
        res = self.connector.getData(self.endpoint+path)
        data = res.get('items',[])
        nextPage = res.get('_links',{}).get('page',{}).get('href','')
        while nextPage != "":
            limit = len(data)
            params = {'start':limit+1,limit:limit}
            res = self.connector.getData(self.endpoint+path,params=params)
            data += res.get('items',[])
            nextPage = res.get('_links',{}).get('page',{}).get('href','')
            if len(res.get('items',[])) == 0:
                nextPage = ""
        return data

    def patchSubjects(self,roleId:str=None,subjectId:str=None,operation:str=None)->dict:
        """
        Manage the subjects attached to a specific role
        Arguments:
            roleId : REQUIRED : The role ID to update
            subjectId : REQUIRED : The subject ID to be updated
            operation : REQUIRED : The operation could be either "add" "replace" "remove"
        """
        if roleId is None:
            raise ValueError("A role ID is required")
        if subjectId is None:
            raise ValueError("A subject ID is required")
        if operation is None:
            raise ValueError("An operation is required")
        if operation not in ["add", "replace", "remove"]:
            raise ValueError("An operation should be one of the following value : [add,replace,remove]")
        path = f"/administration/roles/{roleId}/subjects"
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchSubjects with role id : {roleId}")
        data = {            
            "op": operation,
            "path": "/user",
            "value": subjectId
        }
        res = self.connector.patchData(self.endpoint+path,data=data)
        return res
    
    def getPolicies(self)->list:
        """
        Returns all the policies applying in your organization
        """
        path = f"/administration/policies"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPolicies")
        res = self.connector.getData(self.endpoint+path)
        data = res.get('items',[])
        return data
    
    def getPolicy(self,policyId:str)->dict:
        """
        Returns a specific policy based on its ID.
        Arguments:
            policyId : REQUIRED : The policy ID to be retrieved
        """
        if policyId is None:
            raise ValueError("Requires a policy ID")
        path = f"/administration/policies/{policyId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPolicy")
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def deletePolicy(self,policyId:str)->dict:
        """
        Delete a specific policy based on its ID.
        Arguments:
            policyId : REQUIRED : The policy ID to be deleted
        """
        if policyId is None:
            raise ValueError("Requires a policy ID")
        path = f"/administration/policies/{policyId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting deletePolicy for id : {policyId}")
        res = self.connector.deleteData(self.endpoint+path)
        return res
    
    def createPolicy(self,policyDef:dict=None)->dict:
        """
        Create a policy based on the definition passed
        Arguments:
            policyDef : REQUIRED : The policy definition requires
        """
        if policyDef is None:
            raise ValueError("No policy definition has been passed")
        if "name" not in policyDef.keys():
            raise AttributeError("Require a name for the policy")
        if "rules" not in policyDef.keys():
            raise AttributeError("Require a rules attribute for the policy")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createPolicy")
        path = f"/administration/policies"
        res = self.connector.postData(self.endpoint+path, data=policyDef)
        return res
    
    def putPolicy(self,policyId:str=None,policyDef:dict=None)->dict:
        """
        Replace the policyID provided by the new definition passed.
        Arguments:
            policyId : REQUIRED : The policy ID to replaced
            policyDef : REQUIRED : The new definition of the policy ID.
        """
        if policyDef is None:
            raise ValueError("Requires a policy definition")
        if policyId is None:
            raise ValueError("Requires a policy ID")
        path = f"/administration/policies/{policyId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting putPolicy for this ID : {policyId}")
        res = self.connector.putData(self.endpoint + path, data=policyDef)
        return res
    
    def patchPolicy(self,policyId:str=None,operation:str=None,attribute:str=None,value:str=None)->dict:
        """
        Patch the policyID provided with the operation provided
        Arguments:
            policyId : REQUIRED : The policy ID to be updated
            operation : REQUIRED : The operation to realise ("add" "replace" "remove")
            attribute : REQUIRED : The attribute to be updated. Ex : "/description"
            value : REQUIRED : The new value to be used
        """
        if operation is None:
            raise ValueError("Requires an operation")
        if policyId is None:
            raise ValueError("Requires a policy ID")
        if attribute is None:
            raise ValueError("Requires an attribute")
        if value is None:
            raise ValueError("Requires a value")
        path = f"/administration/policies/{policyId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchPolicy for this ID : {policyId}")
        data = {     
            "op": operation,
            "path": attribute,
            "value": value
        }
        res = self.connector.patchData(self.endpoint + path, data=data)
        return res
    
    def getProducts(self)->list:
        """
        List all entitled products
        """
        path = "/administration/products"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getProducts")
        res = self.connector.getData(self.endpoint + path)
        data = res.get('products',[])
        return data

    def getPermissionCategories(self,productId:str=None)->list:
        """
        Retrieve the permissions categories for a specific product
        Arguments:
            productId : REQUIRED : The product you are looking for
        """
        if productId is None:
            raise ValueError("Product ID is required")
        path = f"/administration/products/{productId}/categories"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPermissionCategories")
        res = self.connector.getData(self.endpoint+path)
        data = res.get('categories',[])
        return data
    
    def getPermissionSets(self,productId:str=None)->list:
        """
        Retrieve the permissions set of the product ID you want to acces.
        Arguments:
            productId : REQUIRED : The product ID permissions set you want to retrieve
        """
        if productId is None:
            raise ValueError("Product ID is required")
        path = f"/administration/products/{productId}/permission-sets"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPermissionSets")
        res = self.connector.getData(self.endpoint+path)
        data = res.get("permission-sets",[])
        return data