#  Copyright 2025 Adobe. All rights reserved.
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
from copy import deepcopy
from typing import Union
import time
import pandas as pd
import json
import re
from .configs import ConnectObject
from aepp.schema import Schema
from aepp import som
from pathlib import Path
from io import FileIO

class DataTypeManager:
    """
    Class to work on the custom data type or create a new data type.
    """

    def __init__(self,
                dataType:Union[str,dict]=None,
                title:str=None,
                schemaAPI:'Schema'=None,
                config: Union[dict,ConnectObject] = aepp.config.config_object,
                description:str="",
                localFolder:str=None,
                sandbox:str=None,
                **kwargs
                )->None:
        """
        Instantiate the DataType Manager Class.
        Arguments:
            dataType : OPTIONAL : Either a data type id ($id or altId) or the data type dictionary itself.
                If dataType Id is passed, you need to provide the schemaAPI connection as well.
            title : OPTIONAL : to set or override the title (default None, use the existing title or do not set one for new data type) 
            schemaAPI : OPTIONAL : It is required if $id or altId are used. It is the instance of the Schema class.
            config : OPTIONAL : The config object in case you want to override the configuration.
            description : OPTIONAL : The description of the data type. Default is empty string.
            localFolder : OPTIONAL : If you want to use local storage to create all the connections between schema and field groups, classes and datatypes
            sandbox : OPTIONAL : If you use localFolder, you can specific the sandbox.
        """
        self.localfolder = None
        self.EDITABLE = False
        self.STATE = "EXISTING"
        self.dataType = {}
        self.dataTypes = {}
        self.dataTypeManagers = {}
        self.id = None
        self.requiredFields = set()
        if schemaAPI is not None and type(schemaAPI) == Schema:
            self.schemaAPI = schemaAPI
        elif config is not None and localFolder is None:
            self.schemaAPI = Schema(config=config)
        elif localFolder is not None:
            self.localfolder = Path(localFolder)
            self.datatypeFolder = self.localfolder / 'datatype'
            if self.localfolder.exists() is False:
                raise Exception(f"The local folder {self.localfolder} does not exist. Please create it and extract your sandbox before using it.")
            self.schemaAPI = None
        if self.schemaAPI is not None:
            self.sandbox = self.schemaAPI.sandbox
        elif sandbox is not None:
            self.sandbox = sandbox
        else:
            self.sandbox = None
        if kwargs.get('tenantId',None) is not None:
            self.tenantId = kwargs.get('tenantId')
        if self.schemaAPI is not None:
            self.tenantId = f"_{self.schemaAPI.getTenantId()}"
        elif type(dataType) == dict:
            if dataType.get('meta:tenantNamespace') is not None:
                self.tenantId = f"_{dataType.get('meta:tenantNamespace')}"
        elif kwargs.get('tenantId',None) is not None:
            self.tenantId = kwargs.get('tenantId')
        else:
            self.tenantId = "  "
        if type(dataType) == dict:
            self.dataType = dataType
            if self.tenantId[1:] in self.dataType['$id']:
                if self.schemaAPI is not None:
                    self.dataType = self.schemaAPI.getDataType(dataType['$id'],full=False)
                    self.EDITABLE = True
                elif self.localfolder is not None:
                    for dataTypeFile in self.datatypeFolder.glob(f"*.json"):
                        tmp_def = json.load(FileIO(dataTypeFile))
                        if tmp_def.get('$id') == dataType.get('$id') or tmp_def.get('meta:altId') == dataType.get('meta:altId'):
                            self.dataType = tmp_def
                    self.EDITABLE = False
            else:
                if self.schemaAPI is not None:
                    self.dataType = self.schemaAPI.getDataType(dataType['$id'],full=True)
                    self.EDITABLE = True
                elif self.localfolder is not None:
                    for dataTypeFile in self.datatypeFolder.glob("*.json"):
                        tmp_def = json.load(FileIO(dataTypeFile))
                        if tmp_def.get('$id') == dataType.get('$id') or tmp_def.get('meta:altId') == dataType.get('meta:altId') or tmp_def.get('title') == dataType.get('title'):   
                            self.dataType = tmp_def
                    self.EDITABLE = False
        elif type(dataType) == str:
            if self.tenantId[1:] in dataType:
                if self.schemaAPI is not None:
                    self.dataType = self.schemaAPI.getDataType(dataType,full=False)
                    if self.dataType is None:
                        raise ValueError(f"Cannot find the data type with id {dataType} in the schema API.")
                    self.EDITABLE = True
                elif self.localfolder is not None:
                    for dataTypeFile in self.datatypeFolder.glob("*.json"):
                        tmp_def = json.load(FileIO(dataTypeFile))
                        if tmp_def.get('$id') == dataType or tmp_def.get('meta:altId') == dataType or tmp_def.get('title') == dataType:
                            self.dataType = tmp_def
                    self.EDITABLE = False
                else:
                    raise Exception("You try to retrieve the datatype definition from the id, but no API or localFolder has been passed as a parameter.")
            else:
                if self.schemaAPI is not None:
                    self.dataType = self.schemaAPI.getDataType(dataType,full=True)
                    if self.dataType is None:
                        raise ValueError(f"Cannot find the data type with id {dataType} in the schema API.")
                    self.EDITABLE = True
                elif self.localfolder is not None:
                    for dataTypeFile in self.datatypeFolder.glob("*.json"):
                        tmp_def = json.load(FileIO(dataTypeFile))
                        if tmp_def.get('$id') == dataType or tmp_def.get('meta:altId') == dataType or tmp_def.get('title') == dataType:
                            self.dataType = tmp_def
                    self.EDITABLE = False
                else:
                    raise Exception("You try to retrieve the datatype definition from the id, but no API or localFolder has been passed as a parameter.")
        else:
            self.STATE = "NEW"
            if self.schemaAPI is not None:
                self.EDITABLE = True
            else:
                self.EDITABLE = False
            self.dataType = {
                "title" : "",
                "description":description,
                "type" : "object",
                "definitions":{
                    "customFields":{
                        "type" : "object",
                        "properties":{}
                        },
                    "property":
                        {"type" : "object",
                        "properties":{}
                        }
                },
                'allOf': [{'$ref': '#/definitions/customFields',
                    'type': 'object',
                    'meta:xdmType': 'object'},
                    {"$ref": "#/definitions/property",
                    "type": "object"
                    }],
                'meta:tenantNamespace': self.tenantId
            }
        if '/datatypes/' in str(self.dataType.get('definitions',{})): ## if custom datatype used in data types
            dataTypeSearch = f"(https://ns.adobe.com/{self.tenantId[1:]}/datatypes/[0-9a-z]+?)'"
            dataTypes = re.findall(dataTypeSearch,str(self.dataType.get('definitions',{})))
            if self.schemaAPI is not None:
                for dt in dataTypes:
                    dt_manager = self.schemaAPI.DataTypeManager(dt)
                    self.dataTypes[dt_manager.id] = dt_manager.title
                    self.dataTypeManagers[dt_manager.title] = dt_manager
            elif self.localfolder is not None:
                for dt in dataTypes:
                    for dataTypeFile in self.datatypeFolder.glob("*.json"):
                        tmp_def = json.load(FileIO(dataTypeFile))
                        if tmp_def.get('$id') == dt or tmp_def.get('meta:altId') == dt or tmp_def.get('title') == dt:
                            dt_manager = DataTypeManager(dataType=tmp_def,localFolder=self.localfolder,tenantId=self.tenantId,sandbox=self.sandbox)
                            self.dataTypes[dt_manager.id] = dt_manager.title
                            self.dataTypeManagers[dt_manager.title] = dt_manager
        if title is not None:
            self.dataType['title'] = title
            self.title = title
        else:
            self.title = self.dataType.get('title','unknown')
        self.__setAttributes__(self.dataType)
    
    def __setAttributes__(self,datatype:dict)->None:
        uniqueId = datatype.get('id',str(int(time.time()*100))[-7:])
        self.title = datatype.get('title',f'unknown:{uniqueId}')
        self.description = datatype.get('description','')
        if datatype.get('$id',False):
            self.id = datatype.get('$id')
        if datatype.get('meta:altId',False):
            self.altId = datatype.get('meta:altId')
            
    def __str__(self)->str:
        return json.dumps(self.dataType,indent=2)
    
    def __repr__(self)->str:
        return json.dumps(self.dataType,indent=2)

    def __simpleDeepMerge__(self,base:dict,append:dict)->dict:
        """
        Loop through the keys of 2 dictionary and append the new found key of append to the base.
        Arguments:
            base : The base you want to extend
            append : the new dictionary to append
        """
        if type(append) == list:
            append = append[0]
        for key in append:
            if type(base)==dict:
                if key in base.keys():
                    self.__simpleDeepMerge__(base[key],append[key])
                else:
                    base[key] = append[key]
            elif type(base)==list:
                base = base[0]
                if type(base) == dict:
                    if key in base.keys():
                        self.__simpleDeepMerge__(base[key],append[key])
                    else:
                        base[key] = append[key]
        return base

    def __accessorAlgo__(self,mydict:dict,path:str=None)->dict:
        """
        recursive method to retrieve all the elements.
        Arguments:
            mydict : REQUIRED : The dictionary containing the elements to fetch (in "properties" key)
            path : REQUIRED : the path with dot notation.
        """
        path = self.__cleanPath__(path)
        pathSplit = path.split('.')
        key = pathSplit[0]
        if 'customFields' in mydict.keys():
            level = self.__accessorAlgo__(mydict.get('customFields',{}).get('properties',{}),'.'.join(pathSplit))
            if 'error' not in level.keys():
                return level
        if 'property' in mydict.keys() :
            level = self.__accessorAlgo__(mydict.get('property',{}).get('properties',{}),'.'.join(pathSplit))
            return level
        level = mydict.get(key,None)
        if level is not None:
            if level["type"] == "object":
                levelProperties = mydict[key].get('properties',None)
                if levelProperties is not None:
                    level = self.__accessorAlgo__(levelProperties,'.'.join(pathSplit[1:]))
                return level
            elif level["type"] == "array":
                levelProperties = mydict[key]['items'].get('properties',None)
                if levelProperties is not None:
                    level = self.__accessorAlgo__(levelProperties,'.'.join(pathSplit[1:]))
                return level
            else:
                if len(pathSplit) > 1: 
                    return {'error':f'cannot find the key "{pathSplit[1]}"'}
                return level
        else:
            if key == "":
                return mydict
            return {'error':f'cannot find the key "{key}"'}

    def __searchAlgo__(self,mydict:dict,string:str=None,partialMatch:bool=False,caseSensitive:bool=False,results:list=None,path:str=None,completePath:str=None)->list:
        """
        recursive method to retrieve all the elements.
        Arguments:
            mydict : REQUIRED : The dictionary containing the elements to fetch (start with fieldGroup definition)
            string : the string to look for with dot notation.
            partialMatch : if you want to use partial match
            caseSensitive : to see if we should lower case everything
            results : the list of results to return
            path : the path currently set
            completePath : the complete path from the start.
        """
        finalPath = None
        if results is None:
            results=[]
        for key in mydict:
            if caseSensitive == False:
                keyComp = key.lower()
                string = string.lower()
            else:
                keyComp = key
                string = string
            if partialMatch:
                if string in keyComp:
                    ### checking if element is an array without deeper object level
                    if mydict[key].get('type') == 'array' and mydict[key]['items'].get('properties',None) is None:
                        finalPath = path + f".{key}[]"
                        if path is not None:
                            finalPath = path + f".{key}"
                        else:
                            finalPath = f"{key}"
                    else:
                        if path is not None:
                            finalPath = path + f".{key}"
                        else:
                            finalPath = f"{key}"
                    value = deepcopy(mydict[key])
                    value['path'] = finalPath
                    value['queryPath'] = self.__cleanPath__(finalPath)
                    if completePath is None:
                        value['completePath'] = f"/definitions/{key}"
                    else:
                        value['completePath'] = completePath + "/" + key
                    results.append({key:value})
            else:
                if caseSensitive == False:
                    if keyComp == string:
                        if path is not None:
                            finalPath = path + f".{key}"
                        else:
                            finalPath = key
                        value = deepcopy(mydict[key])
                        value['path'] = finalPath
                        value['queryPath'] = self.__cleanPath__(finalPath)
                        if completePath is None:
                            value['completePath'] = f"/definitions/{key}"
                        else:
                            value['completePath'] = completePath + "/" + key
                        results.append({key:value})
                else:
                    if keyComp == string:
                        if path is not None:
                            finalPath = path + f".{key}"
                        else:
                            finalPath = key
                        value = deepcopy(mydict[key])
                        value['path'] = finalPath
                        value['queryPath'] = self.__cleanPath__(finalPath)
                        if completePath is None:
                            value['completePath'] = f"/definitions/{key}"
                        else:
                            value['completePath'] = completePath + "/" + key
                        results.append({key:value})
            ## loop through keys
            if mydict[key].get("type") == "object" or 'properties' in mydict[key].keys():
                levelProperties = mydict[key].get('properties',{})
                if levelProperties != dict():
                    if completePath is None:
                        tmp_completePath = f"/definitions/{key}"
                    else:
                        tmp_completePath = f"{completePath}/{key}"
                    tmp_completePath += f"/properties"
                    if path is None:
                        if key != "property" and key != "customFields" :
                            tmp_path = key
                        else:
                            tmp_path = None
                    else:
                        tmp_path = f"{path}.{key}"
                    results = self.__searchAlgo__(levelProperties,string,partialMatch,caseSensitive,results,tmp_path,tmp_completePath)
            elif mydict[key].get("type") == "array":
                levelProperties = mydict[key]['items'].get('properties',{})
                if levelProperties != dict():
                    if completePath is None:
                        tmp_completePath = f"/definitions/{key}"
                    else:
                        tmp_completePath = f"{completePath}/{key}"
                    tmp_completePath += f"/items/properties"
                    if levelProperties is not None:
                        if path is None:
                            if key != "property" and key != "customFields":
                                tmp_path = key
                            else:
                                tmp_path = None
                        else:
                            tmp_path = f"{path}.{key}[]{{}}"
                        results = self.__searchAlgo__(levelProperties,string,partialMatch,caseSensitive,results,tmp_path,tmp_completePath)
        return results

    def __searchAttrAlgo__(self,mydict:dict,key:str=None,value:str=None,regex:bool=False, originalField:str=None, results:list=None)->list:
        """
        recursive method to retrieve all the elements.
        Arguments:
            mydict : REQUIRED : The dictionary containing the elements to fetch (start with fieldGroup definition)
            key : key of the attribute
            value : the value of that key to look for.
            regex : if the regex match should be used.
            originalField : the key used to dig deeper.
            results : the list of results to return
        """
        if results is None:
            results=[]
        for k in mydict:
            if key == k:
                if regex:
                    checkValue = deepcopy(mydict[k])
                    if type(checkValue) == list or type(checkValue) == dict:
                        checkValue = json.dumps(checkValue)
                    if re.match(value,checkValue):
                        if originalField is not None and originalField != 'property' and originalField != 'properties' and originalField != 'items':
                            results.append(originalField)
                else:
                    if mydict[k] == value:
                        if originalField is not None and originalField != 'property' and originalField != 'properties' and originalField != 'items':
                            results.append(originalField)
            ## recursive action for objects and array
            if type(mydict[k]) == dict:
                if k == "properties" or k == 'items':
                    self.__searchAttrAlgo__(mydict[k],key,value,regex,originalField,results)
                else:
                    self.__searchAttrAlgo__(mydict[k],key,value,regex,k,results)
        return results
    
    def __transformationDict__(self,mydict:dict=None,typed:bool=False,dictionary:dict=None)->dict:
        """
        Transform the current XDM schema to a dictionary.
        """
        if dictionary is None:
            dictionary = {}
        else:
            dictionary = dictionary
        for key in mydict:
            if type(mydict[key]) == dict:
                if mydict[key].get('type') == 'object' or 'properties' in mydict[key].keys():
                    properties = mydict[key].get('properties',None)
                    if properties is not None:
                        if key != "property" and key != "customFields":
                            if key not in dictionary.keys():
                                dictionary[key] = {}
                            self.__transformationDict__(mydict[key]['properties'],typed,dictionary=dictionary[key])
                        else:
                            self.__transformationDict__(mydict[key]['properties'],typed,dictionary=dictionary)
                elif mydict[key].get('type') == 'array':
                    levelProperties = mydict[key]['items'].get('properties',None)
                    if levelProperties is not None:
                        dictionary[key] = [{}]
                        self.__transformationDict__(levelProperties,typed,dictionary[key][0])
                    else:
                        if typed:
                            dictionary[key] = [mydict[key]['items'].get('type','object')]
                        else:
                            dictionary[key] = []
                else:
                    if typed:
                        dictionary[key] = mydict[key].get('type','object')
                    else:
                        dictionary[key] = ""
        return dictionary 

    def __transformationDF__(self,
                             mydict:dict=None,
                             dictionary:dict=None,
                             path:str=None,
                             description:bool=False,
                             xdmType:bool=False,
                             queryPath:bool=False,
                             required:bool=False)->dict:
        """
        Transform the current XDM schema to a dictionary.
        Arguments:
            mydict : the fieldgroup
            dictionary : the dictionary that gather the paths
            path : path that is currently being developed
            queryPath: boolean to tell if we want to add the query path
            description : boolean to tell if you want to retrieve the description
            xdmType : boolean to know if you want to retrieve the xdm Type
            required : If you want to have the required field in the dataframe
        """
        if dictionary is None:
            dictionary = {'path':[],'type':[],'title':[]}
            if description:
                dictionary['description'] = []
            if xdmType:
                dictionary['xdmType'] = []
            if queryPath:
                dictionary['queryPath'] = []
        else:
            dictionary = dictionary
        for key in mydict:
            if type(mydict[key]) == dict:
                if mydict[key].get('type') == 'object' or 'properties' in mydict[key].keys():
                    if path is None:
                        if key != "property" and key != "customFields":
                            tmp_path = key
                        else:
                            tmp_path = None
                    else:
                        tmp_path = f"{path}.{key}"
                    if tmp_path is not None:
                        dictionary["path"].append(tmp_path)
                        dictionary["type"].append(f"{mydict[key].get('type')}")
                        dictionary["title"].append(f"{mydict[key].get('title')}")
                        if description:
                            dictionary["description"].append(f"{mydict[key].get('description','')}")
                        if xdmType:
                            dictionary["xdmType"].append(f"{mydict[key].get('meta:xdmType')}")
                        if queryPath:
                            dictionary["querypath"].append(self.__cleanPath__(tmp_path))
                        if required:
                            if len(mydict[key].get('required',[])) > 0:
                                for elRequired in mydict[key].get('required',[]):
                                    if tmp_path is not None:
                                        tmp_reqPath = f"{tmp_path}.{elRequired}"
                                    else:
                                        tmp_reqPath = f"{elRequired}"
                                    self.requiredFields.add(tmp_reqPath)
                    properties = mydict[key].get('properties',None)
                    if properties is not None:
                        self.__transformationDF__(properties,dictionary,tmp_path,description,xdmType,queryPath,required)
                elif mydict[key].get('type') == 'array':
                    levelProperties = mydict[key]['items'].get('properties',None)
                    if levelProperties is not None: ## array of objects
                        if path is None:
                            tmp_path = f"{key}[]{{}}"
                        else :
                            tmp_path = f"{path}.{key}[]{{}}"
                        dictionary["path"].append(tmp_path)
                        dictionary["type"].append(f"{mydict[key].get('type')}")
                        dictionary["title"].append(f"{mydict[key].get('title')}")
                        if description and tmp_path is not None:
                            dictionary["description"].append(mydict[key].get('description',''))
                        if xdmType:
                            dictionary["xdmType"].append(f"{mydict[key].get('meta:xdmType')}")
                        if queryPath:
                            dictionary["querypath"].append(self.__cleanPath__(tmp_path))
                        if required:
                            if len(mydict[key].get('required',[])) > 0:
                                for elRequired in mydict[key].get('required',[]):
                                    if tmp_path is not None:
                                        tmp_reqPath = f"{tmp_path}.{elRequired}"
                                    else:
                                        tmp_reqPath = f"{elRequired}"
                                    self.requiredFields.add(tmp_reqPath)
                        self.__transformationDF__(levelProperties,dictionary,tmp_path,description,xdmType,queryPath,required)
                    else: ## simple arrays
                        if '$ref' in mydict[key].get('items',{}).keys(): ## array of a datatype
                            if path is None:
                                finalpath = f"{key}[]{{}}"
                            else:
                                finalpath = f"{path}.{key}[]{{}}"
                            dictionary["type"].append(f"{mydict[key]['items'].get('type')}[]{{}}")
                        else:
                            if path is not None:
                                finalpath = f"{path}.{key}[]"
                            else:
                                finalpath = f"{key}[]"
                                dictionary["type"].append(f"{mydict[key]['items'].get('type')}[]")
                        dictionary["path"].append(finalpath)
                        dictionary["title"].append(f"{mydict[key].get('title')}")
                        if description and finalpath is not None:
                            dictionary["description"].append(mydict[key].get('description',''))
                        if xdmType:
                            dictionary["xdmType"].append(mydict[key]['items'].get('meta:xdmType',''))
                        if queryPath:
                            dictionary["querypath"].append(self.__cleanPath__(finalpath))
                        if required:
                            if len(mydict[key].get('required',[])) > 0:
                                for elRequired in mydict[key].get('required',[]):
                                    if finalpath is not None:
                                        tmp_reqPath = f"{finalpath}.{elRequired}"
                                    else:
                                        tmp_reqPath = f"{elRequired}"
                                    self.requiredFields.add(tmp_reqPath)
                else:
                    if path is not None:
                        finalpath = f"{path}.{key}"
                    else:
                        finalpath = f"{key}"
                    dictionary["path"].append(finalpath)
                    dictionary["type"].append(mydict[key].get('type','object'))
                    dictionary["title"].append(mydict[key].get('title',''))
                    if description :
                        dictionary["description"].append(mydict[key].get('description',''))
                    if xdmType :
                        dictionary["xdmType"].append(mydict[key].get('meta:xdmType',''))
                    if queryPath:
                        dictionary["querypath"].append(self.__cleanPath__(finalpath))
                    if required:
                        if len(mydict[key].get('required',[])) > 0:
                            for elRequired in mydict[key].get('required',[]):
                                if finalpath is not None:
                                    tmp_reqPath = f"{finalpath}.{elRequired}"
                                else:
                                    tmp_reqPath = f"{elRequired}"
                                self.requiredFields.add(tmp_reqPath)
        return dictionary
    
    def __setField__(self,completePathList:list=None,dataType:dict=None,newField:str=None,obj:dict=None)->dict:
        """
        Create a field with the attribute provided
        Arguments:
            completePathList : list of path to use for creation of the field.
            dataType : the self.datatype attribute
            newField : name of the new field to create
            obj : the object associated with the new field
        """
        foundFlag = False ## Flag to set if the operation has been realized or not
        lastField = completePathList[-1]
        dataType = deepcopy(dataType)
        for key in dataType:
            level = dataType.get(key,None)
            if type(level) == dict and key in completePathList:
                if 'properties' in level.keys():
                    if key != lastField:
                        res,foundFlag = self.__setField__(completePathList,dataType[key]['properties'],newField,obj)
                        dataType[key]['properties'] = res
                    else:
                        dataType[key]['properties'][newField] = obj
                        foundFlag = True
                        return dataType,foundFlag
                elif 'items' in level.keys():
                    if 'properties' in  dataType[key].get('items',{}).keys():
                        if key != lastField:
                            res, foundFlag = self.__setField__(completePathList,dataType[key]['items']['properties'],newField,obj)
                            dataType[key]['items']['properties'] = res
                        else:
                            dataType[key]['items']['properties'][newField] = obj
                            foundFlag = True
                            return dataType,foundFlag
        return dataType,foundFlag
    
    def __removeKey__(self,completePathList:list=None,fieldGroup:dict=None)->dict:
        """
        Remove the key and all element based on the path provided.
        Arugments:
            completePathList : list of path to use for identifying the key to remove
            fieldGroup : the self.fieldgroup attribute
        """
        lastField = deepcopy(completePathList).pop()
        success = False
        for key in fieldGroup:
            level = fieldGroup.get(key,None)
            if type(level) == dict and key in completePathList:
                if 'properties' in level.keys():
                    if lastField in level['properties'].keys():
                        level['properties'].pop(lastField)
                        success = True
                        return success
                    else:
                        sucess = self.__removeKey__(completePathList,fieldGroup[key]['properties'])
                        return sucess
                elif 'items' in level.keys():
                    if 'properties' in level.get('items',{}).keys():
                        if lastField in level.get('items',{}).get('properties'):
                            level['items']['properties'].pop(lastField)
                            success = True
                            return success
                        else:
                            success = self.__removeKey__(completePathList,fieldGroup[key]['items']['properties'])
                            return success
        return success 

    def __transformFieldType__(self,dataType:str=None)->dict:
        """
        return the object with the type and possible meta attribute.
        """
        obj = {}
        if dataType == 'double':
            obj['type'] = "number"
        elif dataType == 'long':
            obj['type'] = "integer"
            obj['maximum'] = 9007199254740991
            obj['minimum'] = -9007199254740991
        elif dataType == "short":
            obj['type'] = "integer"
            obj['maximum'] = 32768
            obj['minimum'] = -32768
        elif dataType == "date":
            obj['type'] = "string"
            obj['format'] = "date"
        elif dataType.lower() == "datetime" or dataType == "date-time":
            obj['type'] = "string"
            obj['format'] = "date-time"
        elif dataType == "byte":
            obj['type'] = "integer"
            obj['maximum'] = 128
            obj['minimum'] = -128
        elif dataType == "int":
            obj['type'] = "integer"
        else:
            obj['type'] = dataType
        return obj

    def __cleanPath__(self,string:str=None)->str:
        """
        An abstraction to clean the path string and remove the following characters : [,],{,}
        Arguments:
            string : REQUIRED : a string 
        """
        return string.replace('[','').replace(']','').replace("{",'').replace('}','')

    def setTitle(self,title:str=None)->None:
        """
        Set the title on the Data Type description
        Argument:
            title : REQUIRED : The title to be set
        """
        if title is None:
            raise ValueError("Require a title")
        self.dataType['title'] = title
        self.title = title
    
    def setDescription(self,description:str=None)->None:
        """
        Set the description to the Data Type.
        Argument:
            description : REQUIRED : The description to be added
        """
        self.dataType['description'] = description
        self.description = description
    
    def getField(self,path:str)->dict:
        """
        Returns the field definition you want want to obtain.
        Arguments:
            path : REQUIRED : path with dot notation to which field you want to access
        """
        definition = self.dataType.get('definitions',self.dataType.get('properties',{}))
        data = self.__accessorAlgo__(definition,path)
        return data

    def getDataTypeManager(self,dataType:str=None)->'DataTypeManager':
        """
        Retrieve the Data Type Manager instance of custom data type
        Argument:
            dataType : REQUIRED : id or name of the data type.
        """
        if dataType is None:
            raise ValueError("Require a data type $id or name")
        if dataType in self.dataTypeManagers.keys(): ## if a Title
            return self.dataTypeManagers[dataType]
        if dataType in self.dataTypes.keys():## if an ID
            return self.dataTypeManagers[self.dataTypes[dataType]]
        
    def getDataTypePaths(self,**kwargs)->dict:
        """
        Return a dictionary of the paths in the field groups and their associated data type reference.
        possible kwargs:
        som_compatible: boolean. Default False.
        """
        dict_results = {}
        for dt_id,dt_title in self.dataTypes.items():
            results = self.searchAttribute({'$ref':dt_id},extendedResults=True)
            paths = [res[list(res.keys())[0]]['path'] for res in results]
            for path in paths:
                res = self.getField(path) ## to ensure the type of the path
                if res['type'] == 'array':
                    path = path +'[]{}'
                dict_results[path] = dt_id
            if kwargs.get('som_compatible',False):
                paths = [path.replace('{}','').replace('[]','.[0]') for path in paths] ## compatible with SOM later
        return dict_results

    def searchField(self,string:str,partialMatch:bool=True,caseSensitive:bool=False)->list:
        """
        Search for a field name based the string passed.
        By default, partial match is enabled and allow case sensitivity option.
        Arguments:
            string : REQUIRED : the string to look for for one of the field
            partialMatch : OPTIONAL : if you want to look for complete string or not. (default True)
            caseSensitive : OPTIONAL : if you want to compare with case sensitivity or not. (default False)
        """
        definition = self.dataType.get('definitions',self.dataType.get('properties',{}))
        data = self.__searchAlgo__(definition,string,partialMatch,caseSensitive)
        return data
    
    def searchAttribute(self,attr:dict=None,regex:bool=False,extendedResults:bool=False,joinType:str='outer', **kwargs)->list:
        """
        Search for an attribute on the field of the data type.
        Returns either the list of fields that match this search or their full definitions.
        Arguments:
            attr : REQUIRED : a dictionary of key value pair(s).  Example : {"type" : "string"} 
                NOTE : If you wish to have the array type on top of the array results, use the key "arrayType". Example : {"type" : "array","arrayType":"string"}
                        This will automatically set the joinType to "inner". Use type for normal search. 
            regex : OPTIONAL : if you want your value of your key to be matched via regex.
                Note that regex will turn every comparison value to string for a "match" comparison.
            extendedResults : OPTIONAL : If you want to have the result to contain all details of these fields. (default False)
            joinType : OPTIONAL : If you pass multiple key value pairs, how do you want to get the match.
                outer : provide the fields if any of the key value pair is matched.
                inner : provide the fields if all the key value pair matched.
        """
        resultsDict = {f"{key}":[] for key in attr.keys()}
        if 'arrayType' in attr.keys(): ## forcing inner join
            joinType = 'inner'
        definition = self.dataType.get('definitions',self.dataType.get('properties',{}))
        for key in attr:
            if key == "arrayType":
                resultsDict[key] += self.__searchAttrAlgo__(definition,"type",attr[key],regex)
            else:
                resultsDict[key] += self.__searchAttrAlgo__(definition,key,attr[key],regex)
        result_combi = []
        if joinType == 'outer':
            for key in resultsDict:
                result_combi += resultsDict[key]
            result_combi = set(result_combi)
        elif joinType == 'inner':
            result_combi = set()
            for key in resultsDict:
                resultsDict[key] = set(resultsDict[key])
                if len(result_combi) == 0:
                    result_combi = resultsDict[key]
                else:
                    result_combi = result_combi.intersection(resultsDict[key]) 
        if extendedResults:
            result_extended = []
            for field in result_combi:
                result_extended += self.searchField(field,partialMatch=False,caseSensitive=True)
            return result_extended
        return list(result_combi)

        
    def addFieldOperation(self,path:str,dataType:str=None,title:str=None,objectComponents:dict=None,array:bool=False,enumValues:dict=None,enumType:bool=None,ref:str=None,**kwargs)->None:
        """
        Return the operation to be used on the data type with the Patch method (patchDataType), based on the element passed in argument.
        Arguments:
            path : REQUIRED : path with dot notation where you want to create that new field.
                In case of array of objects, use the "[]{}" notation
            dataType : REQUIRED : the field type you want to create
                A type can be any of the following: "string","boolean","double","long","integer","int","short","byte","date","dateTime","boolean","object","array","dataType"
                NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
            title : OPTIONAL : if you want to have a custom title.
            objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.
                Example : {'field1':'string','field2':'double'}
            array : OPTIONAL : Boolean. If the element to create is an array. False by default.
            enumValues : OPTIONAL : If your field is an enum, provid a dictionary of value and display name, such as : {'value':'display'}
            enumType: OPTIONAL: If your field is an enum, indicates whether it is an enum (True) or suggested values (False)
            ref : OPTIONAL : If you have used "dataType" as a dataType, you can pass the reference to the Data Type there.
        possible kwargs:
            defaultPath : Define which path to take by default for adding new field on tenant. Default "customFields", possible alternative : "property"
        """
        if self.EDITABLE == False:
            raise Exception("The Data Type is not Editable via Data Type Manager")
        typeTyped = ["string","boolean","double","long","integer","int","short","byte","date","dateTime","boolean","object",'array']
        if dataType not in typeTyped:
            raise TypeError(f'Expecting one of the following type : "string","boolean","double","long","integer","int","short","byte","date","dateTime","boolean","object". Got {dataType}')
        if dataType == 'object' and objectComponents is None:
            raise AttributeError('Require a dictionary providing the object component')       
        if title is None:
            title = self.__cleanPath__(path.split('.').pop())
        if title == 'items' or title == 'properties':
            raise Exception('"item" and "properties" are 2 reserved keywords')
        pathSplit = path.split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        completePath = ['definitions',kwargs.get('defaultPath','customFields')]
        for p in pathSplit:
            if '[]{}' in p:
                completePath.append(self.__cleanPath__(p))
                completePath.append('items')
                completePath.append('properties')
            else:
                completePath.append(self.__cleanPath__(p))
                completePath.append('properties')
        finalPath = '/' + '/'.join(completePath)
        operation = [{
            "op" : "add",
            "path" : finalPath,
            "value": {}
        }]
        if dataType != 'object' and dataType != "array":
            if array: # array argument set to true
                operation[0]['value']['type'] = 'array'
                operation[0]['value']['items'] = self.__transformFieldType__(dataType)
            else:
                operation[0]['value'] = self.__transformFieldType__(dataType)
        else: 
            if dataType == "object":
                operation[0]['value']['type'] = self.__transformFieldType__(dataType)
                operation[0]['value']['properties'] = {key:self.__transformFieldType__(value) for key, value in zip(objectComponents.keys(),objectComponents.values())}
            elif dataType == "array":
                operation[0]['value']['type'] = 'array'
                operation[0]['value']['items'] = {
                    'type': 'object',
                    'properties': {key:self.__transformFieldType__(value) for key, value in zip(objectComponents.keys(),objectComponents.values())}
                }
            elif dataType == "dataType":
                operation[0]['value']['$ref'] = ref
                operation[0]['value']['type'] = 'object'
                operation[0]['value']['title'] = title
                if array:
                    operation[0]['value']['type'] = "array"
                    del operation[0]['value']['$ref']
                    operation[0]['value']['items'] = {
                        'type':"object",
                        "$ref" : ref,
                        "title":title
                    }
                self.dataTypes[ref] = title
                self.dataTypeManagers[ref] = DataTypeManager(dataType=ref,schemaAPI=self.schemaAPI)
        operation[0]['value']['title'] = title
        if enumValues is not None and type(enumValues) == dict:
            if array == False:
                operation[0]['value']['meta:enum'] = enumValues
                if enumType:
                    operation[0]['value']['enum'] = list(enumValues.keys())
            else:
                operation[0]['value']['items']['meta:enum'] = enumValues
                if enumType:
                    operation[0]['value']['items']['enum'] = list(enumValues.keys())
        return operation

    def addField(self,path:str,dataType:str=None,title:str=None,objectComponents:dict=None,array:bool=False,enumValues:dict=None,enumType:bool=None,ref:str=None,**kwargs)->dict:
        """
        Add the field to the existing Data Type definition.
        Returns False when the field could not be inserted.
        Arguments:
            path : REQUIRED : path with dot notation where you want to create that new field. New field name should be included.
            dataType : REQUIRED : the field type you want to create
                A type can be any of the following: "string","boolean","double","long","int","integer","number","short","byte","date","datetime","date-time","boolean","object","array","dataType", "map"
                NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
            title : OPTIONAL : if you want to have a custom title.
            objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.
                Example : {'field1:'string','field2':'double'}
            array : OPTIONAL : Boolean. If the element to create is an array. False by default.
            enumValues : OPTIONAL : If your field is an enum, provid a dictionary of value and display name, such as : {'value':'display'}
            enumType: OPTIONAL: If your field is an enum, indicates whether it is an enum (True) or suggested values (False)
            ref : OPTIONAL : If you have used "dataType" as a dataType, you can pass the reference to the Data Type there.
        possible kwargs:
            defaultPath : Define which path to take by default for adding new field on tenant. Default "customFields", possible alternative : "property"
            description : if you want to add a description on your field
        """
        if self.EDITABLE == False:
            raise Exception("The Data Type is not Editable via Field Group Manager")
        if path is None:
            raise ValueError("path must provided")
        typeTyped = ["string","boolean","double","long","int","integer", "number","short","byte","date","datetime",'date-time',"boolean","object",'array',"dataType", "map"]
        if dataType not in typeTyped:
            raise TypeError(f'Expecting one of the following type : "string","boolean","double","long","integer","number","int","short","byte","date","datetime","date-time","boolean","object","bytes", "array", "dataType", "map". Got {dataType}')
        if title is None:
            title = self.__cleanPath__(path.split('.').pop())
        if title == 'items' or title == 'properties':
            raise Exception('"item" and "properties" are 2 reserved keywords')
        pathSplit = self.__cleanPath__(path).split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        newField = pathSplit.pop()
        description = kwargs.get("description",'')
        obj = {}
        if dataType == 'object':
            if objectComponents is not None:
                obj = { 'type':'object', 'title':title, "description":description,
                    'properties':{key:self.__transformFieldType__(objectComponents[key]) for key in objectComponents }
                }
            else:
                obj = { 'type':'object', 'title':title, "description":description,
                    'properties':{}
                }
        elif dataType == 'array':
            if objectComponents is not None:
                obj = { 'type':'array', 'title':title,"description":description,
                    "items":{
                        'type':'object',
                        'properties':{key:self.__transformFieldType__(objectComponents[key]) for key in objectComponents }
                    }
                }
            else:
                obj = { 'type':'array', 'title':title,"description":description,
                    "items":{
                        'type':'object',
                        'properties':{}
                    }
                }
        elif dataType == "dataType":
            obj = {'$ref': ref,
                    'required': [],
                    'description': description,
                    'type': 'object',
                    'title': title,
                    }
            if array:
                obj['type'] = "array"
                del obj['$ref']
                obj['items'] = {
                    'type':"object",
                    "$ref" : ref,
                    "title":title
                }
            self.dataTypes[ref] = title
            self.dataTypeManagers[ref] = DataTypeManager(dataType=ref,schemaAPI=self.schemaAPI)
        else:
            obj = self.__transformFieldType__(dataType)
            obj['title']= title
            if array:
                obj['type'] = "array"
                obj['items'] = self.__transformFieldType__(dataType)
        if enumValues is not None and type(enumValues) == dict:
            if array == False:
                obj['meta:enum'] = enumValues
                if enumType:
                    obj['enum'] = list(enumValues.keys())
            else:
                obj['items']['meta:enum'] = enumValues
                if enumType:
                    obj['items']['enum'] = list(enumValues.keys())
        completePath:list[str] = [kwargs.get('defaultPath','customFields')] + pathSplit
        definitions,foundFlag = self.__setField__(completePath, self.dataType.get('definitions',{}),newField,obj)
        if foundFlag == False:
            completePath:list[str] = ['property'] + pathSplit
            definitions,foundFlag = self.__setField__(completePath, self.dataType.get('property',{}),newField,obj)
            if foundFlag == False:
                return False
            else:
                self.dataType['property'] = definitions
                return self.dataType
        else:
            self.dataType['definitions'] = definitions
            return self.dataType
        
    def removeField(self,path:str)->dict:
        """
        Remove a field from the definition based on the path provided.
        NOTE: A path that has received data cannot be removed from a schema or field group.
        Argument:
            path : REQUIRED : The path to be removed from the definition.
        """
        if self.EDITABLE == False:
            raise Exception("The Data Type is not Editable via Field Group Manager")
        if path is None:
            raise ValueError('Require a path to remove it')
        pathSplit = self.__cleanPath__(path).split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        success = False
        ## Try customFields
        completePath:list[str] = ['customFields'] + pathSplit
        success = self.__removeKey__(completePath,self.dataType['definitions'])
        ## Try property
        if success == False:
            completePath:list[str] = ['property'] + pathSplit
            success = self.__removeKey__(completePath,self.dataType['definitions'])
        return success

    def to_dict(self,typed:bool=True,save:bool=False)->dict:
        """
        Generate a dictionary representing the field group constitution
        Arguments:
            typed : OPTIONAL : If you want the type associated with the field group to be given.
            save : OPTIONAL : If you wish to save the dictionary in a JSON file
        """
        definition = self.dataType.get('definitions',{})
        if definition == {}:
            definition = self.dataType.get('properties',{})
        data = self.__transformationDict__(definition,typed)
        if save:
            filename = self.dataType.get('title',f'unknown_dataType_{str(int(time.time()))}')
            aepp.saveFile(module='schema',file=data,filename=f"{filename}.json",type_file='json')
        return data
    
    def to_som(self)->'som.Som':
        """
        Generate a SOM object representing the Data Type constitution
        """
        return som.Som(self.to_dict())

    def to_dataframe(self,save:bool=False,description:bool=False,xdmType:bool=True,queryPath:bool=False,required:bool=False)->pd.DataFrame:
        """
        Generate a dataframe with the row representing each possible path.
        Arguments:
            save : OPTIONAL : If you wish to save it with the title used by the field group.
                save as csv with the title used. Not title, used "unknown_fieldGroup_" + timestamp.
            description : OPTIONAL : If you want to have the description used (default False)
            xdmType : OPTIONAL : If you want to retrieve the xdm Data Type (default False)
            required : OPTIONAL : If you want to have the required field in the dataframe (default False)
        """
        definition = self.dataType.get('definitions',{})
        if definition == {}:
            definition = self.dataType.get('properties',{})
        data = self.__transformationDF__(definition,description=description,xdmType=xdmType,queryPath=queryPath,required=required)
        df = pd.DataFrame(data)
        df['origin'] = 'self'
        if len(self.dataTypes)>0:
            paths = self.getDataTypePaths()
            for path,dataElementId in paths.items():
                tmp_dtManager = self.getDataTypeManager(dataElementId)
                df_dataType = tmp_dtManager.to_dataframe(queryPath=queryPath,description=description,xdmType=xdmType,required=required)
                df_dataType['path'] = df_dataType['path'].apply(lambda x : f"{path}.{x}")
                df_dataType['origin'] = 'external'
                df = pd.concat([df,df_dataType],axis=0,ignore_index=True)
        df = df.sort_values(by=['path'],ascending=[True]) ## sort the dataframe
        if save:
            title = self.dataType.get('title',f'unknown_dataType_{str(int(time.time()))}')
            df.to_csv(f"{title}.csv",index=False)
        return df
    
    def to_xdm(self)->dict:
        """
        Return the Data Type definition as XDM
        """
        return self.dataType
    
    def updateDataType(self)->dict:
        """
        Update the Data Type with the modification done before. 
        """
        if self.schemaAPI is None:
            raise Exception('Require a schema API connection. Pass the instance of a Schema class or import a configuration file.')
        res = self.schemaAPI.putDataType(self.dataType['meta:altId'],self.to_xdm())
        if 'status' in res.keys():
            if res['status'] == 400:
                print(res['title'])
                return res
            else:
                return res
        self.schema = res
        self.__setAttributes__(self.dataType)
        return res
    
    def createDataType(self)->dict:
        """
        Use the POST method to create the Data Type in the organization.
        """
        if self.schemaAPI is None:
            Exception('Require a schema API connection. Pass the instance of a Schema class or import a configuration file.')
        res = self.schemaAPI.createDataType(self.to_xdm())
        if 'status' in res.keys():
            if res['status'] >= 400:
                print(res['title'])
                return res
            else:
                return res
        self.dataType = res
        self.STATE = "EXISTING"
        self.__setAttributes__(self.dataType)
        return res
    
    def importDataTypeDefinition(self,datatype:Union[pd.DataFrame,str],sep:str=',',sheet_name:str=None)->None:
        """
        Importing the flat representation of the data type. It could be a dataframe or a CSV file containing the data type element.
        Argument:
            datatype : REQUIRED : The dataframe or csv of the data type
                It needs to contains the following columns : "path", "xdmType"
            sep : OPTIONAL : In case your CSV is separated by something else than comma. Default (',')
            sheet_name : OPTIONAL : In case you are uploading an Excel, you need to provide the sheet name
        """
        if self.EDITABLE != True:
            raise Exception(f'The field group {self.title} cannot be edited (EDITABLE == False). Only Title and Description can be changed via descriptors on the schemas')
        if type(datatype) == str:
            if '.csv' in datatype:
                df_import = pd.read_csv(datatype,sep=sep)
            if '.xlsx' in datatype:
                if sheet_name is None:
                    raise ImportError("You need to pass a sheet name to use Excel")
                df_import = pd.read_excel(datatype,sheet_name=sheet_name)
        elif type(datatype) == pd.DataFrame:
            df_import = datatype.copy()
        if 'path' not in df_import.columns or 'xdmType' not in df_import.columns:
            raise AttributeError("missing a column [xdmType, path] in your fieldgroup")
        df_import = df_import[~(df_import.duplicated('path'))].copy() ## removing duplicated paths
        df_import = df_import[~(df_import['path']==self.tenantId)].copy() ## removing tenant field
        df_import = df_import.fillna('')
        if 'title' not in df_import.columns:
            df_import['title'] = df_import['path'].apply(lambda x : x.split('.')[-1])
        if 'description' not in df_import.columns:
            df_import['description'] = ""
        df_import['pathDot'] = df_import['path'].str.count(r'\.')
        df_import = df_import.sort_values(['pathDot'])##sorting creation of objects
        for index, row in df_import.iterrows():
            #if 'error' in res.keys():
            path = row['path']
            typeElement = row['xdmType']
            if path.endswith("[]"):
                clean_path = self.__cleanPath__(row['path'])
                self.addField(clean_path,typeElement,title=row['title'],description=row['description'],array=True)
            elif path.endswith("[]{}"):
                clean_path = self.__cleanPath__(row['path'])
                self.addField(clean_path,'array',title=row['title'],description=row['description'])
            else:
                clean_path = self.__cleanPath__(row['path'])
                self.addField(clean_path,typeElement,title=row['title'],description=row['description'])
        return self