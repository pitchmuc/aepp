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
import json, re
import numpy as np
from .configs import ConnectObject
from aepp.schema import Schema
from aepp import som
from pathlib import Path
from io import FileIO
from tempfile import TemporaryDirectory
from datamodel_code_generator import InputFileType, generate
from datamodel_code_generator import DataModelType
from aepp.manager_utils import __transformationDict__,__simpleDeepMerge__,__cleanPath__,__accessorAlgo__,__searchAlgo__,__searchAttrAlgo__

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
                localFolder:str|list|None=None,
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
        Possible kwargs:
            tenantId : OPTIONAL : If you want to specific the tenantId for the data type manager (if not provided, it will be retrieved from the schemaAPI or the local folder)
            retry : int to set the number of retry in case of connection error for the schema module (default is the retry number set for the instance)
        """
        self.localfolder = None
        self.STATE = "EXISTING"
        self.dataType = {}
        self.dataTypes = {}
        self.dataTypeManagers = {}
        self.schemaAPI = None
        self.retry = kwargs.get("retry", aepp.config.config_object.get("retry",1))
        self.id = None
        self.requiredFields = set()
        if schemaAPI is not None and type(schemaAPI) == Schema:
            self.schemaAPI = schemaAPI
        elif config is not None and localFolder is None:
            self.schemaAPI = Schema(config=config,retry=self.retry)
        elif localFolder is not None:
            if isinstance(localFolder, str):
                self.localfolder = [Path(localFolder)]
            elif isinstance(localFolder, list):
                self.localfolder = [Path(folder) for folder in localFolder]
            self.datatypeFolder = [folder / 'datatype' for folder in self.localfolder]
            self.datatypeGlobalFolder = [folder / 'global' for folder in self.datatypeFolder]
            for folder in self.datatypeFolder+self.datatypeGlobalFolder:
                if folder.exists() == False:
                    folder.mkdir(exist_ok=True)
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
        elif self.localfolder is not None:
            for folder in self.localfolder:
                if Path(folder / 'config.json').exists():
                    config_json = json.load(FileIO(folder / 'config.json'))
                    if config_json.get('tenantId',None) is not None:
                        self.tenantId = config_json.get('tenantId')
                        break
        else:
            self.tenantId = "  "
        if type(dataType) == dict:
            self.dataType = dataType
            if self.tenantId[1:] in self.dataType['$id']:
                if self.schemaAPI is not None:
                    self.dataType = self.schemaAPI.getDataType(dataType['$id'],full=False)
                elif self.localfolder is not None:
                    found = False
                    for folder in self.datatypeFolder:
                        for dataTypeFile in folder.glob(f"*.json"):
                            tmp_def = json.load(FileIO(dataTypeFile))
                            if tmp_def.get('$id') == dataType.get('$id') or tmp_def.get('meta:altId') == dataType.get('meta:altId'):
                                self.dataType = tmp_def
                                found = True
                                break
                        if found:
                            break
            else:
                if self.schemaAPI is not None:
                    self.dataType = self.schemaAPI.getDataType(dataType['$id'],full=True)
                elif self.localfolder is not None:
                    found = False
                    for folder in self.datatypeGlobalFolder:
                        for dataTypeFile in folder.glob("*.json"):
                            tmp_def = json.load(FileIO(dataTypeFile))
                            if tmp_def.get('$id') == dataType.get('$id') or tmp_def.get('meta:altId') == dataType.get('meta:altId') or tmp_def.get('title') == dataType.get('title'):   
                                self.dataType = tmp_def
                                found = True
                                break
                        if found:
                            break
        elif type(dataType) == str:
            if self.tenantId[1:] in dataType:
                if self.schemaAPI is not None:
                    self.dataType = self.schemaAPI.getDataType(dataType,full=False)
                    if self.dataType is None:
                        raise ValueError(f"Cannot find the data type with id {dataType} in the schema API.")
                elif self.localfolder is not None:
                    found = False
                    for folder in self.datatypeFolder:
                        for dataTypeFile in folder.glob("*.json"):
                            tmp_def = json.load(FileIO(dataTypeFile))
                            if tmp_def.get('$id') == dataType or tmp_def.get('meta:altId') == dataType or tmp_def.get('title') == dataType:
                                self.dataType = tmp_def
                                found = True
                                break
                        if found:
                            break
                else:
                    raise Exception("You try to retrieve the datatype definition from the id, but no API or localFolder has been passed as a parameter.")
            else:
                if self.schemaAPI is not None:
                    self.dataType = self.schemaAPI.getDataType(dataType,full=True)
                    if self.dataType is None:
                        raise ValueError(f"Cannot find the data type with id {dataType} in the schema API.")
                elif self.localfolder is not None:
                    found = False
                    for folder in self.datatypeGlobalFolder:
                        for dataTypeFile in folder.glob("*.json"):
                            tmp_def = json.load(FileIO(dataTypeFile))
                            if tmp_def.get('$id') == dataType or tmp_def.get('meta:altId') == dataType or tmp_def.get('title') == dataType:
                                self.dataType = tmp_def
                                found = True
                                break
                        if found:
                            break
                else:
                    raise Exception("You try to retrieve the datatype definition from the id, but no API or localFolder has been passed as a parameter.")
        else:
            self.STATE = "NEW"
            self.dataType = {
                "title" : "",
                "description":description,
                "type" : "object",
                "definitions":{
                    "customFields":{
                        "type" : "object",
                        "properties":{}
                        }
                },
                'allOf': [{'$ref': '#/definitions/customFields',
                    'type': 'object',
                    'meta:xdmType': 'object'}],
                'meta:extensible': True
            }
            if self.tenantId.strip() != "":
                self.dataType['meta:tenantNamespace'] = self.tenantId
        if '$ref' in str(self.dataType.get('definitions',self.dataType.get('properties',{}))) or '/datatype_name/' in str(self.dataType.get('definitions',self.dataType.get('properties',{}))) or 'meta:referencedFrom' in str(self.dataType.get('definitions',self.dataType.get('properties',{}))): ## if datatype used in data types
            dataTypeSearch_id = f"(https://ns.adobe.com/.+?)'"
            dataTypes_id = re.findall(dataTypeSearch_id,str(self.dataType.get('definitions',self.dataType.get('properties',{}))))
            dataTypeSearch_name = f"(https://[0-9A-Za-z.]+/datatype_name/[0-9a-z]+?)'"
            dataTypes_name = re.findall(dataTypeSearch_name,str(self.dataType.get('definitions',self.dataType.get('properties',{}))))
            metaRefSearch = f"'meta:referencedFrom': '(https://ns.adobe.com/.+?)'"
            dataType_MetaRef_name = re.findall(metaRefSearch,str(self.dataType.get('definitions',self.dataType.get('properties',{}))))
            locationSearch = f"(http://schema.org/.+?)'"
            dataType_Location_name = re.findall(locationSearch,str(self.dataType.get('definitions',self.dataType.get('properties',{}))))
            dataTypes = dataTypes_id + dataTypes_name + dataType_MetaRef_name + dataType_Location_name
            dataTypes = list(set(dataTypes))
            dataTypeManager_ids = list(set(self.getDataTypePaths(list_dt_ids=dataTypes).values()))
            if self.schemaAPI is not None:
                for dt in dataTypeManager_ids:
                    if dt == 'http://schema.org/GeoShape':
                        dt = '_schema.org.GeoShape'
                    elif dt == 'http://schema.org/GeoCoordinates':
                        dt = '_schema.org.GeoCoordinates'
                    elif dt == 'http://schema.org/GeoCircle':
                        dt = '_schema.org.GeoCircle'
                    if dt not in self.dataTypes.keys():
                        dt_manager = self.schemaAPI.DataTypeManager(dt,retry=self.retry)
                        self.dataTypes[dt_manager.id] = dt_manager.title
                        self.dataTypeManagers[dt_manager.title] = dt_manager
            elif self.localfolder is not None:
                for dt in dataTypeManager_ids: ## today only searching custom data types in local folder
                    if dt not in self.dataTypes.keys():
                        found = False
                        for folder in self.datatypeFolder:
                            for dataTypeFile in folder.glob("*.json"):
                                tmp_def = json.load(FileIO(dataTypeFile))
                                if tmp_def.get('$id') == dt or tmp_def.get('meta:altId') == dt or tmp_def.get('title') == dt:
                                    dt_manager = DataTypeManager(dataType=tmp_def,localFolder=self.localfolder,tenantId=self.tenantId,sandbox=self.sandbox,retry=self.retry)
                                    self.dataTypes[dt_manager.id] = dt_manager.title
                                    self.dataTypeManagers[dt_manager.title] = dt_manager
                                    found = True
                                    break
                            if found:
                                break
        if title is not None:
            self.dataType['title'] = title
            self.title = title
        else:
            self.title = self.dataType.get('title','unknown')
        self.EDITABLE = self.dataType.get('meta:extensible', False)
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
    
    def __transformationPydantic__(self,mydict:dict=None,dictionary:dict=None)->dict:
        """
        Transform the current XDM class to a dictionary compatible with pydantic.
        mydict : the class definition to traverse
        dictionary : the dictionary that gather the paths
        """
        if dictionary is None:
            dictionary = {
                'properties':{},
                'type':'object'
            }
            dictionary = dictionary['properties']
        else:
            dictionary = dictionary
        for key in mydict:
            if type(mydict[key]) == dict:
                if mydict[key].get('type') == 'object' or 'properties' in mydict[key].keys():
                    properties = mydict[key].get('properties',None)
                    if properties is not None:
                        if key != "property" and key != "customFields":
                            if key not in dictionary.keys():
                                dictionary[key] = {'properties':{}}
                            self.__transformationPydantic__(mydict[key]['properties'],dictionary=dictionary[key]['properties'])
                        else:
                            self.__transformationPydantic__(mydict[key]['properties'],dictionary=dictionary)
                elif mydict[key].get('type') == 'object' and 'additionalProperties' in mydict[key].keys():
                    properties = mydict[key].get('additionalProperties',{})
                    if properties.get('type') == 'array':
                        items = properties.get('items',{}).get('properties',None)
                        if items is not None:
                            dictionary[key] = {'properties':{'patternProperties':{"^.*$":{'items':{'properties':{},'type':'object'}, 'type':'array'}}},'type':'object'}
                            self.__transformationPydantic__(items,dictionary=dictionary[key]['properties']['patternProperties']["^.*$"]['items']['properties'])
                        else:
                            dictionary[key] = {'properties':{'patternProperties':{"^.*$":{'properties':{'additionalProperties':True},'type':'object'}, 'type':'object'}},'type':'object'}
                elif mydict[key].get('type') == 'array':
                    levelProperties = mydict[key]['items'].get('properties',None)
                    if levelProperties is not None:
                        dictionary[key] = {'type':'array','items':{'properties':{},'type':'object'}}
                        self.__transformationPydantic__(levelProperties,dictionary[key]['items']['properties'])
                    else:
                        if '$ref' in mydict[key]['items'].keys():
                            dictionary[key] = {'type':'array','items':{'properties':{},'type':'object'}}
                        else:
                            dictionary[key] = {'type':'array','items':{'type':mydict[key].get('items',{}).get('type','object')}}
                else:
                    myformat = None
                    mytype = mydict[key].get('type','object')
                    if mytype == "string":
                        if mydict[key].get('format',None) == 'date-time':
                            myformat = 'date-time'
                        elif mydict[key].get('format',None) == 'date':
                            myformat = 'date'
                        elif mydict[key].get('format',None) == 'uri-reference':
                            myformat = 'uri-reference'
                        elif mydict[key].get('format',None) == 'ipv4' or mydict[key].get('format',None) == 'ipv6':
                            myformat = mydict[key].get('format',None)
                    dictionary[key] = {'type':mytype}
                    if myformat is not None:
                        dictionary[key]['format'] = myformat
                    if mydict[key].get('enum',None) is not None:
                        dictionary[key]['enum'] = mydict[key].get('enum',None)
                    if mydict[key].get('minimum',None) is not None and mydict[key].get('maximum',None) is not None:
                        dictionary[key]['minimum'] = mydict[key].get('minimum')
                        dictionary[key]['maximum'] = mydict[key].get('maximum')
                    if mydict[key].get('pattern',None) is not None:
                        dictionary[key]['pattern'] = mydict[key].get('pattern')
        return dictionary

    def __transformationDF__(self,
                             mydict:dict=None,
                             dictionary:dict=None,
                             path:str=None,
                             queryPath:bool=False,
                             required:bool=False,
                             full:bool=False)->dict:
        """
        Transform the current XDM schema to a dictionary.
        Arguments:
            mydict : the fieldgroup
            dictionary : the dictionary that gather the paths
            path : path that is currently being developed
            queryPath: boolean to tell if we want to add the query path
            required : If you want to have the required field in the dataframe
            full : boolean to know if you want to retrieve all the information (minLength, etc)
        """
        if dictionary is None:
            dictionary = {'path':[],'type':[],'title':[],'description':[],'xdmType':[],'mapType':[]}
            if queryPath or full:
                dictionary['querypath'] = []
            if full:
                dictionary['minLength'] = []
                dictionary['maxLength'] = []
                dictionary['minimum'] = []
                dictionary['maximum'] = []
                dictionary['pattern'] = []
                dictionary['enumValues'] = []
                dictionary['enum'] = []
                dictionary['default'] = []
                dictionary['metaStatus'] = []
        else:
            dictionary = dictionary
        for key in mydict:
            if type(mydict[key]) == dict and mydict[key].get('meta:referencedFrom',None) is None: ## if the element is a reference, we skip it as it will be treated separately and avoid duplicates
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
                        dictionary["type"].append(f"{mydict[key].get('type','')}")
                        dictionary["title"].append(f"{mydict[key].get('title','')}")
                        dictionary["description"].append(f"{mydict[key].get('description','')}")
                        dictionary["xdmType"].append(f"{mydict[key].get('meta:xdmType','')}")
                        if mydict[key].get('meta:xdmType') == 'map':
                            dictionary["mapType"].append(f"{mydict[key].get('additionalProperties',{}).get('type','string')}")
                        else:
                            dictionary["mapType"].append(pd.NA)
                        if queryPath or full:
                            dictionary["querypath"].append(__cleanPath__(tmp_path))
                        if full:
                            dictionary['metaStatus'].append(mydict[key].get('meta:status',pd.NA))
                            dictionary['minLength'].append(mydict[key].get('minLength',np.nan))
                            dictionary['maxLength'].append(mydict[key].get('maxLength',np.nan))
                            dictionary['minimum'].append(mydict[key].get('minimum',np.nan))
                            dictionary['maximum'].append(mydict[key].get('maximum',np.nan))
                            dictionary['pattern'].append(mydict[key].get('pattern',pd.NA))
                            dictionary['default'].append(mydict[key].get('default',pd.NA))
                            enumValues = mydict[key].get('meta:enum',pd.NA)
                            dictionary['enumValues'].append(enumValues)
                            if len(mydict[key].get('enum',[])) > 0:
                                dictionary['enum'].append(True)
                            else:
                                dictionary['enum'].append(False)
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
                        self.__transformationDF__(properties,dictionary,tmp_path,queryPath,required,full=full)
                elif mydict[key].get('type') == 'array':
                    levelProperties = mydict[key]['items'].get('properties',None)
                    if levelProperties is not None: ## array of objects
                        if path is None:
                            tmp_path = f"{key}[]{{}}"
                        else :
                            tmp_path = f"{path}.{key}[]{{}}"
                        dictionary["path"].append(tmp_path)
                        dictionary["type"].append(f"{mydict[key].get('type','')}")
                        dictionary["title"].append(f"{mydict[key].get('title','')}")
                        dictionary["description"].append(mydict[key].get('description',''))
                        dictionary["xdmType"].append(f"{mydict[key].get('meta:xdmType','')}")
                        if mydict[key].get('meta:xdmType') == 'map':
                            dictionary["mapType"].append(f"{mydict[key].get('additionalProperties',{}).get('type','string')}")
                        else:
                            dictionary["mapType"].append(pd.NA)
                        if queryPath or full:
                            dictionary["querypath"].append(__cleanPath__(tmp_path))
                        if full:
                            dictionary['metaStatus'].append(mydict[key].get('meta:status',pd.NA))
                            dictionary['minLength'].append(mydict[key].get('minLength',np.nan))
                            dictionary['maxLength'].append(mydict[key].get('maxLength',np.nan))
                            dictionary['minimum'].append(mydict[key].get('minimum',np.nan))
                            dictionary['maximum'].append(mydict[key].get('maximum',np.nan))
                            dictionary['pattern'].append(mydict[key].get('pattern',pd.NA))
                            dictionary['default'].append(mydict[key].get('default',pd.NA))
                            enumValues = mydict[key].get('meta:enum',pd.NA)
                            dictionary['enumValues'].append(enumValues)
                            if len(mydict[key].get('enum',[])) > 0:
                                dictionary['enum'].append(True)
                            else:
                                dictionary['enum'].append(False)
                        if required:
                            if len(mydict[key].get('required',[])) > 0:
                                for elRequired in mydict[key].get('required',[]):
                                    if tmp_path is not None:
                                        tmp_reqPath = f"{tmp_path}.{elRequired}"
                                    else:
                                        tmp_reqPath = f"{elRequired}"
                                    self.requiredFields.add(tmp_reqPath)
                        self.__transformationDF__(levelProperties,dictionary,tmp_path,queryPath,required,full=full)
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
                        dictionary["title"].append(f"{mydict[key].get('title','')}")
                        dictionary["description"].append(mydict[key].get('description',''))
                        dictionary["xdmType"].append(mydict[key]['items'].get('meta:xdmType',''))
                        if mydict[key]['items'].get('meta:xdmType') == 'map':
                            dictionary["mapType"].append(f"{mydict[key]['items'].get('additionalProperties',{}).get('type','string')}")
                        else:
                            dictionary["mapType"].append(pd.NA)
                        if queryPath or full:
                            dictionary["querypath"].append(__cleanPath__(finalpath))
                        if full:
                            dictionary['metaStatus'].append(mydict[key]['items'].get('meta:status',pd.NA))
                            dictionary['minLength'].append(mydict[key]['items'].get('minLength',np.nan))
                            dictionary['maxLength'].append(mydict[key]['items'].get('maxLength',np.nan))
                            dictionary['minimum'].append(mydict[key]['items'].get('minimum',np.nan))
                            dictionary['maximum'].append(mydict[key]['items'].get('maximum',np.nan))
                            dictionary['pattern'].append(mydict[key]['items'].get('pattern',pd.NA))
                            dictionary['default'].append(mydict[key]['items'].get('default',pd.NA))
                            enumValues = mydict[key]['items'].get('meta:enum',pd.NA)
                            dictionary['enumValues'].append(enumValues)
                            if len(mydict[key]['items'].get('enum',[])) > 0:
                                dictionary['enum'].append(True)
                            else:
                                dictionary['enum'].append(False)
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
                    dictionary["description"].append(mydict[key].get('description',''))
                    dictionary["xdmType"].append(mydict[key].get('meta:xdmType',''))
                    if mydict[key].get('meta:xdmType') == 'map':
                        dictionary["mapType"].append(f"{mydict[key].get('additionalProperties',{}).get('type','string')}")
                    else:
                        dictionary["mapType"].append(pd.NA)
                    if queryPath or full:
                        dictionary["querypath"].append(__cleanPath__(finalpath))
                    if full:
                        dictionary['metaStatus'].append(mydict[key].get('meta:status',pd.NA))
                        dictionary['minLength'].append(mydict[key].get('minLength',np.nan))
                        dictionary['maxLength'].append(mydict[key].get('maxLength',np.nan))
                        dictionary['minimum'].append(mydict[key].get('minimum',np.nan))
                        dictionary['maximum'].append(mydict[key].get('maximum',np.nan))
                        dictionary['pattern'].append(mydict[key].get('pattern',pd.NA))
                        dictionary['default'].append(mydict[key].get('default',pd.NA))
                        enumValues = mydict[key].get('meta:enum',pd.NA)
                        dictionary['enumValues'].append(enumValues)
                        if len(mydict[key].get('enum',[])) > 0:
                                dictionary['enum'].append(True)
                        else:
                            dictionary['enum'].append(False)
                    if required:
                        if len(mydict[key].get('required',[])) > 0:
                            for elRequired in mydict[key].get('required',[]):
                                if finalpath is not None:
                                    tmp_reqPath = f"{finalpath}.{elRequired}"
                                else:
                                    tmp_reqPath = f"{elRequired}"
                                self.requiredFields.add(tmp_reqPath)
            elif type(mydict[key]) == dict and mydict[key].get('meta:referencedFrom',None) is not None: ## if the object is referencing a dataType
                if mydict[key].get('type') == 'object' or 'properties' in mydict[key].keys():
                    if path is None:
                        tmp_path = key
                    else:
                        tmp_path = f"{path}.{key}"
                    if tmp_path is not None:
                        dictionary["path"].append(tmp_path)
                        dictionary["type"].append(f"{mydict[key].get('type','')}")
                        dictionary["title"].append(f"{mydict[key].get('title','')}")
                        dictionary["description"].append(f"{mydict[key].get('description','')}")
                        dictionary["xdmType"].append(f"{mydict[key].get('meta:xdmType')}")
                        dictionary["mapType"].append(pd.NA)
                        if queryPath or full:
                            dictionary["querypath"].append(__cleanPath__(tmp_path))
                        if full:
                            dictionary['metaStatus'].append(pd.NA)
                            dictionary['minLength'].append(np.nan)
                            dictionary['maxLength'].append(np.nan)
                            dictionary['minimum'].append(np.nan)
                            dictionary['maximum'].append(np.nan)
                            dictionary['pattern'].append(pd.NA)
                            dictionary['default'].append(pd.NA)
                            dictionary['enumValues'].append(pd.NA)
                            dictionary['enum'].append(False)
                    properties = mydict[key].get('properties',None)
                    if properties is not None:
                        self.__transformationDF__(properties,dictionary,tmp_path,queryPath,required,full=full)
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

    def __transformFieldType__(self,dataType:str=None,**kwargs)->dict:
        """
        return the object with the type and possible meta attribute.
        possible kwargs:
            minimum : minimum value for number/integer
            maximum : maximum value for number/integer
            pattern : pattern for string
            minLength : minimum length for string
            maxLength : maximum length for string
            default : default value for the field
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
        list_possible_kwargs = ['minimum','maximum','pattern','minLength','maxLength','enum','default']
        for kw in kwargs:
            if kw in list_possible_kwargs:
                if kwargs[kw] is not None:
                    obj[kw] = kwargs[kw]
        return obj

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
        data = __accessorAlgo__(definition,path,self.dataType.get('allOf',[]))
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
        if kwargs.get('list_dt_ids') is not None:
            list_ids = kwargs.get('list_dt_ids')
        else:
            list_ids = self.dataTypes.keys()
        for dt_id in list_ids:
            ref_results = self.searchAttribute({'$ref':dt_id},extendedResults=True)
            paths = [res[list(res.keys())[0]]['path'] for res in ref_results]
            for path in paths:
                res = self.getField(path) ## to ensure the type of the path
                if res['type'] == 'array':
                    path = path +'[]{}'
                dict_results[path] = dt_id
            meta_ref_results = self.searchAttribute({'meta:referencedFrom':dt_id},extendedResults=True)
            meta_paths = [res[list(res.keys())[0]]['path'] for res in meta_ref_results if '$ref' in res[list(res.keys())[0]].keys() or 'meta:referencedFrom' in res[list(res.keys())[0]].keys() or '$ref' in res[list(res.keys())[0]].get('items', {}).keys() or 'meta:referencedFrom' in res[list(res.keys())[0]].get('items', {}).keys()]
            for path in meta_paths:
                res = self.getField(path) ## to ensure the type of the path
                if res.get('type') == 'array':
                    path = path +'[]{}'
                dict_results[path] = dt_id
            if kwargs.get('som_compatible',False):
                dict_results = {path.replace('{}','').replace('[]','.[0]'): dt_id for path, dt_id in dict_results.items()} ## compatible with SOM later
        dict_results = {} ## avoid reference to datatype already references in another datatype (in case of nested data type reference)
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
        data = __searchAlgo__(self.dataType.get('allOf',[]),definition,string,partialMatch,caseSensitive)
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
                resultsDict[key] += __searchAttrAlgo__(definition,"type",attr[key],regex)
            else:
                resultsDict[key] += __searchAttrAlgo__(definition,key,attr[key],regex)
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

        
    def addFieldOperation(self,path:str,dataType:str=None,title:str=None,objectComponents:dict=None,array:bool=False,enumValues:dict=None,enumType:bool=None,ref:str=None,mapType:str="string",**kwargs)->None:
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
            mapType : OPTIONAL : If you have used "map" as a dataType, you can pass the type of the map value there. Default is "string", possible alternate value is "integer"
        possible kwargs:
            defaultPath : Define which path to take by default for adding new field on tenant. Default "customFields", possible alternative : "property"
            description : if you want to add a description on your field
            maximum : if you want to add a maximum value for numeric field
            minimum : if you want to add a minimum value for numeric field
            pattern : if you want to add a pattern for string field
            minLength : if you want to add a minimum length for string field
            maxLength : if you want to add a maximum length for string field
            default : if you want to add a default value for the field
        """
        if self.EDITABLE == False:
            raise Exception("The Data Type is not Editable via Data Type Manager")
        typeTyped = ["string","boolean","double","long","integer","int","short","byte","date","dateTime","boolean","object",'array']
        if dataType not in typeTyped:
            raise TypeError(f'Expecting one of the following type : "string","boolean","double","long","integer","int","short","byte","date","dateTime","boolean","object". Got {dataType}')
        if dataType == 'object' and objectComponents is None:
            raise AttributeError('Require a dictionary providing the object component')       
        if title is None:
            title = __cleanPath__(path.split('.').pop())
        if title == 'items' or title == 'properties':
            raise Exception('"item" and "properties" are 2 reserved keywords')
        pathSplit = path.split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        completePath = ['definitions',kwargs.get('defaultPath','customFields')]
        description = kwargs.get("description",'')
        for p in pathSplit:
            if '[]{}' in p:
                completePath.append(__cleanPath__(p))
                completePath.append('items')
                completePath.append('properties')
            else:
                completePath.append(__cleanPath__(p))
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
                operation[0]['value']['description'] = description
                operation[0]['value']['items'] = self.__transformFieldType__(dataType)
            else:
                operation[0]['value'] = self.__transformFieldType__(dataType)
                operation[0]['value']['description'] = description
        else: 
            if dataType == "object":
                operation[0]['value']['type'] = self.__transformFieldType__(dataType)
                operation[0]['value']['properties'] = {key:self.__transformFieldType__(value) for key, value in zip(objectComponents.keys(),objectComponents.values())}
                operation[0]['value']['description'] = description
            elif dataType == "array":
                operation[0]['value']['type'] = 'array'
                operation[0]['value']['description'] = description
                operation[0]['value']['items'] = {
                    'type': 'object',
                    'properties': {key:self.__transformFieldType__(value) for key, value in zip(objectComponents.keys(),objectComponents.values())}
                }
            elif dataType == "dataType":
                operation[0]['value']['$ref'] = ref
                operation[0]['value']['type'] = 'object'
                operation[0]['value']['title'] = title
                operation[0]['value']['description'] = description
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
            elif dataType == "map":
                operation[0]['value'] = {'additionalProperties': {'type': mapType,
                    'meta:xdmType': mapType},
                    'required': [],
                    'note': '',
                    'mapFieldType': mapType,
                    'type': 'object',
                    'description': description,
                    'title': title,
                    'meta:xdmType': 'map'}
                if mapType == "integer":
                    operation[0]['value']['additionalProperties']['maximum'] = 2147483647
                    operation[0]['value']['additionalProperties']['minimum'] = -2147483648
                    operation[0]['value']['additionalProperties']['meta:xdmType'] = "int"
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

    def addField(self,path:str,dataType:str=None,title:str=None,objectComponents:dict=None,array:bool=False,enumValues:dict=None,enumType:bool=None,ref:str=None,mapType:str="string",**kwargs)->dict:
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
            mapType : OPTIONAL : If you have used "map" as a dataType, you can pass the type of the map value there. Default is "string", possible alternate value is "integer"
        possible kwargs:
            defaultPath : Define which path to take by default for adding new field on tenant. Default "customFields", possible alternative : "property"
            description : if you want to add a description on your field
            maximum : if you want to add a maximum value for numeric field
            minimum : if you want to add a minimum value for numeric field
            pattern : if you want to add a pattern for string field
            minLength : if you want to add a minimum length for string field
            maxLength : if you want to add a maximum length for string field
            default : if you want to add a default value for the field
            metaStatus : if you want to add a meta:status value for the field
        """
        if self.EDITABLE == False:
            raise Exception("The Data Type is not Editable via Field Group Manager")
        if path is None:
            raise ValueError("path must provided")
        typeTyped = ["string","boolean","double","long","int","integer", "number","short","byte","date","datetime",'date-time',"boolean","object",'array',"dataType", "map"]
        if dataType not in typeTyped:
            raise TypeError(f'Expecting one of the following type : "string","boolean","double","long","integer","number","int","short","byte","date","datetime","date-time","boolean","object","bytes", "array", "dataType", "map". Got {dataType}')
        if title is None:
            title = __cleanPath__(path.split('.').pop())
        if title == 'items' or title == 'properties':
            raise Exception('"item" and "properties" are 2 reserved keywords')
        pathSplit = __cleanPath__(path).split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        newField = pathSplit.pop()
        description = kwargs.get("description",'')
        metaStatus = kwargs.get("metaStatus",None)
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
            if metaStatus is not None:
                obj['meta:status'] = metaStatus
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
            if metaStatus is not None:
                obj['meta:status'] = metaStatus
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
            if metaStatus is not None:
                obj['meta:status'] = metaStatus
            self.dataTypes[ref] = title
            self.dataTypeManagers[ref] = DataTypeManager(dataType=ref,schemaAPI=self.schemaAPI)
        elif dataType == "map":
            obj = {'additionalProperties': {'type': mapType,
                'meta:xdmType': mapType},
                'required': [],
                'note': '',
                'mapFieldType': mapType,
                'type': 'object',
                'description': description,
                'title': title,
                'meta:xdmType': 'map'}
            if mapType == "integer":
                obj['additionalProperties']['maximum'] = 2147483647
                obj['additionalProperties']['minimum'] = -2147483648
                obj['additionalProperties']['meta:xdmType'] = "int"
            if metaStatus is not None:
                obj['meta:status'] = metaStatus
        else:
            minimum = kwargs.get('minimum',None)
            maximum = kwargs.get('maximum',None)
            pattern = kwargs.get('pattern',None)
            minLength = kwargs.get('minLength',None)
            maxLength = kwargs.get('maxLength',None)
            default = kwargs.get('default',None)
            obj = self.__transformFieldType__(dataType,minimum=minimum,maximum=maximum,pattern=pattern,minLength=minLength,maxLength=maxLength,default=default)
            obj['title']= title
            obj['description']= description
            if metaStatus is not None:
                obj['meta:status'] = metaStatus
            if array:
                obj['type'] = "array"
                obj['items'] = self.__transformFieldType__(dataType,minimum=minimum,maximum=maximum,pattern=pattern,minLength=minLength,maxLength=maxLength,default=default)
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
        pathSplit = __cleanPath__(path).split('.')
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
        definition = deepcopy(self.dataType.get('definitions',{}))
        if definition == {}:
            definition = self.dataType.get('properties',{})
        data = __transformationDict__(definition,typed)
        mysom = som.Som(data)
        if len(self.dataTypes)>0:
            paths = self.getDataTypePaths()
            for path,dataElementId in paths.items():
                tmp_dtManager = self.getDataTypeManager(dataElementId)
                tmp_dict = tmp_dtManager.to_dict()
                clean_path = path.replace('[]{}','.[0]')
                mysom.assign(clean_path,tmp_dict)
        data = mysom.to_dict()
        if save:
            filename = self.dataType.get('title',f'unknown_dataType_{str(int(time.time()))}')
            aepp.saveFile(module='schema',file=data,filename=f"{filename}.json",type_file='json')
        return data
    
    def to_pydantic(self,save:bool=False,origin:str='self',**kwargs)->Union[str,dict]:
        """
        Generate a Pydantic model representing the Data Type constitution
        Arguments:
            save : OPTIONAL : If you wish to save it with the title used by the field group.
                save as json with the title used. Not title, used "unknown_fieldGroup_" + timestamp.
        possible kwargs:
            output_model_type : The model that is outputed, default PydanticV2BaseModel
        """
        definition = deepcopy(self.dataType.get('definitions',{}))
        if definition == {}:
            definition = deepcopy(self.dataType.get('properties',{}))
        data = self.__transformationPydantic__(definition)
        mysom = som.Som(data)
        if len(self.dataTypes)>0:
            paths = self.getDataTypePaths()
            for path,dataElementId in paths.items():
                tmp_dtManager = self.getDataTypeManager(dataElementId)
                tmp_pydantic = tmp_dtManager.to_pydantic(origin="dataType")
                clean_path = path.replace('.','.properties.').replace('[]{}','.items')
                if clean_path.endswith('.'):
                    clean_path = clean_path[:-1]
                if clean_path.endswith('properties') == False:
                    clean_path = f"{clean_path}.properties"
                mysom.assign(path,tmp_pydantic)
        data = mysom.to_dict()
        if origin == 'self':
            modelTypeOutput = kwargs.get("output_model_type",DataModelType.PydanticV2BaseModel)
            pydantic_json = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": self.dataType.get('title',f'unknown_dataType_{str(int(time.time()))}'),
                "description": self.dataType.get('description',''),
                "type": "object",
                "properties": data
            }
            with TemporaryDirectory() as temporary_directory_name:
                temporary_directory = Path(temporary_directory_name)
                output = Path(temporary_directory / 'tmp_model.py')
                generate(
                    json.dumps(pydantic_json),
                    input_file_type=InputFileType.JsonSchema,
                    output=output,
                    output_model_type=modelTypeOutput,
                )
                mydata: str = output.read_text()
            if save:
                with open(f"pydantic_{self.dataType.get('title',f'unknown_dataType_{str(int(time.time()))}')}.py",'w') as f:
                    f.write(mydata)
            return mydata
        return data
    
    def to_som(self)->'som.Som':
        """
        Generate a SOM object representing the Data Type constitution
        """
        return som.Som(self.to_dict())

    def to_dataframe(self,save:bool=False,queryPath:bool=False,required:bool=False,full:bool=False)->pd.DataFrame:
        """
        Generate a dataframe with the row representing each possible path.
        Arguments:
            save : OPTIONAL : If you wish to save it with the title used by the field group.
                save as csv with the title used. Not title, used "unknown_fieldGroup_" + timestamp.
            queryPath : OPTIONAL : If you want to have the query path in the dataframe (only dot notation) (default False)
            required : OPTIONAL : If you want to have the required field in the dataframe (default False)
            full : OPTIONAL : If you want to have all possible attributes in the dataframe (default False)
        """
        definition = self.dataType.get('definitions',{})
        if definition == {}:
            definition = self.dataType.get('properties',{})
        data = self.__transformationDF__(definition,queryPath=queryPath,required=required,full=full)
        tmp_dict = {key:len(value) for key, value in data.items()}
        df = pd.DataFrame(data)
        df['origin'] = 'self'
        if len(self.dataTypes)>0:
            paths = self.getDataTypePaths()
            for path,dataElementId in paths.items():
                tmp_dtManager = self.getDataTypeManager(dataElementId)
                df_dataType = tmp_dtManager.to_dataframe(queryPath=queryPath,required=required,full=full)
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
        df_import = df_import[df_import['origin'] != 'dataType'].copy() ## removing path created by data type
        list_datatype_roots = list(self.getDataTypePaths().keys())
        df_import = df_import[~df_import['path'].isin(list_datatype_roots)].copy() ### removing the path that will link to data type, taking care of them later
        df_import['title'] = df_import['title'].fillna('')
        df_import['description'] = df_import['description'].fillna('')
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
            if typeElement == 'map': ## supporting map types
                mapType = row.get('mapType','string')
            else:
                mapType = None
            minimum = (lambda x : None if pd.isnull(x) else int(x))(row.get('minimum'))
            maximum = (lambda x : None if pd.isnull(x) else int(x))(row.get('maximum'))
            minLength = (lambda x : None if pd.isnull(x) else int(x))(row.get('minLength'))
            maxLength = (lambda x : None if pd.isnull(x) else int(x))(row.get('maxLength'))
            pattern = (lambda x : None if pd.isnull(x) else x)(row.get('pattern',None))
            default = (lambda x : None if pd.isnull(x) else x)(row.get('default',None))
            enumValues = (lambda x : None if pd.isnull(x) else x)(row.get('enumValues',None))
            metastatus = (lambda x : None if pd.isnull(x) else x)(row.get('metaStatus',None))
            if enumValues is None: ## ensuring to forcing a suggested value for empty enumValues
                enumType = None
            else:
                enumType = row.get('enum',False)
            if path.endswith("[]"):
                clean_path = __cleanPath__(row['path'])
                self.addField(clean_path,typeElement,title=row['title'],description=row['description'],array=True,enumType=enumType,enumValues=enumValues,mapType=mapType,minimum=minimum,maximum=maximum,pattern=pattern,minLength=minLength,maxLength=maxLength,default=default,metastatus=metastatus)
            elif path.endswith("[]{}"):
                clean_path = __cleanPath__(row['path'])
                self.addField(clean_path,'array',title=row['title'],description=row['description'],enumType=enumType,enumValues=enumValues,mapType=mapType,minimum=minimum,maximum=maximum,pattern=pattern,minLength=minLength,maxLength=maxLength,default=default,metastatus=metastatus)
            else:
                clean_path = __cleanPath__(row['path'])
                self.addField(clean_path,typeElement,title=row['title'],description=row['description'],enumType=enumType,enumValues=enumValues,mapType=mapType,minimum=minimum,maximum=maximum,pattern=pattern,minLength=minLength,maxLength=maxLength,default=default,metastatus=metastatus)
        return self