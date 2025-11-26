#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

import aepp
from aepp import connector
from copy import deepcopy
import logging
from typing import Union
from .configs import ConnectObject
import json

class Identity:
    """
    Class to manage and retrieve Identity information.
    #!acpdr/swagger-specs/id-service-api.yaml
    This is based on the following API reference : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
    """

    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(
        self,
        region: str = "nld2",
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ):
        """
        Require a region.
        By default, the NLD2 will be selected. (other choice : "va7","aus5", "can2", "ind2")
        Additional kwargs will update the header.
        more info : https://docs.adobe.com/content/help/en/experience-platform/identity/api/getting-started.html
        Arguments:
            region : REQUIRED : either nld2 (default) or "va7" or "aus5 or "can2" or "ind2"
            loggingObject : OPTIONAL : logging object to log messages.
            config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
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
        self.header.update(**kwargs)
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]

        environment = config["environment"]
        base_url = f"https://platform-{region}.adobe.io"

        if environment != "prod":
            base_url = f"https://platform-{environment}-{region}.adobe.io"

        # Construct the endpoint
        self.endpoint = base_url + aepp.config.endpoints["identity"]

    def __str__(self):
        return json.dumps({'class':'Identity','region':self.region,'sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)
    
    def __repr__(self):
        return json.dumps({'class':'Identity','region':self.region,'sandbox':self.sandbox,'clientId':self.connector.config.get("client_id"),'orgId':self.connector.config.get("org_id")},indent=2)

    def getIdentity(
        self, id_str: str = None, nsid: str = None, namespace: str = None
    ) -> dict:
        """
        Given the namespace and an ID in that namespace, returns XID string.
        Arguments:
            id_str : REQUIRED : Id in given namespace (ECID value)
            nsid : REQUIRED : namespace id. (e.g. 411)
            namespace : OPTIONAL : namespace code (e.g. adcloud)
        """
        if id_str is None or (namespace is None and nsid is None):
            raise Exception(
                "Expecting that id_str and (namespace or nsid) arguments to be filled."
            )
        if self.loggingEnabled:
            self.logger.debug(f"Starting getIdentity")
        params = {"id": id_str}
        if nsid is not None:
            params["nsid"] = nsid
        if namespace is not None:
            params["namespace"] = namespace
        path = "/identity/identity"
        privateHeader = deepcopy(self.header)
        privateHeader["Accept"] = "application/json"
        privateHeader["x-uis-cst-ctx"] = "stub"
        res = self.connector.getData(
            self.endpoint + path, headers=privateHeader, params=params
        )
        return res

    def getIdentities(self, only_custom: bool = False, save: bool = False) -> list:
        """
        Get the list of all identity namespaces available in the organization.
        Arguments:
            only_custom : OPTIONAL : if set to True, return only customer made identities (default False)
            save : OPTIONAL : if set to True, save the result in its respective folder (default False)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getIdentities")
        path = "/idnamespace/identities"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        if only_custom:
            res = [identity for identity in res if identity["custom"] == True]
        if save:
            aepp.saveFile(
                module="identity", file=res, filename="identities", type_file="json"
            )
        return res

    def getIdentityDetail(self, id_str: str = None, save: bool = False) -> dict:
        """
        List details of a specific identity namespace by its ID.
        Arguments:
            id_str : REQUIRED : identity of the "id" field.
            save : OPTIONAL : if set to True, save the result in a file, in its respective folder (default False)
        """
        if id_str is None:
            raise Exception("Expected an id for the Identity")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getIdentityDetail")
        path = f"/idnamespace/identities/{id_str}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        if save:
            filename = f"identity_{res['code']}"
            aepp.saveFile(
                module="identity", file=res, filename=filename, type_file="json"
            )
        return res

    def createIdentity(
        self,
        name: str = None,
        code: str = None,
        idType: str = None,
        description: str = None,
        dict_identity: dict = None,
    ) -> dict:
        """
        List details of a specific identity namespace by its ID.
        Arguments:
            name : REQUIRED : Display name of the identity
            code : REQUIRED : Identity Symbol for user interface.
            idType : REQUIRED : one of those : COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE or PHONE.
            description : OPTIONAL : description for this identity
            dict_identity : OPTIONAL : you can use this to directly pass the dictionary.
        """
        creation_dict = {}
        if dict_identity is None:
            if name is None or code is None or idType is None:
                raise Exception("Expecting that name, code and idType to be filled with value")
            creation_dict["name"] = name
            creation_dict["code"] = code
            creation_dict["idType"] = idType
            if description is not None:
                creation_dict["description"] = description
            if " " in code:
                raise TypeError("code can only contain one word with letter and numbers")
            if idType not in [
                "COOKIE",
                "CROSS_DEVICE",
                "DEVICE",
                "EMAIL",
                "MOBILE",
                "NON_PEOPLE",
                "PHONE",
            ]:
                raise TypeError(
                    "idType could only be one of those : COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE, PHONE"
                )
            if self.loggingEnabled:
                self.logger.debug(f"Starting createIdentity")
        else: ## if you want to pass the dictionary directly
            creation_dict = deepcopy(dict_identity)
        path = "/idnamespace/identities"
        res = self.connector.postData(
            self.endpoint + path, headers=self.header, data=creation_dict
        )
        return res
    
    def getLinkedIdentities(self,xids:dict|list=None,projectionType:str="set",aam:bool=False,edgeMeta:bool=False,**kwargs)->dict:
        """
        Given set of identities, returns all linked identities in the graph corresponding to each identity.
        Arguments:
            xids : REQUIRED : A single or a list of xid composite such as: 
                {'nsid':'mynsid','id':'myid','ns':'mynamespace'}
            projectionType : OPTIONAL : This define the format returned. Default is "set". Possible : "graph"
            aam : OPTIONAL : Boolean that cannot be used with graph type. Default False.
            edgeMeta : OPTIONAL : This is and optional field that is used to add edge meta data in the response, such as dataset_ids and batch_ids. 
                    It will only apply if the requested projection_type is graph.
        """
        if xids is None:
            raise Exception("Cannot process the request without Xid")
        if type(xids) == str:
            xids = list(xids)
        if self.loggingEnabled:
            self.logger.debug(f"Starting getLinkedIdentities")
        path = "/identity/v2/graph"
        data = {}
        data["composite_xid"] = xids
        data['projection_type'] = projectionType
        data['aam_properties'] = {'return_data_sources':aam}
        data['require_edge_meta_data'] = edgeMeta
        if len(kwargs)>0:
            for key, value in kwargs.items():
                if key in ['graph_type','traverse','filter']:
                    data[key] = value
        res = self.connector.postData(self.endpoint+path, data=data)
        return res

    def updateIdentity(
        self,
        id_str: str = None,
        name: str = None,
        code: str = None,
        idType: str = None,
        description: str = None,
    ) -> dict:
        """
        Update identity based on its ID.
        Arguments:
            id_str: REQUIRED : ID of the identity namespace to update.
            name : REQUIRED : Display name of the identity
            code : REQUIRED : Identity Symbol for user interface.
            idType : REQUIRED : one of those : COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE or PHONE.
            description : OPTIONAL : description for this identity
        """
        if id_str is None:
            raise Exception("Require an id")
        if name is None or code is None or idType is None:
            raise Exception(
                "Expecting that name, code and idType to be filled with value"
            )
        if idType not in [
            "COOKIE",
            "CROSS_DEVICE",
            "DEVICE",
            "EMAIL",
            "MOBILE",
            "NON_PEOPLE",
            "PHONE",
            "B2B_OPPORTUNITY",
            "B2B_OPPORTUNITY_PERSON",
            "B2B_CAMPAIGN",
            "B2B_CAMPAIGN_MEMBER",
            "B2B_MARKETING_LIST",
            "B2B_MARKETING_LIST_MEMBER",
            "B2B_ACCOUNT_PERSON",
            "B2B_ACCOUNT"
        ]:
            raise TypeError(
                "idType could only be one of those : COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE, PHONE"
            )
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateIdentity")
        path = f"/idnamespace/identities/{id_str}"
        data = {
            "name": name,
            "code": code,
            "idType": idType,
            "description": description,
        }
        res = self.connector.putData(
            self.endpoint + path, headers=self.header, data=data
        )
        return res

    def getIdentitiesIMS(self, imsOrg: str = None) -> list:
        """
        Returns all identities from the IMS Org itself.
        Only shared ones if IMS Org doesn't match the IMS Org sent in the header.
        Arguments:
            imsOrg : OPTIONAL : the IMS org. If not set, takes the current one automatically.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getIdentitiesIMS")
        ims_org = imsOrg or self.connector.config["org_id"]
        path = f"/idnamespace/orgs/{ims_org}/identities"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res


    def getIdentityMapping(
        self,
        xid: str = None,
        targetNs: int = None,
        nsid: int = 411,
        namespace: str = "adcloud",
        id_value: str = None,
        graphType: str = "private",
    ) -> dict:
        """
        Given an XID, returns all XID mappings in the requested namespace (targetNs).
        It is required to pass either xid or (namespace/nsid & id) pair to get mappings in required namespace.
        Arguments:
            xid : REQUIRED : Identity string returns by the getIdentity method.
            nsid : OPTIONAL : namespace id (default : 411)
            namespace : OPTIONAL : namespace code. (default : adcloud)
            id_value : OPTIONAL : ID of the customer in given namespace.
            graphType : OPTIONAL : Graph type (output type) you want to get the cluster from. (default private)
            targetNs : OPTIONAL : The namespace you want to get the mappings from.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getIdentityMapping")
        temp_header = deepcopy(self.header)
        temp_header["Accept"] = "application/vnd.adobe.identity+json;version=1.2"
        temp_header["x-uis-cst-ctx"] = "stub"
        path = "/identity/mapping"
        params = {}
        if xid is not None:
            params["xid"] = xid
            params["graph-type"] = graphType
            params["targetNs"] = targetNs
            res = self.connector.getData(
                self.endpoint + path, params=params, headers=temp_header
            )
            return res
        elif xid is None and id_value is not None:
            params["nsid"] = nsid
            params["namespace"] = namespace
            params["id"] = id_value
            params["targetNs"] = targetNs
            params["graph-type"] = graphType
            res = self.connector.getData(
                self.endpoint + path, params=params, headers=temp_header
            )
            return res

    def postIdentityMapping(
        self, xids: list = None, targetNs: int = 411, version: float = 1.0
    ) -> dict:
        """
        Given an identity, returns all identity mappings in requested namespace (target namespace).
        Arguments:
            xids : REQUIRED : List of identities
            targetNs : REQUIRED : Target Namespace (default 411)
            version : OPTIONAL : version of the mapping
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting postIdentityMapping")
        temp_header = deepcopy(self.header)
        temp_header["Accept"] = "application/vnd.adobe.identity+json;version=1.2"
        temp_header["x-uis-cst-ctx"] = "stub"
        path = "/identity/mapping"
        if type(xids) != list:
            raise TypeError("xids must be of type list")
        list_body = [
            {"xid": [{"xid": xid}], "version": version, "targetNs": targetNs}
            for xid in xids
        ]
        res = self.connector.postData(
            self.endpoint + path, data=list_body, headers=temp_header
        )
        return res

    def createB2BIdentities(self)->list:
        """
        Create the following identities if they do not exist:
            b2b_account
            b2b_account_person_relation
            b2b_marketing_list_member
            b2b_marketing_list
            b2b_campaign_member
            b2b_campaign
            b2b_opportunity_person_relation
            b2b_opportunity
            b2b_person

        It will return the list of the newly created identities
        """
        list_new_identities = [
            {
                'code': 'b2b_person',
                'description': 'Namespace B2B Person created for B2B ingestion purpose',
                'idType': 'CROSS_DEVICE',
                'name': 'B2B Person',
            },
            {
                'code': 'b2b_opportunity',
                'description': 'Namespace B2B Opportunity created for B2B ingestion purpose',
                'idType': 'B2B_OPPORTUNITY',
                'name': 'B2B Opportunity',
            },
            {
                'code': 'b2b_opportunity_person_relation',
                'description': 'Namespace B2B Opportunity Person Relation created for B2B ingestion purpose',
                'idType': 'B2B_OPPORTUNITY_PERSON',
                'name': 'B2B Opportunity Person Relation',
            },
            {
                'code': 'b2b_campaign',
                'description': 'Namespace B2B Campaign created for B2B ingestion purpose',
                'idType': 'B2B_CAMPAIGN',
                'name': 'B2B Campaign',
            },
            {
                'code': 'b2b_campaign_member',
                'description': 'Namespace B2B Campaign Member created for B2B ingestion purpose',
                'idType': 'B2B_CAMPAIGN_MEMBER',
                'name': 'B2B Campaign Member',
            },
            {
                'code': 'b2b_marketing_list',
                'description': 'Namespace B2B Marketing List created for B2B ingestion purpose',
                'idType': 'B2B_MARKETING_LIST',
                'name': 'B2B Marketing List',
            },
            {
                'code': 'b2b_marketing_list_member',
                'description': 'Namespace B2B Marketing List Member created for B2B ingestion purpose',
                'idType': 'B2B_MARKETING_LIST_MEMBER',
                'name': 'B2B Marketing List Member',
            },
            {
                'code': 'b2b_account_person_relation',
                'description': 'Namespace B2B Account Person Relation created for B2B ingestion purpose',
                'idType': 'B2B_ACCOUNT_PERSON',
                'name': 'B2B Account Person Relation',
            },
            {
                'code': 'b2b_account',
                'description': 'Namespace B2B Account created for B2B ingestion purpose',
                'idType': 'B2B_ACCOUNT',
                'name': 'B2B Account',
            }
        ]
        list_identities = self.getIdentities(only_custom=True)
        list_code = [el['code'] for el in list_identities]
        result_creation = []
        for element in list_new_identities:
            if element['code'] not in list_code:
                res = self.createIdentity(dict_identity=element)
                result_creation.append(res)
        return result_creation