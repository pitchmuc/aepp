import json, time, re
from typing import Union
import aepp
from .configs import ConnectObject
from aepp.schema import Schema
import pandas as pd
from copy import deepcopy

class ClassManager:
    def __init__(self,
            aepclass:Union[str,dict]=None,
            title: str=None,
            behavior:str='https://ns.adobe.com/xdm/data/record',
            schemaAPI:'Schema'=None,
            config: Union[dict,ConnectObject] = aepp.config.config_object,
            description: str = 'power by aepp'
            )->None:
        """
        Instantiate the Schema Manager instance.
        Arguments:
            aepclass : OPTIONAL : The classId or the class definition.
            title : OPTIONAL : If you wish to set up the title of your class
            behavior : OPTIONAL : If you want to define which behavioral element it extends. 
                Default: 'https://ns.adobe.com/xdm/data/record', possible values: 'https://ns.adobe.com/xdm/data/time-series','https://ns.adobe.com/xdm/data/adhoc' 
            schemaAPI : OPTIONAL : It is required if $id or altId are used. It is the instance of the Schema class.
            config : OPTIONAL : The config object in case you want to override the configuration.
            description : OPTIONAL : If you want to add a description to your class
        """
        self.EDITABLE = False
        self.STATE = "EXISTING"
        if schemaAPI is not None:
            self.schemaAPI = schemaAPI
        else:
            self.schemaAPI = Schema(config=config)
        tenantNoUnderscore = self.schemaAPI.getTenantId()
        self.tenantId = f"_{tenantNoUnderscore}"
        if type(aepclass) == dict:
            if tenantNoUnderscore in aepclass['id']:
                self.aepclass = self.schemaAPI.getClass(aepclass['id'],full=False,xtype='xed')
            else:
                self.aepclass = self.schemaAPI.getClass(aepclass['id'],full=True,xtype='xed')
            self.__setAttributes__(self.aepclass)
        elif type(aepclass) == str:
            if tenantNoUnderscore in aepclass:
                self.aepclass = self.schemaAPI.getClass(aepclass,full=False,xtype='xed')
            else:
                self.aepclass = self.schemaAPI.getClass(aepclass,full=True,xtype='xed')
            self.__setAttributes__(self.aepclass)
        else:
            self.STATE = "NEW"
            self.EDITABLE = True
            if type(behavior) == list:
                self.behavior = behavior
            else:
                self.behavior = [behavior]
            self.aepclass = {
                "title" : title,
                "description":description,
                "type" : "object",
                "definitions":{
                    "customFields":{},
                    "property":{}
                },
                'allOf': [{'$ref': '#/definitions/customFields',
                    'type': 'object',
                    'meta:xdmType': 'object'},
                    {"$ref": "#/definitions/property",
                    "type": "object"
                    }],
                'meta:extensible': True,
                'meta:extends': self.behavior,
                'meta:tenantNamespace': self.tenantId
            }
            for behav in self.behavior:
                self.aepclass['allOf'].append({'$ref': behav,'type': 'object','meta:xdmType': 'object'})
        if title is not None:
            self.aepclass['title'] = title
            self.title = title
        else:
            self.title = self.aepclass['title']
        self.__setAttributes__(self.aepclass)
        if self.tenantId in self.id:
            self.EDITABLE = True
        else:
            self.EDITABLE = False
        self.requiredFields = set()
    
    def __setAttributes__(self, aepclass:dict):
        self.description = aepclass.get('description','')
        if aepclass.get('title'):
            self.title = aepclass.get('title')
        if aepclass.get('$id'):
            self.id = aepclass.get('$id')
        if aepclass.get("meta:altId"):
            self.altId = aepclass.get("meta:altId")
        if aepclass.get('meta:extends'):
            extends = aepclass.get('meta:extends')
            for ext in extends:
                if 'xdm/data/' in ext:
                    self.behavior = ext 

    def __str__(self)->str:
        return json.dumps(self.aepclass,indent=2)
    
    def __repr__(self)->str:
        return json.dumps(self.aepclass,indent=2)

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

    def setTitle(self,title:str=None)->None:
        """
        Set a name for the class.
        Arguments:
            title : REQUIRED : a string to be used for the title of the class
        """
        if title is None:
            raise ValueError('title must be provided')
        self.aepclass['title'] = title
        self.title = title
        return None
    
    def setDescription(self,description:str=None)->None:
        """
        Set a description for the class.
        Arguments:
            description : REQUIRED : a string to be used for the description of the class
        """
        if description is None:
            raise ValueError('a description must be provided')
        self.aepclass['description'] = description
        self.description = description
        return None
    
    def __cleanPath__(self,string:str=None)->str:
        """
        An abstraction to clean the path string and remove the following characters : [,],{,}
        Arguments:
            string : REQUIRED : a string 
        """
        return deepcopy(string.replace('[','').replace(']','').replace("{",'').replace('}',''))

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
                            fieldGroup[key]['properties'][newField]['description'] = obj["description"]
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
        elif dataType == "DateTime" or dataType == "dateTime":
            obj['type'] = "string"
            obj['format'] = "date-time"
        elif dataType == "byte":
            obj['type'] = "integer"
            obj['maximum'] = 128
            obj['minimum'] = -128
        else:
            obj['type'] = dataType
        return obj
    
    def __transformationDict__(self,mydict:dict=None,typed:bool=False,dictionary:dict=None)->dict:
        """
        Transform the current XDM class to a dictionary.
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

    def __transformationDF__(self,mydict:dict=None,
                             dictionary:dict=None,
                             path:str=None,
                             queryPath:bool=False,
                             description:bool=False,
                             xdmType:bool=False,
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
            required : boolean to know if you want to retrieve the required fields
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
                                    tmp_reqPath = f"{finalpath}.{elRequired}"
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
                                tmp_reqPath = f"{finalpath}.{elRequired}"
                                self.requiredFields.add(tmp_reqPath)
        return dictionary
    
    def getField(self,path:str)->dict:
        """
        Returns the field definition you want want to obtain.
        Arguments:
            path : REQUIRED : path with dot notation to which field you want to access
        """
        definition = self.aepclass.get('definitions',self.aepclass.get('properties',{}))
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
        definition = self.aepclass.get('definitions',self.aepclass.get('properties',{}))
        data = self.__searchAlgo__(definition,string,partialMatch,caseSensitive)
        return data
    
    def searchAttribute(self,attr:dict=None,regex:bool=False,extendedResults:bool=False,joinType:str='outer', **kwargs)->list:
        """
        Search for an attribute on the field of the class.
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
        definition = self.aepclass.get('definitions',self.aepclass.get('properties',{}))
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
    
    def addField(self,path:str,dataType:str=None,title:str=None,objectComponents:dict=None,array:bool=False,enumValues:dict=None,enumType:bool=None,ref:str=None,**kwargs)->dict:
        """
        Add the field to the existing fieldgroup definition.
        Returns False when the field could not be inserted.
        Arguments:
            path : REQUIRED : path with dot notation where you want to create that new field. New field name should be included.
            dataType : REQUIRED : the field type you want to create
                A type can be any of the following: "string","boolean","double","long","integer","number","short","byte","date","dateTime","boolean","object","array","dataType"
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
        typeTyped = ["string","boolean","double","long","integer","number","short","byte","date","dateTime","boolean","object",'array','dataType']
        if dataType not in typeTyped:
            raise TypeError('Expecting one of the following type : "string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object","byte","dataType"')
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
        if 'definitions' not in self.aepclass.keys():
            if 'properties' in self.aepclass.keys():
                definition,foundFlag = self.__setField__(pathSplit, self.aepclass['properties'],newField,obj)
                if foundFlag == False:
                    return False
                else:
                    self.aepclass['properties'] = definition
                    return self.aepclass
        else:
            definition,foundFlag = self.__setField__(completePath, self.aepclass['definitions'],newField,obj)
        if foundFlag == False:
            completePath:list[str] = ['customFields'] + pathSplit ## trying via customFields path
            definition,foundFlag = self.__setField__(completePath, self.aepclass['definitions'],newField,obj)
            if foundFlag == False:
                return False
            else:
                self.aepclass['definitions'] = definition
                return self.aepclass
        else:
            self.aepclass['definitions'] = definition
            return self.aepclass
        
    def removeField(self,path:str)->dict:
        """
        Remove a field from the definition based on the path provided.
        NOTE: A path that has received data cannot be removed from a class or field group.
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
        definition = self.aepclass.get('definitions',self.aepclass.get('properties',{}))
        data = self.__transformationDF__(definition,queryPath=queryPath,description=description,xdmType=xdmType,required=required)
        df = pd.DataFrame(data)
        df = df[~df.path.duplicated()].copy() ## dedup the paths
        df = df[~(df['path']==self.tenantId)].copy()## remove the root
        df['origin'] = 'class'
        if editable:
            df['editable'] = self.EDITABLE
        if excludeObjects:
            df = df[df['type'] != 'object'].copy()
        if save:
            title = self.aepclass.get('title',f'unknown_class_{str(int(time.time()))}')
            df.to_csv(f"{title}.csv",index=False)
        return df

    def to_dict(self,typed:bool=True,save:bool=False)->dict:
        """
        Generate a dictionary representing the field group constitution
        Arguments:
            typed : OPTIONAL : If you want the type associated with the field group to be given.
            save : OPTIONAL : If you wish to save the dictionary in a JSON file
        """
        definition = self.aepclass.get('definitions',self.aepclass.get('properties',{}))
        data = self.__transformationDict__(definition,typed)
        if save:
            filename = self.aepclass.get('title',f'unknown_class_{str(int(time.time()))}')
            aepp.saveFile(module='schema',file=data,filename=f"{filename}.json",type_file='json')
        return data
    
    def to_xdm(self)->dict:
        """
        Return the Data Type definition as XDM
        """
        return self.aepclass
    
    def createClass(self)->dict:
        """
        Create the custom class
        """
        if self.STATE != "NEW":
            raise ValueError("The class already exist and cannot be created")
        path = "/tenant/classes"
        res = self.schemaAPI.createClass(self.aepclass)
        self.aepclass = res
        return res