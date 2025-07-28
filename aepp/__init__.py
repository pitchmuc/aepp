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

def extractSandboxArtefacts(
    sandbox: 'ConnectInConnectObjectstance' = None, 
    localFolder: Union[str, Path] = None,
    region: str = "nld2",

):
    """
    Extract the sandbox in the local folder.
    Arguments:
        sandbox: REQUIRED: the instance of a ConnectObject that contains the sandbox information and connection.
        localFolder: OPTIONAL: the local folder where to extract the sandbox. If not provided, it will use the current working directory and name the folder the name of the sandbox.
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
    from aepp import schema, catalog, identity
    sch = schema.Schema(config=sandbox)
    cat = catalog.Catalog(config=sandbox)
    ide = identity.Identity(config=sandbox,region=region)
    mypath = Path('./')
    completePath.mkdir(exist_ok=True)
    behavPath = completePath / 'behaviour'
    behavPath.mkdir(exist_ok=True)
    classPath = completePath / 'class'
    classPath.mkdir(exist_ok=True)
    schemaPath = completePath / 'schema'
    schemaPath.mkdir(exist_ok=True)
    fieldgroupPath = completePath / 'fieldgroup'
    fieldgroupPath.mkdir(exist_ok=True)
    datatypePath = completePath / 'datatype'
    datatypePath.mkdir(exist_ok=True)
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
        element,path,id_key,method = tuple_element
        try:
            if method is not None:
                definition = method(element[id_key],full=True,xtype='xed')
                with open(f"{path / definition[id_key].split('/').pop()}.json",'w') as f:
                    json.dump(definition,f,indent=2)
            else:
                with open(f"{path / element[id_key]}.json",'w') as f:
                    json.dump(element,f,indent=2)
        except Exception as e: ### some geo data types are not available
            pass
    def writingFalseFile(tuple_element):
        element,path,id_key,method = tuple_element
        try:
            definition = method(element[id_key],full=False,xtype='xed')
            with open(f"{path / definition[id_key].split('/').pop()}.json",'w') as f:
                json.dump(definition,f,indent=2)
        except Exception as e: ### some geo data types are not available
            pass
    behavElements = [(element, behavPath, '$id',sch.getBehavior) for element in behaviors]
    with ThreadPoolExecutor(thread_name_prefix = 'behavior') as thread_pool:
        results = thread_pool.map(writingFullFile, behavElements)
    ## writing classes
    classesElements = [(element, classPath, '$id',sch.getClass) for element in myclasses]
    with ThreadPoolExecutor(thread_name_prefix = 'behavior') as thread_pool:
        results = thread_pool.map(writingFalseFile, classesElements)
    classGlobalElements = [(element, classPath, '$id',sch.getClass) for element in classesGlobal]
    with ThreadPoolExecutor(thread_name_prefix = 'classGlobal') as thread_pool:
        results = thread_pool.map(writingFullFile, classGlobalElements)
    myschemas = sch.getSchemas()
    schemaElement = [(element, schemaPath, '$id', sch.getSchema) for element in myschemas]
    with ThreadPoolExecutor(thread_name_prefix = 'schema') as thread_pool:
        results = thread_pool.map(writingFalseFile, schemaElement)
    ## writing field groups
    myfgs = sch.getFieldGroups()
    fgsElements = [(element, fieldgroupPath, '$id', sch.getFieldGroup) for element in myfgs]
    with ThreadPoolExecutor(thread_name_prefix = 'fieldgroup') as thread_pool:  
        results = thread_pool.map(writingFalseFile, fgsElements)
    globalFgs = sch.getFieldGroupsGlobal()
    globalFgsElements = [(element, fieldgroupPath, '$id', sch.getFieldGroup) for element in globalFgs]
    with ThreadPoolExecutor(thread_name_prefix = 'globalFieldgroup') as thread_pool:
        results = thread_pool.map(writingFullFile, globalFgsElements)
    ## writing data types
    mydt = sch.getDataTypes()
    datatypeElements = [(element, datatypePath, 'meta:altId', sch.getDataType) for element in mydt]
    with ThreadPoolExecutor(thread_name_prefix = 'datatype') as thread_pool:
        results = thread_pool.map(writingFalseFile, datatypeElements)
    globalDataTypes = sch.getDataTypesGlobal()
    globalDataTypesElements = [(element, datatypePath, 'meta:altId', sch.getDataType) for element in globalDataTypes]
    with ThreadPoolExecutor(thread_name_prefix = 'globalDatatype') as thread_pool:
        results = thread_pool.map(writingFalseFile, globalDataTypesElements)
    ## writing descriptors
    descriptors = sch.getDescriptors()
    descriptorsElements = [(element,descriptorPath,'@id',None) for element in descriptors]
    with ThreadPoolExecutor(thread_name_prefix = 'descriptors') as thread_pool:
        results = thread_pool.map(writingFullFile, descriptorsElements)
    datasets = cat.getDataSets()
    for key,value in datasets.items():
        value['id'] = key
        with open(f"{datasetPath / key}.json",'w') as f:
            json.dump(value,f,indent=2)
    identities = ide.getIdentities()
    for el in identities:
        with open(f"{identityPath / el['code']}.json",'w') as f:
            json.dump(el,f,indent=2)