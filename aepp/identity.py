import aepp


class Identity:
    """
    Class to manage and retrieve Identity information.
    #!acpdr/swagger-specs/id-service-api.yaml
    This is based on the following API reference : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
    """

    def __init__(self, region: str = "nld2", **kwargs):
        """
        Require a region.
        By default, the NLD2 will be selected. (other choice : va7)
        more info : https://docs.adobe.com/content/help/en/experience-platform/identity/api/getting-started.html
        """
        self.header = aepp.modules.deepcopy(aepp.config.header)
        self.header.update(**kwargs)
        self.endpoint = f"https://platform-{region}.adobe.io" + \
            aepp.config._endpoint_identity

    def getIdentity(self, id_str: str = None, nsid: str = None, namespace: str = None)->dict:
        """
        Given the namespace and an ID in that namespace, returns XID string.
        Arguments:
            id_str : REQUIRED : Id in given namespace (ECID value)
            nsid : REQUIRED : namespace id. (e.g. 411)
            namespace : OPTIONAL : namespace code (e.g. adcloud)
        """
        if id_str is None or nsid is None:
            raise Exception(
                "Expecting that id_str and namespace arguments to be filled.")
        params = {'id': id_str, 'nsid': nsid}
        if namespace is not None:
            params['namespace'] = namespace
        path = "/identity/identity"
        self.header["Accept"] = "application/vnd.adobe.identity+json;version=1.2"
        self.header["x-uis-cst-ctx"] = "stub"
        res = aepp._getData(self.endpoint + path,
                            headers=self.header, params=params)
        del self.header["x-uis-cst-ctx"]
        self.header['Accept'] = "application/json"
        return res

    def getIdentities(self, only_custom: bool = False, save: bool = False)->list:
        """
        Get the list of all identity namespaces available in the organization.
        Arguments:
            only_custom : OPTIONAL : if set to True, return only customer made identities (default False)
            save : OPTIONAL : if set to True, save the result in its respective folder (default False)
        """
        path = "/idnamespace/identities"
        res = aepp._getData(self.endpoint + path,
                            headers=self.header)
        if only_custom:
            res = [identity for identity in res if identity['custom'] == True]
        if save:
            aepp.saveFile(module='identity', file=res,
                          filename='identities', type_file='json')
        return res

    def getIdentityDetail(self, id_str: str = None, save: bool = False)->dict:
        """
        List details of a specific identity namespace by its ID.
        Arguments:
            id_str : REQUIRED : identity of the "id" field.
            save : OPTIONAL : if set to True, save the result in a file, in its respective folder (default False)
        """
        if id_str is None:
            raise Exception("Expected an id for the Identity")
        path = f"/idnamespace/identities/{id_str}"
        res = aepp._getData(self.endpoint + path,
                            headers=self.header)
        if save:
            filename = f"identity_{res['code']}"
            aepp.saveFile(module='identity', file=res,
                          filename=filename, type_file='json')
        return res

    def createIdentity(self, name: str = None, code: str = None, idType: str = None, description: str = None, dict_identity: dict = None)->dict:
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
        if name is None or code is None or idType is None:
            raise Exception(
                "Expecting that name, code and idType to be filled with value")
        creation_dict['name'] = name
        creation_dict['code'] = code
        creation_dict['idType'] = idType
        if description is not None:
            creation_dict['description'] = description
        if ' ' in code:
            raise TypeError(
                "code can only contain one word with letter and numbers")
        if idType not in ["COOKIE", "CROSS_DEVICE", "DEVICE", "EMAIL", "MOBILE", "NON_PEOPLE", "PHONE"]:
            raise TypeError(
                "idType could only be one of those : COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE, PHONE")
        if dict_identity is not None:
            creation_dict = dict_identity
        path = "/idnamespace/identities"
        res = aepp._postData(self.endpoint + path,
                             headers=self.header, data=creation_dict)
        return res

    def updateIdentity(self, id_str: str = None, name: str = None, code: str = None, idType: str = None, description: str = None)->dict:
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
                "Expecting that name, code and idType to be filled with value")
        if idType not in ["COOKIE", "CROSS_DEVICE", "DEVICE", "EMAIL", "MOBILE", "NON_PEOPLE", "PHONE"]:
            raise TypeError(
                "idType could only be one of those : COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE, PHONE")
        path = f"/idnamespace/identities/{id_str}"
        data = {
            "name": name,
            "code": code,
            "idType": idType,
            "description": description
        }
        res = aepp._putData(self.endpoint + path,
                            headers=self.header, data=data)
        return res

    def getIdentitiesIMS(self)->list:
        """
        Returns all identities from the IMS Org itself.
        """
        path = f"/idnamespace/orgs/{aepp.config.org_id}/identities"
        res = aepp._getData(self.endpoint + path, headers=self.header)
        return res

    def getClustersMembers(self, xid: str = None, nsid: str = "411", namespace: str = "adcloud", id_value: str = None, graphType: str = "private"
                           )->dict:
        """
        Given an XID return all XIDs, in the same or other namespaces, that are linked to it by the device graph type. 
        The related XIDs are considered to be part of the same cluster. 
        It is required to pass either xid or (namespace/nsid & id) pair to get cluster members.
        Arguments:
            xid : REQUIRED : Identity string returns by the getIdentity method.
            nsid : OPTIONAL : namespace id (default : 411)
            namespace : OPTIONAL : namespace code. (default : adcloud)
            id_value : OPTIONAL : ID of the customer in given namespace.
            graphType : OPTIONAL : Graph type (output type) you want to get the cluster from. (default private)
        """
        temp_header = aepp.modules.deepcopy(self.header)
        temp_header['Accept'] = "application/vnd.adobe.identity+json;version=1.2"
        temp_header['x-uis-cst-ctx'] = "stub"
        path = "/identity/cluster/members"
        params = {}
        if xid is not None:
            params['xid'] = xid
            params['graph-type'] = graphType
            res = aepp._getData(self.endpoint + path,
                                params=params, headers=temp_header)
            return res
        elif xid is None and id_value is not None:
            params['nsid'] = nsid
            params['namespace'] = namespace
            params['id'] = id_value
            params['graph-type'] = graphType
            res = aepp._getData(self.endpoint + path,
                                params=params, headers=temp_header)
            return res

    def postClustersMembers(self, xids: list = None, version: float = 1.0, graphType: str = "private")->dict:
        """
        Given set of identities, returns all linked identities in cluster corresponding to each identity.
        Arguments:
            xids : REQUIRED : list of identity as returned by getIdentity method.
            version : OPTIONAL : Version of the clusterMembers (default 1.0)
            graphType : OPTIONAL : Graph type (output type) you want to get the cluster from. (default private)
        """
        temp_header = aepp.modules.deepcopy(self.header)
        temp_header['Accept'] = "application/vnd.adobe.identity+json;version=1.2"
        temp_header['x-uis-cst-ctx'] = "stub"
        path = "/identity/cluster/members"
        if type(xids) != list:
            raise TypeError("xids must be of type list")
        list_body = [{'xid': [{'xid': xid}],
                      "graph-type": graphType, "version": version} for xid in xids]
        res = aepp._postData(self.endpoint + path,
                             data=list_body, headers=temp_header)
        return res

    def getClusterHistory(self, xid: str = None, nsid: int = 411, namespace: str = "adcloud", id_value: str = None, graphType: str = "private"
                          )->dict:
        """
        Given an XID, return all cluster associations with that XID. 
        It is required to pass either xid or (namespace/nsid & id) pair to get cluster history.
        Arguments:
            xid : REQUIRED : Identity string returns by the getIdentity method.
            nsid : OPTIONAL : namespace id (default : 411)
            namespace : OPTIONAL : namespace code. (default : adcloud)
            id_value : OPTIONAL : ID of the customer in given namespace.
            graphType : OPTIONAL : Graph type (output type) you want to get the cluster from. (default private)
        """
        temp_header = aepp.modules.deepcopy(self.header)
        temp_header['Accept'] = "application/vnd.adobe.identity+json;version=1.2"
        temp_header['x-uis-cst-ctx'] = "stub"
        path = "/identity/cluster/history"
        params = {}
        if xid is not None:
            params['xid'] = xid
            params['graph-type'] = graphType
            res = aepp._getData(self.endpoint + path,
                                params=params, headers=temp_header)
            return res
        elif xid is None and id_value is not None:
            params['nsid'] = nsid
            params['namespace'] = namespace
            params['id'] = id_value
            params['graph-type'] = graphType
            res = aepp._getData(self.endpoint + path,
                                params=params, headers=temp_header)
            return res

    def getIdentityMapping(self, xid: str = None, targetNs: int = None, nsid: int = 411, namespace: str = "adcloud", id_value: str = None, graphType: str = "private")->dict:
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
        temp_header = aepp.modules.deepcopy(self.header)
        temp_header['Accept'] = "application/vnd.adobe.identity+json;version=1.2"
        temp_header['x-uis-cst-ctx'] = "stub"
        path = "/identity/mapping"
        params = {}
        if xid is not None:
            params['xid'] = xid
            params['graph-type'] = graphType
            params['targetNs'] = targetNs
            res = aepp._getData(self.endpoint + path,
                                params=params, headers=temp_header)
            return res
        elif xid is None and id_value is not None:
            params['nsid'] = nsid
            params['namespace'] = namespace
            params['id'] = id_value
            params['targetNs'] = targetNs
            params['graph-type'] = graphType
            res = aepp._getData(self.endpoint + path,
                                params=params, headers=temp_header)
            return res

    def postIdentityMapping(self, xids: list = None, targetNs: int = 411, version: float = 1.0)->dict:
        """
        Given an identity, returns all identity mappings in requested namespace (target namespace).
        Arguments:

        """
        temp_header = aepp.modules.deepcopy(self.header)
        temp_header['Accept'] = "application/vnd.adobe.identity+json;version=1.2"
        temp_header['x-uis-cst-ctx'] = "stub"
        path = "/identity/mapping"
        if type(xids) != list:
            raise TypeError("xids must be of type list")
        list_body = [{'xid': [{'xid': xid}],
                      "version": version, "targetNs": targetNs} for xid in xids]
        res = aepp._postData(self.endpoint + path,
                             data=list_body, headers=temp_header)
        return res
