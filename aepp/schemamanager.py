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
from .configs import ConnectObject
from .fieldgroupmanager import FieldGroupManager
from .classmanager import ClassManager
from .catalog import ObservableSchemaManager
from aepp.schema import Schema
from aepp import som

class SchemaManager:
    """
    A class to handle the schema management.
    """
    DESCRIPTOR_TYPES =["xdm:descriptorIdentity","xdm:alternateDisplayInfo","xdm:descriptorOneToOne","xdm:descriptorReferenceIdentity","xdm:descriptorDeprecated","xdm:descriptorTimeSeriesGranularity","xdm:descriptorRelationship"]

    def __init__(self,
                schema:Union[str,dict]=None,
                fieldGroups:list=None,
                title: str=None,
                schemaAPI:'Schema'=None,
                schemaClass:str="https://ns.adobe.com/xdm/context/profile",
                config: Union[dict,ConnectObject] = aepp.config.config_object,
                description : str = "powered by aepp"
                )->None:
        """
        Instantiate the Schema Manager instance.
        Arguments:
            schemaId : OPTIONAL : Either a schemaId ($id or altId) or the schema dictionary itself.
                If schemaId is passed, you need to provide the schemaAPI connection as well.
            fieldGroups : OPTIONAL : Possible to specify a list of fieldGroup. 
                Either a list of fieldGroupIds (schemaAPI should be provided as well) or list of dictionary definition 
            title : OPTIONAL : If you wish to set up the title of your schema
            schemaAPI : OPTIONAL : It is required if $id or altId are used. It is the instance of the Schema class.
            schemaClass : OPTIONAL : If you want to set the class to be a specific class.
                Default value is profile: "https://ns.adobe.com/xdm/context/profile", can be replaced with any class definition.
                Possible default value: "https://ns.adobe.com/xdm/context/experienceevent", "https://ns.adobe.com/xdm/context/segmentdefinition"
            config : OPTIONAL : The config object in case you want to override the configuration.
            description : OPTIONAL : To provide a description to your schema 
        """
        self.fieldGroupIds=[]
        self.fieldGroupsManagers = {}
        self.classIds=[]
        self.classManagers={}
        self.title = title
        self.STATE = "EXISTING"
        if schemaAPI is not None:
            self.schemaAPI = schemaAPI
        else:
            self.schemaAPI = Schema(config=config)
        self.tenantId = f"_{self.schemaAPI.getTenantId()}"
        if type(schema) == dict:
            self.schema = schema
            self.__setAttributes__(self.schema)
            allOf = self.schema.get("allOf",[])
            if len(allOf) == 0:
                Warning("You have passed a schema with -full attribute, you should pass one referencing the fieldGroups.\n Using the meta:extends reference if possible")
                self.fieldGroupIds = [ref for ref in self.schema['meta:extends'] if ('/mixins/' in ref or '/experience/' in ref or '/context/' in ref) and ref != self.classId]
                self.schema['allOf'] = [{"$ref":ref} for ref in self.schema['meta:extends'] if ('/mixins/' in ref or 'xdm/class' in ref or 'xdm/context/' in ref) and ref != self.classId]
                self.classIds = [self.classId]
            else:
                self.fieldGroupIds = [obj['$ref'] for obj in allOf if ('/mixins/' in obj['$ref'] or '/experience/' in obj['$ref'] or '/context/' in obj['$ref']) and obj['$ref'] != self.classId]
                self.classIds = [self.classId]
            if self.schemaAPI is None:
                Warning("No schema instance has been passed or config file imported.\n Aborting the creation of field Group Manager")
            else:
                for ref in self.fieldGroupIds:
                    if '/mixins/' in ref:
                        definition = self.schemaAPI.getFieldGroup(ref,full=False)
                        fgM = FieldGroupManager(fieldGroup=definition,schemaAPI=self.schemaAPI)
                    else:
                        definition = self.schemaAPI.getFieldGroup(ref,full=True)
                        definition['definitions'] = definition['properties']
                        fgM = FieldGroupManager(fieldGroup=definition,schemaAPI=self.schemaAPI)
                    self.fieldGroupsManagers[fgM.title] = fgM
                for clas in self.classIds:
                    clsM = ClassManager(clas,schemaAPI=self.schemaAPI)
                    self.classManagers[clsM.title] = clsM
        elif type(schema) == str:
            if self.schemaAPI is None:
                Warning("No schema instance has been passed or config file imported.\n Aborting the retrieveal of the Schema Definition")
            else:
                self.schema = self.schemaAPI.getSchema(schema,full=False)
                self.__setAttributes__(self.schema)
                allOf = self.schema.get("allOf",[])
                self.fieldGroupIds = [obj.get('$ref','') for obj in allOf if ('/mixins/' in obj.get('$ref','') or '/experience/' in obj.get('$ref','') or '/context/' in obj.get('$ref','')) and obj.get('$ref','') != self.classId]
                self.classIds = [self.classId]
                if self.schemaAPI is None:
                    Warning("fgManager is set to True but no schema instance has been passed.\n Aborting the creation of field Group Manager")
                else:
                    for ref in self.fieldGroupIds:
                        if '/mixins/' in ref:
                            definition = self.schemaAPI.getFieldGroup(ref,full=False)
                        elif ref == '':
                            pass
                        else:
                            ## if the fieldGroup is an OOTB one
                            definition = self.schemaAPI.getFieldGroup(ref,full=True)
                            definition['definitions'] = definition['properties']
                        fgM = FieldGroupManager(fieldGroup=definition,schemaAPI=self.schemaAPI)
                        self.fieldGroupsManagers[fgM.title] = fgM
                    for clas in self.classIds:
                        clsM = ClassManager(clas,schemaAPI=self.schemaAPI)
                        self.classManagers[clsM.title] = clsM
        elif schema is None:
            self.STATE = "NEW"
            self.classId = schemaClass
            self.classIds = [schemaClass]
            self.schema = {
                    "title": self.title,
                    "description": description,
                    "allOf": [
                            {
                            "$ref": schemaClass
                            }
                        ]
                    }
            for clas in self.classIds:
                clsM = ClassManager(clas,schemaAPI=self.schemaAPI)
                self.classManagers[clsM.title] = clsM
        if fieldGroups is not None and type(fieldGroups) == list:
            if fieldGroups[0] == str:
                for fgId in fieldGroups:
                    if self.schemaAPI is None:
                        Warning("fgManager is set to True but no schema instance has been passed.\n Aborting the creation of field Group Manager")
                    else:
                        definition = self.schemaAPI.getFieldGroup(fgId,full=False)
                        fgM = FieldGroupManager(definition,schemaAPI=self.schemaAPI)
                        self.fieldGroupsManagers[fgM.title] = fgM
            elif fieldGroups[0] == dict:
                for fg in fieldGroups:
                    self.fieldGroupIds.append(fg.get('$id'))
                    fgM = FieldGroupManager(fg,schemaAPI=self.schemaAPI)
                    self.fieldGroupsManagers[fgM.title] = fgM
        self.fieldGroupTitles= tuple(fg.title for fg in list(self.fieldGroupsManagers.values()))
        self.fieldGroups = {fg.id:fg.title for fg in list(self.fieldGroupsManagers.values())}
        self.fieldGroupIds = tuple(fg.id for fg in list(self.fieldGroupsManagers.values()))
    
    def __setAttributes__(self,schemaDef:dict)->None:
        """
        Set some basic attributes
        """
        self.description = schemaDef.get('description','')
        if schemaDef.get('title'):
            self.title = schemaDef.get('title')
        if schemaDef.get('$id'):
            self.id = schemaDef.get('$id')
        if schemaDef.get('meta:altId'):
            self.altId = schemaDef.get('meta:altId')
        if schemaDef.get('meta:class'):
            self.classId = schemaDef.get('meta:class')

    def __str__(self)->str:
        return json.dumps(self.schema,indent=2)
    
    def __repr__(self)->str:
        return json.dumps(self.schema,indent=2)

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
        Set a name for the schema.
        Arguments:
            title : REQUIRED : a string to be used for the title of the Schema
        """
        if title is None:
            raise ValueError('title must be provided')
        self.schema['title'] = title
        self.title = title
        return None
    
    def setDescription(self,description:str=None)->None:
        """
        Set a description for the schema.
        Arguments:
            description : REQUIRED : a string to be used for the title of the Schema
        """
        if description is None:
            raise ValueError('description must be provided')
        self.schema['description'] = description
        self.description = description
        return None

    def searchField(self,string:str=None,partialMatch:bool=True,caseSensitive:bool=True)->list:
        """
        Search for a field in the different field group.
        You would need to have set fgManager attribute during instantiation or use the convertFieldGroups
        Arguments:
            string : REQUIRED : The string you are looking for
            partialMatch : OPTIONAL : If you want to use partial match (default True)
            caseSensitive : OPTIONAL : If you want to remove the case sensitivity.
        """
        myResults = []
        for clmanager in list(self.classManagers.values()):
            res = clmanager.searchField(string,partialMatch,caseSensitive)
            for r in res:
                r['class'] = clmanager.title
            myResults += res
        for fgmanager in list(self.fieldGroupsManagers.values()):
            res = fgmanager.searchField(string,partialMatch,caseSensitive)
            for r in res:
                r['fieldGroup'] = fgmanager.title
            myResults += res
        return myResults
    
    def searchAttribute(self,attr:dict=None,regex:bool=False,extendedResults:bool=False,joinType:str='outer', **kwargs)->list:
        """
        Search for an attribute and its value based on the keyword
        Arguments:
            attr : REQUIRED : a dictionary of key value pair(s).  Example : {"type" : "string"} 
                NOTE : If you wish to have the array type, use the key "arrayType". Example : {"type" : "array","arrayType":"string"} 
            regex : OPTIONAL : if you want your value of your key to be matched via regex.
                Note that regex will turn every comparison value to string for a "match" comparison.
            extendedResults : OPTIONAL : If you want to have the result to contain all details of these fields. (default False)
            joinType : OPTIONAL : If you pass multiple key value pairs, how do you want to get the match.
                outer : provide the fields if any of the key value pair is matched. (default)
                inner : provide the fields if all the key value pair matched.
        """
        myResults = []
        for clmanager in list(self.classManagers.values()):
            res = clmanager.searchAttribute(attr=attr,regex=regex,extendedResults=extendedResults,joinType=joinType)
            if extendedResults:
                for r in res:
                    r['class'] = clmanager.title
            myResults += res
        for fgmanager in list(self.fieldGroupsManagers.values()):
            res = fgmanager.searchAttribute(attr=attr,regex=regex,extendedResults=extendedResults,joinType=joinType)
            if extendedResults:
                for r in res:
                    r['fieldGroup'] = fgmanager.title
            myResults += res
        return myResults
    
    def addFieldGroup(self,fieldGroup:Union[str,dict,FieldGroupManager]=None)->Union[None,'FieldGroupManager']:
        """
        Add a field groups to field Group object and the schema. 
        return the specific FieldGroup Manager instance.
        Arguments:
            fieldGroup : REQUIRED : The fieldGroup ID or the dictionary definition connecting to the API.
                if a fieldGroup ID is provided, you should have added a schemaAPI previously.
        """
        if type(fieldGroup) == dict:
            if fieldGroup.get('$id') not in [fg for fg in self.fieldGroupIds]:
                self.schema['allOf'].append({'$ref':fieldGroup['$id'],"type": "object"})
        elif type(fieldGroup) == str:
            fieldGroup = self.schemaAPI.getFieldGroup(fieldGroup,full=False)
            if fieldGroup['$id'] not in self.fieldGroupIds:
                self.schema['allOf'].append({'$ref':fieldGroup['$id'],"type": "object"})
        if type(fieldGroup) == FieldGroupManager:
            fbManager = fieldGroup
            if fbManager.id not in self.fieldGroupIds:
                self.schema['allOf'].append({'$ref':fbManager.id,"type": "object"})
        else:
            fbManager = FieldGroupManager(fieldGroup=fieldGroup,schemaAPI=self.schemaAPI)
        self.fieldGroupsManagers[fbManager.title] = fbManager
        self.fieldGroupTitles = tuple(fgm.title for fgm in list(self.fieldGroupsManagers.values()))
        self.fieldGroupIds = tuple(fgm.id for fgm in list(self.fieldGroupsManagers.values()))
        self.fieldGroups = {fgm.id:fgm.title for fgm in list(self.fieldGroupsManagers.values())}
        return fbManager
    
    def getFieldGroupManager(self,fieldgroup:str=None)->'FieldGroupManager':
        """
        Return a field group Manager of a specific name.
        Only possible if fgManager was set to True during instanciation.
        Argument:
            fieldgroup : REQUIRED : The title or the $id of the field group to retrieve.
        """
        if self.getFieldGroupManager is not None:
            if "ns.adobe.com" in fieldgroup: ## id
                return [fg for fg in list(self.fieldGroupsManagers.values()) if fg.id == fieldgroup][0]
            else:
                return [fg for fg in list(self.fieldGroupsManagers.values()) if fg.title == fieldgroup][0]
        else:
            raise Exception("The field group manager was not set to True during instanciation. No Field Group Manager to return")

    def to_dataframe(self,
                     save:bool=False,
                     queryPath: bool = False,
                     description:bool = False,
                     xdmType:bool=False,
                     editable:bool=False,
                     excludeObjects:bool=False)->pd.DataFrame:
        """
        Extract the information from the Field Groups to a DataFrame. 
        Arguments:
            save : OPTIONAL : If you wish to save it with the title used by the field group.
                save as csv with the title used. Not title, used "unknown_schema_" + timestamp.
            queryPath : OPTIONAL : If you want to have the query path to be used.
            description : OPTIONAL : If you want to have the description added to your dataframe. (default False)
            xdmType : OPTIONAL : If you want to have the xdmType also returned (default False)
            editable : OPTIONAL : If you can manipulate the structure of the field groups
            excludeObjects : OPTIONAL : If you want to exclude object nodes and only get fields containing data.
        """
        df = pd.DataFrame({'path':[],'type':[],'fieldGroup':[]})
        for clManager in list(self.classManagers.values()):
            tmp_df = clManager.to_dataframe(queryPath=queryPath,description=description,xdmType=xdmType,editable=editable)
            tmp_df['fieldGroup'] = 'class'
            df = pd.concat([df,tmp_df],ignore_index=True)
        for fgmanager in list(self.fieldGroupsManagers.values()):
            tmp_df = fgmanager.to_dataframe(queryPath=queryPath,description=description,xdmType=xdmType,editable=editable)
            tmp_df['fieldGroup'] = fgmanager.title
            df = pd.concat([df,tmp_df],ignore_index=True)
        df = df[~df.duplicated(subset=['path','fieldGroup'])].reset_index(drop=True)
        if excludeObjects:
            df = df[df['type'] != 'object'].copy()
        if save:
            title = self.schema.get('title',f'unknown_schema_{str(int(time.time()))}.csv')
            df.to_csv(f"{title}.csv",index=False)
        return df
    
    def to_dict(self)->dict:
        """
        Return a dictionary of the whole schema. You need to have instanciated the Field Group Manager
        """
        list_dict = [fbm.to_dict() for fbm in list(self.fieldGroupsManagers.values())]
        list_class_dicts = [clm.to_dict() for clm in list(self.classManagers.values())]
        result = {}
        for mydict in list_class_dicts:
            result = self.__simpleDeepMerge__(result,mydict)
        for mydict in list_dict:
            result = self.__simpleDeepMerge__(result,mydict)
        return result
    
    def to_som(self)->'som.Som':
        """
        Generate a SOM object representing the Schema constitution
        """
        return som.Som(self.to_dict())

    def createSchema(self)->dict:
        """
        Send a createSchema request to AEP to create the schema.
        It removes the "$id" if one was provided to avoid overriding existing ID.
        """
        if self.schemaAPI is None:
            raise Exception("Require a Schema instance to connect to the API")
        if '$id' in self.schema.keys():
            del self.schema['$id']
        if 'meta:altId' in self.schema.keys():
            del self.schema['meta:altId']
        listMetaTags = [key for key in self.schema.keys() if 'meta' in key]
        if len(listMetaTags)>0:
            for key in listMetaTags:
                del self.schema[key]
        res = self.schemaAPI.createSchema(self.schema)
        if '$id' in res.keys():
            self.schema = res
            self.__setAttributes__(self.schema)
            self.STATE = "EXISTING"
        return res

    def updateSchema(self)->dict:
        """
        Use the PUT method to replace the existing schema with the new definition.
        """
        if self.schemaAPI is None:
            raise Exception("Require a Schema instance to connect to the API")
        res = self.schemaAPI.putSchema(self.id,self.schema)
        if 'status' in res.keys():
            if res['status'] == 400:
                print(res['title'])
                return res
            else:
                return res
        self.schema = res
        self.__setAttributes__(self.schema)
        return res
    
    def createDescriptorOperation(self,descType:str=None,
                                completePath:str=None,
                                identityNSCode:str=None,
                                identityPrimary:bool=False,
                                alternateTitle:str="",
                                alternateDescription:str=None,
                                targetSchema:str=None,
                                targetCompletePath:str=None,
                                targetNamespace:str=None,
                                labels:list=None,
                                timezone:str="UTC",
                                granularity:str="day",
                                cardinality:str="M:1",
                                )->dict:
        """
        Create a descriptor object to be used in the createDescriptor.
        You can see the type of descriptor available in the DESCRIPTOR_TYPES attribute and also on the official documentation:
        https://experienceleague.adobe.com/docs/experience-platform/xdm/api/descriptors.html?lang=en#appendix
        Arguments:
            descType : REQUIRED : The type to be used.
                it can only be one of the following value: "xdm:descriptorIdentity","xdm:alternateDisplayInfo","xdm:descriptorOneToOne","xdm:descriptorReferenceIdentity","xdm:descriptorDeprecated","xdm:descriptorLabel","xdm:descriptorTimeSeriesGranularity", "xdm:descriptorRelationship"
            completePath : REQUIRED : the dot path of the field you want to attach a descriptor to.
                Example: '_tenant.tenantObject.field'
            identityNSCode : OPTIONAL : if the descriptor is identity related, the namespace CODE  used.
            identityPrimary : OPTIONAL : If the primary descriptor added is the primary identity.
            alternateTitle : OPTIONAL : if the descriptor is alternateDisplay, the alternate title to be used.
            alternateDescription : OPTIONAL if you wish to add a new description.
            targetSchema : OPTIONAL : The schema ID for the destination (lookup, B2B lookup, relationship) if the descriptor is "descriptorRelationship" or "descriptorOneToOne".
            targetCompletePath : OPTIONAL : if you have the complete path for the field in the target lookup schema, if the descriptor is "descriptorRelationship" or "descriptorOneToOne".
            targetNamespace: OPTIONAL : if you have the namespace code for the target schema (used for "descriptorRelationship").
            labels : OPTIONAL : list of labels, if your descriptor is a descriptorLabel.
            timezone : OPTIONAL : The proper timezone identifier value from the TZ identifier column (see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
            granularity : OPTION : hour or day (default),
            cardinality : OPTIONAL : The cardinality of the relationship. default is "M:1"
        """
        if descType not in self.DESCRIPTOR_TYPES:
            raise Exception(f"The value provided ({descType}) is not supported by this method")
        if descType != "xdm:descriptorTimeSeriesGranularity":
            if completePath is None:
                raise ValueError("Require a field complete path")
            else:
                if completePath.startswith('/') == False:
                    completePath = '/'+completePath.replace('.','/')
        if descType == "xdm:descriptorIdentity":
            obj = {
                "@type": descType,
                "xdm:sourceSchema": self.id,
                "xdm:sourceVersion": 1,
                "xdm:sourceProperty": completePath,
                "xdm:namespace": identityNSCode,
                "xdm:property": "xdm:code",
                "xdm:isPrimary": identityPrimary
            }
        elif descType == "xdm:alternateDisplayInfo":
            if alternateTitle is None:
                raise ValueError("Require an alternate title")
            obj = {
                "@type": descType,
                "xdm:sourceSchema": self.id,
                "xdm:sourceVersion": 1,
                "xdm:sourceProperty": completePath,
                "xdm:title": {
                    "en_us": alternateTitle
                    }
                }
            if alternateDescription is not None:
                obj["xdm:description"] = {
                    "en_us":alternateDescription
                }
        elif descType == "xdm:descriptorOneToOne":
            obj = {
                "@type": descType,
                "xdm:sourceSchema":self.id,
                "xdm:sourceVersion": 1,
                "xdm:sourceProperty":completePath,
                "xdm:destinationSchema":targetSchema,
                "xdm:destinationVersion": 1,
            }
            if targetCompletePath is not None:
                obj["xdm:destinationProperty"] = targetCompletePath
        elif descType == "xdm:descriptorReferenceIdentity":
            obj = {
                "@type": descType,
                "xdm:sourceSchema": self.id,
                "xdm:sourceVersion": 1,
                "xdm:sourceProperty": completePath,
                "xdm:identityNamespace": identityNSCode
                }
        elif descType == "xdm:descriptorDeprecated":
            obj = {
                "@type": descType,
                "xdm:sourceSchema": self.id,
                "xdm:sourceVersion": 1,
                "xdm:sourceProperty": completePath
            }            
        elif descType == "xdm:descriptorTimeSeriesGranularity":
            obj = {
                "@type": descType,
                "xdm:sourceSchema": self.id,
                "xdm:sourceVersion": 1,
                "xdm:granularity": granularity,
                "xdm:ianaTimezone":timezone
            }
        elif descType == "xdm:descriptorRelationship":##B2B
            obj = {
                "@type": descType,
                "xdm:sourceSchema": self.id,
                "xdm:sourceVersion": 1,
                "xdm:sourceProperty": completePath,
                "xdm:destinationSchema": targetSchema,
                "xdm:destinationProperty": targetCompletePath,
                "xdm:destinationNamespace": targetNamespace,
                "xdm:destinationVersion": 1,
                "xdm:cardinality": cardinality
            }
        return obj
    
    def createDescriptor(self,descriptor:dict=None)->dict:
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

    def compareObservableSchema(self,observableSchemaManager:'ObservableSchemaManager'=None)->pd.DataFrame:
        """
        A method to compare the existing schema with the observable schema and find out the difference in them.
        It output a dataframe with all of the path, the field group, the type (if provided) and the part availability (in that dataset)
        Arguments:
            observableSchemaManager : REQUIRED : the ObservableSchemaManager class instance.
        """
        df_schema = self.to_dataframe()
        df_obs = observableSchemaManager.to_dataframe()
        df_merge = df_schema.merge(df_obs,left_on='path',right_on='path',how='left',indicator=True)
        df_merge = df_merge.rename(columns={"_merge": "availability",'type_x':'type'})
        df_merge = df_merge.drop("type_y",axis=1)
        df_merge['availability'] = df_merge['availability'].str.replace('left_only','schema_only')
        df_merge['availability'] = df_merge['availability'].str.replace('both','schema_dataset')
        return df_merge
    
    def __prepareDescriptors__(self,subDF:pd.DataFrame,dict_SourcePropery_Descriptor:dict,fg:str)->dict:
        """
        Handling the preparation of descriptors for non editable field groups
        """
        operations_create = []
        operations_update = []
        subDF = subDF.fillna('')
        for i, row in subDF.iterrows():
            completePath = '/' + row['path'].replace('.','/')
            if completePath in dict_SourcePropery_Descriptor.keys():
                desc = deepcopy(dict_SourcePropery_Descriptor[completePath])
                if 'title':
                    if row['title'] != "":
                        desc['xdm:title'] = {'en_us': row['title']}
                if 'description' in row.keys():
                    if row['description'] != "":
                        desc["xdm:description"] = {'en_us':row['description']}
                if row.get('description','') != "" or row.get('description','') != "":
                    operations_update.append(desc)
            else:
                if 'title' in row.keys():
                    if row['title'] != "":
                        alternateTitle = row['title']
                else:
                    alternateTitle = ""
                if 'description' in row.keys():
                    if row['description'] != "":
                        alternateDescription = row['description']
                else:
                    alternateDescription = ""
                if row.get('description','') != "" or row.get('description','') != "":
                    operations_create.append(self.createDescriptorOperation("xdm:alternateDisplayInfo",
                                                                completePath=completePath,
                                                                alternateTitle=alternateTitle,
                                                                alternateDescription=alternateDescription))
        dict_operations = {'create':operations_create,'update':operations_update}
        return dict_operations
    
    def getDescriptors(self)->dict:
        """
        Get the descriptors of that schema
        """
        if self.STATE=="NEW" or self.id == "":
            raise Exception("Schema does not exist yet, there can not be a descriptor")    
        res = self.schemaAPI.getDescriptors(prop=f"xdm:sourceSchema=={self.id}")
        return res


    def importSchemaDefinition(self,schema:Union[str,pd.DataFrame]=None,sep:str=',',sheet_name:str=None)->dict:
        """
        Import the definition of all the fields defined in csv or dataframe.
        Update all the corresponding field groups based on that.
        Argument:
            schema : REQUIRED : The schema defined in the CSV.
                It needs to contains the following columns : "path", "type", "fieldGroup","title"
            sep : OPTIONAL : If your CSV is separated by other character  than comma (,)
            sheet_name : OPTIONAL : If you are loading an Excel, please provide the sheet_name. 
        """
        if schema is None:
            raise ValueError("Require a dataframe or a CSV")
        if type(schema) == str:
            if '.csv' in schema:
                df_import = pd.read_csv(schema,sep=sep)
            if '.xls' in schema:
                if sheet_name is None:
                    raise ImportError("You need to pass a sheet name to use Excel")
                df_import = pd.read_excel(schema,sheet_name=sheet_name)
        elif type(schema) == pd.DataFrame:
            df_import = schema
        if 'path' not in df_import.columns or 'type' not in df_import.columns or 'fieldGroup' not in df_import.columns:
            raise AttributeError("missing a column [type, path, or type] in your fieldgroup")
        fieldGroupsImportList = list(df_import['fieldGroup'].unique())
        allFieldGroups = self.schemaAPI.getFieldGroups() ## generate the dictionary in data attribute
        ootbFGS = self.schemaAPI.getFieldGroupsGlobal()
        dictionaryFGs = {fg:None for fg in fieldGroupsImportList}
        dict_SourcePropery_Descriptor = {} ## default descriptors list empty
        if hasattr(self,'id'):
            mydescriptors = self.schemaAPI.getDescriptors(type_desc="xdm:alternateDisplayInfo",prop=f"xdm:sourceSchema=={self.id}")
            dict_SourcePropery_Descriptor = {ex['xdm:sourceProperty']:ex for ex in mydescriptors}
        for fg in fieldGroupsImportList:
            subDF:pd.DataFrame = df_import[df_import['fieldGroup'] == fg].copy()
            if fg in self.fieldGroups.values():
                myFg = self.getFieldGroupManager(fg)
                if myFg.EDITABLE:
                    res = myFg.importFieldGroupDefinition(subDF)
                else:
                    res = self.__prepareDescriptors__(subDF,dict_SourcePropery_Descriptor,fg)
                dictionaryFGs[fg] = res
            elif fg in self.schemaAPI.data.fieldGroups_altId.keys():
                myFg = FieldGroupManager(self.schemaAPI.data.fieldGroups_id[fg],schemaAPI=self.schemaAPI)
                if myFg.EDITABLE:
                    res = myFg.importFieldGroupDefinition(subDF)
                else:
                    if hasattr(self,'id'):
                        res = self.__prepareDescriptors__(subDF,dict_SourcePropery_Descriptor,fg)
                    else:
                        res = {'error':'not descriptors can be added to this schema because it has no $id attached. Create the schema before trying to attach descriptors.'}
                dictionaryFGs[fg] = myFg
            elif fg in  self.schemaAPI.data.fieldGroupsGlobal_altId.keys():
                if hasattr(self,'id'):
                    res = self.__prepareDescriptors__(subDF,dict_SourcePropery_Descriptor,fg)
                else:
                    res = {'error':'not descriptors can be added to this schema because it has no $id attached. Create the schema before trying to attach descriptors.'}
                dictionaryFGs[fg] = res
            else: # does not exist
                myFg = FieldGroupManager(schemaAPI=self.schemaAPI,title=fg)
                if myFg.EDITABLE:
                    myFg.importFieldGroupDefinition(subDF)
                    dictionaryFGs[fg] = myFg
        self.dictFieldGroupWork = dictionaryFGs
        return self.dictFieldGroupWork


    def applyFieldsChanges(self)->dict:
        """
        Apply the changes that you have imported to the field groups and possible descriptors via the importSchemaDefinition
        It also update the references to the schema and add new field groups to the schema definition.
        NOTE: You will need to update the Schema in case of new field groups have been added. 
        Returns a dictionary such as {'fieldGroupName':'{object returned by the action}'}
        """
        dict_result = {}
        for key in self.dictFieldGroupWork.keys():
            myFG:Union[FieldGroupManager,list] = self.dictFieldGroupWork[key]
            if type(myFG) == FieldGroupManager:
                if myFG.STATE == 'NEW':
                    myFG.createFieldGroup()
                    res = self.addFieldGroup(myFG)
                    dict_result[key] = res
                elif myFG.STATE == 'EXISTING':
                    if myFG.EDITABLE:
                        res = myFG.updateFieldGroup()
                        self.addFieldGroup(myFG)
            else:
                res:list = []
                if 'error' not in myFG.keys():
                    for create in myFG['create']:
                        res.append(self.createDescriptor(create))
                    for update in myFG['update']:
                        res.append(self.schemaAPI.putDescriptor(update['@id'],update))
            dict_result[key] = res
        return dict_result  
        