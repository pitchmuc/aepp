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
import time, json
import logging
import pandas as pd
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
        self.dataTypes_id = {}
        self.dataTypes_altId = {}
        self.classes_id = {}
        self.classes_altId = {}

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
        "" :""
    }
    PATCH_OBJ = [{"op": "add", "path": "/meta:immutableTags-", "value": "union"}]
    DESCRIPTOR_TYPES =["xdm:descriptorIdentity","xdm:alternateDisplayInfo","xdm:descriptorOneToOne","xdm:descriptorReferenceIdentity","xdm:descriptorDeprecated","xdm:descriptorTimeSeriesGranularity",'xdm:descriptorLabel']

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        containerId: str = "tenant",
        header=aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ):
        """
        Copy the token and header and initiate the object to retrieve schema elements.
        Arguments:
            config : OPTIONAL : config object in the config module.
            containerId : OPTIONAL : "tenant"(default) or "global"
            header : OPTIONAL : header object  in the config module.
            loggingObject : OPTIONAL : logging object to log messages.
        """
        if loggingObject is not None and sorted(
            ["level", "stream", "format", "filename", "file"]
        ) == sorted(list(loggingObject.keys())):
            self.loggingEnabled = True
            self.logger = logging.getLogger(f"{__name__}")
            self.logger.setLevel(loggingObject["level"])
            formatter = logging.Formatter("%(asctime)s::%(name)s::%(funcName)s::%(levelname)s::%(message)s::%(lineno)d")
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

    def __str__(self):
        return json.dumps({'class':'Schema','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)
    
    def __repr__(self):
        return json.dumps({'class':'Schema','sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)

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

    def getBehavior(self,behaviorId:str=None,full=True,type:str='xdm',**kwargs)->dict:
        """
        Retrieve a specific behavior for class creation.
        Arguments:
            behaviorId : REQUIRED : the behavior ID to be retrieved.
            full : OPTIONAL : True (default) will return the full schema.False just the relationships.
            type : OPTIONAL : either "xdm" (default) or "xed".
        """
        if behaviorId is None:
            raise Exception("Require a behavior ID")
        privateHeader = deepcopy(self.header)
        if behaviorId.startswith("https://"):
            from urllib import parse
            behaviorId = parse.quote_plus(behaviorId)
        if full:
            update_full = "-full"
        else:
            update_full = ""
        if kwargs.get('xtype', None) is not None and kwargs.get('xtype', None) != type:
            type = kwargs.get('xtype', 'xdm')
        privateHeader['Accept'] = f"application/vnd.adobe.{type}{update_full}+json; version=1.0"
        path = f"/global/behaviors/{behaviorId}"
        res = self.connector.getData(self.endpoint + path,headers=privateHeader)
        return res

    def getSchemas(
            self, 
            classFilter: str = None,
            excludeAdhoc: bool = True,
            output: str = 'raw',
            prop: str = None,
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
        params = {}
        if classFilter is not None:
            params["property"] = f"meta:extends=={classFilter}"
        elif excludeAdhoc:
            params["property"] = "meta:extends!=https://ns.adobe.com/xdm/data/adhoc"
        if prop is not None:
            params["property"] = prop
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
    
    def getSchemasGlobal(self,
                         prop:str|None=None,
                         format:str="xed",
                         orderBy:str|None=None,
                         limit:int=300,
                         output:str='raw',
                         **kwargs
                         )->list:
        """
        Retrive the schema that are OOTB available in the global container. These schemas cannot be edited but can be used as a base for your custom schemas.
        Arguments:
            prop : OPTIONAL : A comma-separated list of top-level object properties to be returned in the response. 
                            For example, property=meta:intendedToExtend==https://ns.adobe.com/xdm/context/profile
            format : OPTIONAL : type of response, default "xdm", can be "xed" for xed format.
            orderBy : OPTIONAL : Sort the listed resources by specified fields. For example orderby=title
            limit : OPTIONAL : Number of resources to return per request, default 300 - the max.
            output : OPTIONAL : type of output, default "raw", can be "df" for dataframe.
        kwargs:
            debug : if set to True, will print result for errors
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchemasGlobal")
        privateHeader = deepcopy(self.header)
        privateHeader.update({"Accept": f"application/vnd.adobe.{format}-id+json"})
        params = {"limit":limit}
        if prop is not None:
            if 'property' not in params.keys():
                params["property"] = prop
            else:
                params["property"] += prop
        if orderBy is not None:
            params['orderby'] = orderBy
        path = f"/global/schemas/"
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
        for el in data:
            self.data.schemas_id[el["title"]] = el["$id"]
            self.data.schemas_altId[el["title"]] = el["meta:altId"]
        if output=="df":
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
        Returns a list of the path available in your schema.
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
        rand_number = random.randint(1, 10**10)
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
            schema_id : REQUIRED : $id or meta:altId to be deleted
            It requires a allOf list that contains all the attributes that are required for creating a schema.
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
        res = self.putSchema(schemaId,schemaDef)
        return res        

    def getClasses(self, 
                   prop:str=None,
                   orderBy:str=None,
                   limit:int=300, 
                   output:str='raw',
                   format:str='xdm',
                   excludeAdhoc: bool = True,
                   **kwargs):
        """
        Return the classes of the AEP Instances.
        Arguments:
            prop : OPTIONAL : A comma-separated list of top-level object properties to be returned in the response. 
                            For example, property=meta:intendedToExtend==https://ns.adobe.com/xdm/context/profile
            oderBy : OPTIONAL : Sort the listed resources by specified fields. For example orderby=title
            limit : OPTIONAL : Number of resources to return per request, default 300 - the max.
            format : OPTIONAL : type of response, default "xdm", can be "xed" for xed format.
            excludeAdhoc : OPTIONAL : Exlcude the Adhoc classes that have been created.
            output : OPTIONAL : type of output, default "raw", can be "df" for dataframe.
        kwargs:
            debug : if set to True, will print result for errors
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getClasses")
        privateHeader = deepcopy(self.header)
        privateHeader.update({"Accept": f"application/vnd.adobe.{format}-id+json"})
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
        self.data.classes_id = {cl["title"]: cl["$id"] for cl in data}
        self.data.classes_altId = {cl["title"]: cl["meta:altId"] for cl in data}
        if output=="df":
            df = pd.DataFrame(data)
            return df
        return data
        
    def getClassesGlobal(self, 
                   prop:str=None,
                   format:str='xdm',
                   orderBy:str=None,
                   limit:int=300, 
                   output:str='raw',
                   **kwargs):
        """
        Return the classes of the OOTB AEP Instances.
        Arguments:
            prop : OPTIONAL : A comma-separated list of top-level object properties to be returned in the response. 
                            For example, property=meta:intendedToExtend==https://ns.adobe.com/xdm/context/profile
            format : OPTIONAL : type of response, default "xdm", can be "xed" for xed format.
            oderBy : OPTIONAL : Sort the listed resources by specified fields. For example orderby=title
            limit : OPTIONAL : Number of resources to return per request, default 300 - the max.
            output : OPTIONAL : type of output, default "raw", can be "df" for dataframe.
        kwargs:
            debug : if set to True, will print result for errors
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getClasses")
        privateHeader = deepcopy(self.header)
        privateHeader.update({"Accept": f"application/vnd.adobe.{format}-id+json"})
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
        type: str = "xdm",
        version: int = 1,
        save: bool = False,
        **kwargs
    ):
        """
        Return a specific class.
        Arguments:
            classId : REQUIRED : the meta:altId or $id from the class
            full : OPTIONAL : True (default) will return the full schema.False just the relationships.
            desc : OPTIONAL : If set to True, return the descriptors.
            deprecated : OPTIONAL : Display the deprecated field from that schema (False by default)
            type : OPTIONAL : either "xdm" (default) or "xed". 
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
        if kwargs.get("xtype", None) is not None and kwargs.get("xtype", False) != type:
            type = kwargs.get("xtype", 'xdm')
        privateHeader.update(
                {"Accept": f"application/vnd.adobe.{type}{updateFull}{updateDesc}{updateDeprecated}+json; version=" + str(version)}
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
        params = {}
        verbose = kwargs.get("debug", False)
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = f"application/vnd.adobe.{format}+json"
        res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params, verbose=verbose
        )
        if kwargs.get("verbose", False):
            if "results" not in res.keys():
                print(res)
        data = res.get("results",[])
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
    
    def getFieldGroupsGlobal(self,format: str = "xdm",output:str='raw', prop:str|None=None,**kwargs)->list:
        """
        returns the global fieldGroups of the account.
        Arguments:
            format : OPTIONAL : either "xdm" or "xed" format
            output : OPTIONAL : either "raw" (default) or "df" for dataframe
            prop : OPTIONAL : A comma-separated list of top-level object properties to be returned in the response.
                    For example, prop=meta:intendedToExtend==https://ns.adobe.com/xdm/context/profile 
        kwargs:
            debug : if set to True, will print result for errors
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFieldGroups")
        path = f"/global/fieldgroups/"
        params = {}
        if prop is not None:
            params["property"] = prop
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
            print(f"Getting next page of global field groups : {nextPage}")
        for el in data:
            self.data.fieldGroups_altId[el["title"]] = el["meta:altId"]
            self.data.fieldGroups_id[el["title"]] = el["$id"]
        if output == 'df':
            df = pd.DataFrame(data)
            return df
        return data

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
        **kwargs
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
        if kwargs.get('xtype', None) is not None and kwargs.get('xtype', None) != type:
            type = kwargs.get('xtype', 'xdm')
        update_accept = (f"application/vnd.adobe.{type}{accept_full}{accept_desc}{accept_flat}{accept_deprec}+json; version={version}")
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

    def copyFieldGroup(
        self, fieldGroup: dict = None, tenantId: str = None, title: str = None
    ) -> dict:
        """
        Copy the dictionary returned by getFieldGroup to the only required elements for copying it over.
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
        obj = {}
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
                if tenantId in obj["definitions"]["customFields"]["properties"].keys():
                    obj["definitions"]["customFields"]["properties"][tenantId] = obj["definitions"]["customFields"]["properties"][oldTenant]
                    del obj["definitions"]["customFields"]["properties"][oldTenant]
                else:
                    for c_item in obj["definitions"]["customFields"]["properties"].keys():
                        child_obj = obj["definitions"]["customFields"]["properties"][c_item]
                        if oldTenant in child_obj["properties"].keys():
                            obj["definitions"]["customFields"]["properties"][c_item]["properties"][tenantId] = obj["definitions"]["customFields"]["properties"][c_item]["properties"][oldTenant]
                            del obj["definitions"]["customFields"]["properties"][c_item]["properties"][oldTenant]
        return obj

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

    def deleteFieldGroup(self, fieldGroupId: str = None):
        """
        Arguments:
            fieldGroupId : meta:altId or $id of the field group to be deleted
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
        privateHeader.update({"Accept": "application/vnd.adobe.xdm-full+json; version=" + str(version)})
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
        self.data.dataTypes_id = {mix["title"]: mix["$id"] for mix in data}
        self.data.dataTypes_altId = {mix["title"]: mix["meta:altId"] for mix in data}
        return data
    
    def getDataTypesGlobal(self,**kwargs)->list:
        """
        Get the OOTB data types.
        possible kwargs: Any kwarg pass will be passed as paramter of the request.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDataTypes")
        path = f"/global/datatypes/"
        privateHeader = deepcopy(self.header)
        privateHeader.update({"Accept": "application/vnd.adobe.xdm-id+json"})
        params = {}
        for key in kwargs.keys():
            params[key] = kwargs[key]
        res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params
        )
        data = res["results"]
        page = res.get("_page",{})
        nextPage = page.get('next',None)
        while nextPage is not None:
            res = self.connector.getData(self.endpoint + path, headers=privateHeader, params=params)
            data += res.get("results",[])
            page = res.get("_page",{})
            nextPage = page.get('next',None)
        for el in data:
            self.data.dataTypes_id[el["title"]] = el["$id"]
            self.data.dataTypes_altId[el["title"]] = el["meta:altId"]
        return data


    def getDataType(
        self, dataTypeId: str = None, 
        full: bool = True,
        type: str = 'xed',
        version: str = "1",
        save: bool = False,
        **kwargs
    ):
        """
        Retrieve a specific data type id
        Argument:
            dataTypeId : REQUIRED : The resource meta:altId or URL encoded $id URI.
            full : OPTIONAL : If you want to retrieve the full setup of your data type.(default True)
            type : OPTIONAL : default 'xdm', you can also pass the 'xed' format
            version : OPTIONAL : The version of your data type
            save : OPTIONAL : Save the data type in a JSON file.
        """
        if dataTypeId is None:
            raise Exception("Require a dataTypeId")
        if dataTypeId.startswith("https://"):
            from urllib import parse
            dataTypeId = parse.quote_plus(dataTypeId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDataType")
        privateHeader = deepcopy(self.header)
        xfull = ""
        if full:
            xfull = "-full"
        if full == False:
            xfull = ""
        if kwargs.get('xtype',None) is not None and kwargs.get('xtype', None) != type:
            type = kwargs.get('xtype')
        privateHeader.update(
            {"Accept": f"application/vnd.adobe.{type}{xfull}+json; version={version}"}
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
        Argument:
            dataTypeObj : REQUIRED : The data type definition
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
    
    def deleteDataType(self, dataTypeId: str = None) -> str:
        """
        Delete a specific data type.
        Arguments:
            dataTypeId : REQUIRED : The Data Type ID to be deleted
        """
        if dataTypeId is None:
            raise Exception("Require a data type ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteDataType")
        if dataTypeId.startswith("https://"):
            from urllib import parse
            dataTypeId = parse.quote_plus(dataTypeId)
        path = f"/{self.container}/datatypes/{dataTypeId}"
        res = self.connector.deleteData(self.endpoint + path)
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
        possible kwargs:
            prop : additional property that you want to filter with, such as "prop=f"xdm:sourceSchema==schema$Id"
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDescriptors")
        path = f"/{self.container}/descriptors/"
        params = {}
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
        if kwargs.get('prop',None) is not None:
            if 'property' in params.keys():
                params["property"] += f",{kwargs.get('prop')}"
            else:
                params["property"] = kwargs.get('prop')
        privateHeader = deepcopy(self.header)
        privateHeader[
            "Accept"
        ] = f"application/vnd.adobe.xdm-v2{update_link}{update_id}+json"
        res = self.connector.getData(
            self.endpoint + path, params=params, headers=privateHeader
        )
        data = res.get("results",[])
        page = res.get("_page",None)
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
        **kwargs
    ) -> dict:
        """
        Replace the descriptor with the new definition. It updates the whole definition.
        Arguments:
            descriptorId : REQUIRED : the descriptor id to replace
            descriptorObj : REQUIRED : The full descriptor object if you want to pass it directly.
        """
        if descriptorId is None:
            raise Exception("Require a descriptor id")
        if self.loggingEnabled:
            self.logger.debug(f"Starting putDescriptor")
        path = f"/{self.container}/descriptors/{descriptorId}"
        if descriptorObj is not None and type(descriptorObj) == dict:
            obj = descriptorObj
        else:
            raise ValueError("Require a dictionary representing the descriptor")
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

    def extendFieldGroup(self,fieldGroupId:str=None,values:list=None,tenant:str='tenant')->dict:
        """
        Patch a Field Group to extend its compatibility with ExperienceEvents, IndividualProfile and Record.
        Arguments:
            fieldGroupId : REQUIRED : meta:altId or $id of the field group.
            values : OPTIONAL : If you want to pass the behavior you want to extend the field group to.
                Examples: ["https://ns.adobe.com/xdm/context/profile",
                      "https://ns.adobe.com/xdm/context/experienceevent",
                    ]
                by default profile and experienceEvent will be added to the FieldGroup.
            tenant : OPTIONAL : default "tenant", possible value 'global'
        """
        if fieldGroupId is None:
            raise Exception("Require a field Group ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting extendFieldGroup")
        if fieldGroupId.startswith("https://"):
            from urllib import parse
            fieldGroupId = parse.quote_plus(fieldGroupId)
        path = f"/{tenant}/fieldgroups/{fieldGroupId}"
        if values is not None:
            list_fgs = values
        else:
            list_fgs = ["https://ns.adobe.com/xdm/context/profile",
                      "https://ns.adobe.com/xdm/context/experienceevent"]
        operation = [
           { 
            "op": "replace",
            "path": "/meta:intendedToExtend",
            "value": list_fgs
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
        if schemaId.startswith("https://"):
            from urllib import parse
            schemaId = parse.quote_plus(schemaId)
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
    
    def enableSchemaForUPS(self,schemaId:str=None)->dict:
        """
        Enable a schema for UPS based on its ID.
        Arguments:
            schemaId : REQUIRED : The schema ID required to be updated
        """
        if schemaId is None:
            raise Exception("Require a schema ID")
        if schemaId.startswith("https://"):
            from urllib import parse
            schemaId = parse.quote_plus(schemaId)
        if self.loggingEnabled:
            self.logger.debug(f"Starting enableSchemaForUPS")
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
         Generates a field group Manager instance using the information provided by the schema instance.
         Arguments:
             fieldGroup : OPTIONAL : the field group definition as dictionary OR the ID to access it OR nothing if you want to start from scratch
             title : OPTIONAL : If you wish to change the tile of the field group.
         """
         from .fieldgroupmanager import FieldGroupManager
         return FieldGroupManager(fieldGroup=fieldGroup,title=title,fg_class=fg_class,schemaAPI=self)
    
    def SchemaManager(self,schema:Union[dict,str],fieldGroups:list=None) -> 'SchemaManager':
         """
         Generates a Schema Manager instance using the information provided by the schema instance.
         Arguments:
            schema : OPTIONAL : the schema definition as dictionary OR the ID to access it OR Nothing if you want to start from scratch
            fieldGroups : OPTIONAL : If you wish to add a list of fieldgroups.
            fgManager : OPTIONAL : If you wish to handle the different field group passed into a Field Group Manager instance and have additional methods available.
         """
         from .schemamanager import SchemaManager
         return SchemaManager(schema=schema,fieldGroups=fieldGroups,schemaAPI=self)

    def DataTypeManager(self,dataType:Union[dict,str])->'DataTypeManager':
        """
        Generates a Data Type Manager instance using the information provided by the schema instance.
        Arguments:
            dataType : OPTIONAL : The data Type definition, the reference Id or nothing if you want to start from scratch.
        """
        from .datatypemanager import DataTypeManager
        return DataTypeManager(dataType=dataType,schemaAPI=self)

    def compareDFschemas(self,df1,df2,**kwargs)->dict:
        """
        Compare 2 schema dataframe returned by the SchemaManager `to_dataframe` method.
        Arguments:
            df1 : REQUIRED : the first schema dataframe to compare
            df2 : REQUIRED : the second schema dataframe to compare
        possible keywords:
            title1 : title of the schema used in the dataframe 1 (default df1)
            title2 : title of the schema used in the dataframe 2 (default df2)
        The title1 and title2 will be used instead of df1 or df2 in the results keys presented below.

        Results: 
            Results are stored in a dictionary with these keys:
            - df1 (or title1) : copy of the dataframe 1 passed
            - df2 (or title2) : copy of the dataframe 2 passed
            - fielgroups: dictionary containing
                - aligned : boolean to define if the schema dataframes contain the same field groups
                - df1_missingFieldGroups : tuple of field groups missing on df1 compare to df2
                - df2_missingFieldGroups : tuple of field groups missing on df2 compare to df1
            - paths: dictionary containing
                - aligned : boolean to define if the schema dataframes contain the same fields.
                - df1_missing : tuple of the paths missing in df1 compare to df2
                - df2_missing : tuple of the paths missing in df2 compare to df1
            - type_issues: list of all the paths that are not of the same type in both schemas.
        """
        if type(df1) != pd.DataFrame or type(df2) != pd.DataFrame:
            raise TypeError('Require dataframes to be passed')
        if 'path' not in df1.columns or 'type' not in df1.columns or 'fieldGroup' not in df1.columns:
            raise AttributeError('Your data frame 1 is incomplete, it does not contain one of the following columns : path, type, fieldGroup')
        if 'path' not in df2.columns or 'type' not in df2.columns or 'fieldGroup' not in df2.columns:
            raise AttributeError('Your data frame 2 is incomplete, it does not contain one of the following columns : path, type, fieldGroup')
        name1 = kwargs.get('title1','df1')
        name2 = kwargs.get('title2','df2')
        dict_result = {f'{name1}':df1.copy(),f'{name2}':df2.copy()}
        fieldGroups1 = tuple(sorted(df1.fieldGroup.unique()))
        fieldGroups2 = tuple(sorted(df2.fieldGroup.unique()))
        if fieldGroups1 == fieldGroups2:
            dict_result['fieldGroups'] = {'aligned':True}
        else:
            dict_result['fieldGroups'] = {'aligned':False}
            dict_result['fieldGroups'][f'{name1}_missingFieldGroups'] = tuple(set(fieldGroups2).difference(set(fieldGroups1)))
            dict_result['fieldGroups'][f'{name2}_missingFieldGroups'] = tuple(set(fieldGroups1).difference(set(fieldGroups2)))
        path_df1 = tuple(sorted(df1.path.unique()))
        path_df2 = tuple(sorted(df2.path.unique()))
        if path_df1 == path_df2:
            dict_result['paths'] = {'aligned':True}
        else:
            dict_result['paths'] = {'aligned':False}
            list_path_missing_from_df2 = list(set(path_df2).difference(set(path_df1)))
            list_path_missing_from_df1 = tuple(set(path_df1).difference(set(path_df2)))
            dict_result['paths'][f'{name1}_missing'] = df2[df2["path"].isin(list_path_missing_from_df2)]
            dict_result['paths'][f'{name2}_missing'] = df1[df1["path"].isin(list_path_missing_from_df1)]
        common_paths = tuple(set(path_df2).intersection(set(path_df1)))
        dict_result['type_issues'] = [] 
        for path in common_paths:
            if df1[df1['path'] == path]['type'].values[0] != df2[df2['path'] == path]['type'].values[0]:
                dict_result['type_issues'].append(path)
        return dict_result


    def createB2Bschemas(self,**kwargs)->dict:
        """
        Create the B2B schemas for a sandbox with their different relationships if they do not exist.
        Note: You need to have created the B2B identities before
        Schema created:
            - B2B Account Person Relation
            - B2B Activity
            - B2B Marketing List Member
            - B2B Marketing List
            - B2B Campaign Member
            - B2B Campaign
            - B2B Opportunity Person Relation
            - B2B Opportunity
            - B2B Person
            - B2B Account
        The schemas are created with their descriptors (relationships and identities)
        returns a dictionary of B2B schema name and their schemaManager instances
        possible kwargs:
            debug : boolean to print statement while the script is working
        """
        debug = kwargs.get('debug',False)
        list_existing_schemas = self.getSchemas()
        existing_titles = [el['title'] for el in list_existing_schemas]
        list_b2b_schema_names = ['B2B Account Person Relation',
                                'B2B Activity',
                                'B2B Marketing List Member',
                                'B2B Marketing List',
                                'B2B Campaign Member',
                                'B2B Campaign',
                                'B2B Opportunity Person Relation',
                                'B2B Opportunity',
                                'B2B Person',
                                'B2B Account']
        list_schema_manager = []
        for schemaName in list_b2b_schema_names:
            if schemaName not in existing_titles:
                res = self.__createB2BSchema__(schemaName,debug=debug)
                list_schema_manager.append(res)
            else:
                res = self.__createB2BSchema__(schemaName,schemaId=self.data.schemas_id[schemaName],debug=debug)
                list_schema_manager.append(res)
        dict_schema_id_name = {scManager.id:scManager.title for scManager in list_schema_manager}
        dict_existing_descriptors = {}
        for scManager in list_schema_manager:
            tmp_list_descs = scManager.getDescriptors()
            list_prepared_descriptors = []
            for desc in tmp_list_descs: ## filtering for relationships only
                if desc['@type'] == 'xdm:descriptorOneToOne':
                    data = {
                        '@type':desc['@type'],
                        'xdm:sourceProperty':desc['xdm:sourceProperty'],
                        'xdm:sourceSchema':dict_schema_id_name[desc['xdm:sourceSchema']],
                        'xdm:destinationProperty': desc['xdm:destinationProperty'],
                        'xdm:destinationSchema':dict_schema_id_name[desc['xdm:destinationSchema']],
                        }
                    list_prepared_descriptors.append(data)
                elif desc['@type'] == 'xdm:descriptorRelationship':
                    data = {
                        '@type':desc['@type'],
                        'xdm:sourceProperty':desc['xdm:sourceProperty'],
                        'xdm:sourceSchema':dict_schema_id_name[desc['xdm:sourceSchema']],
                        'xdm:destinationProperty': desc['xdm:destinationProperty'],
                        'xdm:destinationSchema':dict_schema_id_name[desc['xdm:destinationSchema']],
                        'xdm:cardinality': desc['xdm:cardinality'],
                        'xdm:sourceToDestinationTitle': desc['xdm:sourceToDestinationTitle'],
                        'xdm:destinationToSourceTitle': desc['xdm:destinationToSourceTitle'],
                        }
                    list_prepared_descriptors.append(data)
            dict_existing_descriptors[scManager.title] = list_prepared_descriptors
        tmp_schemas = self.getSchemas() ## refresh the self.data.schema_id cache
        dict_new_relationships = {}
        for key,value in dict_existing_descriptors.items():
            dict_new_relationships[key] = self.__createB2Brelationships__(schemaName=key,schemaDescriptors=value,debug=debug)
        return {sc.title:sc for sc in list_schema_manager}
    
    def __createB2BSchema__(self,schemaName:str=None,schemaId:str=None,debug:bool=False)->dict:
        """
        Create a B2B schema.
        Arguments:
            * schema name : name of the schema
            * schemaId : ID of the schema if it exists
        """
        from aepp import schemamanager
        match schemaName:
            case 'B2B Account Person Relation':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_account_person = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/classes/account-person')
                    b2b_account_person.addFieldGroup('https://ns.adobe.com/xdm/context/identitymap')
                    resSchema = b2b_account_person.createSchema()
                    list_descriptors = []
                else:
                    b2b_account_person = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_account_person.getDescriptors()
                list_to_create = [
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/accountKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_account',
                    'xdm:sourceSchema': b2b_account_person.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/personKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_person',
                    'xdm:sourceSchema': b2b_account_person.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/accountPersonKey/sourceKey',
                    'xdm:namespace': 'b2b_account_person_relation',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_account_person.id,
                    'xdm:sourceVersion': 1
                    }
                ]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_account_person,debug=debug)
                return b2b_account_person
            case 'B2B Activity':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_activity = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/context/experienceevent')
                    list_fieldGroupsIds = ['https://ns.adobe.com/xdm/mixins/events/remove-from-list', 'https://ns.adobe.com/xdm/mixins/events/visit-webpage','https://ns.adobe.com/xdm/mixins/person-identifier', 'https://ns.adobe.com/xdm/mixins/events/new-lead', 'https://ns.adobe.com/xdm/mixins/events/convert-lead', 'https://ns.adobe.com/xdm/mixins/events/add-to-list', 'https://ns.adobe.com/xdm/mixins/events/add-to-opportunity', 'https://ns.adobe.com/xdm/mixins/events/remove-from-opportunity', 'https://ns.adobe.com/xdm/mixins/events/interesting-moment', 'https://ns.adobe.com/xdm/mixins/events/formfilledout', 'https://ns.adobe.com/xdm/mixins/events/linkclicks', 'https://ns.adobe.com/xdm/mixins/events/emaildelivered', 'https://ns.adobe.com/xdm/mixins/events/emailbounced',
                                        'https://ns.adobe.com/xdm/mixins/events/emailunsubscribed', 'https://ns.adobe.com/xdm/mixins/events/emailopened', 'https://ns.adobe.com/xdm/mixins/events/emailclicked', 'https://ns.adobe.com/xdm/mixins/events/emailbouncedsoft', 'https://ns.adobe.com/xdm/mixins/events/scorechanged', 'https://ns.adobe.com/xdm/mixins/events/opportunityupdated', 'https://ns.adobe.com/xdm/mixins/events/statusincampaignprogressionchanged', 'https://ns.adobe.com/xdm/mixins/events/callwebhook', 'https://ns.adobe.com/xdm/mixins/events/change-campaign-cadence', 'https://ns.adobe.com/xdm/mixins/events/add-to-campaign', 'https://ns.adobe.com/xdm/mixins/events/change-campaign-stream', 'https://ns.adobe.com/xdm/mixins/events/revenueStageChanged', 'https://ns.adobe.com/xdm/mixins/events/emailsent', 'https://ns.adobe.com/xdm/mixins/events/merge-leads',
                                        'https://ns.adobe.com/xdm/mixins/events/engaged-with-dialogue', 'https://ns.adobe.com/xdm/mixins/events/interacted-with-document-in-dialogue', 'https://ns.adobe.com/xdm/mixins/events/engaged-with-agent-in-dialog', 'https://ns.adobe.com/xdm/mixins/events/engaged-with-conversational-flow', 'https://ns.adobe.com/xdm/mixins/events/interacted-with-document-in-conversational-flow', 'https://ns.adobe.com/xdm/mixins/events/engaged-with-agent-in-conversational-flow', 'https://ns.adobe.com/xdm/mixins/events/responded-to-poll-in-webinar', 'https://ns.adobe.com/xdm/mixins/events/call-to-action-clicked-in-webinar', 'https://ns.adobe.com/xdm/mixins/events/asset-downloads-in-webinar', 'https://ns.adobe.com/xdm/mixins/events/asks-questions-in-webinar']
                    for fg in list_fieldGroupsIds:
                        b2b_activity.addFieldGroup(fg)
                    resSchema = b2b_activity.createSchema()
                    list_descriptors = []
                else: 
                    b2b_activity = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_activity.getDescriptors()
                list_to_create = [
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/leadOperation/campaignProgression/campaignKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_campaign',
                    'xdm:sourceSchema': b2b_activity.id,
                    'xdm:sourceVersion': 1
                    },
                    {
                    '@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/opportunityEvent/opportunityKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_opportunity',
                    'xdm:sourceSchema': b2b_activity.id,
                    'xdm:sourceVersion': 1
                    },
                    {
                    '@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/listOperations/listKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_marketing_list',
                    'xdm:sourceSchema': b2b_activity.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/personKey/sourceKey',
                    'xdm:namespace': 'b2b_person',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_activity.id,
                    'xdm:isPrimary': True,
                    'xdm:sourceVersion': 1
                    }
                ]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_activity,debug=debug)
                return b2b_activity
            case 'B2B Marketing List Member':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_marketing_member = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/classes/marketing-list-member')
                    resSchema = b2b_marketing_member.createSchema()
                    list_descriptors = []
                else: 
                    b2b_marketing_member = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_marketing_member.getDescriptors()
                list_to_create = [
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/marketingListKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_marketing_list',
                    'xdm:sourceSchema': b2b_marketing_member.id,
                    'xdm:sourceVersion': 1
                    },
                    {
                    '@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/personKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_person',
                    'xdm:sourceSchema': b2b_marketing_member.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/marketingListMemberKey/sourceKey',
                    'xdm:namespace': 'b2b_marketing_list_member',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_marketing_member.id,
                    'xdm:isPrimary': True,
                    'xdm:sourceVersion': 1
                    }
                ]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_marketing_member,debug=debug)
                return b2b_marketing_member
            case 'B2B Marketing List':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_marketing_memberList = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/classes/marketing-list')
                    resSchema = b2b_marketing_memberList.createSchema()
                    list_descriptors = []
                else: 
                    b2b_marketing_memberList = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_marketing_memberList.getDescriptors()
                list_to_create = [{
                    '@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/marketingListKey/sourceKey',
                    'xdm:namespace': 'b2b_marketing_list',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_marketing_memberList.id,
                    'xdm:isPrimary': True,
                    'xdm:sourceVersion': 1
                }]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_marketing_memberList,debug=debug)
                return b2b_marketing_memberList
            case 'B2B Campaign Member':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_campaign_member = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/context/campaign-member')
                    b2b_campaign_member.addFieldGroup('https://ns.adobe.com/xdm/context/campaign-member-details')
                    resSchema = b2b_campaign_member.createSchema()
                    list_descriptors = []
                else:
                    b2b_campaign_member = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_campaign_member.getDescriptors()
                list_to_create = [
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/campaignKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_campaign',
                    'xdm:sourceSchema': b2b_campaign_member.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/extSourceSystemAudit/externalKey/sourceKey',
                    'xdm:namespace': 'b2b_campaign_member',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_campaign_member.id,
                    'xdm:isPrimary': False,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/personKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_person',
                    'xdm:sourceSchema': b2b_campaign_member.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/campaignMemberKey/sourceKey',
                    'xdm:namespace': 'b2b_campaign_member',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_campaign_member.id,
                    'xdm:isPrimary': True,
                    'xdm:sourceVersion': 1
                    }
                ]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_campaign_member,debug=debug)
                return b2b_campaign_member
            case 'B2B Campaign':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_campaign = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/classes/campaign')
                    b2b_campaign.addFieldGroup('https://ns.adobe.com/xdm/mixins/campaign-details')
                    resSchema = b2b_campaign.createSchema()
                    list_descriptors = []
                else:
                    b2b_campaign = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_campaign.getDescriptors()
                list_to_create = [
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/extSourceSystemAudit/externalKey/sourceKey',
                    'xdm:namespace': 'b2b_campaign',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_campaign.id,
                    'xdm:isPrimary': False,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/campaignKey/sourceKey',
                    'xdm:namespace': 'b2b_campaign',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_campaign.id,
                    'xdm:isPrimary': True,
                    'xdm:sourceVersion': 1
                    }
                ]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_campaign,debug=debug)
                return b2b_campaign
            case 'B2B Opportunity Person Relation':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_opp_person = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/classes/opportunity-person')
                    resSchema = b2b_opp_person.createSchema()
                    list_descriptors = []
                else:
                    b2b_opp_person = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_opp_person.getDescriptors()
                list_to_create = [
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/opportunityKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_opportunity',
                    'xdm:sourceSchema': b2b_opp_person.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/personKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_person',
                    'xdm:sourceSchema': b2b_opp_person.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/extSourceSystemAudit/externalKey/sourceKey',
                    'xdm:namespace': 'b2b_opportunity_person_relation',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_opp_person.id,
                    'xdm:isPrimary': False,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/opportunityPersonKey/sourceKey',
                    'xdm:namespace': 'b2b_opportunity_person_relation',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_opp_person.id,
                    'xdm:isPrimary': True,
                    'xdm:sourceVersion': 1
                    }
                ]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_opp_person,debug=debug)
                return b2b_opp_person
            case 'B2B Opportunity':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_opportunity = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/context/opportunity')
                    b2b_opportunity.addFieldGroup('https://ns.adobe.com/xdm/mixins/opportunity-details')
                    resSchema = b2b_opportunity.createSchema()
                    list_descriptors = []
                else:
                    b2b_opportunity = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_opportunity.getDescriptors()
                list_to_create = [
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/accountKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_account',
                    'xdm:sourceSchema': b2b_opportunity.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/extSourceSystemAudit/externalKey/sourceKey',
                    'xdm:namespace': 'b2b_opportunity',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_opportunity.id,
                    'xdm:isPrimary': False,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/opportunityKey/sourceKey',
                    'xdm:namespace': 'b2b_opportunity',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_opportunity.id,
                    'xdm:isPrimary': True,
                    'xdm:sourceVersion': 1
                    }
                ]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_opportunity,debug=debug)
                return b2b_opportunity
            case 'B2B Person':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_person = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/context/profile')
                    b2b_person.addFieldGroup('https://ns.adobe.com/xdm/mixins/b2b-person-details')
                    b2b_person.addFieldGroup('https://ns.adobe.com/xdm/mixins/b2b-person-components')
                    b2b_person.addFieldGroup('https://ns.adobe.com/xdm/context/identitymap')
                    b2b_person.addFieldGroup('https://ns.adobe.com/xdm/mixins/profile-consents')
                    resSchema = b2b_person.createSchema()
                    list_descriptors = []
                else:
                    b2b_person = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_person.getDescriptors()
                list_to_create = [
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/workEmail/address',
                    'xdm:namespace': 'Email',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_person.id,
                    'xdm:isPrimary': False,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/extSourceSystemAudit/externalKey/sourceKey',
                    'xdm:namespace': 'b2b_person',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_person.id,
                    'xdm:isPrimary': False,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/b2b/personKey/sourceKey',
                    'xdm:namespace': 'b2b_person',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_person.id,
                    'xdm:isPrimary': True,
                    'xdm:sourceVersion': 1
                    }
                ]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_person,debug=debug)
                return b2b_person
            case 'B2B Account':
                if debug:
                    print(f"Handling : {schemaName}")
                if schemaId is None:
                    b2b_account = schemamanager.SchemaManager(title=schemaName,schemaAPI=self,schemaClass='https://ns.adobe.com/xdm/context/account')
                    b2b_account.addFieldGroup('https://ns.adobe.com/xdm/mixins/account-details')
                    resSchema = b2b_account.createSchema()
                    list_descriptors = []
                else:
                    b2b_account = schemamanager.SchemaManager(schemaId,schemaAPI=self)
                    list_descriptors = b2b_account.getDescriptors()
                list_to_create = [
                    {'@type': 'xdm:descriptorReferenceIdentity',
                    'xdm:sourceProperty': '/accountParentKey/sourceKey',
                    'xdm:identityNamespace': 'b2b_account',
                    'xdm:sourceSchema': b2b_account.id,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/extSourceSystemAudit/externalKey/sourceKey',
                    'xdm:namespace': 'b2b_account',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_account.id,
                    'xdm:isPrimary': False,
                    'xdm:sourceVersion': 1
                    },
                    {'@type': 'xdm:descriptorIdentity',
                    'xdm:sourceProperty': '/accountKey/sourceKey',
                    'xdm:namespace': 'b2b_account',
                    'xdm:property': 'xdm:code',
                    'xdm:sourceSchema': b2b_account.id,
                    'xdm:isPrimary': True,
                    'xdm:sourceVersion': 1
                    }
                ]
                self.__createIdentityDescriptors__(list_to_create,list_descriptors,b2b_account,debug=debug)
                return b2b_account
    
    def __createIdentityDescriptors__(self,listToCreate:list=None,existingList:list=None,scManager:'SchemaManager'=None,debug:bool=False)->None:
        """
        Itirate over the element to create the related identities
        Arguments:
            listToCreate : list of dictionary of element to create
            existingList : list of existing descriptors
            scManager : SchemaManager associated with the schema
        """
        for elToCreate in listToCreate:
            res = None
            if len(existingList)>0: ## comparing only if comparison possible
                if elToCreate['xdm:sourceProperty'] not in [el.get('xdm:sourceProperty','') for el in existingList]:
                    ## creating the missing identities
                    res = scManager.createDescriptor(elToCreate)
            else:
                res = scManager.createDescriptor(elToCreate)
            if debug and res is not None:
                print(res)

    def __createB2Brelationships__(self,schemaName:str=None,schemaDescriptors:list=None,debug:bool=False)->list:
        """
        Create the relationship between the B2B schemas.
        Arguments:
            schemaName : name of the schema
            schemaDescriptors : list of existing descriptors
        """
        dict_desc_to_create = {'B2B Account': [{'@type': 'xdm:descriptorOneToOne',
            'xdm:sourceProperty': '/accountParentKey/sourceKey',
            'xdm:sourceSchema': 'B2B Account',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/accountKey/sourceKey',
            'xdm:destinationSchema': 'B2B Account',
            'xdm:destinationVersion':1,}],
        'B2B Person': [{'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/personComponents[*]/sourceAccountKey/sourceKey',
            'xdm:sourceSchema': 'B2B Person',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/accountKey/sourceKey',
            'xdm:destinationSchema': 'B2B Account',
            'xdm:destinationVersion':1,
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'Account',
            'xdm:destinationToSourceTitle': 'People'}],
        'B2B Opportunity': [{'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/accountKey/sourceKey',
            'xdm:sourceSchema': 'B2B Opportunity',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/accountKey/sourceKey',
            'xdm:destinationSchema': 'B2B Account',
            'xdm:destinationVersion':1,
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'Account',
            'xdm:destinationToSourceTitle': 'Opportunities'}],
        'B2B Opportunity Person Relation': [{'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/opportunityKey/sourceKey',
            'xdm:sourceSchema': 'B2B Opportunity Person Relation',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/opportunityKey/sourceKey',
            'xdm:destinationSchema': 'B2B Opportunity',
            'xdm:destinationVersion':1,
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'Opportunity',
            'xdm:destinationToSourceTitle': 'People'},
            {'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/personKey/sourceKey',
            'xdm:sourceVersion':1,
            'xdm:sourceSchema': 'B2B Opportunity Person Relation',
            'xdm:destinationProperty': '/b2b/personKey/sourceKey',
            'xdm:destinationSchema': 'B2B Person',
            'xdm:destinationVersion':1,
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'Person',
            'xdm:destinationToSourceTitle': 'Opportunities'}],
        'B2B Campaign': [],
        'B2B Campaign Member': [{'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/campaignKey/sourceKey',
            'xdm:sourceSchema': 'B2B Campaign Member',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/campaignKey/sourceKey',
            'xdm:destinationSchema': 'B2B Campaign',
            'xdm:destinationVersion':1,
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'Campaign',
            'xdm:destinationToSourceTitle': 'People'},
            {'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/personKey/sourceKey',
            'xdm:sourceSchema': 'B2B Campaign Member',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/b2b/personKey/sourceKey',
            'xdm:destinationSchema': 'B2B Person',
            'xdm:destinationVersion':1,
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'Person',
            'xdm:destinationToSourceTitle': 'Campaigns'}],
        'B2B Marketing List': [],
        'B2B Marketing List Member': [{'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/marketingListKey/sourceKey',
            'xdm:sourceSchema': 'B2B Marketing List Member',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/marketingListKey/sourceKey',
            'xdm:destinationSchema': 'B2B Marketing List',
            'xdm:destinationVersion':1,
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'List',
            'xdm:destinationToSourceTitle': 'People'},
            {'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/personKey/sourceKey',
            'xdm:sourceSchema': 'B2B Marketing List Member',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/b2b/personKey/sourceKey',
            'xdm:destinationSchema': 'B2B Person',
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'Person',
            'xdm:destinationToSourceTitle': 'Lists',
            'xdm:destinationVersion':1,}],
        'B2B Activity': [{'@type': 'xdm:descriptorOneToOne',
            'xdm:sourceProperty': '/leadOperation/campaignProgression/campaignKey/sourceKey',
            'xdm:sourceSchema': 'B2B Activity',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/campaignKey/sourceKey',
            'xdm:destinationSchema': 'B2B Campaign',
            'xdm:destinationVersion':1,},
            {'@type': 'xdm:descriptorOneToOne',
            'xdm:sourceProperty': '/opportunityEvent/opportunityKey/sourceKey',
            'xdm:sourceSchema': 'B2B Activity',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/opportunityKey/sourceKey',
            'xdm:destinationSchema': 'B2B Opportunity',
            'xdm:destinationVersion':1,},
            {'@type': 'xdm:descriptorOneToOne',
            'xdm:sourceProperty': '/listOperations/listKey/sourceKey',
            'xdm:sourceSchema': 'B2B Activity',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/marketingListKey/sourceKey',
            'xdm:destinationSchema': 'B2B Marketing List',
            'xdm:destinationVersion':1,}],
        'B2B Account Person Relation': [{'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/accountKey/sourceKey',
            'xdm:sourceSchema': 'B2B Account Person Relation',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/accountKey/sourceKey',
            'xdm:destinationSchema': 'B2B Account',
            'xdm:destinationVersion':1,
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'Account',
            'xdm:destinationToSourceTitle': 'Account-Person'},
            {'@type': 'xdm:descriptorRelationship',
            'xdm:sourceProperty': '/personKey/sourceKey',
            'xdm:sourceSchema': 'B2B Account Person Relation',
            'xdm:sourceVersion':1,
            'xdm:destinationProperty': '/b2b/personKey/sourceKey',
            'xdm:destinationSchema': 'B2B Person',
            'xdm:destinationVersion':1,
            'xdm:cardinality': 'M:1',
            'xdm:sourceToDestinationTitle': 'Account-Person',
            'xdm:destinationToSourceTitle': 'Account'}]
        }
        to_create = dict_desc_to_create[schemaName] ## select the correct descriptor based on the schema.
        existing = schemaDescriptors
        new_state_existing = []
        if debug:
            print(f'Handling relationships for {schemaName}')
        for descriptor in to_create:
            if len(existing)>0:
                if descriptor['xdm:sourceProperty'] in [el.get('xdm:sourceProperty') for el in existing]:
                    new_state_existing.append([el for el in existing if el.get('xdm:sourceProperty') == descriptor['xdm:sourceProperty']][0])
                else: ### the descriptor sourceProperty does not exist in the list of descriptor
                    descriptor['xdm:sourceSchema'] = self.data.schemas_id[descriptor['xdm:sourceSchema']] ## replacing name with ID
                    descriptor['xdm:destinationSchema'] = self.data.schemas_id[descriptor['xdm:destinationSchema']] ## replacing name with ID
                    res = self.createDescriptor(descriptorObj=descriptor)
                    new_state_existing.append(res)
            else:
                descriptor['xdm:sourceSchema'] = self.data.schemas_id[descriptor['xdm:sourceSchema']] ## replacing name with ID
                descriptor['xdm:destinationSchema'] = self.data.schemas_id[descriptor['xdm:destinationSchema']] ## replacing name with ID
                res = self.createDescriptor(descriptorObj=descriptor)
                new_state_existing.append(res)
        if debug:
            print(f'Relationships for {schemaName} : {new_state_existing}')
        return new_state_existing

            
    