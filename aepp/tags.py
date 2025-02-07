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
import logging
from typing import Union
from .configs import ConnectObject
import json


class Tags:
    """
    Class to manage and retrieve Tags policy.
    This is based on the following API reference :
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
        Instantiate the class to manage Tags in adobe eco-system
        Arguments:
            config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
            loggingObject : OPTIONAL : logging object to log messages.
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
        self.endpointTag = (
            "https://experience.adobe.io" + aepp.config.endpoints["tags"]
        )
        self.endpointFolders = (
            "https://experience.adobe.io" + aepp.config.endpoints["folders"]
        )
        self.header['x-api-key'] = 'exc_app'
        self.connector.header['x-api-key'] = 'exc_app'

    def __str__(self):
        return json.dumps({'class':'Tags','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)
    
    def __repr__(self):
        return json.dumps({'class':'Tags','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)


    def getCategories(self,limit:int=100)->list:
        """
        Retrieve the categories of the tags.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getCategories")
        path = "/tagCategory"
        params = {"limit":limit}
        res = self.connector.getData(self.endpointTag+path,params=params)
        data = res.get('tags',[])
        return data
    
    def getCategory(self,tagCategoryId:str)->dict:
        """
        Retrieve the tag category based on the ID passed.
        Arguments:
            tagCategoryId : REQUIRED : The Id of the tag category to retrieve
        """
        if tagCategoryId is None:
            raise ValueError("The ID of tag category")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getCategory")
        path = f"/tagCategory/{tagCategoryId}"
        res = self.connector.getData(self.endpointTag+path)
        return res

    def createCategory(self,name:str=None,description:str=None)->dict:
        """
        Create a tag category
        Arguments:
            name : REQUIRED : name of the category
            description : OPTIONAL : description of the category
        """
        if name is None:
            raise ValueError("A name for your category is required")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createCategory with name : {name}")
        if description is None:
            description = ""
        path = "/tagCategory"
        data = {
            "name" : name,
            "description" : description
        }
        res = self.connector.postData(self.endpointTag+path,data=data)
        return res
    
    def patchCategory(self,tagCategoryId:str=None,operation:dict="replace",op:str=None,path:str=None,value:str=None)->dict:
        """
        Patch the category with new definition
        Arguments:
            tagCategoryId : REQUIRED : The ID of the category to update
            operation : OPTIONAL : A dictionary that provides the operation to performed
            ex: {
                    "op": "replace",
                    "path": "description",
                    "value": "Updated sample description"
                }
            op : OPTIONAL : In case the individual value for "op" in the operation is provided. Possible value: "replace"
            path : OPTIONAL : In case the individual value for "path" in the operation is provided.
            value : OPTIONAL : In case the individual value for "value" in the operation is provided.
        """
        if tagCategoryId is None:
            raise ValueError("Require a tag category ID to be provided")
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchCategory with id : {tagCategoryId}")
        path = f"/tagCategory/{tagCategoryId}"
        if operation is not None and type(operation) == dict:
            data = operation
        else:
            if path is None or value is None:
                raise ValueError("Missing some values in path and value arguments")
            data = {
                    "op": op,
                    "path": path,
                    "value": value
                }
        res = self.connector.patchData(self.endpointTag+path,data=data)
        return res
    
    def deleteTagCategory(self,tagCategoryId:str)->dict:
        """
        Delete the tag category based on its ID.
        Arguments:
            tagCategoryId : REQUIRED : Tag Category ID to be deleted
        """
        if tagCategoryId is None:
            raise ValueError("The tag category ID is missing as argument")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteTagCategory with id : {tagCategoryId}")
        path = f"/tagCategory/{tagCategoryId}"
        res = self.connector.deleteData(self.endpointTag+path)
        return res
    
    def getTags(self,tagCategoryId:str=None)->list:
        """
        Retrieve a list of tag based on the categoryId
        Arguments:
            tagCategoryId : OPTIONAL : The id of the category to get your tags
        """
        if tagCategoryId is None:
            path = "/tags"
        else:
            path = f"/tags/{tagCategoryId}"
        params = {'start':''}
        res = self.connector.getData(self.endpointTag+path)
        nextPage = res.get('_page',{}).get('next',None)
        data = res.get('tags')
        while nextPage is not None:
            params['start'] = nextPage
            res = self.connector.getData(self.endpointTag+path, params=params)
            data += res.get('tags')
            nextPage = res.get('_page',{}).get('next',None)
        return data
    
    def getTag(self,tagId:str)->dict:
        """
        Retrieve a specific tag based on its ID.
        Argument:
            tagId : REQUIRED : The tag ID to be used
        """
        if tagId is None:
            raise ValueError("Require a tag ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getTag with id : {tagId}")
        path = f"/tags/{tagId}"
        res = self.connector.getData(self.endpointTag+path)
        return res
    
    def createTag(self,name:str,tagCategoryId:str)->dict:
        """
        Create a new tag.
        Arguments:
            name : REQUIRED : Name of the tag
            tagCategoryId : OPTIONAL : The category ID of the tag
        """
        if name is None:
            raise ValueError("Require a name to be passed")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createTag with name : {name}")
        data = {
            "name":name
        }
        if tagCategoryId is not None:
            data['tagCategoryId'] = tagCategoryId
        path = "/tags"
        res = self.connector.postData(self.endpointTag+path,data=data)
        return res
    
    def patchTag(self,tagId:str=None,operation:dict=None,op:str="replace",path:str=None,value:str=None)->dict:
        """
        Update a specific Tag
        Arguments:
            tagId : REQUIRED : The tag Id to be updated
            operation : OPTIONAL : The full operation dictionary
            ex: {
                    "op": "replace",
                    "path": "description",
                    "value": "Updated sample description"
                }
            op : OPTIONAL : In case the individual value for "op" in the operation is provided. default value: "replace"
            path : OPTIONAL : In case the individual value for "path" in the operation is provided.
            value : OPTIONAL : In case the individual value for "value" in the operation is provided. 
        """
        if tagId is None:
            raise ValueError("Require a tag ID to be provided")
        path = f"/tags/{tagId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchTag with id : {tagId}")
        if operation is not None and type(operation) == dict:
            data = operation
        else:
            if path is None or value is None:
                raise ValueError("Missing some values in path and value arguments")
            data = {
                    "op": op,
                    "path": path,
                    "value": value
                }
        res = self.connector.patchData(self.endpointTag+path,data=data)
        return res
    
    def deleteTag(self,tagId:str=None)->dict:
        """
        Delete a tag by its ID.
        Arguments:
            tagId : REQUIRED : The Tag Id to be deleted
        """
        if tagId is None:
            raise ValueError("A tagId is required")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteTag with id : {tagId}")
        path = f"/tags/{tagId}"
        res = self.connector.deleteData(self.endpointTag+path)
        return res

    def validateTags(self,tagsIds:list=None)->dict:
        """
        Validate if specific tag Ids exist.
        Arguments: 
            tagsIds : REQUIRE : List of tag Ids to validate
        """
        path = "/tags/validate"
        if self.loggingEnabled:
            self.logger.debug(f"Starting validateTags")
        if type(tagsIds) == str:
            tagsIds = list(tagsIds)
        data = {
            "ids" : tagsIds
        }
        res = self.connector.postData(self.endpointTag+path,data=data)
        return res
    
    def getFolders(self,folderType:str='segment')->list:
        """
        Retrieve the folders for the tags.
        Arguments:
            folderType : REQUIRED : Default "segment", possible values: "dataset"
        """
        path = f"/folders/{folderType}/root/folderview"
        res = self.connector.getData(self.endpointFolders+path)
        data = res.get('children',[])
        return data

    def getSubFolders(self,folderType:str="segment",folderId:str=None)->list:
        """
        Return the list of subfolders.
        Arguments:
            folderType : REQUIRED : Default "segment", possible values: "dataset"
            folderId : REQUIRED : The folder ID that you want to retrieve
        """
        if folderId is None:
            raise ValueError("Require a folder ID")
        path = f"/folders/{folderType}/{folderId}/subfolders"
        res = self.connector.getData(self.endpointFolders+path)
        return res
    
    def getSubFolder(self,folderType:str="segment",folderId:str=None)->dict:
        """
        Return a specific sub folder
        Arguments:
            folderType : REQUIRED : Default "segment", possible values: "dataset"
            folderId : REQUIRED : The folder ID that you want to retrieve
        """
        if folderId is None:
            raise ValueError("Require a folder ID")
        path = f"/folders/{folderType}/{folderId}/"
        res = self.connector.getData(self.endpointFolders+path)
        return res
    
    def deleteSubFolder(self,folderType:str="segment",folderId:str=None)->dict:
        """
        Delete a specific subFolder
        Arguments:
            folderType : REQUIRED : Default "segment", possible values: "datasets"
            folderId : REQUIRED : The folder ID you want to delete
        """
        if folderId is None:
            raise ValueError("Require a folder ID")
        path = f"/{folderType}/{folderId}/"
        res = self.connector.deleteData(self.endpointFolders+path)
        return res
    
    def createSubFolder(self,folderType:str="segment",name:str=None,parentId:str=None)->dict:
        """
        Create a sub Folder.
        Arguments:
            folderType : REQUIRED : Default "segment", possible values: "dataset"
            name : REQUIRED : Name of the folder
            parentId : REQUIRED : The parentID attached to your folder 
        """
        if folderType is None:
            raise ValueError("Require a folder type")
        if name is None:
            raise ValueError("Require a name")
        if parentId is None:
            raise ValueError("Require a parent ID")
        path = f"/folder/{folderType}"
        data = {
                    "name": name,
                    "parentId": parentId
                }
        res = self.connector.postData(self.endpointFolders+path,data=data)
        return res
    
    def updateFolder(self,folderType:str="segment",folderId:str=None,name:str=None,parentFolderId:str=None)->dict:
        """
        Update an existing folder name
        Arguments:
            folderType : REQUIRED : Default "segment", possible values: "dataset"
            folderId : REQUIRED : the folder ID you want to rename
            name : OPTIONAL : The new name you want to give that folder
            parentFolderId : OPTIONAL : The new parent folder id 
        """
        if folderType is None:
            raise ValueError("A Folder Type is required")
        if folderId is None:
            raise ValueError("A folder ID is required")
        path = f"/{folderType}/{folderId}"
        data = []
        if name is not None:
            data.append({
                "op": "replace",
                "path": "/name",
                "value": name
            })
        if parentFolderId is not None:
            data.append({
                "op": "replace",
                "path": "/parentFolderId",
                "value": parentFolderId
            })
        res = self.connector.patchData(self.endpointFolders+path,data=data)
        return res
    
    def validateFolder(self,folderType:str="segment",folderId:str=None)->dict:
        """
        Validate if a folder is eligible to have objects in it 
        Arguments:
            folderType : REQUIRED : Default "segment", possible values: "dataset"
            folderId : REQUIRED : The Folder ID
        """
        if folderId is None:
            raise ValueError("Folder ID is required")
        if folderType is None:
            raise ValueError("Folder type is required")
        path = f"/{folderType}/{folderId}/validate"
        res = self.connector.getData(self.endpointFolders+path)
        return res