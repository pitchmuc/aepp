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
from aepp import schema, schemamanager, fieldgroupmanager, datatypemanager,classmanager,identity,catalog,customerprofile,segmentation
from copy import deepcopy
from typing import Union
from pathlib import Path
from io import FileIO
from .configs import ConnectObject
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

class Synchronizer:
    ## TO DO -> Add support for local environment
    def __init__(self,
                 targets:list|None=None,
                 config:ConnectObject|None=None,
                 baseSandbox:str|None=None,
                 region:str='nld2',
                 localFolder:str|list|None=None):
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
        self.baseConfig = None
        self.baseSandbox = None
        self.dict_tag_name_id = {}
        if targets is None:
            raise ValueError("a list of target sandboxes must be provided - at least one")
        if config is None or type(config) != ConnectObject:
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
            if isinstance(localFolder, str):
                self.localfolder = [Path(localFolder)]
            else:
                self.localfolder = [Path(folder) for folder in localFolder]
            self.classFolder = [folder / 'class' for folder in self.localfolder]
            self.schemaFolder = [folder / 'schema' for folder in self.localfolder]
            self.fieldgroupFolder = [folder / 'fieldgroup' for folder in self.localfolder]
            self.fieldgroupGlobalFolder = [folder / 'global' for folder in self.fieldgroupFolder]
            self.datatypeFolder = [folder / 'datatype' for folder in self.localfolder]
            self.datatypeGlobalFolder = [folder / 'global' for folder in self.datatypeFolder]
            self.identityFolder = [folder / 'identity' for folder in self.localfolder]
            self.datasetFolder = [folder / 'dataset' for folder in self.localfolder]
            self.descriptorFolder = [folder / 'descriptor' for folder in self.localfolder]
            self.mergePolicyFolder = [folder / 'mergepolicy' for folder in self.localfolder]
            self.audienceFolder = [folder / 'audience' for folder in self.localfolder]
            self.tagFolder = [folder / 'tag' for folder in self.localfolder]
            for folder in self.tagFolder:
                try:
                    if folder.exists():
                        with open(folder / 'tags.json','r') as f:
                            tags_file = json.load(f)
                        for tag in tags_file:
                            self.dict_tag_name_id[tag['name']] = tag['id']
                    pass
                except Exception as e:
                    print(f"could not load tags from folder {folder} : {e}")
                    pass
            if baseSandbox is not None:
                self.baseSandbox = baseSandbox
            else:
                try:
                    for folder in self.localfolder:
                        if Path(folder / 'config.json').exists():
                            with open(folder / 'config.json','r') as f:
                                local_config = json.load(f)
                                if 'sandbox' in local_config.keys():
                                    self.baseSandbox = local_config['sandbox']
                                    break
                except Exception as e:
                    raise ValueError("baseSandbox must be provided in the constructor or in the config.json file in the local folder")
        self.dict_targetsConfig = {target: aepp.configure(org_id=config_object['org_id'],client_id=config_object['client_id'],scopes=config_object['scopes'],secret=config_object['secret'],sandbox=target,connectInstance=True) for target in targets}
        self.region = region
        self.dict_baseComponents = {'schema':{},'class':{},'fieldgroup':{},'datatype':{},'datasets':{},'identities':{},"schemaDescriptors":{},'mergePolicy':{},'audience':{}}  
        self.dict_targetComponents = {target:{'schema':{},'class':{},'fieldgroup':{},'datatype':{},'datasets':{},'identities':{},"schemaDescriptors":{},'mergePolicy':{},'audience':{}} for target in targets}

    def flush_cache(self)-> None:
        """
        Flush the component cache of the synchronizer. It will clear the cache of the base sandbox and the target sandboxes.
        """
        self.dict_baseComponents = {'schema':{},'class':{},'fieldgroup':{},'datatype':{},'datasets':{},'identities':{},"schemaDescriptors":{},'mergePolicy':{},'audience':{}}  
        self.dict_targetComponents = {target:{'schema':{},'class':{},'fieldgroup':{},'datatype':{},'datasets':{},'identities':{},"schemaDescriptors":{},'mergePolicy':{},'audience':{}} for target in self.dict_targetsConfig.keys()}

    def getSyncFieldGroupManager(self,fieldgroup:str,sandbox:str|None=None)-> dict:
        """
        Get a field group Manager from the synchronizer.
        It searches through the component cache to see if the FieldGroupManager for the target sandbox is already instantiated.
        If not, it generate an error.
        Arguments:
            fieldgroup : REQUIRED : Either $id, or name or alt:Id of the field group to get
            sandbox : REQUIRED : name of the sandbox to get the field group from
        """
        if sandbox is None:
            raise ValueError("a sandbox name must be provided")
        if sandbox == self.baseSandbox:
            if fieldgroup in self.dict_baseComponents['fieldgroup'].keys():
                return self.dict_baseComponents['fieldgroup'][fieldgroup]
            elif fieldgroup in [self.dict_baseComponents['fieldgroup'][fg].id for fg in self.dict_baseComponents['fieldgroup'].keys()]:
                fg_key = [fg for fg in self.dict_baseComponents['fieldgroup'].keys() if self.dict_baseComponents['fieldgroup'][fg].id == fieldgroup][0]
                return self.dict_baseComponents['fieldgroup'][fg_key]
            elif fieldgroup in [self.dict_baseComponents['fieldgroup'][fg].altId for fg in self.dict_baseComponents['fieldgroup'].keys()]:
                fg_key = [fg for fg in self.dict_baseComponents['fieldgroup'].keys() if self.dict_baseComponents['fieldgroup'][fg].altId == fieldgroup][0]
                return self.dict_baseComponents['fieldgroup'][fg_key]
            else:
                raise ValueError(f"the field group '{fieldgroup}' has not been synchronized to the sandbox '{sandbox}'")
        else:
            if fieldgroup in self.dict_targetComponents[sandbox]['fieldgroup'].keys():
                return self.dict_targetComponents[sandbox]['fieldgroup'][fieldgroup]
            elif fieldgroup in [self.dict_targetComponents[sandbox]['fieldgroup'][fg].id for fg in self.dict_targetComponents[sandbox]['fieldgroup'].keys()]:
                fg_key = [fg for fg in self.dict_targetComponents[sandbox]['fieldgroup'].keys() if self.dict_targetComponents[sandbox]['fieldgroup'][fg].id == fieldgroup][0]
                return self.dict_targetComponents[sandbox]['fieldgroup'][fg_key]
            elif fieldgroup in [self.dict_targetComponents[sandbox]['fieldgroup'][fg].altId for fg in self.dict_targetComponents[sandbox]['fieldgroup'].keys()]:
                fg_key = [fg for fg in self.dict_targetComponents[sandbox]['fieldgroup'].keys() if self.dict_targetComponents[sandbox]['fieldgroup'][fg].altId == fieldgroup][0]
                return self.dict_targetComponents[sandbox]['fieldgroup'][fg_key]
            else:
                raise ValueError(f"the field group '{fieldgroup}' has not been synchronized to the sandbox '{sandbox}'")
    
    def getDatasetName(self,datasetId:str,sandbox:str|None=None)-> str:
        """
        Get a dataset name from the synchronizer base on the ID of the dataset.
        Arguments:
            datasetId : REQUIRED : id of the dataset to get
            sandbox : REQUIRED : name of the sandbox to get the dataset from
        """
        if sandbox is None:
            raise ValueError("a sandbox name must be provided")
        if sandbox == self.baseSandbox:
            if datasetId in [item.get('id') for key,item in self.dict_baseComponents['datasets'].items()]:
                return [key for key,item in self.dict_baseComponents['datasets'].items() if item.get('id') == datasetId][0]
            else:
                raise ValueError(f"the dataset '{datasetId}' has not been synchronized to the sandbox '{sandbox}'")
        else:
            if datasetId in [item.get('id') for key,item in self.dict_targetComponents[sandbox]['datasets'].items()]:
                return [key for key,item in self.dict_targetComponents[sandbox]['datasets'].items() if item.get('id') == datasetId][0]
            else:
                raise ValueError(f"the dataset '{datasetId}' has not been synchronized to the sandbox '{sandbox}'")

    def syncComponent(self,component:Union[str,dict],componentType:str|None=None,force:bool=False,verbose:bool=False)-> dict:
        """
        Synchronize a component to the target sandbox.
        The component could be a string (name or id of the component in the base sandbox) or a dictionary with the definition of the component.
        If the component is a string, you have to have provided a base sandbox in the constructor.
        Arguments:
            component : REQUIRED : name or id of the component or a dictionary with the component definition
            componentType : OPTIONAL : type of the component (e.g. "schema", "fieldgroup", "datatype", "class", "identity", "dataset", "mergepolicy", "audience"). Required if a string is passed. 
                It is not required but if the type cannot be inferred from the component, it will raise an error. 
            force : OPTIONAL : if True, it will force the synchronization of the component even if it already exists in the target sandbox. Works for Schema, FieldGroup, DataType and Class.
            verbose : OPTIONAL : if True, it will print the details of the synchronization process
        """
        if type(component) == str:
            if self.baseConfig is None and self.localfolder is None:
                raise ValueError("a base sandbox or a local folder must be provided to synchronize a component by name or id")
            if componentType is None:
                raise ValueError("the type of the component must be provided if the component is a string")
            if componentType not in ['schema', 'fieldgroup', 'datatype', 'class', 'identity', 'dataset', 'mergepolicy', 'audience']:
                raise ValueError("the type of the component is not supported. Please provide one of the following types: schema, fieldgroup, datatype, class, identity, dataset, mergepolicy, audience")
            if componentType in ['schema', 'fieldgroup', 'datatype', 'class']:
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
                        for folder in self.schemaFolder:
                            for file in folder.glob('*.json'):
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
                        for folder in self.fieldgroupFolder:
                            for file in folder.glob('*.json'):
                                fg_file = json.load(FileIO(file))
                                if fg_file['title'] == component or fg_file['$id'] == component or fg_file['meta:altId'] == component:
                                    component = fg_file
                                    break
                    component = fieldgroupmanager.FieldGroupManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                elif componentType == 'datatype':    
                    if base_schema is not None:
                        datatypes = base_schema.getDataTypes()
                        if component in base_schema.data.dataTypes_altId.keys():## replacing name with altId
                            component = base_schema.data.dataTypes_altId[component]
                    if self.localfolder is not None:
                        for folder in self.datatypeFolder:
                            for file in folder.glob('*.json'):
                                dt_file = json.load(FileIO(file))
                                if dt_file['title'] == component or dt_file['$id'] == component or dt_file['meta:altId'] == component:
                                    component = dt_file
                                    break
                    component = datatypemanager.DataTypeManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                elif componentType == 'class':
                    if base_schema is not None:
                        classes = base_schema.getClasses()
                        if component in base_schema.data.classes_altId.keys():## replacing name 
                            component = base_schema.data.classes_altId[component]
                    if self.localfolder is not None:
                        for folder in self.classFolder:
                            for file in folder.glob('*.json'):
                                class_file = json.load(FileIO(file))
                                if class_file['title'] == component or class_file['$id'] == component or class_file['meta:altId'] == component:
                                    component = class_file
                                    break
                    component = classmanager.ClassManager(component,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
            elif componentType == 'identity':
                if self.baseConfig is not None:
                    id_base = identity.Identity(config=self.baseConfig,region=self.region)
                    identities:list = id_base.getIdentities()
                elif self.localfolder is not None:
                    identities = []
                    for folder in self.identityFolder:
                        for file in folder.glob('*.json'):
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
                    found = False
                    for folder in self.datasetFolder:
                        for file in folder.glob('*.json'):
                            ds_file = json.load(FileIO(file))
                            if ds_file['id'] == component or ds_file['name'] == component:
                                if len(ds_file.get('unifiedTags',[])) > 0 and self.dict_tag_name_id is not None:
                                    ds_file['unifiedTags'] = [self.dict_tag_name_id[tag_name] for tag_name in ds_file.get('unifiedTags',[]) if tag_name in self.dict_tag_name_id.keys()]
                                component = ds_file
                                found = True
                                break
                        if found:
                            break
                    if found == False:
                        raise ValueError("the dataset could not be found in the local folder")
                if len(component) == 1: ## if the component is the catalog API response {'key': {dataset definition}}
                    component = component[list(component.keys())[0]] ## accessing the real dataset definition
            elif componentType == "mergepolicy":
                if self.baseConfig is not None:
                    ups_base = customerprofile.Profile(config=self.baseConfig)
                    base_mergePolicies = ups_base.getMergePolicies()
                    if component in [el.get('id','') for el in base_mergePolicies] or component in [el.get('name','') for el in base_mergePolicies]:
                        component = [el for el in base_mergePolicies if el.get('id','') == component or el.get('name','') == component][0]
                elif self.localfolder is not None:
                    for folder in self.mergePolicyFolder:
                        for file in folder.glob('*.json'):
                            mp_file = json.load(FileIO(file))
                            if mp_file.get('id','') == component or mp_file.get('name','') == component:
                                component = mp_file
                                break
            elif componentType == 'audience':
                if self.baseConfig is not None:
                    seg_base = segmentation.Segmentation(config=self.baseConfig)
                    base_audiences = seg_base.getAudiences()
                    if component in [el.get('id','') for el in base_audiences] or component in [el.get('name','') for el in base_audiences]:
                        component = [el for el in base_audiences if el.get('id','') == component or el.get('name','') == component][0]
                elif self.localfolder is not None:
                    for folder in self.audienceFolder:
                        for file in folder.glob('*.json'):
                            au_file = json.load(FileIO(file))
                            if au_file.get('id','') == component or au_file.get('name','') == component:
                                if au_file.get('tags',[]) != [] and self.dict_tag_name_id is not None:
                                    au_file['tags'] = [self.dict_tag_name_id[tag_name] for tag_name in au_file.get('tags',[]) if tag_name in self.dict_tag_name_id.keys()]
                                component = au_file
                                break
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
                if len(component.get('unifiedTags',[])) > 0 and self.dict_tag_name_id is not None:
                    component['unifiedTags'] = [self.dict_tag_name_id[tag_name] for tag_name in component.get('UnifiedTags',[]) if tag_name in self.dict_tag_name_id.keys()]
            elif 'attributeMerge' in component.keys():
                componentType = 'mergepolicy'
            elif 'expression' in component.keys():
                componentType = 'audience'
            else:
                raise TypeError("the component type could not be inferred from the component or is not supported. Please provide the type as a parameter")
        ## Synchronize the component to the target sandboxes
        if componentType == 'datatype':
            self.__syncDataType__(component,verbose=verbose,force=force)
        if componentType == 'fieldgroup':
            self.__syncFieldGroup__(component,verbose=verbose,force=force)
        if componentType == 'schema':
            self.__syncSchema__(component,verbose=verbose,force=force)
        if componentType == 'class': 
            self.__syncClass__(component,verbose=verbose,force=force)
        if componentType == 'identity':
            self.__syncIdentity__(component,verbose=verbose)
        if componentType == 'dataset':
            self.__syncDataset__(component,verbose=verbose)
        if componentType == 'mergepolicy':
            self.__syncMergePolicy__(component,verbose=verbose)
        if componentType == 'audience':
            self.__syncAudience__(component,verbose=verbose,force=force)

    
    def syncAll(self,force:bool=False,verbose:bool=False)-> None:
        """
        Synchronize all the components to the target sandboxes.
        It will synchronize the components in the following order: 
        1. Identities
        2. Data Types
        3. Classes
        4. Field Groups
        5. Schemas
        6. Datasets
        Because the Merge Policies and Audiences needs the dataset and schema to be enabled in the target sandbox, and the synchronizer does not currently support enabling them for UPS.
        They will not sync with that method.
        A variable syncIssues will be created to gather the artefacts that could not be synchronized.
        Arguments:
            force : OPTIONAL : if True, it will force the synchronization of the components even if they already exist in the target sandbox. Works for Schema, FieldGroup, DataType and Class.
            verbose : OPTIONAL : if True, it will print the details of the synchronization process
        """
        base_identities = []
        base_schemas = []
        base_datasets = []
        self.syncIssues = []
        if self.localfolder is None:
            raise Exception("syncAll only allows synchronization based on a local folder. Extract artefacts and curate them before using syncAll.\nSee aepp.extractSandboxArtifacts or extract_artifacts in CLI method")
        if verbose:
            print("Loading base components from the local folder...")
        for folder in self.identityFolder:
            for file in folder.glob('*.json'):
                id_file = json.load(FileIO(file))
                base_identities.append(id_file)
        for folder in self.schemaFolder:
            for file in folder.glob('*.json'):
                sc_file = json.load(FileIO(file))
                mySchemaManager = schemamanager.SchemaManager(sc_file,localFolder=self.localfolder,sandbox=self.baseSandbox) 
                base_schemas.append(mySchemaManager)
        for folder in self.datasetFolder:
            for file in folder.glob('*.json'):
                ds_file = json.load(FileIO(file))
                if len(ds_file.get('unifiedTags',[])) > 0 and self.dict_tag_name_id is not None:
                    ds_file['unifiedTags'] = [self.dict_tag_name_id[tag_name] for tag_name in ds_file.get('unifiedTags',[]) if tag_name in self.dict_tag_name_id.keys()]
                base_datasets.append(ds_file)
        ### syncing identities
        if verbose:
            print("Syncing Identities...")
        for identity in base_identities:
            try:
                self.__syncIdentity__(identity,verbose=verbose)
            except Exception as e:
                self.syncIssues.append({'component':identity.get('name','code not found'),'type':'identity','error':str(e)})
        ### Syncing schema components
        if verbose:
            print("Syncing Schemas...")
        for sch in base_schemas:
            try:
                self.__syncSchema__(sch,force=force,verbose=verbose)
            except Exception as e:
                self.syncIssues.append({'component':sch.title,'type':'schema','error':str(e)})
        ### Syncing datasets
        if verbose:
                print("Syncing Datasets...")
        for ds in base_datasets:
            try:
                self.__syncDataset__(ds,force=force,verbose=verbose)
            except Exception as e:
                self.syncIssues.append({'component':ds.get('name','id not found'),'type':'dataset','error':str(e)})

            
    def __syncClass__(self,baseClass:classmanager.ClassManager,force:bool=False,verbose:bool=False)-> dict:
        """
        Synchronize a class to the target sandboxes.
        Arguments:
            baseClass : REQUIRED : class id or name to synchronize
            force : OPTIONAL : if True, it will force the synchronization of the class even if it already exists in the target sandbox
        """
        if not isinstance(baseClass,classmanager.ClassManager):
            raise TypeError("the baseClass must be a classManager instance")
        self.dict_baseComponents['class'][baseClass.title] = baseClass
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

            
    def __syncDataType__(self,baseDataType:datatypemanager.DataTypeManager,force:bool=False,verbose:bool=False)-> dict:
        """
        Synchronize a data type to the target sandbox.
        Arguments:
            baseDataType : REQUIRED : DataTypeManager object with the data type to synchronize
            force : OPTIONAL : if True, it will force the synchronization of the data type even if it already exists in the target sandbox
        """
        if not isinstance(baseDataType,datatypemanager.DataTypeManager):
            raise TypeError("the baseDataType must be a DataTypeManager object")
        self.dict_baseComponents['datatype'][baseDataType.title] = baseDataType
        name_base_datatype = baseDataType.title
        description_base_datatype = baseDataType.description
        for target in self.dict_targetsConfig.keys():
            targetSchema = schema.Schema(config=self.dict_targetsConfig[target])
            t_datatypes = targetSchema.getDataTypes()
            t_datatypes_global = targetSchema.getDataTypesGlobal()
            t_datatype = None
            if name_base_datatype in self.dict_targetComponents[target]['datatype'].keys(): ## if the datatype is already synchronized in the target cache
                t_datatype = self.dict_targetComponents[target]['datatype'][name_base_datatype]
            if name_base_datatype in targetSchema.data.dataTypes_altId.keys() or name_base_datatype in self.dict_targetComponents[target]['datatype'].keys(): ## datatype already exists in target but not synced recently in the cache or force sync is on
                if t_datatype is None: ## if need toe create the DataTypeManager
                    t_datatype = datatypemanager.DataTypeManager(targetSchema.data.dataTypes_altId[name_base_datatype],config=self.dict_targetsConfig[target],sandbox=target)
                    if t_datatype.dataType.get('meta:extensible',False) == False: ## if the data type is not extensible, it is OOTB can only use it.
                        self.dict_targetComponents[target]['datatype'][t_datatype.title] = t_datatype ## adding it to the cache to avoid checking it again for other datatypes using it as base and to be able to use it if needed as reference when synchronizing other datatypes using it as base
                        continue
                else: ## if the datatype is already synchronized in the target cache
                    if force == False:
                        continue ## if the datatype is already synchronized in the target cache and force sync is not on, we skip the synchronization of this target
                if verbose:
                    print(f"datatype '{name_base_datatype}' already exists in target {target}, checking it")
                df_base = baseDataType.to_dataframe(full=True)
                df_target = t_datatype.to_dataframe(full=True)
                base_paths = df_base['path'].tolist()
                target_paths = df_target['path'].tolist()
                diff_paths = list(set(base_paths) - set(target_paths))
                if len(diff_paths) > 0 or description_base_datatype != t_datatype.description or force==True: ## there are differences
                    base_datatypes_paths = baseDataType.getDataTypePaths()
                    df_base_limited = df_base[df_base['origin'] == 'self'].copy() ## exclude field group native fields
                    df_base_limited = df_base_limited[~df_base_limited['path'].isin(list(base_datatypes_paths.keys()))] ## exclude base of datatype rows
                    if t_datatype.EDITABLE:
                        t_datatype.importDataTypeDefinition(df_base_limited)
                    ## handling data types
                    base_dict_path_dtTitle = {}
                    for path,dt_id in base_datatypes_paths.items():
                        tmp_dt_manager = baseDataType.getDataTypeManager(dt_id)
                        if tmp_dt_manager.EDITABLE:
                            self.__syncDataType__(tmp_dt_manager,force=force,verbose=verbose)
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
                    if t_datatype.EDITABLE: ### avoid OOTB datatype
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
                new_datatype.setDescription(description_base_datatype)
                base_datatypes_paths = baseDataType.getDataTypePaths()
                df_base_limited = df_base[df_base['origin'] == 'self'].copy() ## exclude field group native fields
                df_base_limited = df_base_limited[~df_base_limited['path'].isin(list(base_datatypes_paths.keys()))] ## exclude base of datatype rows
                new_datatype.importDataTypeDefinition(df_base_limited)
                ## handling data types
                base_dict_path_dtTitle = {}
                for path,dt_id in base_datatypes_paths.items():
                    tmp_dt_manager = baseDataType.getDataTypeManager(dt_id)
                    self.__syncDataType__(tmp_dt_manager,force=force,verbose=verbose)
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
                new_datatype.setDescription(description_base_datatype)
                res = new_datatype.createDataType()
                if '$id' in res.keys():
                    t_datatype = datatypemanager.DataTypeManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
                else:
                    print(res)
                    raise Exception("the data type could not be created in the target sandbox")
            self.dict_targetComponents[target]['datatype'][name_base_datatype] = t_datatype

    def __syncFieldGroup__(self,baseFieldGroup:fieldgroupmanager.FieldGroupManager,force:bool=True,verbose:bool=False)-> dict:
        """
        Synchronize a field group to the target sandboxes.
        Argument: 
            baseFieldGroup : REQUIRED : FieldGroupManager object with the field group to synchronize
            force : OPTIONAL : if True, it will force the synchronization of the field group even if it already exists in the target sandbox
        """
        if not isinstance(baseFieldGroup,fieldgroupmanager.FieldGroupManager):
            raise TypeError("the baseFieldGroup must be a FieldGroupManager object")
        self.dict_baseComponents['fieldgroup'][baseFieldGroup.title] = baseFieldGroup
        name_base_fieldgroup = baseFieldGroup.title
        base_fg_classIds = baseFieldGroup.classIds
        base_fg_description = baseFieldGroup.description
        for target in self.dict_targetsConfig.keys():
            t_fieldgroup = None
            targetSchema = schema.Schema(config=self.dict_targetsConfig[target])
            t_fieldgroups = targetSchema.getFieldGroups()
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
            if name_base_fieldgroup in targetSchema.data.fieldGroups_altId.keys(): ## field group already exists in target but not synced recently in the cache or force sync is on
                if verbose:
                    print(f"field group '{name_base_fieldgroup}' already exists in target {target}, checking it")
                if t_fieldgroup is None: ## if need to create the FieldGroupManager
                    t_fieldgroup = fieldgroupmanager.FieldGroupManager(targetSchema.data.fieldGroups_altId[name_base_fieldgroup],config=self.dict_targetsConfig[target],sandbox=target)
                else:
                    if force == False:
                        continue ## if the field group is already synchronized in the target cache and force sync is not on, we skip the synchronization of this target
                for fg_class in t_fieldgroup.classIds:
                    if fg_class not in fg_class_ids:
                        fg_class_ids.append(fg_class)
                ### Aligning class support to the field groups
                t_fieldgroup.schemaAPI.extendFieldGroup(t_fieldgroup.id,fg_class_ids)
                df_base = baseFieldGroup.to_dataframe(full=True)
                df_target = t_fieldgroup.to_dataframe(full=True)
                base_paths = df_base['path'].tolist()
                target_paths = df_target['path'].tolist()
                diff_paths = [path for path in base_paths if path not in target_paths]
                if len(diff_paths) > 0 or base_fg_description != t_fieldgroup.description or force==True:
                    if verbose:
                        print(f"updating field group '{name_base_fieldgroup}' in target {target}")
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
                        self.__syncDataType__(tmp_dt_manager,force=force,verbose=verbose)
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
                    if base_fg_description != t_fieldgroup.description:
                        t_fieldgroup.setDescription(base_fg_description)
                    if t_fieldgroup.EDITABLE: ### avoid OOTB field group
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
                    self.__syncDataType__(tmp_dt_manager,force=force,verbose=verbose)
                    base_dict_path_dtTitle[path] = tmp_dt_manager.title
                for path,dt_title in base_dict_path_dtTitle.items():
                    tmp_t_dt = self.dict_targetComponents[target]['datatype'][dt_title]
                    arrayBool = False
                    if path.endswith('[]{}'):
                        arrayBool = True
                        path = path[:-4] ## removing the [] from the path
                    new_fieldgroup.addField(path=path,dataType='dataType',ref=tmp_t_dt.id,array=arrayBool)
                new_fieldgroup.setDescription(base_fg_description)
                res = new_fieldgroup.createFieldGroup()
                if '$id' in res.keys():
                    t_fieldgroup = fieldgroupmanager.FieldGroupManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
                else:
                    print(res)
                    raise Exception("the field group could not be created in the target sandbox")
            self.dict_targetComponents[target]['fieldgroup'][name_base_fieldgroup] = t_fieldgroup


    def __syncSchema__(self,baseSchema:schemamanager.SchemaManager,force:bool=False,verbose:bool=False)-> dict:
        """
        Sync the schema to the target sandboxes.
        Arguments:
            baseSchema : REQUIRED : SchemaManager object to synchronize
            force : OPTIONAL : if True, it will force the synchronization of field groups even if they already exist in the target schema
        """
        ## TO DO -> sync required fields
        if not isinstance(baseSchema,schemamanager.SchemaManager):
            raise TypeError("the baseSchema must be a SchemaManager object")
        name_base_schema = baseSchema.title
        ## Guard against re-entrant calls caused by circular descriptor relationships (A→B→A).
        ## _syncing_schemas tracks schemas currently mid-flight in this call stack only.
        ## discard() is called at every exit point so sequential re-calls are not blocked.
        if not hasattr(self, '_syncing_schemas'):
            self._syncing_schemas = set()
        if name_base_schema in self._syncing_schemas:
            return
        self._syncing_schemas.add(name_base_schema)
        self.dict_baseComponents['schema'][name_base_schema] = baseSchema
        descriptors = baseSchema.getDescriptors()
        base_field_groups_names = list(baseSchema.fieldGroups.values())
        base_schema_description = baseSchema.description
        dict_base_fg_name_id = {name:fg_id for fg_id,name in baseSchema.fieldGroups.items()}
        if 'meta:service' in baseSchema.schema.keys():
            if verbose:
                print(f"schema '{name_base_schema}' is a service schema, skipping the synchronization")
            self._syncing_schemas.discard(name_base_schema)
            return
        for target in self.dict_targetsConfig.keys():
            targetSchemaAPI = schema.Schema(config=self.dict_targetsConfig[target])
            t_schema = None
            if name_base_schema in self.dict_targetComponents[target]['schema'].keys():
                t_schema = self.dict_targetComponents[target]['schema'][name_base_schema]
            t_schemas = targetSchemaAPI.getSchemas()
            t_fieldGroups = targetSchemaAPI.getFieldGroups()
            if name_base_schema in targetSchemaAPI.data.schemas_altId.keys(): ## schema already exists in target and not synced recently in the cache or force sync is on
                if t_schema is None: ## if need to create the SchemaManager
                    t_schema = schemamanager.SchemaManager(targetSchemaAPI.data.schemas_altId[name_base_schema],config=self.dict_targetsConfig[target],sandbox=target)
                else: ## if the schema is already synchronized in the target cache
                    if force == False:
                        if verbose:
                            print(f"schema '{name_base_schema}' already synchronized. Skipping synchronization.")
                        continue ## if the schema is already synchronized in the target cache and force sync is not on, we skip the synchronization of this target
                if verbose:
                    print(f"schema '{name_base_schema}' already exists in target {target}, checking it")
                t_schema = schemamanager.SchemaManager(targetSchemaAPI.data.schemas_altId[name_base_schema],config=self.dict_targetsConfig[target],sandbox=target)
                new_fieldgroups = [fg for fg in base_field_groups_names if fg not in t_schema.fieldGroups.values()]
                existing_fieldgroups = [fg for fg in base_field_groups_names if fg in t_schema.fieldGroups.values()]
                if len(new_fieldgroups) > 0 or base_schema_description != t_schema.description or force==True: ## if new field groups
                    if verbose:
                        if force == False:
                            print('found difference in the schema, updating it')
                        else:
                            print('force flag is set to True, updating the schema')
                    ## handling field groups
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
                            self.__syncFieldGroup__(tmp_FieldGroup,verbose=verbose,force=force)
                            t_schema.addFieldGroup(self.dict_targetComponents[target]['fieldgroup'][new_fieldgroup].id)
                    t_schema.setDescription(base_schema_description)
                    res = t_schema.updateSchema()
                    if '$id' not in res.keys():
                        raise Exception(res)
                    else:
                        t_schema = schemamanager.SchemaManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
                for fg_name in existing_fieldgroups:
                    if baseSchema.tenantId[1:] in dict_base_fg_name_id[fg_name]: ## custom field group
                        if fg_name not in self.dict_targetComponents[target]['fieldgroup'].keys(): ## if the field group is not already synchronized in the target cache
                            tmp_fieldGroupManager = fieldgroupmanager.FieldGroupManager(dict_base_fg_name_id[fg_name],config=self.baseConfig,sandbox=target,localFolder=self.localfolder)
                        else:
                            tmp_fieldGroupManager = self.dict_targetComponents[target]['fieldgroup'][fg_name]
                        self.__syncFieldGroup__(tmp_fieldGroupManager,force=force,verbose=verbose)
                    else:
                        if verbose:
                            print(f"field group '{fg_name}' is a OOTB field group, using it")
                        if fg_name not in self.dict_targetComponents[target]['fieldgroup'].keys(): ## if the field group is not already synchronized in the target cache
                            self.dict_targetComponents[target]['fieldgroup'][fg_name] = fieldgroupmanager.FieldGroupManager(dict_base_fg_name_id[fg_name],config=self.dict_targetsConfig[target],sandbox=target)
                        else:
                            pass ## if the field group is already in the cache, we can use it directly
                ## handling descriptors
                list_new_descriptors = self.__syncDescriptor__(baseSchema,t_schema,targetSchemaAPI=targetSchemaAPI,verbose=verbose)
                ## handling the meta:refProperty setup if any
                base_allOf = baseSchema.schema.get('allOf',[])
                base_fg_name_metaref = {}
                for refEl in base_allOf: ## retrieving the meta:refProperty from the base schema
                    if 'meta:refProperty' in refEl.keys():
                        tmp_base_fg_id = refEl['$ref']
                        if baseSchema.tenantId[1:] in tmp_base_fg_id:
                            tmp_base_fg_manager = self.getSyncFieldGroupManager(tmp_base_fg_id,sandbox=baseSchema.sandbox)
                            base_fg_name_metaref[tmp_base_fg_manager.title] = refEl['meta:refProperty']
                        else:
                            base_fg_name_metaref[tmp_base_fg_id] = refEl['meta:refProperty']
                for fg_name,ref_property in base_fg_name_metaref.items(): ## updating the target schema with the meta:refProperty
                    for ref in t_schema.schema.get('allOf',[]):
                        tmp_target_fg_id = ref['$ref']
                        if baseSchema.tenantId[1:] in tmp_target_fg_id:
                            tmp_target_fg_manager = self.getSyncFieldGroupManager(tmp_target_fg_id,sandbox=target)
                            if fg_name == tmp_target_fg_manager.title:
                                ref['meta:refProperty'] = ref_property
                        else:
                            if fg_name == ref['$ref']:
                                ref['meta:refProperty'] = ref_property
                self.dict_targetComponents[target]['schemaDescriptors'][name_base_schema] = list_new_descriptors
                t_schema.updateSchema()
            else: ## schema does not exist in target
                if verbose:
                    print(f"schema '{name_base_schema}' does not exist in target {target}, creating it")
                ## Check schema class: 
                ## Limited support -> does not support custom elements defined in classes
                baseClassId = baseSchema.classId
                tenantidId = baseSchema.tenantId
                if tenantidId[1:] in baseClassId: ## custom class
                    if baseClassId not in [value.id for key, value in self.dict_baseComponents['class'].items() if value is not None]: ## if the class is not already synchronized in the base cache
                        baseClassManager = classmanager.ClassManager(baseClassId,config=self.baseConfig,sandbox=target,localFolder=self.localfolder,sandboxBase=self.baseSandbox,tenantidId=tenantidId)
                    else:
                        baseClassManager = [value for key, value in self.dict_baseComponents['class'].items() if value is not None and value.id == baseClassId][0]
                    self.__syncClass__(baseClassManager,force=force,verbose=verbose)
                    targetClassManager = self.dict_targetComponents[target]['class'][baseClassManager.title]
                    classId_toUse = targetClassManager.id
                else:
                    classId_toUse = baseClassId
                new_schema = schemamanager.SchemaManager(title=name_base_schema,config=self.dict_targetsConfig[target],schemaClass=classId_toUse,sandbox=target)
                new_schema.setDescription(base_schema_description)
                for fg_name in base_field_groups_names:
                    if baseSchema.tenantId[1:] not in dict_base_fg_name_id[fg_name]: ## ootb field group
                        new_schema.addFieldGroup(dict_base_fg_name_id[fg_name])
                        if verbose:
                            print(f"field group '{fg_name}' is a OOTB field group, using it")
                        ## adding the field group to the target components
                        self.dict_targetComponents[target]['fieldgroup'][fg_name] = fieldgroupmanager.FieldGroupManager(dict_base_fg_name_id[fg_name],config=self.dict_targetsConfig[target],sandbox=target)
                    else:
                        tmp_FieldGroup = baseSchema.getFieldGroupManager(fg_name)
                        self.__syncFieldGroup__(tmp_FieldGroup,force=force,verbose=verbose)
                        new_schema.addFieldGroup(self.dict_targetComponents[target]['fieldgroup'][fg_name].id)
                res = new_schema.createSchema()
                if '$id' in res.keys():
                    t_schema = schemamanager.SchemaManager(res['$id'],config=self.dict_targetsConfig[target],sandbox=target)
                else:
                    print(res)
                    raise Exception("the schema could not be created in the target sandbox")
                ## copying the schema creation so it can be fetch later for B2B references
                self.dict_targetComponents[target]['schema'][name_base_schema] = t_schema
                ## handling descriptors
                list_new_descriptors = self.__syncDescriptor__(baseSchema,t_schema,targetSchemaAPI,verbose=verbose)
                self.dict_targetComponents[target]['schemaDescriptors'][name_base_schema] = list_new_descriptors
                ## handling the meta:refProperty setup if any
                base_allOf = baseSchema.schema.get('allOf',[])
                base_fg_name_metaref = {}
                for refEl in base_allOf: ## retrieving the meta:refProperty from the base schema
                    if 'meta:refProperty' in refEl.keys():
                        tmp_base_fg_id = refEl['$ref']
                        if baseSchema.tenantId[1:] in tmp_base_fg_id:
                            tmp_base_fg_manager = self.getSyncFieldGroupManager(tmp_base_fg_id,sandbox=baseSchema.sandbox)
                            base_fg_name_metaref[tmp_base_fg_manager.title] = refEl['meta:refProperty']
                        else:
                            base_fg_name_metaref[tmp_base_fg_id] = refEl['meta:refProperty']
                for fg_name,ref_property in base_fg_name_metaref.items(): ## updating the target schema with the meta:refProperty
                    for ref in t_schema.schema.get('allOf',[]):
                        tmp_target_fg_id = ref['$ref']
                        if baseSchema.tenantId[1:] in tmp_target_fg_id:
                            tmp_target_fg_manager = self.getSyncFieldGroupManager(tmp_target_fg_id,sandbox=target)
                            if fg_name == tmp_target_fg_manager.title:
                                ref['meta:refProperty'] = ref_property
                        else:
                            if fg_name == ref['$ref']:
                                ref['meta:refProperty'] = ref_property
                t_schema.updateSchema()
            self.dict_targetComponents[target]['schema'][name_base_schema] = t_schema
        self._syncing_schemas.discard(name_base_schema)

    def __syncDescriptor__(self,baseSchemaManager:schemamanager.SchemaManager|None=None,targetSchemaManager:schemamanager.SchemaManager|None=None,targetSchemaAPI:schema.Schema|None=None,verbose:bool=False)-> dict:
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
        if len(base_descriptors) == 0:
            return []
        if verbose:
            print(f"found {len(base_descriptors)} descriptors in the base schema '{baseSchemaManager.title}'. Synchronizing them to the target schema")
        if self.baseConfig is not None:
            baseSchemaAPI = schema.Schema(config=self.baseConfig)
            myschemas = baseSchemaAPI.getSchemas() ## to populate the data object
        elif self.localfolder is not None:
            myschemas = []
            for folder in self.schemaFolder:
                for json_file in folder.glob('*.json'):
                    myschemas.append(json.load(FileIO(json_file)))
        target_descriptors = targetSchemaManager.getDescriptors()
        list_descriptors = []
        for baseDescriptor in base_descriptors:
            descType = baseDescriptor['@type']
            match descType:
                case "xdm:descriptorIdentity":
                    target_identitiesDecs = [desc for desc in target_descriptors if desc['@type'] == 'xdm:descriptorIdentity']
                    baseIdentityNS = baseDescriptor['xdm:namespace'].lower()
                    if self.baseConfig is not None and self.localfolder is None:
                        identityConn = identity.Identity(config=self.baseConfig,region=self.region)
                        baseIdentities = identityConn.getIdentities()
                    elif self.localfolder is not None:
                        baseIdentities = []
                        for folder in self.identityFolder:
                            for file in folder.glob('*.json'):
                                id_file = json.load(FileIO(file))
                                baseIdentities.append(id_file)
                    if baseIdentityNS not in [el['xdm:namespace'].lower() for el in target_identitiesDecs]: ## identity descriptor does not exists in target schema
                        def_identity = [el for el in baseIdentities if el['code'].lower() == baseIdentityNS][0]
                        self.__syncIdentity__(def_identity,verbose=verbose)
                        new_desc = targetSchemaManager.createDescriptorOperation(descType=descType,
                                                                            completePath=baseDescriptor['xdm:sourceProperty'],
                                                                            identityNSCode=baseIdentityNS,
                                                                            identityPrimary=baseDescriptor['xdm:isPrimary'],
                                                                            )
                        res = targetSchemaManager.createDescriptor(new_desc)
                    else:
                        res = [el for el in target_identitiesDecs if el['xdm:namespace'].lower() == baseIdentityNS][0]
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
                            found = False
                            for folder in self.schemaFolder:
                                for file in folder.glob('*.json'):
                                    base_targetSchema = json.load(FileIO(file))
                                    if base_targetSchema['$id'] == base_targetSchemaId:
                                        base_targetSchemaManager = schemamanager.SchemaManager(base_targetSchema,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                                        found = True
                                        break
                                if found:
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
                        for folder in self.identityFolder:
                            for file in folder.glob('*.json'):
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

    def __syncIdentity__(self,identityDefiniton:dict,verbose:bool=False,**kwargs)-> dict:
        """
        Synchronize an identity to the target sandboxes.
        Arguments:
            identityDefinition : REQUIRED : dictionary with the identity definition
        """
        if not isinstance(identityDefiniton,dict):
            raise TypeError("the identityDefinition must be a dictionary")
        code_base_identity = identityDefiniton['code'].lower()
        self.dict_baseComponents['identities'][code_base_identity] = identityDefiniton
        for target in self.dict_targetsConfig.keys():
            if code_base_identity not in self.dict_targetComponents[target]['identities'].keys(): ## if the identity is not already synchronized in the target cache
                targetIdentity = identity.Identity(config=self.dict_targetsConfig[target])
                t_identities = targetIdentity.getIdentities()
                if code_base_identity in [el['code'].lower() for el in t_identities]:## identity already exists in target
                    if verbose:
                        print(f"identity '{code_base_identity}' already exists in target {target}, saving it")
                    self.dict_targetComponents[target]['identities'][code_base_identity] = [el for el in t_identities if el['code'].lower() == code_base_identity][0]
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
            else:
                if verbose:
                    print(f"identity '{code_base_identity}' already synchronized in target {target}, skipping it")
                pass ## if the identity is already in the cache, we can use it directly
    
    def __syncDataset__(self,baseDataset:dict,verbose:bool=False,force:bool=False)-> dict:
        """
        Synchronize the dataset to the target sandboxes. Mostly creating a new dataset and associated artifacts when not already created.
        Arguments:
            baseDataset : REQUIRED : dictionary with the dataset definition
            verbose : OPTIONAL : if True, it will print the progress of the synchronization
            force : OPTIONAL : if True, it will force the synchronization of the dataset even if it already exists in the target sandbox
        """
        if len(baseDataset) == 1: ## if receiving the dataset as provided by the API {datasetId:{...definition}}
            baseDataset = deepcopy(baseDataset[list(baseDataset.keys())[0]])
        self.dict_baseComponents['datasets'][baseDataset['name']] = baseDataset
        base_datasetName = baseDataset['name']
        if verbose:
            print(f"Synchronizing dataset '{base_datasetName}'")
        base_dataset_related_schemaId = baseDataset['schemaRef']['id']
        base_dataset_unifiedTagIds = baseDataset.get('unifiedTags',[])
        if self.baseConfig is not None:
            baseSchemaAPI = schema.Schema(config=self.baseConfig)
            base_schemas = baseSchemaAPI.getSchemas()
            if base_dataset_related_schemaId in baseSchemaAPI.data.schemas_id.values():
                base_dataset_related_schemaName = [schemaName for schemaName,schemaId in baseSchemaAPI.data.schemas_id.items() if schemaId == base_dataset_related_schemaId][0]
            else: ### using an OOTB schema
                schema_ootb = baseSchemaAPI.getSchemasGlobal()
                if base_dataset_related_schemaId in baseSchemaAPI.data.schemas_id.values():
                    return ## Avoid synchronization for all targets
                else:
                    if verbose:
                        print(f"related schema with id '{base_dataset_related_schemaId}' is not found. Skipping dataset synchronization.")
                    return ## avoid synchronization for all targets since the related schema is not found
        elif self.localfolder is not None:
            base_schemas = []
            for folder in self.schemaFolder:
                for json_file in folder.glob('*.json'):
                    base_schemas.append(json.load(FileIO(json_file)))
            base_dataset_related_schemaName = [sc['title'] for sc in base_schemas if sc['$id'] == base_dataset_related_schemaId][0]
        for target in self.dict_targetsConfig.keys():
            targetCatalog = catalog.Catalog(config=self.dict_targetsConfig[target])
            t_datasets = targetCatalog.getDataSets(output='list')
            if base_datasetName not in [tds['name'] for tds in t_datasets]: ## if dataset does not exist
                if verbose:
                    print(f"dataset '{base_datasetName}' does not exist in target {target}, creating it")
                targetSchema = schema.Schema(config=self.dict_targetsConfig[target])
                t_schemas = targetSchema.getSchemas()
                if base_dataset_related_schemaName not in targetSchema.data.schemas_altId.keys(): ## schema does not exist in target
                    if verbose:
                        print(f"related schema '{base_dataset_related_schemaName}' does not exist in target {target}, creating it")
                    baseSchemaManager = schemamanager.SchemaManager(base_dataset_related_schemaId,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                    self.__syncSchema__(baseSchemaManager,verbose=verbose,force=force)
                    targetSchemaId = self.dict_targetComponents[target]['schema'][base_dataset_related_schemaName].id
                    res = targetCatalog.createDataSet(name=base_datasetName,schemaId=targetSchemaId,unifiedTags=base_dataset_unifiedTagIds)
                    t_datasets = targetCatalog.getDataSets(output='list')
                    t_dataset = [tds for tds in t_datasets if tds['name'] == base_datasetName][0]
                    self.dict_targetComponents[target]['datasets'][base_datasetName] = {t_dataset['id']:t_dataset}
                else: ## schema already exists in target
                    if force == True:
                        if verbose:
                            print(f"related schema '{base_dataset_related_schemaName}' does exist in target {target}, checking it")
                        self.__syncSchema__(baseSchemaManager,verbose=verbose,force=force)
                        target_schema = self.dict_targetComponents[target]['schema'][base_dataset_related_schemaName]
                    if base_dataset_related_schemaName in self.dict_targetComponents[target]['schema'].keys():
                        target_schema = self.dict_targetComponents[target]['schema'][base_dataset_related_schemaName]
                        targetSchemaId = target_schema.id
                    else:
                        targetSchemaId = targetSchema.data.schemas_id[base_dataset_related_schemaName]
                    res = targetCatalog.createDataSet(name=base_datasetName,schemaId=targetSchemaId,unifiedTags=base_dataset_unifiedTagIds)
                    t_datasets = targetCatalog.getDataSets(output='list')
                    t_dataset = [tds for tds in t_datasets if tds['name'] == base_datasetName][0]
                    self.dict_targetComponents[target]['datasets'][base_datasetName] = {t_dataset['id']:t_dataset}
            else: ## dataset already exists in target
                if verbose:
                    print(f"dataset '{base_datasetName}' already exists in target {target}")
                t_dataset = targetCatalog.getDataSet(targetCatalog.data.ids[base_datasetName])
                if force:
                    if verbose:
                        print(f"related schema '{base_dataset_related_schemaName}' does exist in target {target}, checking it")
                    targetSchema = schema.Schema(config=self.dict_targetsConfig[target])
                    t_schemas = targetSchema.getSchemas()
                    baseSchemaManager = schemamanager.SchemaManager(base_dataset_related_schemaId,config=self.baseConfig,localFolder=self.localfolder,sandbox=self.baseSandbox)
                    self.__syncSchema__(baseSchemaManager,verbose=verbose)               
                t_dataset_def = t_dataset[list(t_dataset.keys())[0]]
                t_dataset_def['id'] = list(t_dataset.keys())[0]
                if verbose:
                    print(f"Checking unified tags")
                t_dataset_unifiedTagIds = t_dataset_def.get('unifiedTags',[])
                ### checking if unified tags are the same or not, automatically updating the target dataset from base if not
                if len(t_dataset_unifiedTagIds) != len(base_dataset_unifiedTagIds) or set(t_dataset_unifiedTagIds) != set(base_dataset_unifiedTagIds):
                    t_dataset_def['unifiedTags'] = base_dataset_unifiedTagIds
                    res = targetCatalog.putDataset(t_dataset_def['id'],t_dataset_def)
                self.dict_targetComponents[target]['datasets'][base_datasetName] = {t_dataset_def['id'] : t_dataset_def}

    def __syncMergePolicy__(self,mergePolicy:dict,verbose:bool=False)->None:
        """
        Synchronize the dataset to the target sandboxes. Mostly creating a new dataset and associated artifacts when not already created.
        Arguments:
            mergePolicy : REQUIRED : The merge policy dictionary to sync
        """
        if not isinstance(mergePolicy,dict):
            raise TypeError("the mergePolicy must be a dictionary")
        self.dict_baseComponents['mergePolicy'][mergePolicy.get('id','unknown')] = mergePolicy
        mergePolicy_name = mergePolicy.get('name','unknown')
        if mergePolicy['attributeMerge'].get('type','timestampOrdered') == 'dataSetPrecedence':
            if verbose:
                print(f"handling dataset precedence for merge policy '{mergePolicy_name}'")
                print("syncing the datasets involved in the precedence order")
            base_list_precedenceDatasets = mergePolicy['attributeMerge'].get('order',[])
            for ds_id in base_list_precedenceDatasets:
                res = self.syncComponent(ds_id,componentType='dataset',verbose=verbose)
        for target in self.dict_targetsConfig.keys():
            targetCustomerProfile = customerprofile.Profile(config=self.dict_targetsConfig[target])
            t_mergePolicies = targetCustomerProfile.getMergePolicies()
            if mergePolicy_name not in [el.get('name','') for el in t_mergePolicies]: ## merge policy does not exist in target
                if verbose:
                    print(f"merge policy '{mergePolicy_name}' does not exist in target {target}, creating it")
                mergePolicyDef = {
                    "name":mergePolicy.get('name',''),
                    "schema":mergePolicy.get('schema','_xdm.context.profile'),
                    "identityGraph":mergePolicy.get('identityGraph','pdg'),
                    "isActiveOnEdge":mergePolicy.get('isActiveOnEdge',False),
                }
                if mergePolicy['attributeMerge'].get('type','timestampOrdered') == 'dataSetPrecedence':
                    target_list_precedenceDatasets = []
                    for base_ds_id in mergePolicy['attributeMerge'].get('order',[]):
                        base_ds_name = self.getDatasetName(base_ds_id,sandbox=target)
                        target_ds_id = self.dict_targetComponents[target]['datasets'][base_ds_name]['id']
                        target_list_precedenceDatasets.append(target_ds_id)
                    mergePolicyDef['attributeMerge'] = {
                        "type":mergePolicy['attributeMerge'].get('type','timestampOrdered'),
                        "order":target_list_precedenceDatasets
                    }
                else:
                    mergePolicyDef['attributeMerge'] = {'type':'timestampOrdered'}
                res = targetCustomerProfile.createMergePolicy(mergePolicyDef)
                if 'id' in res.keys():
                    self.dict_targetComponents[target]['mergePolicy'][res['id']] = res
                else:
                    print(res)
                    raise Exception("the merge policy could not be created in the target sandbox")
            else: ## merge policy already exists in target
                if verbose:
                    print(f"merge policy '{mergePolicy_name}' already exists in target {target}, saving it")
                self.dict_targetComponents[target]['mergePolicy'][mergePolicy_name] = [el for el in t_mergePolicies if el.get('name','') == mergePolicy_name][0]

    def __syncAudience__(self,baseAudience:dict,verbose:bool=False,force:bool=False)-> None:
        """
        Synchronize an audience to the target sandboxes.
        Arguments:
            baseAudience : REQUIRED : dictionary with the audience definition
            force : OPTIONAL : boolean to force the update of the audience in the target sandbox even if it already exists (default is False)
        """
        if not isinstance(baseAudience,dict):
            raise TypeError("the baseAudience must be a dictionary")
        audience_name = baseAudience.get('name','unknown')
        self.dict_baseComponents['audience'][audience_name] = baseAudience
        for target in self.dict_targetsConfig.keys():
            targetAudiences = segmentation.Segmentation(config=self.dict_targetsConfig[target])
            t_audiences = targetAudiences.getAudiences()
            if audience_name not in [el['name'] for el in t_audiences]: ## audience does not exist in target
                if verbose:
                    print(f"audience '{audience_name}' does not exist in target {target}, creating it")
                audienceDef = {
                    "name":baseAudience.get('name',''),
                    "description":baseAudience.get('description',''),
                    "type":baseAudience.get('type','SegmentDefinition'),
                    "schema":baseAudience.get('schema','_xdm.context.profile'),
                    "expression":baseAudience.get('expression',[]),
                    "ansibleDataModel":baseAudience.get('ansibleDataModel',{}),
                    "profileInstanceId":baseAudience.get('profileInstanceId',''),
                    "evaluationInfo":baseAudience.get('evaluationInfo',{'batch': {'enabled': True}, 'continuous': {'enabled': False},'synchronous': {'enabled': False}}),
                    "tags":baseAudience.get('tags',[])
                }
                res = targetAudiences.createAudience(audienceDef)
                if 'id' in res.keys():
                    self.dict_targetComponents[target]['audience'][res['id']] = res
                else:
                    print(res)
                    raise Exception("the audience could not be created in the target sandbox")
            else: ## audience already exists in target
                if verbose:
                    print(f"audience '{audience_name}' already exists in target {target}, checking it")
                if str(t_audience['expression']) != str(baseAudience.get('expression',[])) or len(baseAudience.get('tags',[])).difference(set(t_audience.get('tags',[])))>0 or force == True:
                    if verbose:
                        print(f"Updating '{audience_name}' in target {target}")
                    t_audience = [el for el in t_audiences if el['name'] == audience_name][0]
                    t_audience['description'] = baseAudience.get('description','')
                    t_audience['expression'] = baseAudience.get('expression',[])
                    t_audience['ansibleDataModel'] = baseAudience.get('ansibleDataModel',{})
                    t_audience['evaluationInfo'] = baseAudience.get('evaluationInfo',{'batch': {'enabled': True}, 'continuous': {'enabled': False},'synchronous': {'enabled': False}})
                    t_audience['tags'] = baseAudience.get('tags',[])
                    res = targetAudiences.putAudience(t_audience['id'],t_audience)
                    self.dict_targetComponents[target]['audience'][audience_name] = res
                else: 
                    self.dict_targetComponents[target]['audience'][audience_name] = [el for el in t_audiences if el['name'] == audience_name][0]

