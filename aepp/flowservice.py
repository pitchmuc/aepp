import aepp
from aepp import connector

class FlowService:
    """
    The Flow Service manage the ingestion part of the data in AEP.
    For more information, relate to the API Documentation : 
    """

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        """
        initialize the Flow Service instance.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.endpoint = aepp.config.endpoints["global"] + aepp.config.endpoints["flow"]
    

    def getConnections(self,limit:int=20,count:bool=False,**kwargs) -> list:
        """
        Returns the list of connections available.
        Arguments:
            limit : OPTIONAL : number of result returned
            count : OPTIONAL : if set to True, just returns the number of connections
        kwargs will be added as query parameters 
        """
        params = {"limit":limit}
        if count:
            params['count'] = count
        for kwarg in kwargs:
            params[kwarg] = kwargs[kwarg]
        path = "/connections"
        res = self.connector.getData(self.endpoint + path, params=params, header=self.header)
        try:
            data = res['items']
            return data
        except:
            return res
    
    def createConnection(self, data: dict = None, name: str = None, auth: dict = None, connectionSpec: dict = None, **kwargs) -> dict:
        """
        Create a connection based on either the data being passed or the information passed.
        Arguments:
            data : REQUIRED : dictionary containing the different elements required for the creation of the connection.
            
            In case you didn't pass a data parameter, you can pass different information.
            name : REQUIRED : name of the connection.
            auth : REQUIRED : dictionary that contains "specName" and "params"
                specName : string that names of the the type of authentication to be used with the base connection.
                params : dict that contains credentials and values necessary to authenticate and create a connection.
            connectionSpec : REQUIRED : dictionary containing the "id" and "verison" key.
                id : The specific connection specification ID associated with source
                version : Specifies the version of the connection specification ID. Omitting this value will default to the most recent version
        """
        path = "/connections"
        if data is not None:
            if 'name' not in data.keys() or "auth" not in data.keys() or "connectionSpec" not in data.keys():
                raise Exception("Require some keys to be present : name, auth, connectionSpec")
            obj = data
            res = self.connector.postData(self.endpoint + path, data=obj, header=self.header)
            return res
        elif data is None:
            if "specName" not in auth.keys() or "params" not in auth.keys():
                raise Exception("Require some keys to be present in auth dict : specName, params")
            if "id" not in connectionSpec.keys():
                raise Exception("Require some keys to be present in connectionSpec dict : id")
            if name is None:
                raise Exception("Require a name to be present")
            obj = {
                "name": name,
                "auth": auth,
                "connectionSpec" : connectionSpec

            }
            res = self.connector.postData(self.endpoint + path, data=obj, header=self.header)
            return res
    
    def getConnection(self, connectionId: str = None) -> dict:
        """
        Returns a specific connection object.
        Argument:
            connectionId : REQUIRED : The ID of the connection you wish to retrieve.
        """
        if connectionId is None:
            raise Exception("Require a connectionId to be present")
        path = f"/connections/{connectionId}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res
    
    def connectionTest(self, connectionId: str = None) -> dict:
        """
        Test a specific connection ID.
        Argument:
            connectionId : REQUIRED : The ID of the connection you wish to test.
        """
        if connectionId is None:
            raise Exception("Require a connectionId to be present")
        path = f"/connections/{connectionId}/test"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def deleteConnection(self, connectionId: str = None) -> dict:
        """
        Delete a specific connection ID.
        Argument:
            connectionId : REQUIRED : The ID of the connection you wish to delete.
        """
        if connectionId is None:
            raise Exception("Require a connectionId to be present")
        path = f"/connections/{connectionId}"
        res = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res
    
    def getConnectionSpecs(self)->list:
        """
        Returns the list of connectionSpecs in that instance.
        """
        path = "/connectionSpecs"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        try:
            data = res['items']
            return data
        except:
            return res