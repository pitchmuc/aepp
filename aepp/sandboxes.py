import aepp
from aepp import connector

class Sandbox:

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        """
        Instantiate the sandbox class.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        Additional kwargs will update the header.
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.endpoint = aepp.config.endpoints["global"] + aepp.config.endpoints["sandboxes"]

    def getSandboxes(self)->list:
        """
        Return the list of all the sandboxes
        """
        path = self.endpoint + "/sandboxes"
        res = self.connector.getData(path)
        data = res['sandboxes']
        return data


    def createSandbox(self,name: str = None, title: str = None, type_sandbox: str = "development")->dict:
        """
        Create a new sandbox in your AEP instance.
        Arguments:
            name : REQUIRED : name of your sandbox
            title : REQUIRED : display name of your sandbox
            type_sandbox : OPTIONAL : type of your sandbox. default : development.
        """
        if name is None or title is None:
            raise Exception('name and title cannot be empty')
        path = self.endpoint + "/sandboxes"
        data = {
            "name": name,
            "title": title,
            "type": type_sandbox
        }
        res = self.connector.postData(path, data=data)
        return res


    def getSandbox(self,name: str)->dict:
        """
        retrieve a Sandbox information by name
        Argument:
            name : REQUIRED : name of Sandbox
        """
        if name is None:
            raise Exception('Expected a name as parameter')
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.getData(path)
        return res


    def deleteSandbox(self,name: str)->dict:
        """
        Delete a sandbox by its name.
        Arguments: 
            name : REQUIRED : sandbox to be deleted.
        """
        if name is None:
            raise Exception('Expected a name as parameter')
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.deleteData(path)
        return res


    def resetSandbox(self,name: str)->dict:
        """
        Reset a sandbox by its name. Sandbox will be empty.
        Arguments: 
            name : REQUIRED : sandbox to be deleted.
        """
        if name is None:
            raise Exception('Expected a name as parameter')
        path = self.endpoint + f"/sandboxes/{name}"
        res = self.connector.putData(path)
        return res
