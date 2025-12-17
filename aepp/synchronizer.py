#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

import json
import aepp
from aepp import schema, schemamanager, fieldgroupmanager, datatypemanager,classmanager,identity,catalog
from copy import deepcopy
from typing import Union
from pathlib import Path
from io import FileIO


class Synchronizer:
    ## TO DO -> Add support for local environment
    def __init__(self,targets:list=None,config:aepp.ConnectObject=None,baseSandbox:str=None,region:str='nld2',localFolder:str=None):
        """
        Setup the synchronizor object with the base sandbox and target sandbox.
        Arguments:
            targets : REQUIRED : list of target sandboxes as strings
            config : REQUIRED : ConnectObject with the configuration. Make sure that the configuration of your API allows connection to all sandboxes.
            baseSandbox : OPTIONAL : name of the base sandbox
            region : OPTIONAL : region of the sandboxes. default is 'nld2', possible values are: "va7" or "aus5 or "can2" or "ind2"
            localFolder : OPTIONAL : if provided, it will use the local environment as the base. Default is False.
                If localFolder is provided, the baseSandbox and targets are not used, and the configuration is used to connect to the local environment.
                configuration to use local environment is a folder with the name of your sandbox, inside that folder there must a folder for each base component:
                - class
                - schema
                - fieldgroup
                - datatype
                - identity
                - dataset
                - descriptor
        """
        self.baseSandbox = None
        self.localfolder = None
        if targets is None:
            raise ValueError("a list of target sandboxes must be provided - at least one")
        if config is None or type(config) != aepp.ConnectObject:
            raise ValueError("a ConnectObject must be provided")
        config_object = deepcopy(config.getConfigObject())
        if baseSandbox is not None and localFolder is None:
            self.baseConfig = aepp.configure(org_id=config_object['org_id'],
                                            client_id=config_object['client_id'],
                                            scopes=config_object['scopes'],
                                            secret=config_object['secret'],
                                            sandbox=baseSandbox,
                                            connectInstance=True)
            self.baseSandbox = baseSandbox
        elif localFolder is not None:
            self.baseConfig = None
            self.localfolder = Path(localFolder)
            self.classFolder = self.localfolder / 'class'
            self.schemaFolder = self.localfolder / 'schema'
            self.fieldgroupFolder = self.localfolder / 'fieldgroup'
            self.fieldgroupGlobalFolder = self.fieldgroupFolder / 'global'
            self.datatypeFolder = self.localfolder / 'datatype'
            self.datatypeGlobalFolder = self.datatypeFolder / 'global'
            self.identityFolder = self.localfolder / 'identity'
            self.datasetFolder = self.localfolder / 'dataset'
            self.descriptorFolder = self.localfolder / 'descriptor'
            if baseSandbox is not None:
                self.baseSandbox = baseSandbox
        self.dict_targetsConfig = {target: aepp.configure(org_id=config_object['org_id'],client_id=config_object['client_id'],scopes=config_object['scopes'],secret=config_object['secret'],sandbox=target,connectInstance=True) for target in targets}
        self.region = region
        self.dict_targetComponents = {target:{'schema':{},'class':{},'fieldgroup':{},'datatype':{},'datasets':{},'identities':{},"schemaDescriptors":{}} for target in targets}

    def syncComponent(self,component:Union[str,dict],componentType:str=None,verbose:bool=False)-> dict:
        """
        Synchronize a component to the target sandbox.
        The component could be a string (name or id of the component in the base sandbox) or a dictionary with the definition of the component.
        If the component is a string, you have to have provided a base sandbox in the constructor.
        Arguments:
            component : REQUIRED : name or id of the component or a dictionary with the component definition
            componentType : OPTIONAL : type of the component (e.g. "schema", "fieldgroup", "datatypes", "class", "identity", "dataset"). Required if a string is passed. 
            It is not required but if the type cannot be inferred from the component, it will raise an error. 
            verbose : OPTIONAL : if True, it will print the details of the synchronization process
        """
        if type(component) == str:
            if self.baseConfig is None and self.localfolder is None:
                raise ValueError("a base sandbox or a local folder must be provided to synchronize a component by name or id")
            if componentType is None:
                raise ValueError("the type of the component must be provided if the component is a string")
            if componentType not in ['schema', 'fieldgroup', 'datatypes', 'class', 'identity', 'dataset']:
                raise ValueError("the type of the component is not supported. Please provide one of the following types: schema, fieldgroup, datatypes, class, identity, dataset")
            if componentType in ['schema', 'fieldgroup', 'datatypes', 'class']:
                if self.baseConfig is not None:
                    base_schema = schema.Schema(config=self.baseConfig)
                else:
                    base_schema = None
                if componentType == 'schema':
                    if base_schema is not None:
                        schemas = base_schema.getSchemas()
                        if component in base_schema.data.schemas_altId.keys():## replacing name with altId
                            component = base_schema.data.schemas_altId[component]
                    if self.localfolder is not None:
                        for file in self.schemaFolder.glob('*.json'):
                            sc_file = json.load(FileIO(file))
                            if sc_file['title'] == component or sc_file['$id'] == component or sc_file['meta:altId'] == component:
                                component = sc_file
                                break
                    component = schemamanager.SchemaManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                elif componentType == 'fieldgroup':
                    if base_schema is not None:
                        fieldgroups = base_schema.getFieldGroups()
                        if component in base_schema.data.fieldGroups_altId.keys():## replacing name with altId
                            component = base_schema.data.fieldGroups_altId[component]
                    if self.localfolder is not None:
                        for file in self.fieldgroupFolder.glob('*.json'):
                            fg_file = json.load(FileIO(file))
                            if fg_file['title'] == component or fg_file['$id'] == component or fg_file['meta:altId'] == component:
                                component = fg_file
                                break
                    component = fieldgroupmanager.FieldGroupManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                elif componentType == 'datatypes':
                    datatypes = base_schema.getDataTypes()
                    if base_schema is not None:
                        if component in base_schema.data.dataTypes_altId.keys():## replacing name with altId
                            component = base_schema.data.dataTypes_altId[component]
                    if self.localfolder is not None:
                        for file in self.datatypeFolder.glob('*.json'):
                            dt_file = json.load(FileIO(file))
                            if dt_file['title'] == component or dt_file['$id'] == component or dt_file['meta:altId'] == component:
                                component = dt_file
                                break
                    component = datatypemanager.DataTypeManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                elif componentType == 'class':
                    classes = base_schema.getClasses()
                    if component in base_schema.data.classes_altId.keys():## replacing name 
                        component = base_schema.data.classes_altId[component]
                    component = classmanager.ClassManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
            elif componentType == 'identity':
                if self.baseConfig is not None:
                    id_base = identity.Identity(config=self.baseConfig,region=self.region)
                    identities:list = id_base.getIdentities()
                elif self.localfolder is not None:
                    identities = []
                    for file in self.identityFolder.glob('*.json'):
                        id_file = json.load(FileIO(file))
                        identities.append(id_file)
                if component in [el['code'] for el in identities]:
                    component = [el for el in identities if el['code'] == component][0]
                elif component in [el['name'] for el in identities]:
                    component = [el for el in identities if el['name'] == component][0]
                else:
                    raise ValueError("the identity could not be found in the base sandbox")
            elif componentType == 'dataset':
                if self.baseConfig is not None:
                    cat_base = catalog.Catalog(config=self.baseConfig)
                    datasets = cat_base.getDataSets()
                    if component in cat_base.data.ids.keys():## replacing name with id
                        component = cat_base.data.ids[component]
                    component = cat_base.getDataSet(component)
                elif self.localfolder is not None:
                    for file in self.datasetFolder.glob('*.json'):
                        ds_file = json.load(FileIO(file))
                        if ds_file['id'] == component or ds_file['name'] == component:
                            component = ds_file
                            break
                if len(component) == 1: ## if the component is the catalog API response {'key': {dataset definition}}
                    component = component[list(component.keys())[0]] ## accessing the real dataset definition
        elif type(component) == dict:
            if 'meta:resourceType' in component.keys():
                componentType = component['meta:resourceType']
                if componentType == 'schema':
                    component = schemamanager.SchemaManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                elif componentType == 'fieldgroup':
                    component = fieldgroupmanager.FieldGroupManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                elif componentType == 'datatypes':
                    component = datatypemanager.DataTypeManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                elif componentType == 'class':
                    component = classmanager.ClassManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
            elif 'namespaceType' in component.keys():
                componentType = 'identity'
            elif 'files' in component.keys():
                componentType = 'dataset'
            else:
                raise TypeError("the component type could not be inferred from the component or is not supported. Please provide the type as a parameter")
        ## Synchronize the component to the target sandboxes
        if componentType == 'datatypes':
            self.__syncDataType__(component,verbose=verbose)
        if componentType == 'fieldgroup':
            self.__syncFieldGroup__(component,verbose=verbose)
        if componentType == 'schema':
            self.__syncSchema__(component,verbose=verbose)
        if componentType == 'class': 
            self.__syncClass__(component,verbose=verbose)
        if componentType == 'identity':
            self.__syncIdentity__(component,verbose=verbose)
        if componentType == 'dataset':
            self.__syncDataset__(component,verbose=verbose)

    def __syncClass__(self,baseClass:'ClassManager',verbose:bool=False)-> dict:
        """
        Synchronize a class to the target sandboxes.
        Arguments:
            baseClass : REQUIRED : class id or name to synchronize
        """
        if not isinstance(baseClass,classmanager.ClassManager):
            raise TypeError("the baseClass must be a classManager instance")
        baseClassName = baseClass.title
        baseBehavior = baseClass.behavior
        for target in self.dict_targetsConfig.keys():
            targetSchema = schema.Schema(config=self.dict_targetsConfig[target])
            t_classes = targetSchema.getClasses()
            if baseClassName in targetSchema.data.classes_id.keys(): ## class already exists in target
                if verbose:
                    print(f"Class '{baseClassName}' already exists in target {target}, checking it")
                targetClassManager = classmanager.ClassManager(targetSchema.data.classes_id[baseClassName],config=self.dict_targetsConfig[target])
                self.dict_targetComponents[target]['class'][baseClassName] = targetClassManager
            else: ## class does not exist in target
                ## For now -> Does not support custom element created in class
                if verbose:
                    print(f"Class '{baseClassName}' does not exists in target {target}, creating it")
                t_newClass = classmanager.ClassManager(title=baseClassName,behavior=baseBehavior,config=self.dict_targetsConfig[target])
                res = t_newClass.createClass()
                self.dict_targetComponents[target]['class'][baseClassName] = t_newClass

            
    def __syncDataType__(self,baseDataType:'DataTypeManager',verbose:bool=False)-> dict:
        """
        Synchronize a data type to the target sandbox.
        Arguments:
            baseDataType : REQUIRED : DataTypeManager object with the data type to synchronize
        """
        if not isinstance(baseDataType,datatypemanager.DataTypeManager):
            raise TypeError("the baseDataType must be a DataTypeManager object")
        name_base_datatype = baseDataType.title
        for target in self.dict_targetsConfig.keys():
            targetSchema = schema.Schema(config=self.dict_targetsConfig[target])
            t_datatype = None
            if name_base_datatype in self.dict_targetComponents[target]['datatype'].keys():
                t_datatype = self.dict_targetComponents[target]['datatype'][name_base_datatype]
            else:
                t_datatypes = targetSchema.getDataTypes()
            if name_base_datatype in targetSchema.data.dataTypes_altId.keys() or t_datatype is not None: ## datatype already exists in target
                if verbose:
                    print(f"datatype '{name_base_datatype}' already exists in target {target}, checking it")
                if t_datatype is None: ## if need toe create the DataTypeManager
                    t_datatype = datatypemanager.DataTypeManager(targetSchema.data.dataTypes_altId[name_base_datatype],config=self.dict_targetsConfig[target],sandbox=target)
                df_base = baseDataType.to_dataframe(full=True)
                df_target = t_datatype.to_dataframe(full=True)
                base_paths = df_base['path'].tolist()
                target_paths = df_target['path'].tolist()
                diff_paths = list(set(base_paths) - set(target_paths))
                if len(diff_paths) > 0: ## there are differences
                    base_datatypes_paths = baseDataType.getDataTypePaths()
                    df_base_limited = df_base[df_base['origin'] == 'self'].copy() ## exclude field group native fields
                    df_base_limited = df_base_limited[~df_base_limited['path'].isin(list(base_datatypes_paths.keys()))] ## exclude base of datatype rows
                    t_datatype.importDataTypeDefinition(df_base_limited)
                    ## handling data types
                    base_dict_path_dtTitle = {}
                    for path,dt_id in base_datatypes_paths.items():
                        tmp_dt_manager = baseDataType.getDataTypeManager(dt_id)
                        self.__syncDataType__(tmp_dt_manager,verbose=verbose)
                        base_dict_path_dtTitle[path] = tmp_dt_manager.title
                    target_datatypes_paths = t_datatype.getDataTypePaths(som_compatible=True)
                    target_datatypes_paths_list = list(target_datatypes_paths.keys())
                    for path,dt_title in base_dict_path_dtTitle.items():
                        if path not in target_datatypes_paths_list:
                            tmp_t_dt = self.dict_targetComponents[target]['datatype'][dt_title]
                            arrayBool = False
                            if path.endswith('[]{}'):
                                arrayBool = True
                                path = path[:-4] ## removing the [] from the path
                            t_datatype.addField(path=path,dataType='dataType',ref=tmp_t_dt.id,array=arrayBool)
                    res = t_datatype.updateDataType()
                    if '$id' not in res.keys():
                        print(res)
                        raise Exception("the data type could not be updated in the target sandbox")
                    else:
                        t_datatype = datatypemanager.DataTypeManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)                     
            else:## datatype does not exist in target
                if verbose:
                    print(f"datatype '{name_base_datatype}' does not exist in target {target}, creating it")
                df_base = baseDataType.to_dataframe(full=True)
                new_datatype = datatypemanager.DataTypeManager(title=name_base_datatype,config=self.dict_targetsConfig[target],sandbox=target)
                base_datatypes_paths = baseDataType.getDataTypePaths()
                df_base_limited = df_base[df_base['origin'] == 'self'].copy() ## exclude field group native fields
                df_base_limited = df_base_limited[~df_base_limited['path'].isin(list(base_datatypes_paths.keys()))] ## exclude base of datatype rows
                new_datatype.importDataTypeDefinition(df_base_limited)
                ## handling data types
                base_dict_path_dtTitle = {}
                for path,dt_id in base_datatypes_paths.items():
                    tmp_dt_manager = baseDataType.getDataTypeManager(dt_id)
                    self.__syncDataType__(tmp_dt_manager,verbose=verbose)
                    base_dict_path_dtTitle[path] = tmp_dt_manager.title
                target_datatypes_paths = new_datatype.getDataTypePaths(som_compatible=True)
                target_datatypes_paths_list = list(target_datatypes_paths.keys())
                for path,dt_title in base_dict_path_dtTitle.items():
                    tmp_t_dt = self.dict_targetComponents[target]['datatype'][dt_title]
                    arrayBool = False
                    if path.endswith('[]{}'):
                        arrayBool = True
                        path = path[:-4] ## removing the [] from the path
                    new_datatype.addField(path=path,dataType='dataType',ref=tmp_t_dt.id,array=arrayBool)
                new_datatype.setDescription(baseDataType.description)
                res = new_datatype.createDataType()
                if '$id' in res.keys():
                    t_datatype = datatypemanager.DataTypeManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
                else:
                    print(res)
                    raise Exception("the data type could not be created in the target sandbox")
            self.dict_targetComponents[target]['datatype'][name_base_datatype] = t_datatype

    def __syncFieldGroup__(self,baseFieldGroup:'FieldGroupManager',verbose:bool=False)-> dict:
        """
        Synchronize a field group to the target sandboxes.
        Argument: 
            baseFieldGroup : REQUIRED : FieldGroupManager object with the field group to synchronize
        """
        if not isinstance(baseFieldGroup,fieldgroupmanager.FieldGroupManager):
            raise TypeError("the baseFieldGroup must be a FieldGroupManager object")
        name_base_fieldgroup = baseFieldGroup.title
        base_fg_classIds = baseFieldGroup.classIds
        for target in self.dict_targetsConfig.keys():
            t_fieldgroup = None
            targetSchema = schema.Schema(config=self.dict_targetsConfig[target])
            ### handling custom class associated with FG
            fg_class_ids = []
            for baseClassId in base_fg_classIds:
                if baseFieldGroup.tenantId[1:] in baseClassId:
                    baseCustomClassManager = classmanager.ClassManager(baseClassId,config=self.baseConfig,localFolder=self.localfolder)
                    self.__syncClass__(baseCustomClassManager,verbose=verbose)
                    fg_class_ids.append(self.dict_targetComponents[target]['class'][baseCustomClassManager.title].id)
                else:
                    fg_class_ids.append(baseClassId)
            if name_base_fieldgroup in self.dict_targetComponents[target]['fieldgroup'].keys():
                t_fieldgroup = self.dict_targetComponents[target]['fieldgroup'][name_base_fieldgroup]
            else:
                t_fieldgroups = targetSchema.getFieldGroups()
            if name_base_fieldgroup in targetSchema.data.fieldGroups_altId.keys() or t_fieldgroup is not None: ## field group already exists in target
                if verbose:
                    print(f"field group '{name_base_fieldgroup}' already exists in target {target}, checking it")
                if t_fieldgroup is None: ## if need to create the FieldGroupManager
                    t_fieldgroup = fieldgroupmanager.FieldGroupManager(targetSchema.data.fieldGroups_altId[name_base_fieldgroup],config=self.dict_targetsConfig[target],sandbox=target)
                df_base = baseFieldGroup.to_dataframe(full=True)
                df_target = t_fieldgroup.to_dataframe(full=True)
                base_paths = df_base['path'].tolist()
                target_paths = df_target['path'].tolist()
                diff_paths = [path for path in base_paths if path not in target_paths]
                if len(diff_paths) > 0:
                    base_datatypes_paths = baseFieldGroup.getDataTypePaths()
                    ## handling fieldgroup native fields
                    df_base_limited = df_base[df_base['origin'] == 'fieldGroup'].copy() ## exclude datatypes
                    df_base_limited = df_base_limited[~df_base_limited['path'].isin(list(base_datatypes_paths.keys()))] ## exclude base of datatype rows
                    df_base_limited = df_base_limited[df_base_limited['origin'] != 'fieldGroup - extended'].copy() ## exclude extended field groups 
                    df_base_limited = df_base_limited.assign(fieldGroup=baseFieldGroup.title)
                    t_fieldgroup.importFieldGroupDefinition(df_base_limited,title=baseFieldGroup.title)
                    ## handling field groups extensions
                    if baseFieldGroup.metaExtend is not None:
                        for fgId in baseFieldGroup.metaExtend:
                            t_fieldgroup.extendFieldGroup(fgId)
                        base_allOf = baseFieldGroup.fieldGroup.get('allOf',[])
                        targetAllOfRef = [el["$ref"] for el in t_fieldgroup.fieldGroup.get('allOf',[])]
                        for el in base_allOf:
                            if el['$ref'] not in targetAllOfRef:
                                t_fieldgroup.fieldGroup['allOf'].append(el)      
                    ## handling data types
                    base_dict_path_dtTitle = {}
                    for path,dt_id in base_datatypes_paths.items():
                        tmp_dt_manager = baseFieldGroup.getDataTypeManager(dt_id)
                        self.__syncDataType__(tmp_dt_manager,verbose=verbose)
                        base_dict_path_dtTitle[path] = tmp_dt_manager.title
                    target_datatypes_paths = t_fieldgroup.getDataTypePaths(som_compatible=True)
                    target_datatypes_paths_list = list(target_datatypes_paths.keys())
                    for path,dt_title in base_dict_path_dtTitle.items():
                        if path not in target_datatypes_paths_list:
                            tmp_t_dt = self.dict_targetComponents[target]['datatype'][dt_title]
                            arrayBool = False
                            if path.endswith('[]{}'):
                                arrayBool = True
                                path = path[:-4] ## removing the [] from the path
                            t_fieldgroup.addField(path=path,dataType='dataType',ref=tmp_t_dt.id,array=arrayBool)
                    if len(t_fieldgroup.classIds) != len(fg_class_ids):
                        t_fieldgroup.updateClassSupported(fg_class_ids)
                    res = t_fieldgroup.updateFieldGroup()
                    if '$id' not in res.keys():
                        raise Exception(res)
                    else:
                        t_fieldgroup = fieldgroupmanager.FieldGroupManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
                else:
                    if len(t_fieldgroup.classIds) != len(fg_class_ids):
                        t_fieldgroup.updateClassSupported(fg_class_ids)
                        res = t_fieldgroup.updateFieldGroup()
                        if '$id' not in res.keys():
                            raise Exception(res)
                        else:
                            t_fieldgroup = fieldgroupmanager.FieldGroupManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
            else: ## field group does not exist in target
                if verbose:
                    print(f"field group '{name_base_fieldgroup}' does not exist in target {target}, creating it")
                df_base = baseFieldGroup.to_dataframe(full=True)
                new_fieldgroup = fieldgroupmanager.FieldGroupManager(title=name_base_fieldgroup,config=self.dict_targetsConfig[target],fg_class=fg_class_ids,sandbox=target)
                base_datatypes_paths = baseFieldGroup.getDataTypePaths(som_compatible=True)
                ## handling field group native field
                df_base_limited = df_base[df_base['origin'] == 'fieldGroup'].copy() ## exclude datatypes fields
                df_base_limited = df_base_limited[~df_base_limited['path'].isin(list(base_datatypes_paths.keys()))] ## exclude base of datatype rows
                df_base_limited = df_base_limited[df_base_limited['origin'] != 'fieldGroup - extended'].copy() ## exclude extended field groups 
                df_base_limited = df_base_limited.assign(fieldGroup=baseFieldGroup.title)
                new_fieldgroup.importFieldGroupDefinition(df_base_limited,title=baseFieldGroup.title)
                ## taking care of field group meta:extends
                if baseFieldGroup.metaExtend is not None:
                    for fgId in baseFieldGroup.metaExtend:
                        new_fieldgroup.extendFieldGroup(fgId)
                    base_allOf = baseFieldGroup.fieldGroup.get('allOf',[])
                    targetAllOfRef = [el["$ref"] for el in new_fieldgroup.fieldGroup.get('allOf',[])]
                    for el in base_allOf:
                        if el['$ref'] not in targetAllOfRef:
                            new_fieldgroup.fieldGroup['allOf'].append(el)
                ## taking care of the datatypes
                base_dict_path_dtTitle = {}
                for path,dt_id in base_datatypes_paths.items():
                    tmp_dt_manager = baseFieldGroup.getDataTypeManager(dt_id)
                    self.__syncDataType__(tmp_dt_manager,verbose=verbose)
                    base_dict_path_dtTitle[path] = tmp_dt_manager.title
                for path,dt_title in base_dict_path_dtTitle.items():
                    tmp_t_dt = self.dict_targetComponents[target]['datatype'][dt_title]
                    arrayBool = False
                    if path.endswith('[]{}'):
                        arrayBool = True
                        path = path[:-4] ## removing the [] from the path
                    new_fieldgroup.addField(path=path,dataType='dataType',ref=tmp_t_dt.id,array=arrayBool)
                new_fieldgroup.setDescription(baseFieldGroup.description)
                res = new_fieldgroup.createFieldGroup()
                if '$id' in res.keys():
                    t_fieldgroup = fieldgroupmanager.FieldGroupManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
                else:
                    print(res)
                    raise Exception("the field group could not be created in the target sandbox")
            self.dict_targetComponents[target]['fieldgroup'][name_base_fieldgroup] = t_fieldgroup


    def __syncSchema__(self,baseSchema:'SchemaManager',verbose:bool=False)-> dict:
        """
        Sync the schema to the target sandboxes.
        Arguments:
            baseSchema : REQUIRED : SchemaManager object to synchronize
        """
        ## TO DO -> sync required fields
        if not isinstance(baseSchema,schemamanager.SchemaManager):
            raise TypeError("the baseSchema must be a SchemaManager object")
        name_base_schema = baseSchema.title
        descriptors = baseSchema.getDescriptors()
        base_field_groups_names = list(baseSchema.fieldGroups.values())
        dict_base_fg_name_id = {name:fg_id for fg_id,name in baseSchema.fieldGroups.items()}
        for target in self.dict_targetsConfig.keys():
            targetSchemaAPI = schema.Schema(config=self.dict_targetsConfig[target])
            t_schemas = targetSchemaAPI.getSchemas()
            t_fieldGroups = targetSchemaAPI.getFieldGroups()
            if name_base_schema in targetSchemaAPI.data.schemas_altId.keys(): ## schema already exists in target
                if verbose:
                    print(f"schema '{name_base_schema}' already exists in target {target}, checking it")
                t_schema = schemamanager.SchemaManager(targetSchemaAPI.data.schemas_altId[name_base_schema],config=self.dict_targetsConfig[target],sandbox=target)
                new_fieldgroups = [fg for fg in base_field_groups_names if fg not in t_schema.fieldGroups.values()]
                existing_fieldgroups = [fg for fg in base_field_groups_names if fg in t_schema.fieldGroups.values()]
                if len(new_fieldgroups) > 0: ## if new field groups
                    if verbose:
                        print('found new field groups to add to the schema')
                    for new_fieldgroup in new_fieldgroups:
                        if baseSchema.tenantId[1:] not in dict_base_fg_name_id[new_fieldgroup]: ## ootb field group
                            if verbose:
                                print(f"field group '{new_fieldgroup}' is a OOTB field group, using it")
                            self.dict_targetComponents[target]['fieldgroup'][new_fieldgroup] = fieldgroupmanager.FieldGroupManager(dict_base_fg_name_id[new_fieldgroup],config=self.dict_targetsConfig[target],sandbox=target)
                            t_schema.addFieldGroup(self.dict_targetComponents[target]['fieldgroup'][new_fieldgroup].id)
                        else:
                            if verbose:
                                print(f"field group '{new_fieldgroup}' is a custom field group, syncing it")
                            tmp_FieldGroup = baseSchema.getFieldGroupManager(new_fieldgroup)
                            self.__syncFieldGroup__(tmp_FieldGroup,verbose=verbose)
                            t_schema.addFieldGroup(self.dict_targetComponents[target]['fieldgroup'][new_fieldgroup].id)
                    t_schema.setDescription(baseSchema.description)
                    res = t_schema.updateSchema()
                    if '$id' not in res.keys():
                        raise Exception(res)
                    else:
                        t_schema = schemamanager.SchemaManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
                ## handling descriptors
                for fg_name in existing_fieldgroups:
                    if baseSchema.tenantId[1:] in dict_base_fg_name_id[fg_name]: ## custom field group
                        tmp_fieldGroupManager = fieldgroupmanager.FieldGroupManager(dict_base_fg_name_id[fg_name],config=self.baseConfig,sandbox=target,localFolder=self.localfolder)
                        self.__syncFieldGroup__(tmp_fieldGroupManager,verbose=verbose)
                    else:
                        if verbose:
                            print(f"field group '{fg_name}' is a OOTB field group, using it")
                        self.dict_targetComponents[target]['fieldgroup'][fg_name] = fieldgroupmanager.FieldGroupManager(dict_base_fg_name_id[fg_name],config=self.dict_targetsConfig[target],sandbox=target)
                list_new_descriptors = self.__syncDescriptor__(baseSchema,t_schema,targetSchemaAPI=targetSchemaAPI,verbose=verbose)
                self.dict_targetComponents[target]['schemaDescriptors'][name_base_schema] = list_new_descriptors
            else: ## schema does not exist in target
                if verbose:
                    print(f"schema '{name_base_schema}' does not exist in target {target}, creating it")
                ## Check schema class: 
                ## Limited support -> does not support custom elements defined in classes
                baseClassId = baseSchema.classId
                tenantidId = baseSchema.tenantId
                if tenantidId[1:] in baseClassId: ## custom class
                    baseClassManager = classmanager.ClassManager(baseClassId,config=self.baseConfig,sandbox=target,localFolder=self.localfolder,sandboxBase=self.baseSandbox,tenantidId=tenantidId)
                    self.__syncClass__(baseClassManager,verbose=verbose)
                    targetClassManager = self.dict_targetComponents[target]['class'][baseClassManager.title]
                    classId_toUse = targetClassManager.id
                else:
                    classId_toUse = baseClassId
                new_schema = schemamanager.SchemaManager(title=name_base_schema,config=self.dict_targetsConfig[target],schemaClass=classId_toUse,sandbox=target)
                for fg_name in base_field_groups_names:
                    if baseSchema.tenantId[1:] not in dict_base_fg_name_id[fg_name]: ## ootb field group
                        new_schema.addFieldGroup(dict_base_fg_name_id[fg_name])
                        if verbose:
                            print(f"field group '{fg_name}' is a OOTB field group, using it")
                        ## adding the field group to the target components
                        self.dict_targetComponents[target]['fieldgroup'][fg_name] = fieldgroupmanager.FieldGroupManager(dict_base_fg_name_id[fg_name],config=self.dict_targetsConfig[target],sandbox=target)
                    else:
                        tmp_FieldGroup = baseSchema.getFieldGroupManager(fg_name)
                        self.__syncFieldGroup__(tmp_FieldGroup,verbose=verbose)
                        new_schema.addFieldGroup(self.dict_targetComponents[target]['fieldgroup'][fg_name].id)
                new_schema.setDescription(baseSchema.description)
                res = new_schema.createSchema()
                if '$id' in res.keys():
                    t_schema = schemamanager.SchemaManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
                else:
                    print(res)
                    raise Exception("the schema could not be created in the target sandbox")
                ## handling descriptors
                list_new_descriptors = self.__syncDescriptor__(baseSchema,t_schema,targetSchemaAPI,verbose=verbose)
                self.dict_targetComponents[target]['schemaDescriptors'][name_base_schema] = list_new_descriptors
            self.dict_targetComponents[target]['schema'][name_base_schema] = t_schema

    def __syncDescriptor__(self,baseSchemaManager:'SchemaManager'=None,targetSchemaManager:'SchemaManager'=None,targetSchemaAPI:'Schema'=None,verbose:bool=False)-> dict:
        """
        Synchronize a descriptor to the target schema.
        Arguments:
            baseSchemaManager : REQUIRED : SchemaManager object with the base schema
            targetSchemaManager : REQUIRED : SchemaManager object with the target schema
        """
        if baseSchemaManager is None:
            raise ValueError("the baseSchemaManager must be provided")
        if targetSchemaManager is None:
            raise ValueError("the targetSchemaManager must be provided")
        if not isinstance(baseSchemaManager,schemamanager.SchemaManager):
            raise TypeError("the baseSchemaMaanger must be a SchemaManager object")
        if not isinstance(targetSchemaManager,schemamanager.SchemaManager):
            raise TypeError("the targetSchemaManager must be a SchemaManager object")
        base_descriptors = baseSchemaManager.getDescriptors()
        if self.baseConfig is not None:
            baseSchemaAPI = schema.Schema(config=self.baseConfig)
            myschemas = baseSchemaAPI.getSchemas() ## to populate the data object
        elif self.localfolder is not None:
            myschemas = []
            for json_file in self.schemaFolder.glob('*.json'):
                myschemas.append(json.load(FileIO(json_file)))
        target_descriptors = targetSchemaManager.getDescriptors()
        list_descriptors = []
        for baseDescriptor in base_descriptors:
            descType = baseDescriptor['@type']
            if verbose:
                print(f"Synchronizing descriptors '{descType}'")
            match descType:
                case "xdm:descriptorIdentity":
                    target_identitiesDecs = [desc for desc in target_descriptors if desc['@type'] == 'xdm:descriptorIdentity']
                    baseIdentityNS = baseDescriptor['xdm:namespace']
                    if self.baseConfig is not None and self.localfolder is None:
                        identityConn = identity.Identity(config=self.baseConfig,region=self.region)
                        baseIdentities = identityConn.getIdentities()
                    elif self.localfolder is not None:
                        baseIdentities = []
                        for file in self.identityFolder.glob('*.json'):
                            id_file = json.load(FileIO(file))
                            baseIdentities.append(id_file)
                    if baseIdentityNS not in [el['xdm:namespace'] for el in target_identitiesDecs]: ## identity descriptor does not exists in target schema
                        def_identity = [el for el in baseIdentities if el['code'] == baseIdentityNS][0]
                        self.__syncIdentity__(def_identity,verbose=verbose)
                        new_desc = targetSchemaManager.createDescriptorOperation(descType=descType,
                                                                            completePath=baseDescriptor['xdm:sourceProperty'],
                                                                            identityNSCode=baseIdentityNS,
                                                                            identityPrimary=baseDescriptor['xdm:isPrimary'],
                                                                            )
                        res = targetSchemaManager.createDescriptor(new_desc)
                    else:
                        res = [el for el in target_identitiesDecs if el['xdm:namespace'] == baseIdentityNS][0]
                    list_descriptors.append(res)
                case "xdm:descriptorOneToOne": ## lookup definition
                    target_OneToOne = [desc for desc in target_descriptors if desc['@type'] == 'xdm:descriptorOneToOne']
                    base_targetSchemaId = baseDescriptor['xdm:destinationSchema']
                    if self.baseConfig is not None:                        
                        base_targetSchemaName = [schemaName for schemaName,schemaId in baseSchemaAPI.data.schemas_id.items() if schemaId == base_targetSchemaId][0]
                    elif self.localfolder is not None:
                        base_targetSchemaName = [sc['title'] for sc in myschemas if sc['$id'] == base_targetSchemaId][0]
                    if base_targetSchemaName in list(targetSchemaAPI.data.schemas_altId.keys()):## schema already exists in target
                        target_targetSchemaId = targetSchemaAPI.data.schemas_id[base_targetSchemaName]
                        ## checking if the descriptor already exists in target
                        if target_targetSchemaId not in [el['xdm:destinationSchema'] for el in target_OneToOne]: ## descriptor does not exist in target
                            new_desc = targetSchemaManager.createDescriptorOperation(descType=descType,
                                                                        completePath=baseDescriptor['xdm:sourceProperty'],
                                                                        targetSchema=target_targetSchemaId)
                            res = targetSchemaManager.createDescriptor(new_desc)
                        else:
                            res = [el for el in target_OneToOne if el['xdm:destinationSchema'] == target_targetSchemaId][0]
                    else: ## schema does not exist in target
                        if self.baseConfig is not None and self.localfolder is None:
                            base_targetSchemaManager = schemamanager.SchemaManager(base_targetSchemaId,config=self.baseConfig)
                        elif self.localfolder is not None:
                            for file in self.schemaFolder.glob('*.json'):
                                base_targetSchema = json.load(FileIO(file))
                                if base_targetSchema['$id'] == base_targetSchemaId:
                                    base_targetSchemaManager = schemamanager.SchemaManager(base_targetSchema,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                                    break
                        self.__syncSchema__(base_targetSchemaManager,verbose=verbose)
                        target_targetSchemaId = self.dict_targetComponents[targetSchemaManager.sandbox]['schema'][base_targetSchemaName].id
                        new_desc = targetSchemaManager.createDescriptorOperation(descType=descType,
                                                                        completePath=baseDescriptor['xdm:sourceProperty'],
                                                                        targetSchema=target_targetSchemaId)
                        res = targetSchemaManager.createDescriptor(new_desc)
                    list_descriptors.append(res)
                case "xdm:descriptorLabel":
                    ## handling labels on Field Groups
                    labels = baseDescriptor['xdm:labels']
                    fgId = baseDescriptor['xdm:sourceSchema']
                    baseFG = baseSchemaManager.getFieldGroupManager(fgId)
                    targetFG = self.dict_targetComponents[targetSchemaManager.sandbox]['fieldgroup'][baseFG.title]
                    target_descriptors = targetFG.getDescriptors()
                    if baseDescriptor["xdm:sourceProperty"] not in [el['xdm:sourceProperty'] for el in target_descriptors]: ## descriptor does not exist in target
                        new_desc = targetFG.createDescriptorOperation(descType=descType,
                                                                        completePath=baseDescriptor['xdm:sourceProperty'],
                                                                        labels=labels,
                                                                        )
                        res = targetFG.createDescriptor(new_desc)
                    else: ## descriptor already exists in target
                        ## check if all labels are the same
                        res = [el for el in target_descriptors if el['xdm:sourceProperty'] == baseDescriptor["xdm:sourceProperty"]][0]
                        target_labels = res['xdm:labels']
                        if len(target_labels) != len(labels):
                            new_def = {"@type": res["@type"],'xdm:sourceProperty':res['xdm:sourceProperty'],
                                        'xdm:sourceSchema':res['xdm:sourceSchema'],"xdm:sourceVersion":int(res['xdm:sourceVersion'])+1,
                                        'xdm:labels':labels}
                            res = targetFG.updateDescriptor(new_def)
                    list_descriptors.append(res)
                            
                case "xdm:alternateDisplayInfo":
                    target_alternateDisplayInfo = [desc for desc in target_descriptors if desc['@type'] == 'xdm:alternateDisplayInfo']
                    alternateTitle = baseDescriptor.get('xdm:title',{}).get('en_us',None)
                    alternateDescription = baseDescriptor.get('xdm:description',{}).get('en_us',None)
                    alternateDescription = baseDescriptor.get('xdm:description',{}).get('en_us',None)
                    alternateNote = baseDescriptor.get('xdm:note',{}).get('en_us',None)
                    alternateEnum = baseDescriptor.get('xdm:excludeMetaEnum',None)
                    alternateDescription = baseDescriptor.get('xdm:description',{}).get('en_us',None)
                    if baseDescriptor['xdm:sourceProperty'] not in [el['xdm:sourceProperty'] for el in target_alternateDisplayInfo]: ## descriptor does not exists in target
                        new_desc = targetSchemaManager.createDescriptorOperation(descType=descType,
                                                                            completePath=baseDescriptor['xdm:sourceProperty'],
                                                                            alternateTitle=alternateTitle,alternateDescription=alternateDescription,
                                                                            alternateNote=alternateNote,alternateEnum=alternateEnum)
                        res = targetSchemaManager.createDescriptor(new_desc)
                    else: ## descriptor already exists in target
                        res = [el for el in target_alternateDisplayInfo if el['xdm:sourceProperty'] == baseDescriptor['xdm:sourceProperty']][0]
                        target_alternateTitle = res.get('xdm:title',{}).get('en_us',None)
                        target_alternateNote = res.get('xdm:note',{}).get('en_us',None)
                        target_alternateDescription = res.get('xdm:description',{}).get('en_us',None)
                        target_alternateNote = baseDescriptor.get('xdm:note',{}).get('en_us',None)
                        target_alternateEnum = baseDescriptor.get('xdm:excludeMetaEnum',None)
                        ## check if the alternateTitle, alternateNote and alternateDescription are the same
                        if target_alternateTitle != alternateTitle or target_alternateNote != alternateNote or target_alternateDescription != alternateDescription or str(target_alternateEnum) != str(alternateEnum):
                            new_desc = targetSchemaManager.createDescriptorOperation(descType=descType,
                                                                            completePath=baseDescriptor['xdm:sourceProperty'],
                                                                            alternateTitle=alternateTitle,alternateDescription=alternateDescription,
                                                                            alternateNote=alternateNote,alternateEnum=alternateEnum)
                            res = targetSchemaManager.updateDescriptor(new_def)
                    list_descriptors.append(res)
                case "xdm:descriptorReferenceIdentity": ## can be referenced by other schemas
                    baseIdentityNS = baseDescriptor['xdm:identityNamespace']
                    if self.baseConfig is not None and self.localfolder is None:
                        identityConn = identity.Identity(config=self.baseConfig,region=self.region)
                        baseIdentities = identityConn.getIdentities()
                    elif self.localfolder is not None:
                        baseIdentities = []
                        for file in self.identityFolder.glob('*.json'):
                            id_file = json.load(FileIO(file))
                            baseIdentities.append(id_file)
                    def_identity = [el for el in baseIdentities if el['code'] == baseIdentityNS][0]
                    self.__syncIdentity__(def_identity,verbose=verbose)
                    target_referenceIdentity = [desc for desc in target_descriptors if desc['@type'] == 'xdm:descriptorReferenceIdentity']
                    if baseDescriptor['xdm:sourceProperty'] not in [el['xdm:sourceProperty'] for el in target_referenceIdentity]: ## descriptor does not exists in target
                        new_desc = targetSchemaManager.createDescriptorOperation(descType=descType,
                                                                        completePath=baseDescriptor['xdm:sourceProperty'],
                                                                        identityNSCode=baseDescriptor['xdm:identityNamespace'],
                                                                        )
                        res = targetSchemaManager.createDescriptor(new_desc)
                    else: ## descriptor already exists in target
                        res = [el for el in target_referenceIdentity if el['xdm:sourceProperty'] == baseDescriptor['xdm:sourceProperty']][0]
                    list_descriptors.append(res)
                case "xdm:descriptorDeprecated":
                    target_deprecated = [desc for desc in target_descriptors if desc['@type'] == 'xdm:descriptorDeprecated']
                    if baseDescriptor['xdm:sourceProperty'] not in [el['xdm:sourceProperty'] for el in target_deprecated]: ## descriptor does not exists in target
                        new_desc = targetSchemaManager.createDescriptorOperation(descType=descType,completePath=baseDescriptor['xdm:sourceProperty'])
                        res = targetSchemaManager.createDescriptor(new_desc)
                    else:
                        res = [el for el in target_deprecated if el['xdm:sourceProperty'] == baseDescriptor['xdm:sourceProperty']][0]
                    list_descriptors.append(res)
        return list_descriptors

    def __syncIdentity__(self,identityDefiniton:dict,verbose:bool=False)-> dict:
        """
        Synchronize an identity to the target sandboxes.
        Arguments:
            identityDefinition : REQUIRED : dictionary with the identity definition
        """
        if not isinstance(identityDefiniton,dict):
            raise TypeError("the identityDefinition must be a dictionary")
        code_base_identity = identityDefiniton['code']
        for target in self.dict_targetsConfig.keys():
            targetIdentity = identity.Identity(config=self.dict_targetsConfig[target],region=self.region)
            t_identities = targetIdentity.getIdentities()
            if code_base_identity in [el['code'] for el in t_identities]:## identity already exists in target
                if verbose:
                    print(f"identity '{code_base_identity}' already exists in target {target}, saving it")
                self.dict_targetComponents[target]['identities'][code_base_identity] = [el for el in t_identities if el['code'] == code_base_identity][0]
            else:
                if verbose:
                    print(f"identity '{code_base_identity}' does not exist in target {target}, creating it")
                identityDef = {'name':identityDefiniton['name'],'code':identityDefiniton['code'],'namespaceType':identityDefiniton['namespaceType'],"idType":identityDefiniton['idType'],'description':identityDefiniton.get('description','')}
                res = targetIdentity.createIdentity(dict_identity=identityDef)
                if 'code' in res.keys():
                    self.dict_targetComponents[target]['identities'][code_base_identity] = identityDef
                else:
                    print(res)
                    raise Exception("the identity could not be created in the target sandbox")
    
    def __syncDataset__(self,baseDataset:dict,verbose:bool=False)-> dict:
        """
        Synchronize the dataset to the target sandboxes. Mostly creating a new dataset and associated artefacts when not already created.
        Arguments:
            baseDataset : REQUIRED : dictionary with the dataset definition
        """
        if len(baseDataset) == 1: ## if receiving the dataset as provided by the API {datasetId:{...definition}}
            baseDataset = deepcopy(baseDataset[list(baseDataset.keys()[0])])
        base_datasetName = baseDataset['name']
        base_dataset_related_schemaId = baseDataset['schemaRef']['id']
        if self.baseConfig is not None:
            baseSchemaAPI = schema.Schema(config=self.baseConfig)
            base_schemas = baseSchemaAPI.getSchemas()
            base_dataset_related_schemaName = [schemaName for schemaName,schemaId in baseSchemaAPI.data.schemas_id.items() if schemaId == base_dataset_related_schemaId][0]
        elif self.localfolder is not None:
            base_schemas = []
            for json_file in self.schemaFolder.glob('*.json'):
                base_schemas.append(json.load(FileIO(json_file)))
            base_dataset_related_schemaName = [sc['title'] for sc in base_schemas if sc['$id'] == base_dataset_related_schemaId][0]
        for target in self.dict_targetsConfig.keys():
            targetCatalog = catalog.Catalog(config=self.dict_targetsConfig[target])
            t_datasets = targetCatalog.getDataSets()
            if base_datasetName not in targetCatalog.data.ids.keys(): ## only taking care if dataset does not exist
                if verbose:
                    print(f"dataset '{base_datasetName}' does not exist in target {target}, creating it")
                targetSchema = schema.Schema(config=self.dict_targetsConfig[target])
                t_schemas = targetSchema.getSchemas()
                if base_dataset_related_schemaName not in targetSchema.data.schemas_altId.keys(): ## schema does not exist in target
                    if verbose:
                        print(f"related schema '{base_dataset_related_schemaName}' does not exist in target {target}, creating it")
                    baseSchemaManager = schemamanager.SchemaManager(base_dataset_related_schemaId,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                    self.__syncSchema__(baseSchemaManager,verbose=verbose)
                    targetSchemaId = self.dict_targetComponents[target]['schema'][base_dataset_related_schemaName].id
                    res = targetCatalog.createDataSet(name=base_datasetName,schemaId=targetSchemaId)
                    self.dict_targetComponents[target]['datasets'][base_datasetName] = res
                else: ## schema already exists in target
                    if verbose:
                        print(f"related schema '{base_dataset_related_schemaName}' does exist in target {target}, checking it")
                    baseSchemaManager = schemamanager.SchemaManager(base_dataset_related_schemaId,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                    self.__syncSchema__(baseSchemaManager,verbose=verbose)
                    targetSchemaId = targetSchema.data.schemas_id[base_dataset_related_schemaName]
                    res = targetCatalog.createDataSet(name=base_datasetName,schemaId=targetSchemaId)
                    self.dict_targetComponents[target]['datasets'][base_datasetName] = res
            else: ## dataset already exists in target
                if verbose:
                    print(f"dataset '{base_datasetName}' already exists in target {target}, checking its schema")
                t_dataset = targetCatalog.getDataSet(targetCatalog.data.ids[base_datasetName])
                targetSchema = schema.Schema(config=self.dict_targetsConfig[target])
                t_schemas = targetSchema.getSchemas()
                baseSchemaManager = schemamanager.SchemaManager(base_dataset_related_schemaId,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                self.__syncSchema__(baseSchemaManager,verbose=verbose)

