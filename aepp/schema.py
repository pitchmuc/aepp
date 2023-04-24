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
import aepp
from dataclasses import dataclass
from aepp import connector
from copy import deepcopy
from typing import Union
import time
import logging
import pandas as pd
import json
import re
from .configs import ConnectObject

json_extend = [
    {
        "op": "replace",
        "path": "/meta:intendedToExtend",
        "value": [
            "https://ns.adobe.com/xdm/context/profile",
            "https://ns.adobe.com/xdm/context/experienceevent",
        ],
    }
]


@dataclass
class _Data:
    def __init__(self):
        self.schemas = {}
        self.schemas_id = {}
        self.schemas_altId = {}
        self.fieldGroups_id = {}
        self.fieldGroups_altId = {}
        self.fieldGroups = {}


class Schema:
    """
    This class is a wrapper around the schema registry API for Adobe Experience Platform.
    More documentation on these endpoints can be found here :
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/schema-registry.yaml

    When Patching a schema, you can use the PATCH_OBJ reference to help you.
    """

    schemas = {}  # caching

    ## logging capability
    loggingEnabled = False
    logger = None

    _schemaClasses = {
        "event": "https://ns.adobe.com/xdm/context/experienceevent",
        "profile": "https://ns.adobe.com/xdm/context/profile",
    }
    PATCH_OBJ = [{"op": "add", "path": "/meta:immutableTags-", "value": "union"}]
    DESCRIPTOR_TYPES =["xdm:descriptorIdentity","xdm:alternateDisplayInfo","xdm:descriptorOneToOne","xdm:descriptorReferenceIdentity","xdm:descriptorDeprecated"]

    def __init__(
        self,
        containerId: str = "tenant",
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header=aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ):
        """
        Copy the token and header and initiate the object to retrieve schema elements.
        Arguments:
            containerId : OPTIONAL : "tenant"(default) or "global"
            loggingObject : OPTIONAL : logging object to log messages.
            config : OPTIONAL : config object in the config module.
            header : OPTIONAL : header object  in the config module.
        possible kwargs:
            x-sandbox-name : name of the sandbox you want to use (default : "prod").
        """
        if loggingObject is not None and sorted(
            ["level", "stream", "format", "filename", "file"]
        ) == sorted(list(loggingObject.keys())):
            self.loggingEnabled = True
            self.logger = logging.getLogger(f"{__name__}")
            self.logger.setLevel(loggingObject["level"])
            if type(loggingObject["format"]) == str:
                formatter = logging.Formatter(loggingObject["format"])
            elif type(loggingObject["format"]) == logging.Formatter:
                formatter = loggingObject["format"]
            if loggingObject["file"]:
                fileHandler = logging.FileHandler(loggingObject["filename"])
                fileHandler.setFormatter(formatter)
                self.logger.addHandler(fileHandler)
            if loggingObject["stream"]:
                streamHandler = logging.StreamHandler()
                streamHandler.setFormatter(formatter)
                self.logger.addHandler(streamHandler)
        if type(config) == dict: ## Supporting either default setup or passing a ConnectObject
            config = config
        elif type(config) == ConnectObject:
            header = config.getConfigHeader()
            config = config.getConfigObject()
        self.connector = connector.AdobeRequest(
            config=config,
            header=header,
            loggingEnabled=self.loggingEnabled,
            logger=self.logger,
        )
        self.header = self.connector.header
        self.header["Accept"] = "application/vnd.adobe.xed+json"
        self.connector.header['Accept'] = "application/vnd.adobe.xed+json"
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.header.update(**kwargs)
        self.endpoint = (
            aepp.config.endpoints["global"] + aepp.config.endpoints["schemas"]
        )
        self.container = containerId
        self.data = _Data()

    def getResource(
        self,
        endpoint: str = None,
        params: dict = None,
        format: str = "json",
        save: bool = False,
        **kwargs,
    ) -> dict:
        """
        Template for requesting data with a GET method.
        Arguments:
            endpoint : REQUIRED : The URL to GET
            params: OPTIONAL : dictionary of the params to fetch
            format : OPTIONAL : Type of response returned. Possible values:
                json : default
                txt : text file
                raw : a response object from the requests module
        """
        if endpoint is None:
            raise ValueError("Require an endpoint")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getResource")
        res = self.connector.getData(endpoint, params=params, format=format)
        if save:
            if format == "json":
                aepp.saveFile(
                    module="catalog",
                    file=res,
                    filename=f"resource_{int(time.time())}",
                    type_file="json",
                    encoding=kwargs.get("encoding", "utf-8"),
                )
            elif format == "txt":
                aepp.saveFile(
                    module="catalog",
                    file=res,
                    filename=f"resource_{int(time.time())}",
                    type_file="txt",
                    encoding=kwargs.get("encoding", "utf-8"),
                )
            else:
                print(
                    "element is an object. Output is unclear. No save made.\nPlease save this element manually"
                )
        return res

    def updateSandbox(self, sandbox: str = None) -> None:
        """
        Update the sandbox used in your request.
        Arguments:
            sandbox : REQUIRED : name of the sandbox to be used
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateSandbox")
        if not sandbox:
            raise ValueError("`sandbox` must be specified in the arguments.")
        self.header["x-sandbox-name"] = sandbox
        self.sandbox = sandbox

    def getStats(self) -> list:
        """
        Returns a list of the last actions realized on the Schema for this instance of AEP.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getStats")
        path = "/stats/"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def getTenantId(self) -> str:
        """
        Return the tenantID for the AEP instance.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getTenantId")
        res = self.getStats()
        tenant = res["tenantId"]
        return tenant

    def getBehaviors(self)->list:
        """
        Return a list of behaviors.
        """
        path = "/global/behaviors"
        res = self.connector.getData(self.endpoint + path)
        data = res.get("results",[])
        return data

    def getBehavior(self,behaviorId:str=None)->dict:
        """
        Retrieve a specific behavior for class creation.
        Arguments:
            behaviorId : REQUIRED : the behavior ID to be retrieved.
        """
        if behaviorId is None:
            raise Exception("Require a behavior ID")
        path = f"/global/behaviors/{behaviorId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def getSchemas(
            self, 
            classFilter: str = None,
            excludeAdhoc: bool = False,
            output: str = 'raw',
            **kwargs
    ) -> list:
        """
        Returns the list of schemas retrieved for that instances in a "results" list.
        Arguments:
            classFilter : OPTIONAL : filter to a specific class.
                Example :
                    https://ns.adobe.com/xdm/context/experienceevent
                    https://ns.adobe.com/xdm/context/profile
                    https://ns.adobe.com/xdm/data/adhoc
            excludeAdhoc : OPTIONAL : exclude the adhoc schemas
            output : OPTIONAL : either "raw" for a list or "df" for dataframe
        Possible kwargs:
            debug : if set to true, will print the result when error happens
            format : if set to "xed", returns the full JSON for each resource (default : "xed-id" -  short summary)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchemas")
        path = f"/{self.container}/schemas/"
        start = kwargs.get("start", 0)
        params = {"start": start}
        if classFilter is not None:
            params["property"] = f"meta:intendedToExtend=={classFilter}"
        if excludeAdhoc:
            params["property"] = "meta:extends!=https://ns.adobe.com/xdm/data/adhoc"
        verbose = kwargs.get("debug", False)
        privateHeader = deepcopy(self.header)
        format = kwargs.get("format", "xed-id")
        privateHeader["Accept"] = f"application/vnd.adobe.{format}+json"
        res = self.connector.getData(
            self.endpoint + path, params=params, headers=privateHeader, verbose=verbose
        )
        if kwargs.get("debug", False):
            if "results" not in res.keys():
                print(res)
        data = res.get("results",[])
        if len(data) == 0:
            return res
        page = res.get("_page",{})
        nextPage = page.get('next',None)
        while nextPage is not None:
            params['start'] = nextPage
            res = self.connector.getData(
            self.endpoint + path, params=params, headers=privateHeader, verbose=verbose
            )
            data += res.get('results',[])
            page = res.get("_page",{'next':None})
            nextPage = page.get('next',None)
        self.data.schemas_id = {schem["title"]: schem["$id"] for schem in data}
        self.data.schemas_altId = {
            schem["title"]: schem["meta:altId"] for schem in data
        }
        if output == 'df':
            df = pd.DataFrame(data)
            return df
        return data

    def getSchema(
        self,
        schemaId: str = None,
        version: int = 1,
        full: bool = True,
        desc: bool = False,
        deprecated:bool=False,
        schema_type: str = "xdm",
        flat: bool = False,
        save: bool = False,
        **kwargs,
    ) -> dict:
        """
        Get the Schema. Requires a schema id.
        Response provided depends on the header set, you can change the Accept header with kwargs.
        Arguments:
            schemaId : REQUIRED : $id or meta:altId
            version : OPTIONAL : Version of the Schema asked (default 1)
            full : OPTIONAL : True (default) will return the full schema.False just the relationships.
            desc : OPTIONAL : If set to True, return the identity used as the descriptor.
            deprecated : OPTIONAL : Display the deprecated field from that schema
            flat : OPTIONAL : If set to True, return a flat schema for pathing.
            schema_type : OPTIONAL : set the type of output you want (xdm or xed) Default : xdm.
            save : OPTIONAL : save the result in json file (default False)
        Possible kwargs:
            Accept : Accept header to change the type of response.
            # /Schemas/lookup_schema
            more details held here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchema")
        privateHeader = deepcopy(self.header)
        if schemaId is None:
            raise Exception("Require a schemaId as a parameter")
        update_full,update_desc,update_flat,update_deprecated="","","",""
        if full:
            update_full = "-full"
        if desc:
            update_desc = "-desc"
        if flat:
            update_flat = "-flat"
        if deprecated:
            update_deprecated = "-deprecated"
        if schema_type != "xdm" and schema_type != "xed":
            raise ValueError("schema_type parameter can only be xdm or xed")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchema")
        privateHeader['Accept'] = f"application/vnd.adobe.{schema_type}{update_full}{update_desc}{update_flat}{update_deprecated}+json; version={version}"
        if kwargs.get("Accept", None) is not None:
            privateHeader["Accept"] = kwargs.get("Accept", self.header["Accept"])
        privateHeader["Accept-Encoding"] = "identity"
        if schemaId.startswith("https://"):
            from urllib import parse
            schemaId = parse.quote_plus(schemaId)
        path = f"/{self.container}/schemas/{schemaId}"
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        if "title" not in res.keys() and "notext" not in privateHeader["Accept"]:
            print("Issue with the request. See response.")
            return res
        if save:
            aepp.saveFile(
                module="schema", file=res, filename=res["title"], type_file="json"
            )
        if "title" in res.keys():
            self.data.schemas[res["title"]] = res
        else:
            print("no title in the response. Not saved in the data object.")
        return res

    def getSchemaPaths(
        self, schemaId: str, simplified: bool = True, save: bool = False
    ) -> list:
        """
        Returns a list of the path available in your schema. BETA.
        Arguments:
            schemaId : REQUIRED : The schema you want to retrieve the paths for
            simplified : OPTIONAL : Default True, only returns the list of paths for your schemas.
            save : OPTIONAL : Save your schema paths in a file. Always the NOT simplified version.
        """
        if schemaId is None:
            raise Exception("Require a schemaId as a parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchemaPaths")
        res = self.getSchema(schemaId, flat=True)
        keys = res["properties"].keys()
        paths = [
            key.replace("/", ".").replace("xdm:", "").replace("@", "_") for key in keys
        ]
        if save:
            aepp.saveFile(
                module="schema",
                file=res,
                filename=f"{res['title']}_paths",
                type_file="json",
            )
        if simplified:
            return paths
        return res

    def getSchemaSample(
        self, schemaId: str = None, save: bool = False, version: int = 1
    ) -> dict:
        """
        Generate a sample data from a schema id.
        Arguments:
            schema_id : REQUIRED : The schema ID for the sample data to be created.
            save : OPTIONAL : save the result in json file (default False)
            version : OPTIONAL : version of the schema to request
        """
        privateHeader = deepcopy(self.header)
        import random

        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchemaSample")
        rand_number = random.randint(1, 10e10)
        if schemaId is None:
            raise Exception("Require an ID for the schema")
        if schemaId.startswith("https://"):
            from urllib import parse

            schemaId = parse.quote_plus(schemaId)
        path = f"/rpc/sampledata/{schemaId}"
        accept_update = f"application/vnd.adobe.xed+json; version={version}"
        privateHeader["Accept"] = accept_update
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        if save:
            schema = self.getSchema(schemaId=schemaId, full=False)
            aepp.saveFile(
                module="schema",
                file=res,
                filename=f"{schema['title']}_{rand_number}",
                type_file="json",
            )
        return res

    def patchSchema(self, schemaId: str = None, changes: list = None, **kwargs) -> dict:
        """
        Enable to patch the Schema with operation.
        Arguments:
            schema_id : REQUIRED : $id or meta:altId
            change : REQUIRED : List of changes that need to take place.
            Example:
                [
                    {
                        "op": "add",
                        "path": "/allOf",
                        "value": {'$ref': 'https://ns.adobe.com/emeaconsulting/mixins/fb5b3cd49707d27367b93e07d1ac1f2f7b2ae8d051e65f8d',
                    'type': 'object',
                    'meta:xdmType': 'object'}
                    }
                ]
        information : http://jsonpatch.com/
        """
        if schemaId is None:
            raise Exception("Require an ID for the schema")
        if type(changes) == dict:
            changes = list(changes)
        if schemaId.startswith("https://"):
            from urllib import parse

            schemaId = parse.quote_plus(schemaId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchSchema")
        path = f"/{self.container}/schemas/{schemaId}"
        res = self.connector.patchData(
            self.endpoint + path, data=changes)
        return res

    def putSchema(self, schemaId: str = None, schemaDef: dict = None, **kwargs) -> dict:
        """
        A PUT request essentially re-writes the schema, therefore the request body must include all fields required to create (POST) a schema.
        This is especially useful when updating a lot of information in the schema at once.
        Arguments:
            schemaId : REQUIRED : $id or meta:altId
            schemaDef : REQUIRED : dictionary of the new schema.
            It requires a allOf list that contains all the attributes that are required for creating a schema.
            #/Schemas/replace_schema
            More information on : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        if schemaId is None:
            raise Exception("Require an ID for the schema")
        if schemaId.startswith("https://"):
            from urllib import parse
            schemaId = parse.quote_plus(schemaId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting putSchema")
        path = f"/{self.container}/schemas/{schemaId}"
        res = self.connector.putData(
            self.endpoint + path, data=schemaDef, headers=self.header
        )
        return res

    def deleteSchema(self, schemaId: str = None, **kwargs) -> str:
        """
        Delete the request
        Arguments:
            schema_id : REQUIRED : $id or meta:altId
            It requires a allOf list that contains all the attributes that are required for creating a schema.
            #/Schemas/replace_schema
            More information on : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        if schemaId is None:
            raise Exception("Require an ID for the schema")
        if schemaId.startswith("https://"):
            from urllib import parse
            schemaId = parse.quote_plus(schemaId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteSchema")
        path = f"/{self.container}/schemas/{schemaId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def createSchema(self, schema: dict = None) -> dict:
        """
        Create a Schema based on the data that are passed in the Argument.
        Arguments:
            schema : REQUIRED : The schema definition that needs to be created.
        """
        path = f"/{self.container}/schemas/"
        if type(schema) != dict:
            raise TypeError("Expecting a dictionary")
        if "allOf" not in schema.keys():
            raise Exception(
                "The schema must include an ‘allOf’ attribute (a list) referencing the $id of the base class the schema will implement."
            )
        if self.loggingEnabled:
            self.logger.debug(f"Starting createSchema")
        res = self.connector.postData(
            self.endpoint + path, data=schema
        )
        return res

    def createExperienceEventSchema(
        self,
        name: str = None,
        mixinIds: Union[list, dict] = None,
        fieldGroupIds : Union[list, dict] = None,
        description: str = "",
    ) -> dict:
        """
        Create an ExperienceEvent schema based on the list mixin ID provided.
        Arguments:
            name : REQUIRED : Name of your schema
            mixinIds : REQUIRED : dict of mixins $id and their type ["object" or "array"] to create the ExperienceEvent schema
                Example {'mixinId1':'object','mixinId2':'array'}
                if just a list is passed, it infers a 'object type'
            fieldGroupIds : REQUIRED : List of fieldGroup $id to create the Indiviudal Profile schema
                Example {'fgId1':'object','fgId2':'array'}
                if just a list is passed, it infers a 'object type'
            description : OPTIONAL : Schema description
        """
        if name is None:
            raise ValueError("Require a name")
        if mixinIds is None and fieldGroupIds is None:
            raise ValueError("Require a mixin ids or a field group id")
        if mixinIds is None and fieldGroupIds is not None:
            mixinIds = fieldGroupIds
        obj = {
            "title": name,
            "description": description,
            "allOf": [
                {
                    "$ref": "https://ns.adobe.com/xdm/context/experienceevent",
                    "type": "object",
                    "meta:xdmType": "object",
                }
            ],
        }
        if type(mixinIds) == list:
            for mixin in mixinIds:
                obj["allOf"].append(
                    {"$ref": mixin, "type": "object", "meta:xdmType": "object"}
                )
        if type(mixinIds) == dict:
            for mixin in mixinIds:
                if mixinIds[mixin] == "array":
                    subObj = {
                        "$ref": mixin,
                        "type": mixinIds[mixin],
                        "meta:xdmType": mixinIds[mixin],
                        "items": {"$ref": mixin},
                    }
                    obj["allOf"].append(subObj)
                else:
                    subObj = {
                        "$ref": mixin,
                        "type": mixinIds[mixin],
                        "meta:xdmType": mixinIds[mixin],
                    }
                    obj["allOf"].append(subObj)
        if self.loggingEnabled:
            self.logger.debug(f"Starting createExperienceEventSchema")
        res = self.createSchema(obj)
        return res

    def createProfileSchema(
        self,
        name: str = None,
        mixinIds: Union[list, dict] = None,
        fieldGroupIds : Union[list, dict] = None,
        description: str = "",
        **kwargs
    ) -> dict:
        """
        Create an IndividualProfile schema based on the list mixin ID provided.
        Arguments:
            name : REQUIRED : Name of your schema
            mixinIds : REQUIRED : List of mixins $id to create the Indiviudal Profile schema
                Example {'mixinId1':'object','mixinId2':'array'}
                if just a list is passed, it infers a 'object type'
            fieldGroupIds : REQUIRED : List of fieldGroup $id to create the Indiviudal Profile schema
                Example {'fgId1':'object','fgId2':'array'}
                if just a list is passed, it infers a 'object type'
            description : OPTIONAL : Schema description
        """
        if name is None:
            raise ValueError("Require a name")
        if mixinIds is None and fieldGroupIds is None:
            raise ValueError("Require a mixin ids or a field group id")
        if mixinIds is None and fieldGroupIds is not None:
            mixinIds = fieldGroupIds
        obj = {
            "title": name,
            "description": description,
            "allOf": [
                {
                    "$ref": "https://ns.adobe.com/xdm/context/profile",
                    "type": "object",
                    "meta:xdmType": "object",
                }
            ],
        }
        if type(mixinIds) == list:
            for mixin in mixinIds:
                obj["allOf"].append(
                    {"$ref": mixin, "type": "object", "meta:xdmType": "object"}
                )
        if type(mixinIds) == dict:
            for mixin in mixinIds:
                if mixinIds[mixin] == "array":
                    subObj = {
                        "$ref": mixin,
                        "type": mixinIds[mixin],
                        "meta:xdmType": mixinIds[mixin],
                        "items": {"$ref": mixin},
                    }
                    obj["allOf"].append(subObj)
                else:
                    subObj = {
                        "$ref": mixin,
                        "type": mixinIds[mixin],
                        "meta:xdmType": mixinIds[mixin],
                    }
                    obj["allOf"].append(subObj)
        if self.loggingEnabled:
            self.logger.debug(f"Starting createProfileSchema")
        res = self.createSchema(obj)
        return res
    
    def addFieldGroupToSchema(self,schemaId:str=None,fieldGroupIds:Union[list,dict]=None)->dict:
        """
        Take the list of field group ID to extend the schema.
        Return the definition of the new schema with added field groups.
        Arguments
            schemaId : REQUIRED : The ID of the schema (alt:metaId or $id)
            fieldGroupIds : REQUIRED : The IDs of the fields group to add. It can be a list or dictionary.
                Example {'fgId1':'object','fgId2':'array'}
                if just a list is passed, it infers a 'object type'
        """
        if schemaId is None:
            raise ValueError("Require a schema ID")
        if fieldGroupIds is None:
            raise ValueError("Require a list of field group to add")
        schemaDef = self.getSchema(schemaId,full=False)
        allOf = schemaDef.get('allOf',[])
        if type(allOf) != list:
            raise TypeError("Expecting a list for 'allOf' key")
        if type(fieldGroupIds) == list:
            for mixin in fieldGroupIds:
                allOf.append(
                    {"$ref": mixin, "type": "object", "meta:xdmType": "object"}
                )
        if type(fieldGroupIds) == dict:
            for mixin in fieldGroupIds:
                if fieldGroupIds[mixin] == "array":
                    subObj = {
                        "$ref": mixin,
                        "type": fieldGroupIds[mixin],
                        "meta:xdmType": fieldGroupIds[mixin],
                        "items": {"$ref": mixin},
                    }
                    allOf.append(subObj)
                else:
                    subObj = {
                        "$ref": mixin,
                        "type": fieldGroupIds[mixin],
                        "meta:xdmType": fieldGroupIds[mixin],
                    }
                    allOf.append(subObj)
        res = self.putSchema(schemaDef)
        return res        

    def getClasses(self, 
                   prop:str=None,
                   orderBy:str=None,
                   limit:int=300, 
                   output:str='raw',
                   excludeAdhoc: bool = False,
                   **kwargs):
        """
        Return the classes of the AEP Instances.
        Arguments:
            prop : OPTIONAL : A comma-separated list of top-level object properties to be returned in the response. 
                            For example, property=meta:intendedToExtend==https://ns.adobe.com/xdm/context/profile
            oderBy : OPTIONAL : Sort the listed resources by specified fields. For example orderby=title
            limit : OPTIONAL : Number of resources to return per request, default 300 - the max.
            excludeAdhoc : OPTIONAL : Exlcude the Adhoc classes that have been created.
            output : OPTIONAL : type of output, default "raw", can be "df" for dataframe.
        kwargs:
            debug : if set to True, will print result for errors
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getClasses")
        privateHeader = deepcopy(self.header)
        privateHeader.update({"Accept": "application/vnd.adobe.xdm-id+json"})
        params = {"limit":limit}
        if excludeAdhoc:
            params["property"] = "meta:extends!=https://ns.adobe.com/xdm/data/adhoc"
        if prop is not None:
            if 'property' not in params.keys():
                params["property"] = prop
            else:
                params["property"] += prop
        if orderBy is not None:
            params['orderby'] = orderBy
        path = f"/{self.container}/classes/"
        verbose = kwargs.get("verbose", False)
        res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params, verbose=verbose
        )
        if kwargs.get("debug", False):
            if "results" not in res.keys():
                print(res)
        data = res["results"]
        page = res["_page"]
        while page["next"] is not None:
            params["start"]= page["next"]
            res = self.connector.getData(
                self.endpoint + path, headers=privateHeader, params=params, verbose=verbose
            )
            data += res["results"]
            page = res["_page"]
        if output=="df":
            df = pd.DataFrame(data)
            return df
        return data
        
    def getClassesGlobal(self, 
                   prop:str=None,
                   orderBy:str=None,
                   limit:int=300, 
                   output:str='raw',
                   **kwargs):
        """
        Return the classes of the AEP Instances.
        Arguments:
            prop : OPTIONAL : A comma-separated list of top-level object properties to be returned in the response. 
                            For example, property=meta:intendedToExtend==https://ns.adobe.com/xdm/context/profile
            oderBy : OPTIONAL : Sort the listed resources by specified fields. For example orderby=title
            limit : OPTIONAL : Number of resources to return per request, default 300 - the max.
            output : OPTIONAL : type of output, default "raw", can be "df" for dataframe.
        kwargs:
            debug : if set to True, will print result for errors
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getClasses")
        privateHeader = deepcopy(self.header)
        privateHeader.update({"Accept": "application/vnd.adobe.xdm-id+json"})
        params = {"limit":limit}
        if prop is not None:
            if 'property' not in params.keys():
                params["property"] = prop
            else:
                params["property"] += prop
        if orderBy is not None:
            params['orderby'] = orderBy
        path = f"/global/classes/"
        verbose = kwargs.get("verbose", False)
        res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params, verbose=verbose
        )
        if kwargs.get("debug", False):
            if "results" not in res.keys():
                print(res)
        data = res["results"]
        page = res["_page"]
        while page["next"] is not None:
            params["start"]= page["next"]
            res = self.connector.getData(
                self.endpoint + path, headers=privateHeader, params=params, verbose=verbose
            )
            data += res["results"]
            page = res["_page"]
        if output=="df":
            df = pd.DataFrame(data)
            return df
        return data

    def getClass(
        self,
        classId: str = None,
        full: bool = True,
        desc: bool = False,
        deprecated: bool = False,
        xtype : str = "xdm",
        version: int = 1,
        save: bool = False,
    ):
        """
        Return a specific class.
        Arguments:
            classId : REQUIRED : the meta:altId or $id from the class
            full : OPTIONAL : True (default) will return the full schema.False just the relationships.
            desc : OPTIONAL : If set to True, return the descriptors.
            deprecated : OPTIONAL : Display the deprecated field from that schema (False by default)
            xtype : OPTIONAL : either "xdm" (default) or "xed". 
            version : OPTIONAL : the version of the class to retrieve.
            save : OPTIONAL : To save the result of the request in a JSON file.
        """
        privateHeader = deepcopy(self.header)
        if classId is None:
            raise Exception("Require a class_id")
        if classId.startswith("https://"):
            from urllib import parse
            classId = parse.quote_plus(classId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting getClass")
        privateHeader["Accept-Encoding"] = "identity"
        updateFull,updateDesc, updateDeprecated = "","",""
        if full:
            updateFull = "-full"
        if desc:
            updateDesc = "-desc"
        if deprecated:
            updateDeprecated = "-deprecated"
        privateHeader.update(
                {"Accept": f"application/vnd.adobe.{xtype}{updateFull}{updateDesc}{updateDeprecated}+json; version=" + str(version)}
            )
        path = f"/{self.container}/classes/{classId}"
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        if save:
            aepp.saveFile(
                module="schema", file=res, filename=res["title"], type_file="json"
            )
        return res

    def createClass(self, class_obj: dict = None,title:str=None, class_template:str=None, **kwargs):
        """
        Create a class based on the object pass. It should include the "allOff" element.
        Arguments:
            class_obj : REQUIRED : You can pass a complete object to create a class, include a title and a "allOf" element.
            title : REQUIRED : Title of the class if you want to pass individual elements
            class_template : REQUIRED : type of behavior for the class, either "https://ns.adobe.com/xdm/data/record" or "https://ns.adobe.com/xdm/data/time-series"
        Possible kwargs: 
            description : To add a description to a class.
        """
        path = f"/{self.container}/classes/"
        
        if class_obj is not None:
            if type(class_obj) != dict:
                raise TypeError("Expecting a dictionary")
            if "allOf" not in class_obj.keys():
                raise Exception(
                    "The class object must include an ‘allOf’ attribute (a list) referencing the $id of the base class the schema will implement."
                )
        elif class_obj is None and title is not None and class_template is not None:
            class_obj = {
                "type": "object",
                "title": title,
                "description": "Generated by aepp",
                "allOf": [
                    {
                    "$ref": class_template
                    }
                ]
                }
        if kwargs.get("descriptor","") != "":
            class_obj['descriptor'] = kwargs.get("descriptor")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createClass")
        res = self.connector.postData(
            self.endpoint + path, data=class_obj
        )
        return res
    
    def putClass(self,classId:str=None,class_obj:dict=None)->dict:
        """
        Replace the current definition with the new definition.
        Arguments:
            classId : REQUIRED : The class to be updated ($id or meta:altId)
            class_obj : REQUIRED : The dictionary defining the new class definition
        """
        if classId is None:
            raise Exception("Require a classId")
        if classId.startswith("https://"):
            from urllib import parse
            classId = parse.quote_plus(classId)
        if class_obj is None:
            raise Exception("Require a new definition for the class")
        if self.loggingEnabled:
            self.logger.debug(f"Starting putClass")
        path = f"/{self.container}/classes/{classId}"
        res = self.connector.putData(self.endpoint + path,data=class_obj)
        return res

    def patchClass(self,classId:str=None,operation:list=None)->dict:
        """
        Patch a class with the operation specified such as:
        update = [{
            "op": "replace",
            "path": "title",
            "value": "newTitle"
        }]
        Possible operation value : "replace", "remove", "add"
        Arguments:
            classId : REQUIRED : The class to be updated  ($id or meta:altId)
            operation : REQUIRED : List of operation to realize on the class
        """
        if classId is None:
            raise Exception("Require a classId")
        if classId.startswith("https://"):
            from urllib import parse
            classId = parse.quote_plus(classId)
        if operation is None or type(operation) != list:
            raise Exception("Require a list of operation for the class")
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchClass")
        path = f"/{self.container}/classes/{classId}"
        res = self.connector.patchData(self.endpoint + path,data=operation)
        return res

    def deleteClass(self,classId: str = None)->str:
        """
        Delete a class based on the its ID.
        Arguments:
            classId : REQUIRED : The class to be deleted  ($id or meta:altId)
        """
        if classId is None:
            raise Exception("Require a classId")
        if classId.startswith("https://"):
            from urllib import parse
            classId = parse.quote_plus(classId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchClass")
        path = f"/{self.container}/classes/{classId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def getFieldGroups(self, format: str = "xdm", **kwargs) -> list:
        """
        returns the fieldGroups of the account.
        Arguments:
            format : OPTIONAL : either "xdm" or "xed" format
        kwargs:
            debug : if set to True, will print result for errors
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFieldGroups")
        path = f"/{self.container}/fieldgroups/"
        start = kwargs.get("start", 0)
        params = {"start": start}
        verbose = kwargs.get("debug", False)
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = f"application/vnd.adobe.{format}+json"
        res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params, verbose=verbose
        )
        if kwargs.get("verbose", False):
            if "results" not in res.keys():
                print(res)
        data = res["results"]
        page = res.get("_page",{})
        nextPage = page.get('next',None)
        while nextPage is not None:
            params['start'] = nextPage
            res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params, verbose=verbose
            )
            data += res.get("results")
            page = res.get("_page",{})
            nextPage = page.get('next',None)
        self.data.fieldGroups_id = {mix["title"]: mix["$id"] for mix in data}
        self.data.fieldGroups_altId = {mix["title"]: mix["meta:altId"] for mix in data}
        return data
    
    def getFieldGroupsGlobal(self,format: str = "xdm",output:str='raw', **kwargs)->list:
        """
        returns the global fieldGroups of the account.
        Arguments:
            format : OPTIONAL : either "xdm" or "xed" format
            output : OPTIONAL : either "raw" (default) or "df" for dataframe 
        kwargs:
            debug : if set to True, will print result for errors
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFieldGroups")
        path = f"/global/fieldgroups/"
        start = kwargs.get("start", 0)
        params = {"start": start}
        verbose = kwargs.get("debug", False)
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = f"application/vnd.adobe.{format}+json"
        res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params, verbose=verbose
        )
        if kwargs.get("verbose", False):
            if "results" not in res.keys():
                print(res)
        data = res["results"]
        page = res.get("_page",{})
        nextPage = page.get('next',None)
        while nextPage is not None:
            params['start'] = nextPage
            res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params, verbose=verbose
            )
            data += res.get("results")
            page = res.get("_page",{})
            nextPage = page.get('next',None)
        self.data.fieldGroups_id = {mix["title"]: mix["$id"] for mix in data}
        self.data.fieldGroups_altId = {mix["title"]: mix["meta:altId"] for mix in data}
        if output == 'df':
            df = pd.DataFrame(data)
            return df
        return data

    # def getMixin(
    #     self,
    #     mixinId: str = None,
    #     version: int = 1,
    #     full: bool = True,
    #     save: bool = False,
    # ):
    #     """
    #     Returns a specific mixin / field group.
    #     Arguments:
    #         mixinId : REQUIRED : meta:altId or $id
    #         version : OPTIONAL : version of the mixin
    #         full : OPTIONAL : True (default) will return the full schema.False just the relationships.
    #     """
    #     if mixinId.startswith("https://"):
    #         from urllib import parse

    #         mixinId = parse.quote_plus(mixinId)
    #     if self.loggingEnabled:
    #         self.logger.debug(f"Starting getMixin")
    #     privateHeader = deepcopy(self.header)
    #     privateHeader["Accept-Encoding"] = "identity"
    #     if full:
    #         accept_full = "-full"
    #     else:
    #         accept_full = ""
    #     update_accept = (
    #         f"application/vnd.adobe.xed{accept_full}+json; version={version}"
    #     )
    #     privateHeader.update({"Accept": update_accept})
    #     path = f"/{self.container}/mixins/{mixinId}"
    #     res = self.connector.getData(self.endpoint + path, headers=privateHeader)
    #     if save:
    #         aepp.saveFile(
    #             module="schema", file=res, filename=res["title"], type_file="json"
    #         )
    #     if "title" in res.keys():
    #         self.data.mixins[res["title"]] = res
    #     return res

    def getFieldGroup(
        self,
        fieldGroupId: str = None,
        version: int = 1,
        full: bool = True,
        desc: bool = False,
        type: str = 'xed',
        flat: bool = False,
        deprecated: bool = False,
        save: bool = False,
    ):
        """
        Returns a specific mixin / field group.
        Arguments:
            fieldGroupId : REQUIRED : meta:altId or $id
            version : OPTIONAL : version of the mixin
            full : OPTIONAL : True (default) will return the full schema.False just the relationships
            desc : OPTIONAL : Add descriptor of the field group
            type : OPTIONAL : Either "xed" (default) or "xdm"
            flat : OPTIONAL : if the fieldGroup is flat (false by default)
            deprecated : OPTIONAL : Display the deprecated fields from that schema
            save : Save the fieldGroup to a JSON file
        """
        if fieldGroupId.startswith("https://"):
            from urllib import parse
            fieldGroupId = parse.quote_plus(fieldGroupId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFieldGroup")
        privateHeader = deepcopy(self.header)
        privateHeader["Accept-Encoding"] = "identity"
        accept_full, accept_desc,accept_flat,accept_deprec= "","","",""
        if full:
            accept_full = "-full"
        if desc:
            accept_desc = "-desc"
        if flat:
            accept_flat = "-flat"
        if deprecated:
            accept_deprec = "-deprecated"
        update_accept = (
            f"application/vnd.adobe.{type}{accept_full}{accept_desc}{accept_flat}{accept_deprec}+json; version={version}"
        )
        privateHeader.update({"Accept": update_accept})
        path = f"/{self.container}/fieldgroups/{fieldGroupId}"
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        if save:
            aepp.saveFile(
                module="schema", file=res, filename=res["title"], type_file="json"
            )
        if "title" in res.keys():
            self.data.fieldGroups[res["title"]] = res
        return res

    def copyMixin(
        self, mixin: dict = None, tenantId: str = None, title: str = None
    ) -> dict:
        """
        Copy the dictionary returned by getMixin to the only required elements for copying it over.
        Arguments:
            mixin : REQUIRED : the object retrieved from the getMixin.
            tenantId : OPTIONAL : if you want to change the tenantId (if None doesn't rename)
            name : OPTIONAL : rename your mixin (if None, doesn't rename it)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting copyMixin")
        if mixin is None:
            raise ValueError("Require a mixin  object")
        mixin_obj = deepcopy(mixin)
        oldTenant = mixin_obj["meta:tenantNamespace"]
        if "definitions" in mixin_obj.keys():
            obj = {
                "type": mixin_obj["type"],
                "title": title or mixin_obj["title"],
                "description": mixin_obj["description"],
                "meta:intendedToExtend": mixin_obj["meta:intendedToExtend"],
                "definitions": mixin_obj.get("definitions"),
                "allOf": mixin_obj.get(
                    "allOf",
                    [
                        {
                            "$ref": "#/definitions/property",
                            "type": "object",
                            "meta:xdmType": "object",
                        }
                    ],
                ),
            }
        elif "properties" in mixin_obj.keys():
            obj = {
                "type": mixin_obj["type"],
                "title": title or mixin_obj["title"],
                "description": mixin_obj["description"],
                "meta:intendedToExtend": mixin_obj["meta:intendedToExtend"],
                "definitions": {
                    "property": {
                        "properties": mixin_obj["properties"],
                        "type": "object",
                        "['meta:xdmType']": "object",
                    }
                },
                "allOf": mixin_obj.get(
                    "allOf",
                    [
                        {
                            "$ref": "#/definitions/property",
                            "type": "object",
                            "meta:xdmType": "object",
                        }
                    ],
                ),
            }
        if tenantId is not None:
            if tenantId.startswith("_") == False:
                tenantId = f"_{tenantId}"
            obj["definitions"]["property"]["properties"][tenantId] = obj["definitions"][
                "property"
            ]["properties"][oldTenant]
            del obj["definitions"]["property"]["properties"][oldTenant]
        return obj

    def copyFieldGroup(
        self, fieldGroup: dict = None, tenantId: str = None, title: str = None
    ) -> dict:
        """
        Copy the dictionary returned by getMixin to the only required elements for copying it over.
        Arguments:
            fieldGroup : REQUIRED : the object retrieved from the getFieldGroup.
            tenantId : OPTIONAL : if you want to change the tenantId (if None doesn't rename)
            name : OPTIONAL : rename your mixin (if None, doesn't rename it)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting copyFieldGroup")
        if fieldGroup is None:
            raise ValueError("Require a mixin  object")
        mixin_obj = deepcopy(fieldGroup)
        oldTenant = mixin_obj["meta:tenantNamespace"]
        if "definitions" in mixin_obj.keys():
            obj = {
                "type": mixin_obj["type"],
                "title": title or mixin_obj["title"],
                "description": mixin_obj["description"],
                "meta:intendedToExtend": mixin_obj["meta:intendedToExtend"],
                "definitions": mixin_obj.get("definitions"),
                "allOf": mixin_obj.get(
                    "allOf",
                    [
                        {
                            "$ref": "#/definitions/property",
                            "type": "object",
                            "meta:xdmType": "object",
                        }
                    ],
                ),
            }
        elif "properties" in mixin_obj.keys():
            obj = {
                "type": mixin_obj["type"],
                "title": title or mixin_obj["title"],
                "description": mixin_obj["description"],
                "meta:intendedToExtend": mixin_obj["meta:intendedToExtend"],
                "definitions": {
                    "property": {
                        "properties": mixin_obj["properties"],
                        "type": "object",
                        "['meta:xdmType']": "object",
                    }
                },
                "allOf": mixin_obj.get(
                    "allOf",
                    [
                        {
                            "$ref": "#/definitions/property",
                            "type": "object",
                            "meta:xdmType": "object",
                        }
                    ],
                ),
            }
        if tenantId is not None:
            if tenantId.startswith("_") == False:
                tenantId = f"_{tenantId}"
            if 'property' in obj["definitions"].keys():
                obj["definitions"]["property"]["properties"][tenantId] = obj["definitions"]["property"]["properties"][oldTenant]
                del obj["definitions"]["property"]["properties"][oldTenant]
            elif 'customFields' in obj["definitions"].keys():
                obj["definitions"]["customFields"]["properties"][tenantId] = obj["definitions"]["customFields"]["properties"][oldTenant]
                del obj["definitions"]["customFields"]["properties"][oldTenant]
        return obj

    def createMixin(self, mixin_obj: dict = None) -> dict:
        """
        Create a mixin based on the dictionary passed.
        Arguments :
            mixin_obj : REQUIRED : the object required for creating the mixin.
            Should contain title, type, definitions
        """
        if mixin_obj is None:
            raise Exception("Require a mixin object")
        if (
            "title" not in mixin_obj
            or "type" not in mixin_obj
            or "definitions" not in mixin_obj
        ):
            raise AttributeError(
                "Require to have at least title, type, definitions set in the object."
            )
        if self.loggingEnabled:
            self.logger.debug(f"Starting createMixin")
        path = f"/{self.container}/mixins/"
        res = self.connector.postData(
            self.endpoint + path, data=mixin_obj)
        return res

    def createFieldGroup(self, fieldGroup_obj: dict = None) -> dict:
        """
        Create a mixin based on the dictionary passed.
        Arguments :
            fieldGroup_obj : REQUIRED : the object required for creating the field group.
            Should contain title, type, definitions
        """
        if fieldGroup_obj is None:
            raise Exception("Require a mixin object")
        if (
            "title" not in fieldGroup_obj
            or "type" not in fieldGroup_obj
            or "definitions" not in fieldGroup_obj
        ):
            raise AttributeError(
                "Require to have at least title, type, definitions set in the object."
            )
        if self.loggingEnabled:
            self.logger.debug(f"Starting createFieldGroup")
        path = f"/{self.container}/fieldgroups/"
        res = self.connector.postData(
            self.endpoint + path, data=fieldGroup_obj)
        return res

    def deleteMixin(self, mixinId: str = None):
        """
        Arguments:
            mixinId : meta:altId or $id
        """
        if mixinId is None:
            raise Exception("Require an ID")
        if mixinId.startswith("https://"):
            from urllib import parse

            mixinId = parse.quote_plus(mixinId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteMixin")
        path = f"/{self.container}/mixins/{mixinId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def deleteFieldGroup(self, fieldGroupId: str = None):
        """
        Arguments:
            fieldGroupId : meta:altId or $id
        """
        if fieldGroupId is None:
            raise Exception("Require an ID")
        if fieldGroupId.startswith("https://"):
            from urllib import parse

            fieldGroupId = parse.quote_plus(fieldGroupId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteFieldGroup")
        path = f"/{self.container}/fieldgroups/{fieldGroupId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def patchMixin(self, mixinId: str = None, changes: list = None):
        """
        Update the mixin with the operation described in the changes.
        Arguments:
            mixinId : REQUIRED : meta:altId or $id
            changes : REQUIRED : dictionary on what to update on that mixin.
            Example:
                [
                    {
                        "op": "add",
                        "path": "/allOf",
                        "value": {'$ref': 'https://ns.adobe.com/emeaconsulting/mixins/fb5b3cd49707d27367b93e07d1ac1f2f7b2ae8d051e65f8d',
                    'type': 'object',
                    'meta:xdmType': 'object'}
                    }
                ]
        information : http://jsonpatch.com/
        """
        if mixinId is None or changes is None:
            raise Exception("Require an ID and changes")
        if mixinId.startswith("https://"):
            from urllib import parse

            mixinId = parse.quote_plus(mixinId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchMixin")
        path = f"/{self.container}/mixins/{mixinId}"
        if type(changes) == dict:
            changes = list(changes)
        res = self.connector.patchData(
            self.endpoint + path, data=changes)
        return res

    def patchFieldGroup(self, fieldGroupId: str = None, changes: list = None):
        """
        Update the mixin with the operation described in the changes.
        Arguments:
            fieldGroupId : REQUIRED : meta:altId or $id
            changes : REQUIRED : dictionary on what to update on that mixin.
            Example:
                [
                    {
                        "op": "add",
                        "path": "/allOf",
                        "value": {'$ref': 'https://ns.adobe.com/emeaconsulting/mixins/fb5b3cd49707d27367b93e07d1ac1f2f7b2ae8d051e65f8d',
                    'type': 'object',
                    'meta:xdmType': 'object'}
                    }
                ]
        information : http://jsonpatch.com/
        """
        if fieldGroupId is None or changes is None:
            raise Exception("Require an ID and changes")
        if fieldGroupId.startswith("https://"):
            from urllib import parse

            fieldGroupId = parse.quote_plus(fieldGroupId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchFieldGroup")
        path = f"/{self.container}/fieldgroups/{fieldGroupId}"
        if type(changes) == dict:
            changes = list(changes)
        res = self.connector.patchData(
            self.endpoint + path, data=changes)
        return res

    def putMixin(self, mixinId: str = None, mixinObj: dict = None, **kwargs) -> dict:
        """
        A PUT request essentially re-writes the schema, therefore the request body must include all fields required to create (POST) a schema.
        This is especially useful when updating a lot of information in the schema at once.
        Arguments:
            mixinId : REQUIRED : $id or meta:altId
            mixinObj : REQUIRED : dictionary of the new schema.
            It requires a allOf list that contains all the attributes that are required for creating a schema.
            #/Schemas/replace_schema
            More information on : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        if mixinId is None:
            raise Exception("Require an ID for the schema")
        if mixinId.startswith("https://"):
            from urllib import parse

            mixinId = parse.quote_plus(mixinId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting putMixin")
        path = f"/{self.container}/mixins/{mixinId}"
        res = self.connector.putData(
            self.endpoint + path, data=mixinObj)
        return res

    def putFieldGroup(
        self, fieldGroupId: str = None, fieldGroupObj: dict = None, **kwargs
    ) -> dict:
        """
        A PUT request essentially re-writes the schema, therefore the request body must include all fields required to create (POST) a schema.
        This is especially useful when updating a lot of information in the schema at once.
        Arguments:
            fieldGroupId : REQUIRED : $id or meta:altId
            fieldGroupObj : REQUIRED : dictionary of the new Field Group.
            It requires a allOf list that contains all the attributes that are required for creating a schema.
            #/Schemas/replace_schema
            More information on : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        if fieldGroupId is None:
            raise Exception("Require an ID for the schema")
        if fieldGroupId.startswith("https://"):
            from urllib import parse

            fieldGroupId = parse.quote_plus(fieldGroupId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting putMixin")
        path = f"/{self.container}/fieldgroups/{fieldGroupId}"
        res = self.connector.putData(
            self.endpoint + path, data=fieldGroupObj)
        return res

    def getUnions(self, **kwargs):
        """
        Get all of the unions that has been set for the tenant.
        Returns a dictionary.

        Possibility to add option using kwargs
        """
        path = f"/{self.container}/unions"
        params = {}
        if len(kwargs) > 0:
            for key in kwargs.key():
                if key == "limit":
                    if int(kwargs["limit"]) > 500:
                        kwargs["limit"] = 500
                params[key] = kwargs.get(key, "")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getUnions")
        res = self.connector.getData(
            self.endpoint + path, params=params)
        data = res["results"]  # issue when requesting directly results.
        return data

    def getUnion(self, union_id: str = None, version: int = 1):
        """
        Get a specific union type. Returns a dictionnary
        Arguments :
            union_id : REQUIRED :  meta:altId or $id
            version : OPTIONAL : version of the union schema required.
        """
        if union_id is None:
            raise Exception("Require an ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getUnion")
        if union_id.startswith("https://"):
            from urllib import parse

            union_id = parse.quote_plus(union_id)
        path = f"/{self.container}/unions/{union_id}"
        privateHeader = deepcopy(self.header)
        privateHeader.update(
            {"Accept": "application/vnd.adobe.xdm-full+json; version=" + str(version)}
        )
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        return res

    def getXDMprofileSchema(self):
        """
        Returns a list of all schemas that are part of the XDM Individual Profile.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getXDMprofileSchema")
        path = "/tenant/schemas?property=meta:immutableTags==union&property=meta:class==https://ns.adobe.com/xdm/context/profile"
        res = self.connector.getData(self.endpoint + path)
        return res

    def getDataTypes(self, **kwargs):
        """
        Get the data types from a container.
        Possible kwargs:
            properties : str :limit the amount of properties return by comma separated list.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDataTypes")
        path = f"/{self.container}/datatypes/"
        params = {}
        if kwargs.get("properties", None) is not None:
            params = {"properties": kwargs.get("properties", "title,$id")}
        privateHeader = deepcopy(self.header)
        privateHeader.update({"Accept": "application/vnd.adobe.xdm-id+json"})
        res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params
        )
        data = res["results"]
        page = res.get("_page",{})
        nextPage = page.get('next',None)
        while nextPage is not None:
            res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params
            )
            data += res.get("results",[])
            page = res.get("_page",{})
            nextPage = page.get('next',None)
        return data

    def getDataType(
        self, dataTypeId: str = None, version: str = "1", save: bool = False
    ):
        """
        Retrieve a specific data type id
        Argument:
            dataTypeId : REQUIRED : The resource meta:altId or URL encoded $id URI.
        """
        if dataTypeId is None:
            raise Exception("Require a dataTypeId")
        if dataTypeId.startswith("https://"):
            from urllib import parse

            dataTypeId = parse.quote_plus(dataTypeId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDataType")
        privateHeader = deepcopy(self.header)
        privateHeader.update(
            {"Accept": "application/vnd.adobe.xdm-full+json; version=" + version}
        )
        path = f"/{self.container}/datatypes/{dataTypeId}"
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        if save:
            aepp.saveFile(
                module="schema", file=res, filename=res["title"], type_file="json"
            )
        return res

    def createDataType(self, dataTypeObj: dict = None)->dict:
        """
        Create Data Type based on the object passed.
        """
        if dataTypeObj is None:
            raise Exception("Require a dictionary to create the Data Type")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createDataTypes")
        path = f"/{self.container}/datatypes/"
        res = self.connector.postData(
            self.endpoint + path, data=dataTypeObj)
        return res
    
    def patchDataType(self,dataTypeId:str=None,operations:list=None)->dict:
        """
        Patch an existing data type with the operation provided.
        Arguments:
            dataTypeId : REQUIRED : The Data Type ID to be used
            operations : REQUIRED : The list of operation to be applied on that Data Type.
                    Example : '[
                                {
                                "op": "replace",
                                "path": "/loyaltyLevel/meta:enum",
                                "value": {
                                    "ultra-platinum": "Ultra Platinum",
                                    "platinum": "Platinum",
                                    "gold": "Gold",
                                    "silver": "Silver",
                                    "bronze": "Bronze"
                                }
                                }
                            ]'
        """
        if dataTypeId is None:
            raise Exception("Require a a data type ID")
        if operations is None:
            raise Exception("Require a list of operation to patch")
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchDataType")
        path = f"/{self.container}/datatypes/{dataTypeId}"
        res = self.connector.patchData(
            self.endpoint + path, data=operations)
        return res

    
    def putDataType(self,dataTypeId:str=None,dataTypeObj:dict=None)->dict:
        """
        Replace an existing data type definition with the new definition provided.
        Arguments:
            dataTypeId : REQUIRED : The Data Type ID to be replaced
            dataTypeObj : REQUIRED : The new Data Type definition.
        """
        if dataTypeId is None:
            raise Exception("Require a a data type ID")
        if dataTypeObj is None:
            raise Exception("Require a dictionary to replace the Data Type definition")
        if self.loggingEnabled:
            self.logger.debug(f"Starting putDataType")
        path = f"/{self.container}/datatypes/{dataTypeId}"
        res = self.connector.putData(
            self.endpoint + path, data=dataTypeObj)
        return res

    def getDescriptors(
        self,
        type_desc: str = None,
        id_desc: bool = False,
        link_desc: bool = False,
        save: bool = False,
        **kwargs,
    ) -> list:
        """
        Return a list of all descriptors contains in that tenant id.
        By default return a v2 for pagination.
        Arguments:
            type_desc : OPTIONAL : if you want to filter for a specific type of descriptor. None default.
                (possible value : "xdm:descriptorIdentity")
            id_desc : OPTIONAL : if you want to return only the id.
            link_desc : OPTIONAL : if you want to return only the paths.
            save : OPTIONAL : Boolean that would save your descriptors in the schema folder. (default False)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDescriptors")
        path = f"/{self.container}/descriptors/"
        params = {"start": kwargs.get("start", 0)}
        if type_desc is not None:
            params["property"] = f"@type=={type_desc}"
        if id_desc:
            update_id = "-id"
        else:
            update_id = ""
        if link_desc:
            update_link = "-link"
        else:
            update_link = ""
        privateHeader = deepcopy(self.header)
        privateHeader[
            "Accept"
        ] = f"application/vnd.adobe.xdm-v2{update_link}{update_id}+json"
        res = self.connector.getData(
            self.endpoint + path, params=params, headers=privateHeader
        )
        data = res["results"]
        page = res["_page"]
        while page["next"] is not None:
            data += self.getDescriptors(start=page["next"])
        if save:
            aepp.saveFile(
                module="schema", file=data, filename="descriptors", type_file="json"
            )
        return data

    def getDescriptor(self, descriptorId: str = None, save: bool = False) -> dict:
        """
        Return a specific descriptor
        Arguments:
            descriptorId : REQUIRED : descriptor ID to return (@id).
            save : OPTIONAL : Boolean that would save your descriptors in the schema folder. (default False)
        """
        if descriptorId is None:
            raise Exception("Require a descriptor id")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDescriptor")
        path = f"/{self.container}/descriptors/{descriptorId}"
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = f"application/vnd.adobe.xdm+json"
        res = self.connector.getData(self.endpoint + path, headers=privateHeader)
        if save:
            aepp.saveFile(
                module="schema",
                file=res,
                filename=f'{res["@id"]}_descriptors',
                type_file="json",
            )
        return res

    def createDescriptor(
        self,
        descriptorObj:dict = None,
        desc_type: str = "xdm:descriptorIdentity",
        sourceSchema: str = None,
        sourceProperty: str = None,
        namespace: str = None,
        primary: bool = None,
        **kwargs,
    ) -> dict:
        """
        Create a descriptor attached to a specific schema.
        Arguments:
            descriptorObj : REQUIRED : If you wish to pass the whole object.
            desc_type : REQUIRED : the type of descriptor to create.(default Identity)
            sourceSchema : REQUIRED : the schema attached to your identity ()
            sourceProperty : REQUIRED : the path to the field
            namespace : REQUIRED : the namespace used for the identity
            primary : OPTIONAL : Boolean (True or False) to define if it is a primary identity or not (default None).
        possible kwargs:
            version : version of the creation (default 1)
            xdm:property : type of property
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createDescriptor")
        path = f"/tenant/descriptors"
        if descriptorObj:
            res = self.connector.postData(
            self.endpoint + path, data=descriptorObj)
        else:
            if sourceSchema is None or sourceProperty is None:
                raise Exception("Missing required arguments.")
            obj = {
                "@type": desc_type,
                "xdm:sourceSchema": sourceSchema,
                "xdm:sourceVersion": kwargs.get("version", 1),
                "xdm:sourceProperty": sourceProperty,
            }
            if namespace is not None:
                obj["xdm:namespace"] = namespace
            if primary is not None:
                obj["xdm:isPrimary"] = primary
            for key in kwargs:
                if 'xdm:' in key:
                    obj[key] = kwargs.get(key)
            res = self.connector.postData(
                self.endpoint + path, data=obj)
        return res

    def deleteDescriptor(self, descriptor_id: str = None) -> str:
        """
        Delete a specific descriptor.
        Arguments:
            descriptor_id : REQUIRED : the descriptor id to delete
        """
        if descriptor_id is None:
            raise Exception("Require a descriptor id")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteDescriptor")
        path = f"/{self.container}/descriptors/{descriptor_id}"
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = f"application/vnd.adobe.xdm+json"
        res = self.connector.deleteData(self.endpoint + path, headers=privateHeader)
        return res

    def putDescriptor(
        self,
        descriptorId: str = None,
        descriptorObj:dict = None,
        desc_type: str = "xdm:descriptorIdentity",
        sourceSchema: str = None,
        sourceProperty: str = None,
        namespace: str = None,
        xdmProperty: str = "xdm:code",
        primary: bool = False,
        **kwargs
    ) -> dict:
        """
        Replace the descriptor with the new definition. It updates the whole definition.
        Arguments:
            descriptorId : REQUIRED : the descriptor id to replace
            descriptorObj : REQUIRED : The full descriptor object if you want to pass it directly.
            desc_type : REQUIRED : the type of descriptor to create.(default Identity)
            sourceSchema : REQUIRED : the schema attached to your identity ()
            sourceProperty : REQUIRED : the path to the field
            namespace : REQUIRED : the namespace used for the identity
            xdmProperty : OPTIONAL : xdm code for the descriptor (default : xdm:code)
            primary : OPTIONAL : Boolean to define if it is a primary identity or not (default False).
        """
        if descriptorId is None:
            raise Exception("Require a descriptor id")
        if self.loggingEnabled:
            self.logger.debug(f"Starting putDescriptor")
        path = f"/{self.container}/descriptors/{descriptorId}"
        if sourceSchema is None or sourceProperty is None or namespace is None:
            raise Exception("Missing required arguments.")
        if descriptorObj is not None and type(descriptorObj) == dict:
            obj = descriptorObj
        else:
            obj = {
            "@type": desc_type,
            "xdm:sourceSchema": sourceSchema,
            "xdm:sourceVersion": 1,
            "xdm:sourceProperty": sourceProperty,
            "xdm:namespace": namespace,
            "xdm:property": xdmProperty,
            "xdm:isPrimary": primary,
            }
            for key in kwargs:
                if 'xdm:' in key:
                    obj[key] = kwargs.get(key)
        res = self.connector.putData(
            self.endpoint + path, data=obj)
        return res


    def getAuditLogs(self, resourceId: str = None) -> list:
        """
        Returns the list of the changes made to a ressource (schema, class, mixin).
        Arguments:
            resourceId : REQUIRED : The "$id" or "meta:altId" of the resource.
        """
        if not resourceId:
            raise ValueError("resourceId should be included as a parameter")
        if resourceId.startswith("https://"):
            from urllib import parse
            resourceId = parse.quote_plus(resourceId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting createDescriptor")
        path: str = f"/rpc/auditlog/{resourceId}"
        res: list = self.connector.getData(self.endpoint + path)
        return res
    
    def exportResource(self,resourceId:str=None,Accept:str="application/vnd.adobe.xed+json; version=1")->dict:
        """
        Return all the associated references required for importing the resource in a new sandbox or a new Org.
        Argument:
            resourceId : REQUIRED : The $id or meta:altId of the resource to export.
            Accept : OPTIONAL : If you want to change the Accept header of the request.
        """
        if resourceId is None:
            raise ValueError("Require a resource ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting exportResource for resourceId : {resourceId}")
        if resourceId.startswith("https://"):
            from urllib import parse
            resourceId = parse.quote_plus(resourceId)
        privateHeader = deepcopy(self.header)
        privateHeader['Accept'] = Accept
        path = f"/rpc/export/{resourceId}"
        res = self.connector.getData(self.endpoint +path,headers=privateHeader)
        return res

    def importResource(self,dataResource:dict = None)->dict:
        """
        Import a resource based on the export method.
        Arguments:
            dataResource : REQUIRED : dictionary of the resource retrieved.
        """
        if dataResource is None:
            raise ValueError("a dictionary presenting the resource to be imported should be included as a parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting importResource")
        path: str = f"/rpc/export/"
        res: list = self.connector.postData(self.endpoint + path, data=dataResource)
        return res

    def extendFieldGroup(self,fieldGroupId:str=None,values:list=None)->dict:
        """
        Patch a Field Group to extend its compatibility with ExperienceEvents, IndividualProfile and Record.
        Arguments:
            fieldGroupId : REQUIRED : meta:altId or $id of the field group.
            values : OPTIONAL : If you want to pass the behavior you want to extend the field group to.
                Examples: ["https://ns.adobe.com/xdm/context/profile",
                      "https://ns.adobe.com/xdm/context/experienceevent",
                    ]
                by default profile and experienceEvent will be added to the FieldGroup.
        """
        if fieldGroupId is None:
            raise Exception("Require a field Group ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting extendFieldGroup")
        path = f"/{self.container}/fieldgroups/{fieldGroupId}"
        operation = [
           { 
            "op": "replace",
            "path": "/meta:intendedToExtend",
            "value": ["https://ns.adobe.com/xdm/context/profile",
                      "https://ns.adobe.com/xdm/context/experienceevent",
                    ]
            }
        ]
        res = self.connector.patchData(self.endpoint + path,data=operation)
        return res
    
    def enableSchemaForRealTime(self,schemaId:str=None)->dict:
        """
        Enable a schema for real time based on its ID.
        Arguments:
            schemaId : REQUIRED : The schema ID required to be updated
        """
        if schemaId is None:
            raise Exception("Require a schema ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting enableSchemaForRealTime")
        path = f"/{self.container}/schemas/{schemaId}/"
        operation = [
           { 
            "op": "add",
            "path": "/meta:immutableTags",
            "value": ["union"]
            }
        ]
        res = self.connector.patchData(self.endpoint + path,data=operation)
        return res
    
    def FieldGroupManager(self,fieldGroup:Union[dict,str,None],title:str=None,fg_class:list=["experienceevent","profile"]) -> 'FieldGroupManager':
         """
         Generate a field group Manager instance using the information provided by the schema instance.
         Arguments:
             fieldGroup : OPTIONAL : the field group definition as dictionary OR the ID to access it OR nothing if you want to start from scratch
             title : OPTIONAL : If you wish to change the tile of the field group.
         """
         tenantId = self.getTenantId()
         return FieldGroupManager(tenantId=tenantId,fieldGroup=fieldGroup,title=title,fg_class=fg_class,schemaAPI=self)
    
    def SchemaManager(self,schema:Union[dict,str],fieldGroups:list=None,fgManager:bool=False) -> 'FieldGroupManager':
         """
         Generate a Schema Manager instance using the information provided by the schema instance.
         Arguments:
            schema : OPTIONAL : the schema definition as dictionary OR the ID to access it OR Nothing if you want to start from scratch
            fieldGroups : OPTIONAL : If you wish to add a list of fieldgroups.
            fgManager : OPTIONAL : If you wish to handle the different field group passed into a Field Group Manager instance and have additional methods available.
         """
         return SchemaManager(schema=schema,fieldGroups=fieldGroups,schemaAPI=self,fgManager=fgManager)



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
        """
        
        self.fieldGroup = {}
        if schemaAPI is not None:
            self.schemaAPI = schemaAPI
        else:
            self.schemaAPI = Schema(config=config)
        self.tenantId = f"_{self.schemaAPI.getTenantId()}"
        if fieldGroup is not None:
            if type(fieldGroup) == dict:
                if fieldGroup.get("meta:resourceType",None) == "mixins":
                    self.fieldGroup = fieldGroup
            elif type(fieldGroup) == str and (fieldGroup.startswith('https:') or fieldGroup.startswith(f'{self.tenantId}.')):
                if self.schemaAPI is None:
                    raise Exception("You try to retrieve the fieldGroup definition from the id, but no API has been passed in the schemaAPI parameter.")
                self.fieldGroup = self.schemaAPI.getFieldGroup(fieldGroup,full=False)
            else:
                raise ValueError("the element pass is not a field group definition")
        else:
            self.fieldGroup = {
                "title" : "",
                "meta:resourceType":"mixins",
                "description" : "",
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
        self.__setAttributes__(self.fieldGroup)
        if title is not None:
            self.fieldGroup['title'] = title
            self.title = title
        
    
    def __setAttributes__(self,fieldGroup:dict)->None:
        uniqueId = fieldGroup.get('id',str(int(time.time()*100))[-7:])
        self.title = self.fieldGroup.get('title',f'unknown:{uniqueId}')
        if self.fieldGroup.get('$id',False):
            self.id = self.fieldGroup.get('$id')
        if self.fieldGroup.get('meta:altId',False):
            self.altId = self.fieldGroup.get('meta:altId')
    
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
    
    def __accessorAlgo__(self,mydict:dict,path:list=None)->dict:
        """
        recursive method to retrieve all the elements.
        Arguments:
            mydict : REQUIRED : The dictionary containing the elements to fetch (in "properties" key)
            path : the path with dot notation.
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

    def __transformationDF__(self,mydict:dict=None,dictionary:dict=None,path:str=None,queryPath:bool=False,description:bool=False,xdmType:bool=False)->dict:
        """
        Transform the current XDM schema to a dictionary.
        Arguments:
            mydict : the fieldgroup
            dictionary : the dictionary that gather the paths
            path : path that is currently being developed
            queryPath: boolean to tell if we want to add the query path
            description : boolean to tell if you want to retrieve the description
            xdmType : boolean to know if you want to retrieve the xdm Type
        """
        if dictionary is None:
            dictionary = {'path':[],'type':[]}
            if queryPath:
                dictionary['querypath'] = []
            if description:
                dictionary['description'] = []
        else:
            dictionary = dictionary
        for key in mydict:
            if type(mydict[key]) == dict:
                if mydict[key].get('type') == 'object':
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
                        if queryPath:
                            dictionary["querypath"].append(self.__cleanPath__(tmp_path))
                        if description:
                            dictionary["description"].append(f"{mydict[key].get('description','')}")
                    properties = mydict[key].get('properties',None)
                    if properties is not None:
                        self.__transformationDF__(properties,dictionary,tmp_path,queryPath,description)
                elif mydict[key].get('type') == 'array':
                    levelProperties = mydict[key]['items'].get('properties',None)
                    if levelProperties is not None:
                        if path is None:
                            tmp_path = key
                        else :
                            tmp_path = f"{path}.{key}[]{{}}"
                        dictionary["path"].append(tmp_path)
                        dictionary["type"].append(f"[{mydict[key]['items'].get('type')}]")
                        if queryPath and tmp_path is not None:
                            dictionary["querypath"].append(self.__cleanPath__(tmp_path))
                        if description and tmp_path is not None:
                            dictionary["description"].append(mydict[key]['items'].get('description',''))
                        self.__transformationDF__(levelProperties,dictionary,tmp_path,queryPath,description)
                    else:
                        finalpath = f"{path}.{key}"
                        dictionary["path"].append(finalpath)
                        dictionary["type"].append(f"[{mydict[key]['items'].get('type')}]")
                        if queryPath and finalpath is not None:
                            dictionary["querypath"].append(self.__cleanPath__(finalpath))
                        if description and finalpath is not None:
                            dictionary["description"].append(mydict[key]['items'].get('description',''))
                else:
                    if path is not None:
                        finalpath = f"{path}.{key}"
                    else:
                        finalpath = f"{key}"
                    dictionary["path"].append(finalpath)
                    dictionary["type"].append(mydict[key].get('type','object'))
                    if queryPath and finalpath is not None:
                        dictionary["querypath"].append(self.__cleanPath__(finalpath))
                    if description and finalpath is not None:
                        dictionary["description"].append(mydict[key].get('description',''))

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
        lastField = completePathList[-1]
        fieldGroup = deepcopy(fieldGroup)
        for key in fieldGroup:
            level = fieldGroup.get(key,None)
            if type(level) == dict and key in completePathList:
                if 'properties' in level.keys():
                    if key != lastField:
                        res,foundFlag = self.__setField__(completePathList,fieldGroup[key]['properties'],newField,obj)
                        fieldGroup[key]['properties'] = res
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
        elif dataType == "DateTime":
            obj['type'] = "string"
            obj['format'] = "date-time"
        elif dataType == "byte":
            obj['type'] = "integer"
            obj['maximum'] = 128
            obj['minimum'] = -128
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
    
    def setTitle(self,name:str=None)->None:
        """
        Set a name for the schema.
        Arguments:
            name : REQUIRED : a string to be used for the title of the FieldGroup
        """
        self.fieldGroup['title'] = name
        return None

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

        
    def addFieldOperation(self,path:str,dataType:str=None,title:str=None,objectComponents:dict=None,array:bool=False,enumValues:dict=None,**kwargs)->None:
        """
        Return the operation to be used on the field group with the Patch method (patchFieldGroup), based on the element passed in argument.
        Arguments:
            path : REQUIRED : path with dot notation where you want to create that new field.
                In case of array of objects, use the "[]{}" notation
            dataType : REQUIRED : the field type you want to create
                A type can be any of the following: "string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object","array"
                NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
            title : OPTIONAL : if you want to have a custom title.
            objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.
                Example : {'field1':'string','field2':'double'}
            array : OPTIONAL : Boolean. If the element to create is an array. False by default.
            enumValues : OPTIONAL : If your field is an enum, provid a dictionary of value and display name, such as : {'value':'display'}
        possible kwargs:
            defaultPath : Define which path to take by default for adding new field on tenant. Default "property", possible alternative : "customFields"
        """
        typeTyped = ["string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object",'array']
        if dataType not in typeTyped:
            raise TypeError('Expecting one of the following type : "string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object"')
        if dataType == 'object' and objectComponents is None:
            raise AttributeError('Require a dictionary providing the object component')       
        if title is None:
            title = self.__cleanPath__(path.split('.').pop())
        if title == 'items' or title == 'properties':
            raise Exception('"item" and "properties" are 2 reserved keywords')
        pathSplit = path.split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        completePath = ['definitions',kwargs.get('defaultPath','property')]
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
        operation[0]['value']['title'] = title
        if enumValues is not None and type(enumValues) == dict:
            if array == False:
                operation[0]['value']['enum'] = [enumValues.keys()]
                operation[0]['value']['meta:enum'] = enumValues
            else:
                operation[0]['value']['items']['enum'] = [enumValues.keys()]
                operation[0]['value']['items']['meta:enum'] = enumValues
        return operation

    def addField(self,path:str,dataType:str=None,title:str=None,objectComponents:dict=None,array:bool=False,enumValues:dict=None,**kwargs)->dict:
        """
        Add the field to the existing fieldgroup definition.
        Returns False when the field could not be inserted.
        Arguments:
            path : REQUIRED : path with dot notation where you want to create that new field. New field name should be included.
                In case of array of objects, use the "[*]" notation
            dataType : REQUIRED : the field type you want to create
                A type can be any of the following: "string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object","array"
                NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
            title : OPTIONAL : if you want to have a custom title.
            objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.
                Example : {'field1:'string','field2':'double'}
            array : OPTIONAL : Boolean. If the element to create is an array. False by default.
            enumValues : OPTIONAL : If your field is an enum, provid a dictionary of value and display name, such as : {'value':'display'}
        possible kwargs:
            defaultPath : Define which path to take by default for adding new field on tenant. Default "property", possible alternative : "customFields"
        """
        if path is None:
            raise ValueError("path must provided")
        typeTyped = ["string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object",'array']
        if dataType not in typeTyped:
            raise TypeError('Expecting one of the following type : "string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object","bytes"')
        if dataType == 'object' and objectComponents is None:
            raise AttributeError('Require a dictionary providing the object component')
        if title is None:
            title = self.__cleanPath__(path.split('.').pop())
        if title == 'items' or title == 'properties':
            raise Exception('"item" and "properties" are 2 reserved keywords')
        pathSplit = self.__cleanPath__(path).split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        newField = pathSplit.pop()
        obj = {}
        if dataType == 'object':
            obj = { 'type':'object', 'title':title,
                'properties':{key:self.__transformFieldType__(objectComponents[key]) for key in objectComponents }
            }
        elif dataType == 'array':
            obj = { 'type':'array', 'title':title,
                "items":{
                    'type':'object',
                    'properties':{key:self.__transformFieldType__(objectComponents[key]) for key in objectComponents }
                }
            }
        else:
            obj = self.__transformFieldType__(dataType)
            obj['title']= title
            if array:
                obj['type'] = "array"
                obj['items'] = self.__transformFieldType__(dataType)
        if enumValues is not None and type(enumValues) == dict:
            if array == False:
                obj['enum'] = [enumValues.keys()]
                obj['meta:enum'] = enumValues
            else:
                obj['items']['enum'] = [enumValues.keys()]
                obj['items']['meta:enum'] = enumValues
        completePath:list[str] = [kwargs.get('defaultPath','property')] + pathSplit
        customFields,foundFlag = self.__setField__(completePath, self.fieldGroup['definitions'],newField,obj)
        if foundFlag == False:
            return False
        else:
            self.fieldGroup['definitions'] = customFields
            return self.fieldGroup
        
    def removeField(self,path:str)->dict:
        """
        Remove a field from the definition based on the path provided.
        NOTE: A path that has received data cannot be removed from a schema or field group.
        Argument:
            path : REQUIRED : The path to be removed from the definition.
        """
        if path is None:
            raise ValueError('Require a path to remove it')
        pathSplit = self.__cleanPath__(path).split('.')
        if pathSplit[0] == '':
            del pathSplit[0]
        success = False
        ## Try customFields
        completePath:list[str] = ['customFields'] + pathSplit
        success = self.__removeKey__(completePath,self.fieldGroup['definitions'])
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
        if save:
            filename = self.fieldGroup.get('title',f'unknown_fieldGroup_{str(int(time.time()))}')
            aepp.saveFile(module='schema',file=data,filename=f"{filename}.json",type_file='json')
        return data

    def to_dataframe(self,save:bool=False,queryPath:bool=False,description:bool=False)->pd.DataFrame:
        """
        Generate a dataframe with the row representing each possible path.
        Arguments:
            save : OPTIONAL : If you wish to save it with the title used by the field group.
                save as csv with the title used. Not title, used "unknown_fieldGroup_" + timestamp.
            queryPath : OPTIONAL : If you want to have the query path to be used.
            description : OPTIONAL : If you want to have the description used
        """
        definition = self.fieldGroup.get('definitions',self.fieldGroup.get('properties',{}))
        data = self.__transformationDF__(definition,queryPath=queryPath,description=description)
        df = pd.DataFrame(data)
        if save:
            title = self.fieldGroup.get('title',f'unknown_fieldGroup_{str(int(time.time()))}')
            df.to_csv(f"{title}.csv",index=False)
        return df
    
    def to_xdm(self)->dict:
        """
        Return the fieldgroup definition as XDM
        """
        return self.fieldGroup

    def patchFieldGroup(self,operations:list=None)->dict:
        """
        Patch the field group with the given operation.
        Arguments:
            operation : REQUIRED : The list of operation to realise
        """
        if operations is None or type(operations) != list:
            raise ValueError('Require a list of operations')
        if self.schemaAPI is None:
            Exception('Require a schema API connection. Pass the instance of a Schema class or import a configuration file.')
        res = self.schemaAPI.patchFieldGroup(self.id,operations)
        self.fieldGroup = res
        self.__setAttributes__(self.fieldGroup)
        return res
    
    def updateFieldGroup(self)->dict:
        """
        Use the PUT method to push the current field group representation to AEP via API request.
        """
        if self.schemaAPI is None:
            Exception('Require a schema API connection. Pass the instance of a Schema class or import a configuration file.')
        res = self.schemaAPI.putFieldGroup(self.id,self.to_xdm())
        self.fieldGroup = res
        self.__setAttributes__(self.fieldGroup)
        return res
    
    def createFieldGroup(self)->dict:
        """
        Use the POST method to create the field group in the organization.
        """
        if self.schemaAPI is None:
            Exception('Require a schema API connection. Pass the instance of a Schema class or import a configuration file.')
        res = self.schemaAPI.createFieldGroup(self.to_xdm())
        return res


class SchemaManager:
    """
    A class to handle the schema management.
    """
    DESCRIPTOR_TYPES =["xdm:descriptorIdentity","xdm:alternateDisplayInfo","xdm:descriptorOneToOne","xdm:descriptorReferenceIdentity","xdm:descriptorDeprecated"]

    def __init__(self,schema:Union[str,dict],
                fieldGroupIds:list=None,
                schemaAPI:'Schema'=None,
                schemaClass:str=None,
                config: Union[dict,ConnectObject] = aepp.config.config_object,
                )->None:
        """
        Instantiate the Schema Manager instance.
        Arguments:
            schemaId : OPTIONAL : Either a schemaId ($id or altId) or the schema dictionary itself.
                If schemaId is passed, you need to provide the schemaAPI connection as well.
            fieldGroupIds : OPTIONAL : Possible to specify a list of fieldGroup. 
                Either a list of fieldGroupIds (schemaAPI should be provided as well) or list of dictionary definition 
            schemaAPI : OPTIONAL : It is required if $id or altId are used. It is the instance of the Schema class.
            schemaClass : OPTIONAL : If you want to set the class to be a specific class.
                Default value is profile: "https://ns.adobe.com/xdm/context/profile", can be replaced with any class definition.
                Possible default value: "https://ns.adobe.com/xdm/context/experienceevent", "https://ns.adobe.com/xdm/context/segmentdefinition"
            config : OPTIONAL : The config object in case you want to override the configuration.
        """
        self.fieldGroupIds=[]
        self.fieldGroupsManagers = []
        self.title = None
        if schemaAPI is not None:
            self.schemaAPI = schemaAPI
        else:
            self.schemaAPI = Schema(config=config)
        if type(schema) == dict:
            self.schema = schema
            self.__setAttributes__(self.schema)
            allOf = self.schema.get("allOf",[])
            if len(allOf) == 0:
                Warning("You have passed a schema with -full attribute, you should pass one referencing the fieldGroups.\n Using the meta:extends reference if possible")
                self.fieldGroupIds = [ref for ref in self.schema['meta:extends'] if ('/mixins/' in ref or '/experience/' in ref or '/context/' in ref) and ref != self.classId]
                self.schema['allOf'] = [{"$ref":ref} for ref in self.schema['meta:extends'] if ('/mixins/' in ref or 'xdm/class' in ref or 'xdm/context/' in ref) and ref != self.classId]
            else:
                self.fieldGroupIds = [obj['$ref'] for obj in allOf if ('/mixins/' in obj['$ref'] or '/experience/' in obj['$ref'] or '/context/' in obj['$ref']) and obj['$ref'] != self.classId]
            if self.schemaAPI is None:
                Warning("No schema instance has been passed or config file imported.\n Aborting the creation of field Group Manager")
            else:
                for ref in self.fieldGroupIds:
                    if '/mixins/' in ref:
                        definition = self.schemaAPI.getFieldGroup(ref,full=False)
                    else:
                        definition = self.schemaAPI.getFieldGroup(ref,full=True)
                    self.fieldGroupsManagers.append(FieldGroupManager(fieldGroup=definition))
        elif type(schema) == str:
            if self.schemaAPI is None:
                Warning("No schema instance has been passed or config file imported.\n Aborting the retrieveal of the Schema Definition")
            else:
                self.schema = self.schemaAPI.getSchema(schema,full=False)
                self.__setAttributes__(self.schema)
                allOf = self.schema.get("allOf",[])
                self.fieldGroupIds = [obj['$ref'] for obj in allOf if ('/mixins/' in obj['$ref'] or '/experience/' in obj['$ref'] or '/context/' in obj['$ref']) and obj['$ref'] != self.classId]
                if self.schemaAPI is None:
                    Warning("fgManager is set to True but no schema instance has been passed.\n Aborting the creation of field Group Manager")
                else:
                    for ref in self.fieldGroupIds:
                        if '/mixins/' in ref:
                            definition = self.schemaAPI.getFieldGroup(ref,full=False)
                        else:
                            definition = self.schemaAPI.getFieldGroup(ref,full=True)
                        self.fieldGroupsManagers.append(FieldGroupManager(fieldGroup=definition))
        elif schema is None:
            self.schema = {
                    "title": None,
                    "description": "power by aepp",
                    "allOf": [
                            {
                            "$ref": "https://ns.adobe.com/xdm/context/profile"
                            }
                        ]
                    }
        if schemaClass is not None:
            self.schema['allOf'][0]['$ref'] = schemaClass
        if fieldGroupIds is not None and type(fieldGroupIds) == list:
            if fieldGroupIds[0] == str:
                for fgId in fieldGroupIds:
                    self.fieldGroupIds.append(fgId)
                    if self.schemaAPI is None:
                        Warning("fgManager is set to True but no schema instance has been passed.\n Aborting the creation of field Group Manager")
                    else:
                        definition = self.schemaAPI.getFieldGroup(ref)
                        self.fieldGroupsManagers.append(FieldGroupManager(definition))
            elif fieldGroupIds[0] == dict:
                for fg in fieldGroupIds:
                    self.fieldGroupIds.append(fg.get('$id'))
                    self.fieldGroupsManagers.append(FieldGroupManager(fg))
        self.fieldGroupTitles= tuple(fg.title for fg in self.fieldGroupsManagers)
        self.fieldGroups = {fg.id:fg.title for fg in self.fieldGroupsManagers}
    
    def __setAttributes__(self,schemaDef:dict)->None:
        """
        Set some basic attributes
        """
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
        for fgmanager in self.fieldGroupsManagers:
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
        for fgmanager in self.fieldGroupsManagers:
            res = fgmanager.searchAttribute(attr=attr,regex=regex,extendedResults=extendedResults,joinType=joinType)
            if extendedResults:
                for r in res:
                    r['fieldGroup'] = fgmanager.title
            myResults += res
        return myResults
    
    def addFieldGroup(self,fieldGroup:Union[str,dict]=None)->Union[None,'FieldGroupManager']:
        """
        Add a field groups to field Group object and the schema. 
        return the specific FieldGroup Manager instance.
        Arguments:
            fieldGroup : REQUIRED : The fieldGroup ID or the dictionary definition connecting to the API.
                if a fieldGroup ID is provided, you should have added a schemaAPI previously.
        """
        if type(fieldGroup) == dict:
            if fieldGroup.get('$id') not in [fg for fg in self.fieldGroupIds]:
                self.fieldGroupIds.append(fieldGroup['$id'])
                self.schema['allOf'].append({'$ref':fieldGroup['$id'],"type": "object"})
                
        elif type(fieldGroup) == str:
            if fieldGroup not in [fg for fg in self.fieldGroupIds]:
                self.fieldGroupIds.append(fieldGroup)
                self.schema['allOf'].append({'$ref':fieldGroup,"type": "object"})
                if self.schemaAPI is None:
                    raise AttributeError('Missing the schema API attribute. Please use the addSchemaAPI method to add it.')
                else:
                    fieldGroup = self.schemaAPI.getFieldGroup(fieldGroup)
        fbManager = FieldGroupManager(fieldGroup=fieldGroup)
        self.fieldGroupsManagers.append(fbManager)
        self.fieldGroupTitles = tuple(fgm.title for fgm in self.fieldGroupsManagers)
        self.fieldGroups = {fgm.id:fgm.title for fgm in self.fieldGroupsManagers}
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
                return [fg for fg in self.fieldGroupsManagers if fg.id == fieldgroup][0]
            else:
                return [fg for fg in self.fieldGroupsManagers if fg.title == fieldgroup][0]
        else:
            raise Exception("The field group manager was not set to True during instanciation. No Field Group Manager to return")

    def setTitle(self,name:str=None)->None:
        """
        Set a name for the schema.
        Arguments:
            name : REQUIRED : a string to be used for the title of the FieldGroup
        """
        self.schema['title'] = name
        self.title = name
        return None

    def to_dataframe(self,save:bool=False,queryPath: bool = False,description:bool = False)->pd.DataFrame:
        """
        Extract the information from the Field Group to DataFrame. You need to have instanciated the Field Group manager.
        Arguments:
            save : OPTIONAL : If you wish to save it with the title used by the field group.
                save as csv with the title used. Not title, used "unknown_schema_" + timestamp.
            queryPath : OPTIONAL : If you want to have the query path to be used.
        """
        df = pd.DataFrame({'path':[],'type':[],'fieldGroup':[]})
        for fgmanager in self.fieldGroupsManagers:
            tmp_df = fgmanager.to_dataframe(queryPath=queryPath,description=description)
            tmp_df['fieldGroup'] = fgmanager.title
            df = df.append(tmp_df,ignore_index=True)
        if save:
            title = self.schema.get('title',f'unknown_schema_{str(int(time.time()))}.csv')
            df.to_csv(f"{title}.csv",index=False)
        df = df[~df.duplicated('path')].reset_index(drop=True)
        return df
    
    def to_dict(self)->dict:
        """
        Return a dictionary of the whole schema. You need to have instanciated the Field Group Manager
        """
        list_dict = [fbm.to_dict() for fbm in self.fieldGroupsManagers]
        result = {}
        for mydict in list_dict:
            result = self.__simpleDeepMerge__(result,mydict)
        return result

    def createSchema(self)->dict:
        """
        Send a createSchema request to AEP to create the schema.
        It removes the "$id" if one was provided to avoid overriding existing ID.
        """
        if self.schemaAPI is None:
            raise Exception("Require a Schema instance to connect to the API")
        res = self.schemaAPI.createSchema(self.schema)
        self.schema = res
        self.__setAttributes__(self.schema)
        return res

    def updateSchema(self)->dict:
        """
        Use the PUT method to replace the existing schema with the new definition.
        """
        if self.schemaAPI is None:
            raise Exception("Require a Schema instance to connect to the API")
        res = self.schemaAPI.putSchema(self.id,self.schema)
        self.schema = res
        self.__setAttributes__(self.schema)
        return res
    
    def createDescriptorOperation(self,descType:str=None,
                                completePath:str=None,
                                identityNSCode:str=None,
                                identityPrimary:bool=False,
                                alternateTitle:str=None,
                                alternateDescription:str=None,
                                lookupSchema:str=None,
                                targetCompletePath:str=None,
                                )->dict:
        """
        Create a descriptor object to be used in the createDescriptor.
        You can see the type of descriptor available in the DESCRIPTOR_TYPES attribute and also on the official documentation:
        https://experienceleague.adobe.com/docs/experience-platform/xdm/api/descriptors.html?lang=en#appendix
        Arguments:
            descType : REQUIRED : The type to be used.
                it can only be one of the following value: "xdm:descriptorIdentity","xdm:alternateDisplayInfo","xdm:descriptorOneToOne","xdm:descriptorReferenceIdentity","xdm:descriptorDeprecated"
            completePath : REQUIRED : the complete path of the field you want to attach a descriptor.
                Example: '/definitions/customFields/properties/_tenant/properties/tenantObject/properties/field'
            identityNSCode : OPTIONAL : if the descriptor is identity related, the namespace CODE  used.
            identityPrimary : OPTIONAL : If the primary descriptor added is the primary identity.
            alternateTitle : OPTIONAL : if the descriptor is alternateDisplay, the alternate title to be used.
            alternateDescription : OPTIONAL if you wish to add a new description.
            lookupSchema : OPTIONAL : The schema ID for the lookup if the descriptor is for lookup setup
            targetCompletePath : OPTIONAL : if you have the complete path for the field in the target lookup schema.
        """
        if descType not in self.DESCRIPTOR_TYPES:
            raise Exception(f"The value provided ({descType}) is not supported by this method")
        if completePath is None:
            raise ValueError("Require a field complete path")
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
                "xdm:destinationSchema":lookupSchema,
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