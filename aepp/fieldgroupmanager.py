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
import time, re
import pandas as pd
import json
from .configs import ConnectObject
from .datatypemanager import DataTypeManager
from aepp.schema import Schema
from aepp import som

class FieldGroupManager:
    """
    Class that reads and generate custom field groups
    """

    def __init__(self,
                fieldGroup:Union[dict,str]=None,
                title:str=None,
                fg_class:list=["experienceevent","profile"],
                schemaAPI:'Schema'=None,
                config: Union[dict,ConnectObject] = aepp.config.config_object,
                description:str="powered by aepp",
                full:bool=None,
                )->None:
        """
        Instantiator for field group creation.
        Arguments:
            fieldGroup : OPTIONAL : the field group definition as dictionary OR the $id/altId to access it.
                If you pass the $id or altId, you should pass the schemaAPI instance or have uploaded a configuration file.
            title : OPTIONAL : If you want to name the field group.
            fg_class : OPTIONAL : the class that will support this field group.
                by default events and profile, possible value : "record"
            schemaAPI : OPTIONAL : The instance of the Schema class. Provide a way to connect to the API.
            config : OPTIONAL : The config object in case you want to override the configuration.
            description : OPTIONAL : if you want to have a description.
            full : OPTIONAL : Capability to force the full definition to be downloaded or not
        """
        self.EDITABLE = False
        self.STATE = "EXISTING"
        self.fieldGroup = {}
        self.dataTypes = {}
        self.dataTypeManagers = {} 
        self.requiredFields = set()
        if schemaAPI is not None and type(schemaAPI) == Schema:
            self.schemaAPI = schemaAPI
        else:
            self.schemaAPI = Schema(config=config)
        self.tenantId = f"_{self.schemaAPI.getTenantId()}"
        if fieldGroup is not None:
            if type(fieldGroup) == dict:
                if fieldGroup.get("meta:resourceType",None) == "mixins":
                    if fieldGroup.get('definitions',None) is not None:
                        if 'mixins' in fieldGroup.get('$id') and self.tenantId[1:] in fieldGroup.get('$id'):
                            self.fieldGroup = self.schemaAPI.getFieldGroup(fieldGroup['$id'],full=False)

                            if '/datatypes/' in str(self.fieldGroup): ## if custom datatype used in Field Group
                                dataTypeSearch = f"(https://ns.adobe.com/{self.tenantId[1:]}/datatypes/[0-9a-z]+?)'"
                                dataTypes = re.findall(dataTypeSearch,str(self.fieldGroup))
                                for dt in dataTypes:
                                    dt_manager = self.schemaAPI.DataTypeManager(dt)
                                    self.dataTypes[dt_manager.id] = dt_manager.title
                                    self.dataTypeManagers[dt_manager.title] = dt_manager
                                if full:
                                    self.fieldGroup = self.schemaAPI.getFieldGroup(self.fieldGroup['$id'],full=True)
                                else:
                                    self.EDITABLE = True
                            else:
                                self.EDITABLE = True
                        else:
                            tmp_def = self.schemaAPI.getFieldGroup(fieldGroup['$id'],full=True) ## handling OOTB mixins
                            tmp_def['definitions'] = tmp_def['properties']
                            self.fieldGroup = tmp_def
                    else:
                        self.fieldGroup = self.schemaAPI.getFieldGroup(fieldGroup['$id'],full=False)
            elif type(fieldGroup) == str:
                if self.schemaAPI is None:
                    raise Exception("You try to retrieve the fieldGroup definition from the id, but no API has been passed in the schemaAPI parameter.")
                if 'mixins' in fieldGroup and ((fieldGroup.startswith('https:') and self.tenantId[1:] in fieldGroup) or fieldGroup.startswith(f'{self.tenantId}.')):
                    self.fieldGroup = self.schemaAPI.getFieldGroup(fieldGroup,full=False)
                    if '/datatypes/' in str(self.fieldGroup): ## if custom datatype used in Field Groupe
                        dataTypeSearch = f"(https://ns.adobe.com/{self.tenantId[1:]}/datatypes/[0-9a-z]+?)'"
                        dataTypes = re.findall(dataTypeSearch,str(self.fieldGroup))
                        for dt in dataTypes:
                            dt_manager = self.schemaAPI.DataTypeManager(dt)
                            self.dataTypes[dt_manager.id] = dt_manager.title
                            self.dataTypeManagers[dt_manager.title] = dt_manager
                        if full:
                            self.fieldGroup = self.schemaAPI.getFieldGroup(self.fieldGroup['$id'],full=True)
                        else:
                            self.EDITABLE = True
                    else:
                        self.EDITABLE = True
                else: ## handling default mixins
                    tmp_def = self.schemaAPI.getFieldGroup(fieldGroup,full=True) ## handling default mixins
                    self.fieldGroup = tmp_def
            else:
                raise ValueError("the element pass is not a field group definition")
        else:
            self.EDITABLE = True
            self.STATE = "NEW"
            self.fieldGroup = {
                "title" : "",
                "meta:resourceType":"mixins",
                "description" : description,
                "type": "object",
                "definitions":{
                    "customFields":{
                        "type" : "object",
                        "properties":{
                            self.tenantId:{
                                "properties":{},
                                "type" : "object"
                            },
                        }
                    },
                    "property":{
                        "type" : "object",
                        "properties":{
                            self.tenantId:{
                                "properties":{},
                                "type" : "object"
                            },
                        }
                    },
                },
                'allOf':[{
                    "$ref": "#/definitions/customFields",
                    "type": "object"
                },
                {
                    "$ref": "#/definitions/property",
                    "type": "object"
                }],
                "meta:intendedToExtend":[],
                "meta:containerId": "tenant",
                "meta:tenantNamespace": self.tenantId,
            }
            if self.fieldGroup.get("meta:intendedToExtend") == []:
                for cls in fg_class:
                    if 'experienceevent' in cls or "https://ns.adobe.com/xdm/context/experienceevent" ==cls:
                        self.fieldGroup["meta:intendedToExtend"].append("https://ns.adobe.com/xdm/context/experienceevent")
                    elif "profile" in cls or "https://ns.adobe.com/xdm/context/profile" == cls:
                        self.fieldGroup["meta:intendedToExtend"].append("https://ns.adobe.com/xdm/context/profile")
                    elif "record" in cls or "https://ns.adobe.com/xdm/data/record" == cls:
                        self.fieldGroup["meta:intendedToExtend"].append("https://ns.adobe.com/xdm/context/profile")
                    else:
                        self.fieldGroup["meta:intendedToExtend"].append(cls)
        if len(self.fieldGroup.get('allOf',[]))>1:
            ### handling the custom field group based on existing ootb field groups
            for element in self.fieldGroup.get('allOf'):
                if element.get('$ref') != '#/definitions/customFields' and element.get('$ref') != '#/definitions/property':
                    additionalDefinition = self.schemaAPI.getFieldGroup(element.get('$ref'),full=True)
                    self.fieldGroup['definitions'] = self.__simpleDeepMerge__(self.fieldGroup['definitions'],additionalDefinition.get('properties'))
        self.__setAttributes__(self.fieldGroup)
        if title is not None:
            self.fieldGroup['title'] = title
            self.title = title
        
    
    def __setAttributes__(self,fieldGroup:dict)->None:
        uniqueId = fieldGroup.get('id',str(int(time.time()*100))[-7:])
        self.title = fieldGroup.get('title',f'unknown:{uniqueId}')
        self.description = fieldGroup.get('description','')
        if self.fieldGroup.get('$id',False):
            self.id = self.fieldGroup.get('$id')
        if self.fieldGroup.get('meta:altId',False):
            self.altId = self.fieldGroup.get('meta:altId')
        self.classIds = self.fieldGroup.get('meta:intendedToExtend')
    
    def __str__(self)->str:
        return json.dumps(self.fieldGroup,indent=2)
    
    def __repr__(self)->dict:
        return json.dumps(self.fieldGroup,indent=2)
    
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

    def __transformationDF__(self,mydict:dict=None,dictionary:dict=None,path:str=None,queryPath:bool=False,description:bool=False,xdmType:bool=False,required:bool=False)->dict:
        """
        Transform the current XDM schema to a dictionary.
        Arguments:
            mydict : the fieldgroup
            dictionary : the dictionary that gather the paths
            path : path that is currently being developed
            queryPath: boolean to tell if we want to add the query path
            description : boolean to tell if you want to retrieve the description
            xdmType : boolean to know if you want to retrieve the xdm Type
            required : boolean to know if you want to retrieve the required field
        """
        if dictionary is None:
            dictionary = {'path':[],'type':[],'title':[]}
            if queryPath:
                dictionary['querypath'] = []
            if description:
                dictionary['description'] = []
            if xdmType:
                dictionary['xdmType'] = []
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
                        if queryPath:
                            dictionary["querypath"].append(self.__cleanPath__(tmp_path))
                        if description:
                            dictionary["description"].append(f"{mydict[key].get('description','')}")
                        if xdmType:
                            dictionary["xdmType"].append(f"{mydict[key].get('meta:xdmType')}")
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
                        self.__transformationDF__(properties,dictionary,tmp_path,queryPath,description,xdmType,required)
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
                        if queryPath and tmp_path is not None:
                            dictionary["querypath"].append(self.__cleanPath__(tmp_path))
                        if description and tmp_path is not None:
                            dictionary["description"].append(mydict[key].get('description',''))
                        if xdmType:
                            dictionary["xdmType"].append(f"{mydict[key].get('meta:xdmType')}")
                        if required:
                            if len(mydict[key].get('required',[])) > 0:
                                for elRequired in mydict[key].get('required',[]):
                                    if tmp_path is not None:
                                        tmp_reqPath = f"{tmp_path}.{elRequired}"
                                    else:
                                        tmp_reqPath = f"{elRequired}"
                                    self.requiredFields.add(tmp_reqPath)
                        self.__transformationDF__(levelProperties,dictionary,tmp_path,queryPath,description,xdmType,required)
                    else: ## simple arrays
                        if path is None:
                            finalpath = f"{key}[]"
                        else:
                            finalpath = f"{path}.{key}[]"
                        dictionary["path"].append(finalpath)
                        dictionary["type"].append(f"{mydict[key]['items'].get('type')}[]")
                        dictionary["title"].append(f"{mydict[key].get('title')}")
                        if queryPath and finalpath is not None:
                            dictionary["querypath"].append(self.__cleanPath__(finalpath))
                        if description and finalpath is not None:
                            dictionary["description"].append(mydict[key].get('description',''))
                        if xdmType:
                            dictionary["xdmType"].append(mydict[key]['items'].get('meta:xdmType',''))
                        if required:
                            if len(mydict[key].get('required',[])) > 0:
                                for elRequired in mydict[key].get('required',[]):
                                    if tmp_path is not None:
                                        tmp_reqPath = f"{tmp_path}.{elRequired}"
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
                    if queryPath and finalpath is not None:
                        dictionary["querypath"].append(self.__cleanPath__(finalpath))
                    if description :
                        dictionary["description"].append(mydict[key].get('description',''))
                    if xdmType :
                        dictionary["xdmType"].append(mydict[key].get('meta:xdmType',''))
                    if required:
                        if len(mydict[key].get('required',[])) > 0:
                            for elRequired in mydict[key].get('required',[]):
                                if finalpath is not None:
                                    tmp_reqPath = f"{finalpath}.{elRequired}"
                                else:
                                    tmp_reqPath = f"{elRequired}"
                                self.requiredFields.add(tmp_reqPath)

        return dictionary
    
    def __setField__(self,completePathList:list=None,fieldGroup:dict=None,newField:str=None,obj:dict=None)->dict:
        """
        Create a field with the attribute provided
        Arguments:
            completePathList : list of path to use for creation of the field.
            fieldGroup : the self.fieldgroup attribute
            newField : name of the new field to create
            obj : the object associated with the new field
        """
        foundFlag = False ## Flag to set if the operation has been realized or not
        lastField = completePathList[-1] ## last field where to put the new object.
        fieldGroup = deepcopy(fieldGroup)
        for key in fieldGroup:
            level = fieldGroup.get(key,None)
            if type(level) == dict and key in completePathList:
                if 'properties' in level.keys():
                    if key != lastField:
                        res,foundFlag = self.__setField__(completePathList,fieldGroup[key]['properties'],newField,obj)
                        fieldGroup[key]['properties'] = res
                    else:
                        if newField in fieldGroup[key]['properties'].keys():
                            fieldGroup[key]['properties'][newField]['title'] = obj["title"]
                            fieldGroup[key]['properties'][newField]['description'] = obj.get("description","")
                        else:
                            fieldGroup[key]['properties'][newField] = obj
                        foundFlag = True
                        return fieldGroup,foundFlag
                elif 'items' in level.keys():
                    if 'properties' in  fieldGroup[key].get('items',{}).keys():
                        if key != lastField:
                            res, foundFlag = self.__setField__(completePathList,fieldGroup[key]['items']['properties'],newField,obj)
                            fieldGroup[key]['items']['properties'] = res
                        else:
                            if newField in fieldGroup[key]['items']['properties'].keys():
                                fieldGroup[key]['items']['properties'][newField]['title'] = obj['title']
                                fieldGroup[key]['items']['properties'][newField]['description'] = obj['description']
                            else:
                                fieldGroup[key]['items']['properties'][newField] = obj
                            foundFlag = True
                            return fieldGroup,foundFlag
        return fieldGroup,foundFlag
    
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
        return deepcopy(string.replace('[','').replace(']','').replace("{",'').replace('}',''))
    
    def setTitle(self,title:str=None)->None:
        """
        Set a name for the Field Group.
        Arguments:
            title : REQUIRED : a string to be used for the title of the FieldGroup
        """
        if title is None:
            raise ValueError('title must be provided')
        self.fieldGroup['title'] = title
        self.title = title
        return None
    
    def setDescription(self,description:str=None)->None:
        """
        Set the description to the Field Group.
        Argument:
            description : REQUIRED : The description to be added
        """
        self.fieldGroup['description'] = description
        self.description = description

    def updateClassSupported(self,classIds:list=None)->None:
        """
        Update the "meta:intendedToExtend" attribute of the Field Group definition.
        Arguments: 
            classIds : REQUIRED : A list of class ID to support for that field group
        """
        if classIds is None or type(classIds) != list:
            raise ValueError("Require a list of class ids")
        self.fieldGroup["meta:intendedToExtend"] = classIds

    def getField(self,path:str)->dict:
        """
        Returns the field definition you want want to obtain.
        Arguments:
            path : REQUIRED : path with dot notation to which field you want to access
        """
        definition = self.fieldGroup.get('definitions',self.fieldGroup.get('properties',{}))
        data = self.__accessorAlgo__(definition,path)
        return data

    def searchField(self,string:str,partialMatch:bool=True,caseSensitive:bool=False)->list:
        """
        Search for a field name based the string passed.
        By default, partial match is enabled and allow case sensitivity option.
        Arguments:
            string : REQUIRED : the string to look for for one of the field
            partialMatch : OPTIONAL : if you want to look for complete string or not. (default True)
            caseSensitive : OPTIONAL : if you want to compare with case sensitivity or not. (default False)
        """
        definition = self.fieldGroup.get('definitions',self.fieldGroup.get('properties',{}))
        data = self.__searchAlgo__(definition,string,partialMatch,caseSensitive)
        return data
    
    def searchAttribute(self,attr:dict=None,regex:bool=False,extendedResults:bool=False,joinType:str='outer', **kwargs)->list:
        """
        Search for an attribute on the field of the field groups.
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
        definition = self.fieldGroup.get('definitions',self.fieldGroup.get('properties',{}))
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
        Return the operation to be used on the field group with the Patch method (patchFieldGroup), based on the element passed in argument.
        Arguments:
            path : REQUIRED : path with dot notation where you want to create that new field.
                In case of array of objects, use the "[]{}" notation
            dataType : REQUIRED : the field type you want to create
                A type can be any of the following: "string","boolean","double","long","integer","int","number","short","byte","date","datetime","date-time","boolean","object","array","dataType"
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
            raise Exception("The Field Group is not Editable via Field Group Manager")
        typeTyped = ["string","boolean","double","long","integer","int","number","short","byte","date","datetime","date-time","boolean","object","array","dataType"]
        dataType = dataType.replace('[]','')
        if dataType not in typeTyped:
            raise TypeError(f'Expecting one of the following type : "string","boolean","double","long","int,"integer","short","byte","date","datetime","date-time","boolean","object","dataType". Got {dataType}')
        if dataType == "dataType" and ref is None:
            raise ValueError("Required a reference to be passed when selecting 'dataType' type of data.")
        if dataType == 'object' and objectComponents is None:
            raise AttributeError('Require a dictionary providing the object component')       
        if title is None:
            title = self.__cleanPath__(path.split('.').pop())
        if title == 'items' or title == 'properties':
            raise Exception('"item" and "properties" are 2 reserved keywords')
        pathSplit = path.split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        completePath = ['definitions',kwargs.get('defaultPath','customFields'),'properties']
        for p in pathSplit:
            if '[]{}' in p:
                completePath.append(self.__cleanPath__(p))
                completePath.append('items')
                completePath.append('properties')
            else:
                completePath.append(self.__cleanPath__(p))
                completePath.append('properties')
        if dataType == "dataType":
            completePath.pop() ## removing last part
        finalPath = '/' + '/'.join(completePath)
        operation = [{
            "op" : "add",
            "path" : finalPath,
            "value": {}
        }]
        if dataType != 'object' and dataType != "array" and dataType != "dataType":
            if array: # array argument set to true
                operation[0]['value']['type'] = 'array'
                operation[0]['value']['items'] = self.__transformFieldType__(dataType)
            else:
                operation[0]['value'] = self.__transformFieldType__(dataType)
        else: 
            if dataType == "object":
                operation[0]['value']['type'] = self.__transformFieldType__(dataType)
                operation[0]['value']['properties'] = {key:self.__transformFieldType__(value) for key, value in zip(objectComponents.keys(),objectComponents.values())}
            elif dataType == "dataType":
                operation[0]['value']['type'] = "object"
                operation[0]['value']['$ref'] = ref
                if array:
                    del operation[0]['value']['$ref']
                    operation[0]['value']['items'] = {
                        "$ref" : ref,
                        "type" : "object"
                    }
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
        Add the field to the existing fieldgroup definition.
        Returns False when the field could not be inserted.
        Arguments:
            path : REQUIRED : path with dot notation where you want to create that new field. New field name should be included.
            dataType : REQUIRED : the field type you want to create
                A type can be any of the following: "string","boolean","double","long","integer","int","number","short","byte","date","datetime","date-time","boolean","object","array","dataType"
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
            raise Exception("The Field Group is not Editable via Field Group Manager")
        if path is None:
            raise ValueError("path must provided")
        dataType = dataType.replace('[]','')
        typeTyped = ["string","boolean","double","long","int","integer","number","short","byte","date","datetime",'date-time',"boolean","object",'array','dataType']
        if dataType not in typeTyped:
            raise TypeError(f'Expecting one of the following type : "string","boolean","double","long","int","integer","short","byte","date","datetime","date-time","boolean","object","byte","dataType". Got {dataType}')
        if dataType == "dataType" and ref is None:
            raise ValueError("Required a reference to be passed when selecting 'dataType' type of data.")
        if title is None:
            title = self.__cleanPath__(path.split('.').pop())
        if title == 'items' or title == 'properties':
            raise Exception('"items" and "properties" are 2 reserved keywords')
        pathSplit = self.__cleanPath__(path).split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        newField = pathSplit.pop()
        description = kwargs.get("description",'')
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
            obj['title'] = title
            obj["description"] = description,
            if type(obj["description"]) == tuple:
                obj["description"] = obj["description"][0]
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
        if 'definitions' not in self.fieldGroup.keys():
            if 'properties' in self.fieldGroup.keys():
                definition,foundFlag = self.__setField__(pathSplit, self.fieldGroup.get('properties',{}),newField,obj)
                if foundFlag == False:
                    return False
                else:
                    self.fieldGroup['properties'] = definition
                    return self.fieldGroup
        else:
            definition,foundFlag = self.__setField__(completePath, self.fieldGroup.get('definitions'),newField,obj)
        if foundFlag == False:
            completePath:list[str] = ['property'] + pathSplit ## trying via property
            definition,foundFlag = self.__setField__(completePath, self.fieldGroup.get('property',{}),newField,obj)
            if foundFlag == False:
                return False
            else:
                self.fieldGroup['definitions'] = definition
                return self.fieldGroup
        else:
            self.fieldGroup['definitions'] = definition
            return self.fieldGroup
        
    def removeField(self,path:str)->dict:
        """
        Remove a field from the definition based on the path provided.
        NOTE: A path that has received data cannot be removed from a schema or field group.
        Argument:
            path : REQUIRED : The path to be removed from the definition.
        """
        if self.EDITABLE == False:
            raise Exception("The Field Group is not Editable via Field Group Manager")
        if path is None:
            raise ValueError('Require a path to remove it')
        pathSplit = self.__cleanPath__(path).split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        success = False
        ## Try customFields
        completePath:list[str] = ['customFields'] + pathSplit
        success = self.__removeKey__(completePath,self.fieldGroup.get('definitions'))
        ## Try property
        if success == False:
            completePath:list[str] = ['property'] + pathSplit
            success = self.__removeKey__(completePath,self.fieldGroup['definitions'])
        return success

    def to_dict(self,typed:bool=True,save:bool=False)->dict:
        """
        Generate a dictionary representing the field group constitution
        Arguments:
            typed : OPTIONAL : If you want the type associated with the field group to be given.
            save : OPTIONAL : If you wish to save the dictionary in a JSON file
        """
        definition = self.fieldGroup.get('definitions',self.fieldGroup.get('properties',{}))
        data = self.__transformationDict__(definition,typed)
        mySom = som.Som(data)
        if len(self.dataTypes)>0:
            paths = self.getDataTypePaths()
            for path,dataElementId in paths.items():
                dict_dataType = self.getDataTypeManager(dataElementId).to_dict()
                clean_path = path.replace('[]{}','.[0]')
                mySom.assign(clean_path,dict_dataType)
        if save:
            filename = self.fieldGroup.get('title',f'unknown_fieldGroup_{str(int(time.time()))}')
            aepp.saveFile(module='schema',file=mySom.to_dict(),filename=f"{filename}.json",type_file='json')
        return mySom.to_dict()
    
    def to_som(self)->'som.Som':
        """
        Generate a SOM object representing the field group constitution
        """
        return som.Som(self.to_dict())

    def to_dataframe(self,
                     save:bool=False,
                     queryPath:bool=False,
                     description:bool=False,
                     xdmType:bool=True,
                     editable:bool=False,
                     excludeObjects:bool=False,
                     required:bool=False)->pd.DataFrame:
        """
        Generate a dataframe with the row representing each possible path.
        Arguments:
            save : OPTIONAL : If you wish to save it with the title used by the field group.
                save as csv with the title used. Not title, used "unknown_fieldGroup_" + timestamp.
            queryPath : OPTIONAL : If you want to have the query path to be used.
            description : OPTIONAL : If you want to have the description used (default False)
            xdmType : OPTIONAL : If you want to have the xdmType also returned (default True)
            editable : OPTIONAL : If you can manipulate the structure of the field groups (default False)
            excludeObjects : OPTIONAL : Remove the fields that are noted down as object so only fields containing data are returned.
            required : OPTIONAL : If you want to have the required field in the dataframe (default False)
        """
        definition = self.fieldGroup.get('definitions',self.fieldGroup.get('properties',{}))
        data = self.__transformationDF__(definition,queryPath=queryPath,description=description,xdmType=xdmType,required=required)
        df = pd.DataFrame(data)
        df = df[~df.path.duplicated()].copy() ## dedup the paths
        df = df[~(df['path']==self.tenantId)].copy()## remove the root
        if required:
            if(len(self.requiredFields) > 0):
                df['required'] = df['path'].isin(self.requiredFields)
            else:
                df['required'] = False
        df['origin'] = 'fieldGroup'
        if len(self.dataTypes)>0:
            paths = self.getDataTypePaths()
            for path,dataElementId in paths.items():
                tmp_dtManager = self.getDataTypeManager(dataElementId)
                df_dataType = tmp_dtManager.to_dataframe(queryPath=queryPath,description=description,xdmType=xdmType,required=required)
                list_required = tmp_dtManager.requiredFields
                df_dataType['path'] = df_dataType['path'].apply(lambda x : f"{path}.{x}")
                if required:
                    if len(list_required) > 0:
                        list_required = [f"{path}.{x}" for x in list_required]
                        df_dataType['required'] = df_dataType['path'].isin(list_required)
                    else:
                        df_dataType['required'] = False
                df_dataType['origin'] = 'dataType'
                df = pd.concat([df,df_dataType],axis=0,ignore_index=True)
        df = df.sort_values(by=['path'],ascending=[True]) ## sort the dataframe
        if editable:
            df['editable'] = self.EDITABLE
        if excludeObjects:
            df = df[df['type'] != 'object'].copy()
        if save:
            title = self.fieldGroup.get('title',f'unknown_fieldGroup_{str(int(time.time()))}')
            df.to_csv(f"{title}.csv",index=False)
        return df
    
    def to_xdm(self)->dict:
        """
        Return the fieldgroup definition as XDM
        """
        return self.fieldGroup
    
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
            if kwargs.get('som_compatible',False):
                paths = [path.replace('{}','').replace('[]','.[0]') for path in paths] ## compatible with SOM later
            for path in paths:
                dict_results[path] = dt_id
        return dict_results
    

    def patchFieldGroup(self,operations:list=None)->dict:
        """
        Patch the field group with the given operation.
        Arguments:
            operation : REQUIRED : The list of operation to realise
                    Possible operations : add, remove, and replace
        """
        if self.EDITABLE == False:
            raise Exception("The Field Group is not Editable via Field Group Manager")
        if operations is None or type(operations) != list:
            raise ValueError('Require a list of operations')
        if self.schemaAPI is None:
            Exception('Require a schema API connection. Pass the instance of a Schema class or import a configuration file.')
        res = self.schemaAPI.patchFieldGroup(self.id,operations)
        if 'status' in res.keys():
            if res['status'] >= 400:
                print(res['title'])
                return res
            else:
                return res
        self.fieldGroup = res
        self.__setAttributes__(self.fieldGroup)
        return res
    
    def updateFieldGroup(self)->dict:
        """
        Use the PUT method to push the current field group representation to AEP via API request.
        """
        if self.EDITABLE == False:
            raise Exception("The Field Group is not Editable via Field Group Manager")
        if self.STATE == "NEW":
            raise Exception("The Field Group does not exist yet and therefore cannot be updated")
        if self.schemaAPI is None:
            Exception('Require a schema API connection. Pass the instance of a Schema class or import a configuration file.')
        res = self.schemaAPI.putFieldGroup(self.id,self.to_xdm())
        if 'status' in res.keys():
            if res['status'] >= 400:
                print(res['title'])
                return res
            else:
                return res
        self.fieldGroup = res
        self.__setAttributes__(self.fieldGroup)
        return res
    
    def createFieldGroup(self)->dict:
        """
        Use the POST method to create the field group in the organization.
        """
        if self.STATE != "NEW":
            raise Exception("The Field Group already exists and cannot be created again")
        if self.schemaAPI is None:
            raise Exception('Require a schema API connection. Pass the instance of a Schema class or import a configuration file.')
        res = self.schemaAPI.createFieldGroup(self.to_xdm())
        if 'status' in res.keys():
            if res['status'] >= 400:
                print(res['title'])
                return res
            else:
                return res
        self.fieldGroup = res
        self.__setAttributes__(self.fieldGroup)
        self.STATE = "EXISTING"
        return res

    def importFieldGroupDefinition(self,fieldgroup:Union[pd.DataFrame,str],sep:str=',',sheet_name:str=None,title:str=None)->None:
        """
        Importing the flat representation of the field group. It could be a dataframe or a CSV file containing the field group element.
        The field group needs to be editable to be updated.
        Argument:
            fieldGroup : REQUIRED : The dataframe or csv of the field group
                It needs to contains the following columns : "path", "xdmType", "fieldGroup"
            sep : OPTIONAL : In case your CSV is separated by something else than comma. Default (',')
            sheet_name : OPTIONAL : In case you are uploading an Excel, you need to provide the sheet name
            title : OPTIONAL : If you want to set a title for the field group. Default is the mode of the fieldGroup column.
        """
        if self.EDITABLE != True:
            raise Exception(f'The field group {self.title} cannot be edited (EDITABLE == False). Only Title and Description can be changed via descriptors on the schemas')
        if type(fieldgroup) == str:
            if '.csv' in fieldgroup:
                df_import = pd.read_csv(fieldgroup,sep=sep)
            if '.xls' in fieldgroup:
                if sheet_name is None:
                    raise ImportError("You need to pass a sheet name to use Excel")
                df_import = pd.read_excel(fieldgroup,sheet_name=sheet_name)
        elif type(fieldgroup) == pd.DataFrame:
            df_import = fieldgroup.copy()
        if 'path' not in df_import.columns or 'xdmType' not in df_import.columns or 'fieldGroup' not in df_import.columns:
            raise AttributeError("missing a column [xdmType, path, or fieldGroup] in your dataframe fieldgroup")
        df_import = df_import[~(df_import.duplicated('path'))].copy() ## removing duplicated paths
        df_import = df_import[~(df_import['path']==self.tenantId)].copy() ## removing tenant field
        df_import = df_import.fillna('')
        underscoreDF = df_import[df_import.path.str.contains(r'\._')].copy() ## special fields not supported
        if len(underscoreDF)>0:
            list_paths = underscoreDF['path'].to_list()
            objectRoots = set([p.split('.')[-2] for p in list_paths]) ## removing all objects using these fields
            print(f"{objectRoots} objects will not be supported in the field group manager setup. Handle them manually")
            for tobject in objectRoots: ## excluding the 
                df_import = df_import[~df_import.path.str.contains(tobject)].copy()
        if 'title' not in df_import.columns:
            df_import['title'] = df_import['path'].apply(lambda x : x.split('.')[-1])
        if 'description' not in df_import.columns:
            df_import['description'] = ""
        df_import['pathDot'] = df_import.path.str.count(r'\.')
        df_import = df_import.sort_values(['pathDot'])##sorting creation of objects
        for index, row in df_import.iterrows():
            #if 'error' in res.keys():
            path = row['path']
            clean_path = self.__cleanPath__(row['path'])
            typeElement = row['xdmType']
            if path.endswith("[]"):
                self.addField(clean_path,typeElement,title=row['title'],description=row['description'],array=True)
            elif path.endswith("[]{}"):
                self.addField(clean_path,'array',title=row['title'],description=row['description'])
            else:
                self.addField(clean_path,typeElement,title=row['title'],description=row['description'])
        if title is not None:
            self.setTitle(title)
        else:
            self.setTitle(df_import['fieldGroup'].mode().values[0])
        return self
    
    def getDescriptors(self)->list:
        """
        Get the descriptors of that schema
        """
        if self.STATE=="NEW" or self.id == "":
            raise Exception("Schema does not exist yet, there can not be a descriptor")    
        res = self.schemaAPI.getDescriptors(prop=f"xdm:sourceSchema=={self.id}")
        return res

    def createDescriptorOperation(self,descType:str=None,
                                  completePath:str=None,
                                  labels:list=None)->dict:
        """
        Support the creation of a descriptor operation for 'xdm:descriptorLabel' descriptor type. 
        Arguments:
            descType : REQUIRED : The type of descriptor to be created.
            completePath : REQUIRED : The path to be used for the descriptor.
            labels : OPTIONAL : A list of labels to be used for the descriptor.
        """
        if descType not in ['xdm:descriptorLabel']:
            raise ValueError('Type of descriptor not supported by Field Group Manager')
        if completePath is None:
            raise ValueError('Require a path to be used for the descriptor')
        if labels is None:
            raise Warning('No label provided. The descriptor will be created without any label')
        if descType == 'xdm:descriptorLabel':
            obj = {
                "@type": descType,
                "xdm:sourceSchema": self.id,
                "xdm:sourceVersion": 1,
                "xdm:sourceProperty": completePath,
                "xdm:labels": labels
            }
        return obj

    def createDescriptor(self,descriptor:dict=None)->None:
        """
        Create a descriptor attached to that class bsaed on the creatorDescriptor operation provided. 
        Arguments:
            descriptor : REQUIRED : The operation to add a descriptor to the schema.
        """
        if descriptor is None:
            raise ValueError('Require an operation to be used')
        res = self.schemaAPI.createDescriptor(descriptor)
        return res
    
    def updateDescriptor(self,descriptorId:str=None,descriptorObj:dict=None)->dict:
        """
        Update a descriptor with the put method. Wrap the putDescriptor method of the Schema class.
        Arguments:
            descriptorId : REQUIRED : The descriptor ID to be updated
            descriptorObj : REQUIRED : The new definition of the descriptor as a dictionary.
        """
        if descriptorId is None:
            raise ValueError("Require a Descriptor ID")
        if descriptorObj is None or type(descriptorObj) != dict:
            raise ValueError("Require a dictionary for the new definition")
        res = self.schemaAPI.putDescriptor(descriptorId, descriptorObj)
        return res