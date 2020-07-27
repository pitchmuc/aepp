import aepp
from aepp import config
from copy import deepcopy


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
        self.header = deepcopy(config._header)
        self.header.update(**kwargs)
        self.endpoint = f"https://platform-{region}.adobe.io" + \
            config._endpoint_identity

    def getIdentity(self, id_str: str = None, nsid: str = None, namespace: str = None):
        """
        Given the namespace and an ID in that namespace, returns XID string.
        Arguments:
            id_str : REQUIRED : Id in given namespace
            nsid : REQUIRED : namespace id. (e.g. 411)
            namespace : OPTIONAL : namespace code (e.g. adcloud)
        """
        if id_str is None or nsid is None:
            raise("Expecting that id_str and namespace arguments to be filled.")
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

    def getIdentities(self):
        """
        Get the list of all identity namespace available in the organization.
        """
        path = "/idnamespace/identities"
        res = aepp._getData(self.endpoint + path,
                            headers=self.header)
        return res

    def getIdentityDetail(self, id_str: str = None):
        """
        List details of a specific identity namespace by its ID.
        Arguments:
            id_str : REQUIRED : identity of the "id" field.
        """
        if id_str is None:
            raise Exception("Expected an id for the Identity")
        path = f"/idnamespace/identities/{id_str}"
        res = aepp._getData(self.endpoint + path,
                            headers=self.header)
        return res

    def createIdentity(self, name: str = None, code: str = None, idType: str = None, description: str = None, dict_identity: dict = None):
        """
        List details of a specific identity namespace by its ID.
        Arguments:
            name : REQUIRED : Display name of the identity 
            code : REQUIRED : Identity Symbol for user interface.
            idType : REQUIRED : one of those : Cookie, Cross-device, Device, Email, Mobile, Non-people, or Phone
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
        if idType not in ["Cookie", "Cross-device", "Device", "Email", "Mobile", "Non-people", "Phone"]:
            raise TypeError(
                "idType could only be one of those : Cookie, Cross-device, Device, Email, Mobile, Non-people, or Phone")
        if dict_identity is not None:
            creation_dict = dict_identity
        path = "/idnamespace/identities"
        res = aepp._postData(self.endpoint + path,
                             headers=self.header, body=creation_dict)
        return res
