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
import re

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

def setRetry(rety:int)->None:
    """
    Set the number of retry for the connection and the modules.
    Arguments:
        retry : REQUIRED : int to set the number of retry in case of connection error for the connection and the modules.
    """
    config.config_object["retry"] = rety
    if connection is not None:
        connection.retry = rety

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


def __make_filename_safe__(filename, replacement="_"):
    # 1. Remove characters that are illegal in Windows or Linux
    # Windows: < > : " / \ | ? * # Linux: / (and NULL)
    filename = re.sub(r'[<>:"/\\|?*]', replacement, filename)
    # 2. Remove control characters (ASCII 0-31)
    filename = re.sub(r'[\x00-\x1f]', replacement, filename)
    # 3. Trim whitespace and trailing dots (Windows doesn't like trailing dots)
    filename = filename.strip().strip('.')
    # 4. Handle Windows Reserved Names (CON, PRN, AUX, NUL, COM1, LPT1, etc.)
    reserved_names = {
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9"
    }
    # Check the base name without extension
    base_name = os.path.splitext(filename)[0].upper()
    if base_name in reserved_names:
        filename = f"{replacement}{filename}"
    # 5. Length limit (standard for most file systems is 255 chars)
    if len(filename) > 255:
        filename = filename[:255]
    # 6. Default to a placeholder if the string is empty after cleaning
    return filename if filename else "unnamed_file"


def saveFile(
    module: str | None = None,
    file: object = None,
    filename: str = None,
    type_file: str = "json",
    encoding: str = "utf-8",
):
    """
    Save the file in the approriate folder depending on the module sending the information.
     Arguments:
          module: OPTIONAL: Module requesting the save file.
          file: REQUIRED: an object containing the file to save.
          filename: REQUIRED: the filename to be used.
          type_file: REQUIRED: the type of file to be saveed(default: json)
          encoding : OPTIONAL : encoding used to write the file.
    """
    if file is None or filename is None:
        raise ValueError("Require a object for file and a name for the file")
    here = Path(Path.cwd())
    if module is not None:
        folder = module.capitalize()
        new_location = Path.joinpath(here, folder)
    else:
        new_location = here
    if new_location.exists() == False:
        new_location.mkdir()
    filename = __make_filename_safe__(filename)
    if type_file == "json":
        filename = f"{filename}.json"
        complete_path = Path.joinpath(new_location, filename)
        with open(complete_path, "w", encoding=encoding) as f:
            f.write(json.dumps(file, indent=4))
    elif type_file == "txt":
        filename = f"{filename}.txt"
        complete_path = Path.joinpath(new_location, filename)
        with open(complete_path, "w", encoding=encoding) as f:
            f.write(file)
    else:
        filename = f"{filename}.{type_file}"
        complete_path = Path.joinpath(new_location, filename)
        with open(complete_path, "wb") as f:
            f.write(file)
    return complete_path

def __titleSafe__(text: str) -> str:
    """
    Create a safe title for a file name
    Arguments:
        text : REQUIRED : the text to be converted
    """
    valid_chars = "[^a-zA-Z0-9_\n\\.]"
    text = re.sub(valid_chars, "_", text)
    return text


def extractSandboxArtifacts(
    sandbox: 'ConnectObject' = None, 
    localFolder: Union[str, Path] = None,
    ootb: bool = True,
    retry: int = 2,
    **kwargs
):
    """
    Extract the sandbox in the local folder.
    Arguments:
        sandbox: REQUIRED: the instance of a ConnectObject that contains the sandbox information and connection.
        localFolder: OPTIONAL: the local folder where to extract the sandbox. If not provided, it will use the current working directory and name the folder the name of the sandbox.
        ootb : OPTIONAL : If you want to also download the OOTB elements
        retry: OPTIONAL: the number of retry in case of connection error for the modules (default is 2)
    """
    if sandbox is None:
        raise ValueError("You need to provide a ConnectObject instance with the sandbox information")
    if localFolder is None:
        mypath = Path('./') 
        completePath = mypath / f'{sandbox.sandbox}'
    else:
        completePath = Path(localFolder)
    from aepp import schema, catalog, identity,customerprofile, segmentation, tags
    sch = schema.Schema(config=sandbox,retry=retry)
    cat = catalog.Catalog(config=sandbox)
    ide = identity.Identity(config=sandbox)
    completePath.mkdir(exist_ok=True)
    globalConfig = {
        "imsOrgId":sandbox.org_id,
        "tenantId":f"_{sch.getTenantId()}",
        "sandbox":sandbox.sandbox
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
    mergePolicyPath = completePath / 'mergePolicy'
    mergePolicyPath.mkdir(exist_ok=True)
    audiencePath = completePath / 'audience'
    audiencePath.mkdir(exist_ok=True)
    tagPath = completePath / 'tag'
    tagPath.mkdir(exist_ok=True)
    ## handling tags
    tag_manager = tags.Tags(config=sandbox)
    all_tags = tag_manager.getTags()
    dict_id_name = {tag['id']:tag['name'] for tag in all_tags}
    with open(tagPath / "tags.json",'w') as f:
        json.dump(all_tags,f,indent=2)
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
        ### exception for a fieldgroup not supported by default getFieldGroups endpoint
        myfg = sch.getFieldGroup('https://ns.adobe.com/experience/intelligentServices/event-journeyai-sendtimeoptimization-summary',full=True,xtype='xed')
        title_myfg = __titleSafe__(myfg.get('title',myfg.get('$id','unknown')))
        with open(f"{fieldgroupPathGlobale / title_myfg}.json",'w') as f:
            json.dump(myfg,f,indent=2)
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
        if len(value.get('unifiedTags',[])) > 0:
            tag_names = [dict_id_name.get(tag_id) for tag_id in value.get('unifiedTags',[])]
            value['unifiedTags'] = tag_names
        with open(f"{datasetPath / value.get('tags',{}).get('adobe/pqs/table',[key])[0]}.json",'w') as f:
            json.dump(value,f,indent=2)
    identities = ide.getIdentities()
    for el in identities:
        with open(f"{identityPath / el['code']}.json",'w') as f:
            json.dump(el,f,indent=2)
    ## merge policies
    ups = customerprofile.Profile(config=sandbox)
    mymergePolicies = ups.getMergePolicies()
    for el in mymergePolicies:
        with open(f"{mergePolicyPath / el.get('id','unknown')}.json",'w') as f:
            json.dump(el,f,indent=2)
    ## audiences
    mysegmentation = segmentation.Segmentation(config=sandbox) 
    audiences = mysegmentation.getAudiences()
    for el in audiences:
        safe_name = __titleSafe__(el.get('name','unknown'))
        if len(el.get('tags',[])) > 0:
            tag_names = [dict_id_name.get(tag_id) for tag_id in el.get('tags',[])]
            el['tags'] = tag_names
        with open(f"{audiencePath / safe_name}.json",'w') as f:
            json.dump(el,f,indent=2)

def extractSandboxArtifact(
    sandbox: 'ConnectObject' = None,
    localFolder: Union[str, Path] = None,
    artifact: str = None,
    artifactType: str = None,
    retry: int = 2
):
    """
    Export a single artifact and its dependencies from the sandbox.
    Arguments:
        sandbox: REQUIRED: the instance of a ConnectObject that contains the sandbox information and connection.
        localFolder: OPTIONAL: the local folder where to extract the sandbox. If not provided, it will use the current working directory and name the folder the name of the sandbox.
        artifact: REQUIRED: the id or the name of the artifact to export.
        artifactType: REQUIRED: the type of artifact to export. Possible values are: 'class','schema','fieldgroup','datatype','descriptor','dataset','identity','mergepolicy',audience'
        retry: OPTIONAL: the number of retry in case of connection error for the modules (default is 2)
    """
    if sandbox is None:
        raise ValueError("You need to provide a ConnectObject instance with the sandbox information")
    if localFolder is None:
        mypath = Path('./') 
        completePath = mypath / f'{sandbox.sandbox}'
    else:
        completePath = Path(localFolder)
    completePath.mkdir(exist_ok=True)
    from aepp import schema,catalog, tags
    sch = schema.Schema(config=sandbox,retry=2)
    cat = catalog.Catalog(config=sandbox)
    globalConfig = {
        "imsOrgId":sandbox.org_id,
        "tenantId":f"_{sch.getTenantId()}",
        "sandbox":sandbox.sandbox
    }
    with open(f'{completePath}/config.json','w') as f:
        json.dump(globalConfig,f,indent=2)
    ### taking care of tas
    tagPath = completePath / 'tag'
    tagPath.mkdir(exist_ok=True)
    tag_manager = tags.Tags(config=sandbox)
    all_tags = tag_manager.getTags()
    dict_tag_id_name = {tag['id']:tag['name'] for tag in all_tags}
    with open(f'{tagPath}/tags.json','w') as f:
        json.dump(all_tags,f,indent=2)
    if artifactType == 'class':
        __extractClass__(artifact,completePath,sandbox,retry)
    elif artifactType == 'schema':
        __extractSchema__(artifact,completePath,sandbox,retry)
    elif artifactType == 'fieldgroup':
        __extractFieldGroup__(artifact,completePath,sandbox,retry)
    elif artifactType == 'datatype':
        __extractDataType__(artifact,completePath,sandbox,retry)
    elif artifactType == 'dataset':
        __extractDataset__(artifact,completePath,sandbox,dict_tag_id_name=dict_tag_id_name,retry=retry)
    elif artifactType == 'identity':
        __extractIdentity__(artifact,completePath,sandbox,retry=retry)
    elif artifactType == 'mergepolicy':
        __extractMergePolicy__(artifact,completePath,sandbox,dict_tag_id_name=dict_tag_id_name)
    elif artifactType == 'audience':
        __extractAudience__(artifact,completePath,sandbox,dict_tag_id_name)
    else:
        raise ValueError("artifactType not recognized")

def __extractClass__(classEl: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None,retry: int = 2):
    classPath = Path(folder) / 'class'
    classPath.mkdir(exist_ok=True)
    from aepp import schema
    sch = schema.Schema(config=sandbox,retry=retry)
    tenantId = sch.getTenantId()
    myclasses = sch.getClasses()
    myclassesGlobal = sch.getClassesGlobal()
    all_classes = myclasses + myclassesGlobal
    try:
        myclass = [el for el in all_classes if el.get('$id','') == classEl or el.get('title','') == classEl or el.get('meta:altId') == classEl][0]
    except IndexError:
        raise IndexError("The class you want to extract is not present in the sandbox or the id/name provided is not correct")
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

def __extractDataType__(dataType: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None,retry: int = 2):
    dtPath = Path(folder) / 'datatype'
    dtPath.mkdir(exist_ok=True)
    dtPathGlobal = dtPath / 'global'
    dtPathGlobal.mkdir(exist_ok=True)
    from aepp import schema, datatypemanager
    sch = schema.Schema(config=sandbox,retry=retry)
    tenantId = sch.getTenantId()
    dts = sch.getDataTypes()
    globalDts = sch.getDataTypesGlobal()
    all_dts = dts + globalDts
    try:
        mydt = [el for el in all_dts if el.get('meta:altId','') == dataType or el.get('title','') == dataType or el.get('$id') == dataType][0]
    except IndexError:
        raise IndexError("The data type you want to extract is not present in the sandbox or the id/name provided is not correct")
    if mydt.get('$id','') in ['http://schema.org/GeoShape', 'http://schema.org/GeoCoordinates', 'http://schema.org/GeoCircle']:
        mydt_manager = datatypemanager.DataTypeManager(mydt.get('meta:altId'),config=sandbox,retry=retry)
    else:
        mydt_manager = datatypemanager.DataTypeManager(mydt.get('$id'),config=sandbox,retry=retry)
    if tenantId in mydt.get('$id',''):
        definition = sch.getDataType(mydt.get('$id',''),full=False,xtype='xed')
        path_to_use = dtPath
    else:
        dt_id = mydt.get('$id','')
        if dt_id in ['http://schema.org/GeoShape', 'http://schema.org/GeoCoordinates', 'http://schema.org/GeoCircle']:
            dt_id = mydt.get('meta:altId')
        definition = sch.getDataType(dt_id,full=True,xtype='xed')
        path_to_use = dtPathGlobal
    file_name = __titleSafe__(definition.get('title',definition.get('meta:altId','unknown')))
    with open(f"{path_to_use / file_name}.json",'w') as f:
        json.dump(definition,f,indent=2)
    other_dts = list(mydt_manager.dataTypes.keys())
    if len(other_dts) > 0:
        for dt in other_dts:
            if dt == 'http://schema.org/GeoShape':
                dt = '_schema.org.GeoShape'
            elif dt == 'http://schema.org/GeoCoordinates':
                dt = '_schema.org.GeoCoordinates'
            elif dt == 'http://schema.org/GeoCircle':
                dt = '_schema.org.GeoCircle'
            __extractDataType__(dt,folder,sandbox)

def __extractFieldGroup__(fieldGroup: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None,retry: int = 2):
    fgPath = Path(folder) / 'fieldgroup'
    fgPath.mkdir(exist_ok=True)
    fgPathGlobal = fgPath / 'global'
    fgPathGlobal.mkdir(exist_ok=True)
    from aepp import schema, fieldgroupmanager
    sch = schema.Schema(config=sandbox,retry=retry)
    tenantId = sch.getTenantId()
    fgs = sch.getFieldGroups()
    globalFgs = sch.getFieldGroupsGlobal()
    all_fgs = fgs + globalFgs
    try:
        myfg = [el for el in all_fgs if el.get('$id','') == fieldGroup or el.get('title','') == fieldGroup or el.get('meta:altId','') == fieldGroup][0]
    except IndexError:
        raise IndexError("The field group you want to extract is not present in the sandbox or the id/name provided is not correct")
    myfg_manager = fieldgroupmanager.FieldGroupManager(myfg.get('$id'),config=sandbox,retry=retry)
    definition = sch.getFieldGroup(myfg['$id'],full=False,xtype='xed')
    if tenantId in myfg.get('$id',''):
        path_to_use = fgPath
    else:
        path_to_use = fgPathGlobal
    file_name = __titleSafe__(definition.get('title',definition.get('$id','unknown')))
    with open(f"{path_to_use / file_name}.json",'w') as f:
        json.dump(definition,f,indent=2)
    myfg_manager_dataTypes = list(myfg_manager.dataTypes.keys())
    if len(myfg_manager_dataTypes) > 0:
        def unpack_dt_call(dtElements):
            element,folder,sandbox,retry = dtElements
            __extractDataType__(element,folder,sandbox,retry)
        dtElements = [(element,folder,sandbox,retry) for element in myfg_manager_dataTypes]
        with ThreadPoolExecutor(thread_name_prefix = 'datatypes') as thread_pool:
            results = thread_pool.map(unpack_dt_call, dtElements)
    descriptors = myfg_manager.getDescriptors()
    if len(descriptors) > 0:
        descriptorPath = Path(folder) / 'descriptor'
        descriptorPath.mkdir(exist_ok=True)
        for descriptor in descriptors:
            with open(f"{descriptorPath / descriptor['@id']}.json",'w') as f:
                json.dump(descriptor,f,indent=2)
    classes = myfg_manager.classIds
    for cls in classes:
        __extractClass__(cls,folder,sandbox,retry)

def __extractSchema__(schemaEl: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None,retry: int = 2, _visited: set = None):
    if _visited is None: ## to avoid circular dependencies
        _visited = set()
    schemaPath = Path(folder) / 'schema'
    schemaPath.mkdir(exist_ok=True)
    from aepp import schema, schemamanager
    sch = schema.Schema(config=sandbox,retry=retry)
    myschemas = sch.getSchemas()
    try:
        myschema = [el for el in myschemas if el.get('$id','') == schemaEl or el.get('title','') == schemaEl or el.get('meta:altId') == schemaEl][0]
    except IndexError:
        raise IndexError("The schema you want to extract is not present in the sandbox or the id/name provided is not correct")
    schema_id = myschema['$id']
    if schema_id in _visited:
        return
    _visited.add(schema_id)
    definition = sch.getSchema(schema_id,full=False,xtype='xed')
    schema_manager = schemamanager.SchemaManager(schema_id,config=sandbox,retry=retry)
    file_name = __titleSafe__(definition.get('title',definition.get('$id','unknown')))
    with open(f"{schemaPath / file_name}.json",'w') as f:
        json.dump(definition,f,indent=2)
    # extract field groups
    fg_list = schema_manager.fieldGroupIds
    if len(fg_list) > 0:
        def unpack_fg_call(fgsElements):
            element,folder,sandbox,retry = fgsElements
            __extractFieldGroup__(element,folder,sandbox,retry)
        fgsElements = [(element,folder,sandbox,retry) for element in fg_list]
        with ThreadPoolExecutor(thread_name_prefix = 'fieldGroup') as thread_pool:
            results = thread_pool.map(unpack_fg_call, fgsElements)
    class_id = schema_manager.classId
    __extractClass__(class_id,folder,sandbox,retry)
    descriptors = schema_manager.getDescriptors()
    if len(descriptors) > 0:
        descriptorPath = Path(folder) / 'descriptor'
        descriptorPath.mkdir(exist_ok=True)
        for descriptor in descriptors:
            with open(f"{descriptorPath / descriptor['@id']}.json",'w') as f:
                json.dump(descriptor,f,indent=2)
            if descriptor.get('@type','') == 'xdm:descriptorIdentity':
                namespace = descriptor['xdm:namespace']
                __extractIdentity__(namespace,folder,sandbox,retry)
            if descriptor.get('@type','') == 'xdm:descriptorRelationship' or descriptor.get('@type','') == 'xdm:descriptorOneToOne':
                targetSchema = descriptor['xdm:destinationSchema']
                if targetSchema not in _visited:
                    __extractSchema__(targetSchema,folder,sandbox,retry,_visited)


def __extractIdentity__(identityStr: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None,retry: int = 2):
    from aepp import identity
    ide = identity.Identity(config=sandbox,retry=retry)
    identities = ide.getIdentities()
    try:
        myIdentity = [el for el in identities if el.get('code','').lower() == identityStr.lower() or el.get('name','') == identityStr][0]
    except IndexError:
        raise IndexError(f"The identity {identityStr} you want to extract is not present in the sandbox or the code/name provided is not correct")
    identityPath = Path(folder) / 'identity'
    identityPath.mkdir(exist_ok=True)
    file_name = __titleSafe__(myIdentity.get('code',myIdentity.get('name','unknown')))
    with open(f"{identityPath / file_name}.json",'w') as f:
        json.dump(myIdentity,f,indent=2)

def __extractDataset__(dataset: str,folder: Union[str, Path] = None,sandbox: 'ConnectObject' = None,dict_tag_id_name: dict = None, retry:int=2, _visited: set = None,**kwargs):
    from aepp import catalog
    cat = catalog.Catalog(config=sandbox)
    datasets = cat.getDataSets()
    myDataset = None
    for key,value in datasets.items():
        if key == dataset or value.get('tags',{}).get('adobe/pqs/table',[''])[0] == dataset or value.get('name','') == dataset:
            myDataset = value
            myDataset['id'] = key
            if dict_tag_id_name is not None and len(myDataset.get('unifiedTags',[])) > 0:
                tag_names = [dict_tag_id_name.get(tag_id) for tag_id in myDataset.get('unifiedTags',[])]
                myDataset['unifiedTags'] = tag_names
    if myDataset is None:
        raise IndexError("The dataset you want to extract is not present in the sandbox or the id/name provided is not correct")
    datasetPath = Path(folder) / 'dataset'
    datasetPath.mkdir(exist_ok=True)
    file_name = __titleSafe__(myDataset.get('tags',{}).get('adobe/pqs/table',[myDataset.get('id','unknown')])[0])
    with open(f"{datasetPath / file_name}.json",'w') as f:
        json.dump(myDataset,f,indent=2)
    schema = myDataset.get('schemaRef',{}).get('id',None)
    if schema is not None:
        __extractSchema__(schema,folder,sandbox,retry,_visited)

def __extractMergePolicy__(mergePolicy: str = None,folder:Union[str, Path]=None, sandbox: 'ConnectObject' = None,dict_tag_id_name: dict = None,**kwargs):
    from aepp import customerprofile
    ups = customerprofile.Profile(config=sandbox)
    mymergePolicies = ups.getMergePolicies()
    mymergePolicy = [el for el in mymergePolicies if el.get('id','') == mergePolicy or el.get('name','') == mergePolicy][0]
    if mymergePolicy['attributeMerge'].get('type','timestampOrdered') == 'dataSetPrecedence':
        list_ds = mymergePolicy['attributeMerge'].get('order',[])
        for ds in list_ds:
            __extractDataset__(ds,folder,sandbox,dict_tag_id_name=dict_tag_id_name)
    mergePolicyPath = Path(folder) / 'mergePolicy'
    mergePolicyPath.mkdir(exist_ok=True)
    with open(f"{mergePolicyPath / mymergePolicy.get('id','unknown')}.json",'w') as f:
        json.dump(mymergePolicy,f,indent=2)

def __extractAudience__(audienceName: str = None,folder:Union[str, Path]=None, sandbox: 'ConnectObject' = None,dict_tag_id_name: dict = None,**kwargs):
    from aepp import segmentation
    mysegmentation = segmentation.Segmentation(config=sandbox) 
    audiences = mysegmentation.getAudiences()
    try:
        myaudience = [el for el in audiences if el.get('name','') == audienceName or el.get('id','') == audienceName][0]
    except IndexError:
        raise IndexError("The audience you want to extract is not present in the sandbox or the name/id provided is not correct")
    audiencePath = Path(folder) / 'audience'
    audiencePath.mkdir(exist_ok=True)
    safe_name = __titleSafe__(myaudience.get('name','unknown'))
    if len(myaudience.get('tags',[])) > 0 and dict_tag_id_name is not None:
        tag_names = [dict_tag_id_name.get(tag_id) for tag_id in myaudience.get('tags',[])]
        myaudience['tags'] = tag_names
    with open(f"{audiencePath / safe_name}.json",'w') as f:
        json.dump(myaudience,f,indent=2)