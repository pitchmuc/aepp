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
        path:str = f"/connections/{connectionId}/test"
        res:dict = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def deleteConnection(self, connectionId: str = None) -> dict:
        """
        Delete a specific connection ID.
        Argument:
            connectionId : REQUIRED : The ID of the connection you wish to delete.
        """
        if connectionId is None:
            raise Exception("Require a connectionId to be present")
        path:str = f"/connections/{connectionId}"
        res:dict = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res
    
    def getConnectionSpecs(self)->list:
        """
        Returns the list of connectionSpecs in that instance.
        If that doesn't work, return the response.
        """
        path:str = "/connectionSpecs"
        res:dict = self.connector.getData(self.endpoint + path, headers=self.header)
        try:
            data:list = res['items']
            return data
        except:
            return res

    def getConnectionSpec(self,specId:str=None)->dict:
        """
        Returns the detail for a specific connection.
        Arguments:
            specId : REQUIRED : The specification ID of a connection
        """
        if specId is None:
            raise Exception("Require a specId to be present")
        path:str = f"/connectionSpecs/{specId}"
        res:dict = self.connector.getData(self.endpoint + path, headers=self.header)
        return res 

    def getFlows(self,limit:int=10,prop:str=None,**kwargs)->list:
        """
        Returns the flows set between Source and Target connection.
        Arguments:
            limit : OPTIONAL : Number of results returned
            prop : OPTIONAL : A comma separated list of top-level object properties to be returned in the response. 
                Used to cut down the amount of data returned in the response body. 
                For example, prop=id==3416976c-a9ca-4bba-901a-1f08f66978ff,6a8d82bc-1caf-45d1-908d-cadabc9d63a6,3c9b37f8-13a6-43d8-bad3-b863b941fedd.
        """
        params:dict = {"limit":limit,"count":kwargs.get("count",False)}
        if property is not None:
            params['property'] = prop
        if kwargs.get("continuationToken",False) != False:
            params['continuationToken'] = kwargs.get("continuationToken")
        path:str = "/flows"
        res:dict = self.connector.getData(self.endpoint + path,params=params,headers=self.header) 
        items = res['items']
        if res['_links']["next"].get("href","") != "":
            token:str = res['_links']["next"].get("href","")
            continuationToken = token.split("=")[1]
            params["continuationToken"] = continuationToken
            items += self.connector.getData(self.endpoint + path,params=params,headers=self.header)
        return items
    
    def getFlow(self,flowId:str=None)->dict:
        """
        Returns the details of a specific flow.
        Arguments:
            flowId : REQUIRED : the flow ID to be returned
        """
        if flowId is None:
            raise Exception("Require a flowId to be present")
        path:str = f"/flows/{flowId}"
        res:dict = self.connector.getData(self.endpoint+path,headers=self.header)
        return res

    def deleteFlow(self,flowId:str=None)->dict:
        """
        Delete a specific flow by its ID.
        Arguments:
            flowId : REQUIRED : the flow ID to be returned
        """
        if flowId is None:
            raise Exception("Require a flowId to be present")
        path:str = f"/flows/{flowId}"
        res:dict = self.connector.deleteData(self.endpoint+path,headers=self.header)
        return res
    
    def createFlow(self,obj:dict=None)->dict:
        """
        Create a flow with the API.
        Arguments:
            obj : REQUIRED : body to create the flow service.
                Details can be seen at https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Flows/postFlow 
                requires following keys : name, flowSpec, sourceConnectionIds, targetConnectionIds, transformations, scheduleParams. 
        """
        if obj is None:
            raise Exception("Require a dictionary to create the flow")
        if "name" not in obj.keys():
            raise KeyError("missing 'name' parameter in the dictionary")
        if "flowSpec" not in obj.keys():
            raise KeyError("missing 'flowSpec' parameter in the dictionary")
        if "sourceConnectionIds" not in obj.keys():
            raise KeyError("missing 'sourceConnectionIds' parameter in the dictionary")
        if "targetConnectionIds" not in obj.keys():
            raise KeyError("missing 'targetConnectionIds' parameter in the dictionary")
        if "transformations" not in obj.keys():
            raise KeyError("missing 'transformations' parameter in the dictionary")
        if "scheduleParams" not in obj.keys():
            raise KeyError("missing 'scheduleParams' parameter in the dictionary")
        path:str = "/flows"
        res:dict = self.connector.postData(self.endpoint + path, data=obj, header=self.header)
        return res
    
    def getFlowSpecs(self, prop:str=None)->list:
        """
        Returns the flow specifications.
        Arguments:
            prop : OPTIONAL : A comma separated list of top-level object properties to be returned in the response. 
                Used to cut down the amount of data returned in the response body. 
                For example, prop=id==3416976c-a9ca-4bba-901a-1f08f66978ff,6a8d82bc-1caf-45d1-908d-cadabc9d63a6,3c9b37f8-13a6-43d8-bad3-b863b941fedd.
        """
        path:str = "/flowSpecs"
        params = {}
        if prop is not None:
            params['property'] = prop
        res:dict = self.connector.getData(self.endpoint + path,params=params,headers=self.header)
        items:list = res['items']
        return items
    
    def getFlowSpec(self,flowSpecId)-> dict:
        """
        Return the detail of a specific flow ID Spec
        Arguments:
            flowSpecId : REQUIRED : The flow ID spec to be checked
        """
        if flowSpecId is None:
            raise Exception("Require a flowSpecId to be present")
        path:str = f"/flowSpecs/{flowSpecId}"
        res:dict = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def getRuns(self,limit:int = 10,max:int = 100,prop:str=None, **kwargs)->list:
        """
        Returns the list of runs. Runs are instances of a flow execution.
        Arguments:
            limit : OPTIONAL : Number of results returned per request
            max : OPTIONAL : Maximum number of results.
            prop : OPTIONAL : A comma separated list of top-level object properties to be returned in the response. 
                Used to cut down the amount of data returned in the response body. 
                For example, prop=id==3416976c-a9ca-4bba-901a-1f08f66978ff,6a8d82bc-1caf-45d1-908d-cadabc9d63a6,3c9b37f8-13a6-43d8-bad3-b863b941fedd.
        """
        path = "/runs"
        params = {"limit":limit,"count":kwargs.get("count",False)}
        if prop is not None:
            params['property'] = prop
        if kwargs.get("continuationToken",False):
            params['continuationToken'] = kwargs.get("continuationToken")
        itemsDone = kwargs.get('nbItems',0)
        res:dict = self.connector.getData(self.endpoint + path, params=params,headers=self.header)
        items:list = res['items']
        if res['_links']["next"].get("href","") != "":
            token:str = res['_links']["next"].get("href","")
            continuationToken:str = token.split("=")[1]
            params["continuationToken"] = continuationToken
            items += self.connector.getData(self.endpoint + path,params=params,headers=self.header)
        return items
    
    def createRun(self,flowId:str=None,status:str="active")->dict:
        """
        Generate a run based on the flowId.
        Arguments:
            flowId : REQUIRED : the flow ID to run
            stats : OPTIONAL : Status of the flow
        """
        path = "/runs"
        if flowId is None:
            raise Exception("Require a flowId to be present")
        obj = {"flowId":flowId,"status":status}
        res:dict = self.connector.postData(self.endpoint + path, data=obj, headers=self.header)
        return res
    
    def getRun(self,runId:str=None)->dict:
        """
        Return a specific runId.
        Arguments:
            runId : REQUIRED : the run ID to return
        """
        if runId is None:
            raise Exception("Require a runId to be present")
        path:str = f"runs/{runId}"
        res:dict = self.connector.getData(self.endpoint + path,headers=self.header)
        return res
    
    def getSourceConnection(self,sourceConnectionId:str=None)->dict:
        """
        Return detail of the sourceConnection ID
        Arguments:
            sourceConnectionId : REQUIRED : The source connection ID to be retrieved
        """
        if sourceConnectionId is None:
            raise Exception("Require a sourceConnectionId to be present")
        path:str = f"/sourceConnections/{sourceConnectionId}"
        res:dict = self.connector.getData(self.endpoint + path, headers=self.header)
        return res
    
    def deleteSourceConnection(self,sourceConnectionId:str=None)->dict:
        """
        Delete a sourceConnection ID
        Arguments:
            sourceConnectionId : REQUIRED : The source connection ID to be deleted
        """
        if sourceConnectionId is None:
            raise Exception("Require a sourceConnectionId to be present")
        path:str = f"/sourceConnections/{sourceConnectionId}"
        res:dict = self.connector.deleteData(self.endpoint + path, headers=self.header)
        return res

    def createSourceConnection(self,obj:dict=None)->dict:
        """
        Create a sourceConnection based on the dictionary passed.
        Arguments:
            obj : REQUIRED : the data to be passed for creation of the Source Connection.
                Details can be seen at https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Source_connections/postSourceConnection 
                requires following keys : name, baseConnectionId, data, params, connectionSpec. 
        """
        if obj is None:
            raise Exception("Require a dictionary with data to be present")
        if "name" in obj.keys():
            raise KeyError("Require a 'name' key in the dictionary passed")
        if "baseConnectionId" in obj.keys():
            raise KeyError("Require a 'baseConnectionId' key in the dictionary passed")
        if "data" in obj.keys():
            raise KeyError("Require a 'data' key in the dictionary passed")
        if "params" in obj.keys():
            raise KeyError("Require a 'params' key in the dictionary passed")
        if "connectionSpec" in obj.keys():
            raise KeyError("Require a 'connectionSpec' key in the dictionary passed")
        path:str = f"/sourceConnections"
        res:dict = self.connector.postData(self.endpoint + path, data=obj, headers=self.header)
        return res




