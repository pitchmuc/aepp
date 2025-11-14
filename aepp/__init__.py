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
from aepp import config
from aepp import connector
from .configs import *
from .__version__ import __version__
from typing import Union

## other libraries
from copy import deepcopy
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor

connection = None


def home(product: str = None, limit: int = 50):
    """
    Return the IMS Organization setup and the container existing for the organization
    Arguments:
        product : OPTIONAL : specify one or more product contexts for which to return containers. If absent, containers for all contexts that you have rights to will be returned. The product parameter can be repeated for multiple contexts. An example of this parameter is product=acp
        limit : OPTIONAL : Optional limit on number of results returned (default = 50).
    """
    global connection
    if connection is None:
        connection = connector.AdobeRequest(
            config_object=config.config_object, header=config.header
        )
    endpoint = config.endpoints["global"] + "/data/core/xcore/"
    params = {"product": product, "limit": limit}
    myHeader = deepcopy(connection.header)
    myHeader["Accept"] = "application/vnd.adobe.platform.xcore.home.hal+json"
    res = connection.getData(endpoint, params=params, headers=myHeader)
    return res


def getPlatformEvents(
    limit: int = 50, n_results: Union[int, str] = "inf", prop: str = None, **kwargs
) -> dict:
    """
    Timestamped records of observed activities in Platform. The API allows you to query events over the last 90 days and create export requests.
    Arguments:
        limit : OPTIONAL : Number of events to retrieve per request (50 by default)
        n_results : OPTIONAL : Number of total event to retrieve per request.
        prop : OPTIONAL : An array that contains one or more of a comma-separated list of properties (prop="action==create,assetType==Sandbox")
            If you want to filter results using multiple values for a single filter, pass in a comma-separated list of values. (prop="action==create,update")
    """
    global connection
    if connection is None:
        connection = connector.AdobeRequest(
            config_object=config.config_object, header=config.header
        )
    endpoint = "https://platform.adobe.io/data/foundation/audit/events"
    params = {"limit": limit}
    if prop is not None:
        params["property"] = prop
    # myHeader = deepcopy(connection.header)
    lastPage = False
    data = list()
    while lastPage != True:
        res = connection.getData(endpoint, params=params)
        data += res.get("_embedded", {}).get("events", [])
        nextPage = res.get("_links", {}).get("next", {}).get('href','')
        if float(len(data)) >= float(n_results):
            lastPage = True
        if nextPage == "" and lastPage != True:
            lastPage = True
        else:
            start = nextPage.split("start=")[1].split("&")[0]
            queryId = nextPage.split("queryId=")[1].split("&")[0]
            params["queryId"] = queryId
            params["start"] = start
    return data


def saveFile(
    module: str = None,
    file: object = None,
    filename: str = None,
    type_file: str = "json",
    encoding: str = "utf-8",
):
    """
    Save the file in the approriate folder depending on the module sending the information.
     Arguments:
          module: REQUIRED: Module requesting the save file.
          file: REQUIRED: an object containing the file to save.
          filename: REQUIRED: the filename to be used.
          type_file: REQUIRED: the type of file to be saveed(default: json)
          encoding : OPTIONAL : encoding used to write the file.
    """
    if module is None:
        raise ValueError("Require the module to create a folder")
    if file is None or filename is None:
        raise ValueError("Require a object for file and a name for the file")
    here = Path(Path.cwd())
    folder = module.capitalize()
    new_location = Path.joinpath(here, folder)
    if new_location.exists() == False:
        new_location.mkdir()
    if type_file == "json":
        filename = f"{filename}.json"
        complete_path = Path.joinpath(new_location, filename)
        with open(complete_path, "w", encoding=encoding) as f:
            f.write(json.dumps(file, indent=4))
    else:
        filename = f"{filename}.txt"
        complete_path = Path.joinpath(new_location, filename)
        with open(complete_path, "w", encoding=encoding) as f:
            f.write(file)

def __titleSafe__(text: str) -> str:
    """
    Create a safe title for a file name
    Arguments:
        text : REQUIRED : the text to be converted
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', ' ']
    for char in invalid_chars:
        text = text.replace(char, '_')
    return text


def extractSandboxArtefacts(
    sandbox: 'ConnectObject' = None, 
    localFolder: Union[str, Path] = None,
    region: str = "nld2",
    ootb: bool = True,
):
    """
    Extract the sandbox in the local folder.
    Arguments:
        sandbox: REQUIRED: the instance of a ConnectObject that contains the sandbox information and connection.
        localFolder: OPTIONAL: the local folder where to extract the sandbox. If not provided, it will use the current working directory and name the folder the name of the sandbox.
        region: OPTIONAL: the region of the sandbox (default: nld2). This is used to fetch the correct API endpoints for the identities. 
            Possible values: "va7","aus5", "can2", "ind2"
        ootb : OPTIONAL : If you want to also download the OOTB elements
    """
    if sandbox is None:
        raise ValueError("You need to provide a ConnectObject instance with the sandbox information")
    if localFolder is None:
        mypath = Path('./') 
        completePath = mypath / f'{sandbox.sandbox}'
    else:
        completePath = Path(localFolder)
    from aepp import schema, catalog, identity
    sch = schema.Schema(config=sandbox)
    cat = catalog.Catalog(config=sandbox)
    ide = identity.Identity(config=sandbox,region=region)
    completePath.mkdir(exist_ok=True)
    globalConfig = {
        "imsOrgId":sandbox.org_id,
        "tenantId":f"_{sch.getTenantId()}"
    }
    with open(f'{completePath}/config.json','w') as f:
        json.dump(globalConfig,f,indent=2)
    behavPath = completePath / 'behaviour'
    behavPath.mkdir(exist_ok=True)
    classPath = completePath / 'class'
    classPath.mkdir(exist_ok=True)
    schemaPath = completePath / 'schema'
    schemaPath.mkdir(exist_ok=True)
    fieldgroupPath = completePath / 'fieldgroup'
    fieldgroupPath.mkdir(exist_ok=True)
    fieldgroupPathGlobale = fieldgroupPath / 'global'
    fieldgroupPathGlobale.mkdir(exist_ok=True)
    datatypePath = completePath / 'datatype'
    datatypePath.mkdir(exist_ok=True)
    datatypePathGlobal = datatypePath / 'global'
    datatypePathGlobal.mkdir(exist_ok=True)
    descriptorPath = completePath / 'descriptor'
    descriptorPath.mkdir(exist_ok=True)
    identityPath = completePath / 'identity'
    identityPath.mkdir(exist_ok=True)
    datasetPath = completePath / 'dataset'
    datasetPath.mkdir(exist_ok=True)
    myclasses = sch.getClasses()
    classesGlobal = sch.getClassesGlobal()
    behaviors = sch.getBehaviors()
    def writingFullFile(tuple_element):
        element,path,id_key,name,method = tuple_element
        try:
            if method is not None:
                definition = method(element[id_key],full=True,xtype='xed')
                file_name = __titleSafe__(definition.get(name,definition.get(id_key,'unknown')))
                with open(f"{path / file_name}.json",'w') as f:
                    json.dump(definition,f,indent=2)
            else:
                with open(f"{path / element[id_key]}.json",'w') as f:
                    json.dump(element,f,indent=2)
        except Exception as e: ### some geo data types are not available
            print(e)
    def writingFalseFile(tuple_element):
        element,path,id_key,name,method = tuple_element
        try:
            definition = method(element[id_key],full=False,xtype='xed')
            file_name = __titleSafe__(definition.get(name,definition.get(id_key,'unknown')))
            with open(f"{path / file_name}.json",'w') as f:
                json.dump(definition,f,indent=2)
        except Exception as e: ### some geo data types are not available
            pass
    behavElements = [(element, behavPath, '$id', 'title', sch.getBehavior) for element in behaviors]
    with ThreadPoolExecutor(thread_name_prefix = 'behavior') as thread_pool:
        results = thread_pool.map(writingFullFile, behavElements)
    ## writing classes
    classesElements = [(element, classPath, '$id', 'title',sch.getClass) for element in myclasses]
    with ThreadPoolExecutor(thread_name_prefix = 'behavior') as thread_pool:
        results = thread_pool.map(writingFalseFile, classesElements)
    classGlobalElements = [(element, classPath, '$id', 'title',sch.getClass) for element in classesGlobal]
    with ThreadPoolExecutor(thread_name_prefix = 'classGlobal') as thread_pool:
        results = thread_pool.map(writingFullFile, classGlobalElements)
    myschemas = sch.getSchemas()
    schemaElement = [(element, schemaPath, '$id', 'title', sch.getSchema) for element in myschemas]
    with ThreadPoolExecutor(thread_name_prefix = 'schema') as thread_pool:
        results = thread_pool.map(writingFalseFile, schemaElement)
    ## writing field groups
    myfgs = sch.getFieldGroups()
    fgsElements = [(element, fieldgroupPath, '$id', 'title', sch.getFieldGroup) for element in myfgs]
    with ThreadPoolExecutor(thread_name_prefix = 'fieldgroup') as thread_pool:  
        results = thread_pool.map(writingFalseFile, fgsElements)
    if ootb:
        globalFgs = sch.getFieldGroupsGlobal()
        globalFgsElements = [(element, fieldgroupPathGlobale, '$id', 'title', sch.getFieldGroup) for element in globalFgs]
        with ThreadPoolExecutor(thread_name_prefix = 'globalFieldgroup') as thread_pool:
            results = thread_pool.map(writingFullFile, globalFgsElements)
    ## writing data types
    mydt = sch.getDataTypes()
    datatypeElements = [(element, datatypePath, 'meta:altId', 'title', sch.getDataType) for element in mydt]
    with ThreadPoolExecutor(thread_name_prefix = 'datatype') as thread_pool:
        results = thread_pool.map(writingFalseFile, datatypeElements)
    if ootb:
        globalDataTypes = sch.getDataTypesGlobal()
        globalDataTypesElements = [(element, datatypePathGlobal, 'meta:altId', 'title', sch.getDataType) for element in globalDataTypes]
        with ThreadPoolExecutor(thread_name_prefix = 'globalDatatype') as thread_pool:
            results = thread_pool.map(writingFalseFile, globalDataTypesElements)
    ## writing descriptors
    descriptors = sch.getDescriptors()
    descriptorsElements = [(element,descriptorPath,'@id',"@id",None) for element in descriptors]
    with ThreadPoolExecutor(thread_name_prefix = 'descriptors') as thread_pool:
        results = thread_pool.map(writingFullFile, descriptorsElements)
    datasets = cat.getDataSets()
    for key,value in datasets.items():
        value['id'] = key
        with open(f"{datasetPath / value.get('tags',{}).get('adobe/pqs/table',[key])[0]}.json",'w') as f:
            json.dump(value,f,indent=2)
    identities = ide.getIdentities()
    for el in identities:
        with open(f"{identityPath / el['code']}.json",'w') as f:
            json.dump(el,f,indent=2)

def extractSandboxArtefact(
    sandbox: 'ConnectObject' = None,
    localFolder: Union[str, Path] = None,
    artefact: str = None,
    artefactType: str = None,
    region: str = "nld2",
):
    """
    Export a single artefact and its dependencies from the sandbox.
    Arguments:
        sandbox: REQUIRED: the instance of a ConnectObject that contains the sandbox information and connection.
        localFolder: OPTIONAL: the local folder where to extract the sandbox. If not provided, it will use the current working directory and name the folder the name of the sandbox.
        artefact: REQUIRED: the id or the name of the artefact to export.
        artefactType: REQUIRED: the type of artefact to export. Possible values are: 'class','schema','fieldgroup','datatype','descriptor','dataset','identity'
        region: OPTIONAL: the region of the sandbox (default: nld2). This is used to fetch the correct API endpoints for the identities. 
            Possible values: "va7","aus5", "can2", "ind2"
    """
    if sandbox is None:
        raise ValueError("You need to provide a ConnectObject instance with the sandbox information")
    if localFolder is None:
        mypath = Path('./') 
        completePath = mypath / f'{sandbox.sandbox}'
    else:
        completePath = Path(localFolder)
    completePath.mkdir(exist_ok=True)
    from aepp import schema
    sch = schema.Schema(config=sandbox)
    globalConfig = {
        "imsOrgId":sandbox.org_id,
        "tenantId":f"_{sch.getTenantId()}"
    }
    with open(f'{completePath}/config.json','w') as f:
        json.dump(globalConfig,f,indent=2)
    
    from aepp import schema, catalog, identity
    sch = schema.Schema(config=sandbox)
    cat = catalog.Catalog(config=sandbox)
    if artefactType == 'class':
        __extractClass__(artefact,completePath,sandbox)
    elif artefactType == 'schema':
        __extractSchema__(artefact,completePath,sandbox)
    elif artefactType == 'fieldgroup':
        __extractFieldGroup__(artefact,completePath,sandbox)
    elif artefactType == 'datatype':
        __extractDataType__(artefact,completePath,sandbox)
    elif artefactType == 'dataset':
        __extractDataset__(artefact,completePath,sandbox)
    elif artefactType == 'identity':
        __extractIdentity__(artefact,region,completePath,sandbox)
    else:
        raise ValueError("artefactType not recognized")
    
def __extractClass__(classEl: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None):
    classPath = Path(folder) / 'class'
    classPath.mkdir(exist_ok=True)
    from aepp import schema
    sch = schema.Schema(config=sandbox)
    tenantId = sch.getTenantId()
    myclasses = sch.getClasses()
    myclassesGlobal = sch.getClassesGlobal()
    all_classes = myclasses + myclassesGlobal
    myclass = [el for el in all_classes if el.get('$id','') == classEl or el.get('title','') == classEl or el.get('meta:altId') == classEl][0]
    if tenantId in myclass.get('$id',''):
        definition = sch.getClass(myclass['$id'],full=False,xtype='xed')
    else:
        definition = sch.getClass(myclass['$id'],full=True,xtype='xed')
    file_name = __titleSafe__(definition.get('title',definition.get('$id','unknown')))
    with open(f"{classPath / file_name}.json",'w') as f:
        json.dump(definition,f,indent=2)
    behaviors = definition.get("meta:extends",[""])
    mybeahav = [el for el in behaviors if el == 'https://ns.adobe.com/xdm/data/record' or el == 'https://ns.adobe.com/xdm/data/time-series' or el == 'https://ns.adobe.com/xdm/data/adhoc'][0]
    behavDef = sch.getBehavior(mybeahav,full=True,xtype='xed')
    behavPath = Path(folder) / 'behaviour'
    behavPath.mkdir(exist_ok=True)
    behav_file_name = __titleSafe__(behavDef.get('title',behavDef.get('$id','unknown')))
    with open(f"{behavPath / behav_file_name}.json",'w') as f:
        json.dump(behavDef,f,indent=2)

def __extractDataType__(dataType: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None):
    dtPath = Path(folder) / 'datatype'
    dtPath.mkdir(exist_ok=True)
    dtPathGlobal = dtPath / 'global'
    dtPathGlobal.mkdir(exist_ok=True)
    from aepp import schema, datatypemanager
    sch = schema.Schema(config=sandbox)
    tenantId = sch.getTenantId()
    dts = sch.getDataTypes()
    globalDts = sch.getDataTypesGlobal()
    all_dts = dts + globalDts
    mydt = [el for el in all_dts if el.get('meta:altId','') == dataType or el.get('title','') == dataType or el.get('$id') == dataType][0]
    mydt_manager = datatypemanager.DataTypeManager(mydt.get('$id'),config=sandbox)
    if tenantId in mydt.get('$id',''):
        definition = sch.getDataType(mydt.get('$id',''),full=False,xtype='xed')
        path_to_use = dtPath
    else:
        definition = sch.getDataType(mydt.get('$id',''),full=True,xtype='xed')
        path_to_use = dtPathGlobal
    file_name = __titleSafe__(definition.get('title',definition.get('meta:altId','unknown')))
    with open(f"{path_to_use / file_name}.json",'w') as f:
        json.dump(definition,f,indent=2)
    other_dts = list(mydt_manager.dataTypes.keys())
    if len(other_dts) > 0:
        for dt in other_dts:
            __extractDataType__(dt,folder,sandbox)

def __extractFieldGroup__(fieldGroup: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None):
    fgPath = Path(folder) / 'fieldgroup'
    fgPath.mkdir(exist_ok=True)
    fgPathGlobal = fgPath / 'global'
    fgPathGlobal.mkdir(exist_ok=True)
    from aepp import schema, fieldgroupmanager
    sch = schema.Schema(config=sandbox)
    tenantId = sch.getTenantId()
    fgs = sch.getFieldGroups()
    globalFgs = sch.getFieldGroupsGlobal()
    all_fgs = fgs + globalFgs
    myfg = [el for el in all_fgs if el.get('$id','') == fieldGroup or el.get('title','') == fieldGroup or el.get('meta:altId','') == fieldGroup][0]
    myfg_manager = fieldgroupmanager.FieldGroupManager(myfg.get('$id'),config=sandbox)
    if tenantId in myfg.get('$id',''):
        definition = sch.getFieldGroup(myfg['$id'],full=False,xtype='xed')
        path_to_use = fgPath
    else:
        definition = sch.getFieldGroup(myfg['$id'],full=True,xtype='xed')
        path_to_use = fgPathGlobal
    file_name = __titleSafe__(definition.get('title',definition.get('$id','unknown')))
    with open(f"{path_to_use / file_name}.json",'w') as f:
        json.dump(definition,f,indent=2)
    myfg_manager_dataTypes = list(myfg_manager.dataTypes.keys())
    if len(myfg_manager_dataTypes) > 0:
        def unpack_dt_call(dtElements):
            element,folder,sandbox = dtElements
            __extractDataType__(element,folder,sandbox)
        dtElements = [(element,folder,sandbox) for element in myfg_manager_dataTypes]
        with ThreadPoolExecutor(thread_name_prefix = 'datatypes') as thread_pool:
            results = thread_pool.map(unpack_dt_call, dtElements)
    descriptors = myfg_manager.getDescriptors()
    if len(descriptors) > 0:
        descriptorPath = Path(folder) / 'descriptor'
        descriptorPath.mkdir(exist_ok=True)
        for descriptor in descriptors:
            with open(f"{descriptorPath / descriptor['@id']}.json",'w') as f:
                json.dump(descriptor,f,indent=2)

def __extractSchema__(schemaEl: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None):
    schemaPath = Path(folder) / 'schema'
    schemaPath.mkdir(exist_ok=True)
    from aepp import schema, schemamanager
    sch = schema.Schema(config=sandbox)
    tenantId = sch.getTenantId()
    myschemas = sch.getSchemas()
    myschema = [el for el in myschemas if el.get('$id','') == schemaEl or el.get('title','') == schemaEl or el.get('meta:altId') == schemaEl][0]
    definition = sch.getSchema(myschema['$id'],full=False,xtype='xed')
    schema_manager = schemamanager.SchemaManager(myschema.get('$id'),config=sandbox)
    file_name = __titleSafe__(definition.get('title',definition.get('$id','unknown')))
    with open(f"{schemaPath / file_name}.json",'w') as f:
        json.dump(definition,f,indent=2)
    # extract field groups
    fg_list = schema_manager.fieldGroupIds
    if len(fg_list) > 0:
        def unpack_fg_call(fgsElements):
            element,folder,sandbox = fgsElements
            __extractFieldGroup__(element,folder,sandbox)
        fgsElements = [(element,folder,sandbox) for element in fg_list]
        with ThreadPoolExecutor(thread_name_prefix = 'fieldGroup') as thread_pool:
            results = thread_pool.map(unpack_fg_call, fgsElements)
    class_id = schema_manager.classId
    __extractClass__(class_id,folder,sandbox)
    descriptors = schema_manager.getDescriptors()
    if len(descriptors) > 0:
        descriptorPath = Path(folder) / 'descriptor'
        descriptorPath.mkdir(exist_ok=True)
        for descriptor in descriptors:
            with open(f"{descriptorPath / descriptor['@id']}.json",'w') as f:
                json.dump(descriptor,f,indent=2)

def __extractIdentity__(identity: str,region:str=None,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None):
    from aepp import identity
    ide = identity.Identity(config=sandbox,region=region)
    identities = ide.getIdentities()
    myIdentity = [el for el in identities if el.get('code','') == identity or el.get('name','') == identity][0]
    identityPath = Path(folder) / 'identity'
    identityPath.mkdir(exist_ok=True)
    file_name = __titleSafe__(myIdentity.get('code',myIdentity.get('name','unknown')))
    with open(f"{identityPath / file_name}.json",'w') as f:
        json.dump(myIdentity,f,indent=2)

def __extractDataset__(dataset: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None):
    from aepp import catalog
    cat = catalog.Catalog(config=sandbox)
    datasets = cat.getDataSets()
    myDataset = None
    for key,value in datasets.items():
        if key == dataset or value.get('tags',{}).get('adobe/pqs/table',[''])[0] == dataset or value.get('name','') == dataset:
            myDataset = value
            myDataset['id'] = key
    if myDataset is None:
        raise ValueError("Dataset not found")
    datasetPath = Path(folder) / 'dataset'
    datasetPath.mkdir(exist_ok=True)
    file_name = __titleSafe__(myDataset.get('tags',{}).get('adobe/pqs/table',[myDataset.get('id','unknown')])[0])
    with open(f"{datasetPath / file_name}.json",'w') as f:
        json.dump(myDataset,f,indent=2)
    schema = myDataset.get('schemaRef',{}).get('id',None)
    if schema is not None:
        __extractSchema__(schema,folder,sandbox)