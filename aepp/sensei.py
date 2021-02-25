# internal library
import aepp
from aepp import connector

class Sensei:
    """
    This module is based on the Sensei Machine Learning API from Adobe Experience Platform.
    You can find more documentation on the endpoints here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/
    """

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs)->None:
        """
        Initialize the class with the config header used.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        Additional kwargs will update the header.
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header['Accept'] = "application/vnd.adobe.platform.sensei+json;profile=mlInstanceListing.v1.json"
        self.header.update(**kwargs)
        self.sandbox = self.connector.config['sandbox']
        self.endpoint = aepp.config.endpoints["global"]+aepp.config.endpoints["sensei"]

    def getEngines(self, limit: int = 25, **kwargs)->list:
        """
        Return the list of all engines.
        Arguments:
            limit : OPTIONAL : number of element per requests
        kwargs: 
            property : filtering, example value "name==test."
        """
        path = "/engines"
        params = {'limit': limit}
        if kwargs.get('property', False) != False:
            params['property'] = kwargs.get('property', '')
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
        data = res['children']
        return data

    def getEngine(self, engineId: str = None)->dict:
        """
        return a specific engine information based on its id.
        Arguments:
            engineId : REQUIRED : the engineId to return.
        """
        if engineId is None:
            raise Exception("require an engineId parameter")
        path = f"/engines/{engineId}"
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header)
        return res

    def getDockerRegistery(self)->dict:
        """
        Return the docker registery information.
        """
        path = "/engines/dockerRegistry"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def deleteEngine(self, engineId: str = None)->str:
        """
        Delete an engine based on the id passed.
        Arguments:
            engineId : REQUIRED : Engine ID to be deleted.
        """
        if engineId is None:
            raise Exception("require an engineId parameter")
        path = f"/engines/{engineId}"
        res = self.connector.deleteData(self.endpoint+path,
                               headers=self.header)
        return res

    def getMLinstances(self, limit: int = 25)->list:
        """
        Return a list of all of the ml instance
        Arguments: 
            limit : OPTIONAL : number of elements retrieved.
        """
        path = "/mlInstances"
        params = {"limit": limit}
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
        data = res['children']
        return data

    def createMLinstances(self, name: str = None, engineId: str = None, description: str = None):
        """
        Create a ML instance with the name and instanceId provided.
        Arguments:
            name : REQUIRED : name of the ML instance
            engineId : REQUIRED : engine attached to the ML instance
            description : OPTIONAL : description of the instance.
        """
        path = "/mlInstances"
        self.header['Content'] = "application/vnd.adobe.platform.sensei+json;profile=mlInstanceListing.v1.json"
        if name is None and engineId is None:
            raise Exception("Requires a name and an egineId")
        body = {
            'name': name,
            'engineId': engineId,
            'description': description
        }
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, data=body)
        return res
