import aepp
from aepp import connector

class AccessControl:
    """
    Access Control API endpoints
    """

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs)->None:
        """
        Instantiate the access controle API wrapper.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        kwargs : 
            header options
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.endpoint = aepp.config.endpoints['global']+aepp.config.endpoints["access"]

    def getReferences(self)->dict:
        """
        List all available permission names and resource types.
        """
        path = "/acl/reference"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def postEffectivePolicies(self, listElements: list = None):
        """
        List all effective policies for a user on given resources within a sandbox.
        Arguments:
            listElements : REQUIRED : List of resource urls. Example url : /resource-types/{resourceName} or /permissions/{highLevelPermissionName}
        """
        if type(listElements) != list:
            raise TypeError("listElements should be a list of elements")
        path = "/acl/effective-policies"
        res = self.connector.postData(self.endpoint+path,
                             data=listElements, headers=self.header)
        return res
