# Internal Library
import aepp
from dataclasses import dataclass
from aepp import connector

json_extend = [{'op': 'replace',
                'path': '/meta:intendedToExtend',
                'value': ['https://ns.adobe.com/xdm/context/profile',
                          'https://ns.adobe.com/xdm/context/experienceevent']}]


@dataclass
class _Data:

    def __init__(self):
        self.ids = {}
        self.schemas = {}
        self.paths = {}


class Schema:
    """
    This class is a wrapper around the schema registry API for Adobe Experience Platform.
    More documentation on these endpoints can be found here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/schema-registry.yaml

    """
    schemas = {}
    _schemaClasses = {
        "event": "https://ns.adobe.com/xdm/context/experienceevent",
        "profile": "https://ns.adobe.com/xdm/context/profile"
    }

    def __init__(self, container_id: str = "tenant",config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        """
        Copy the token and header and initiate the object to retrieve schema elements.
        Arguments:
            container_id : OPTIONAL : "tenant"(default) or "global"
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module. 
        possible kwargs:
            x-sandbox-name : name of the sandbox you want to use (default : "prod").
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header['Accept'] = "application/vnd.adobe.xdm+json"
        self.header.update(**kwargs)
        self.endpoint = aepp.config.endpoints["global"]+aepp.config.endpoints["schemas"]
        self.container = container_id
        self.data = _Data()

    def getStats(self)->list:
        """
        Returns a list of the last actions realized on the Schema for this instance of AEP. 
        """
        path = '/stats/'
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def getTenantId(self)->str:
        """
        Return the tenantID for the AEP instance.
        """
        res = self.getStats()
        tenant = res['tenantId']
        return tenant

    def getSchemas(self, **kwargs)->list:
        """
        Returns the list of schemas retrieved for that instances in a "results" list.
        Kwargs:
            debug : if set to true, will print the result when error happens
        """
        path = f'/{self.container}/schemas/'
        start = kwargs.get("start", 0)
        params = {"start": start}
        verbose = kwargs.get("debug",False)
        res = self.connector.getData(self.endpoint+path,
                            params=params, headers=self.header,verbose=verbose)
        if kwargs.get('debug', False):
            if "results" not in res.keys():
                print(res)
        data = res['results']
        page = res['_page']
        while page['next'] is not None:
            data += self.getSchemas(start=page['next'])
        return data

    def getSchema(self, schema_id: str = None, version: int = 1, save: bool = False, full: bool = True, desc: bool = False, schema_type: str = 'xdm', **kwargs)->dict:
        """
        Get the Schema. Requires a schema id.
        Response provided depends on the header set, you can change the Accept header with kwargs.
        Arguments:
            schema_id : REQUIRED : $id or meta:altId
            version : OPTIONAL : Version of the Schema asked (default 1)
            save : OPTIONAL : save the result in json file (default False)
            full : OPTIONAL : True (default) will return the full schema.False just the relationships.
            desc : OPTIONAL : If set to True, return the identity used as the descriptor.
            schema_type : OPTIONAL : set the type of output you want (xdm or xed) Default : xdm. 
        Possible kwargs:
            Accept : Accept header to change the type of response.
            # /Schemas/lookup_schema
            more details held here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        if schema_id is None:
            raise Exception("Require a schema_id as a parameter")
        if full:
            update_full = "-full"
        else:
            update_full = ""
        if desc:
            update_desc = "-desc"
        else:
            update_desc = ""
        if schema_type != 'xdm' and schema_type != 'xed':
            raise ValueError("schema_type parameter can only be xdm or xed")
        accept_update = f"application/vnd.adobe.{schema_type}{update_full}{update_desc}+json; version={version}"
        self.header["Accept"] = accept_update
        if kwargs.get('Accept', None) is not None:
            self.header['Accept'] = kwargs.get('Accept', self.header['Accept'])
        self.header['Accept-Encoding'] = 'identity'
        if schema_id.startswith('https://'):
            from urllib import parse
            schema_id = parse.quote_plus(schema_id)
        path = f'/{self.container}/schemas/{schema_id}'
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        del self.header['Accept-Encoding']
        if "title" not in res.keys() and 'notext' not in self.header['Accept']:
            print('Issue with the request. See response.')
            return res
        self.header['Accept'] = "application/json"
        if save:
            aepp.saveFile(module='schema', file=res,
                          filename=res['title'], type_file='json')
        if 'title' in res.keys():
            self.data.schemas[res['title']] = res
        else:
            print("no title in the response. Not saved in the data object.")
        return res

    def getSchemaSample(self, schema_id: str = None, save: bool = False, version: int = 1) -> dict:
        """
        Generate a sample data from a schema id.
        Arguments:
            schema_id : REQUIRED : The schema ID for the sample data to be created.
            save : OPTIONAL : save the result in json file (default False)
        """
        import random
        rand_number = random.randint(1, 10e10)
        if schema_id is None:
            raise Exception("Require an ID for the schema")
        if schema_id.startswith('https://'):
            from urllib import parse
            schema_id = parse.quote_plus(schema_id)
        path = f'/rpc/sampledata/{schema_id}'
        accept_update = f"application/vnd.adobe.xed+json; version={version}"
        self.header["Accept"] = accept_update
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        if save:
            schema = self.getSchema(schema_id=schema_id, full=False)
            aepp.saveFile(module='schema', file=res,
                          filename=f"{schema['title']}_{rand_number}", type_file='json')
        self.header['Accept'] = "application/json"
        return res

    def patchSchema(self, schema_id: str = None, changes: list = None, **kwargs)->dict:
        """
        Enable to patch the Schema with operation.
        Arguments:
            schema_id : REQUIRED : $id or meta:altId
            change : REQUIRED : List of changes that need to take place.
        information : http://jsonpatch.com/
        """
        if schema_id is None:
            raise Exception("Require an ID for the schema")
        if type(changes) == dict:
            changes = list(changes)
        if schema_id.startswith('https://'):
            from urllib import parse
            schema_id = parse.quote_plus(schema_id)
        path = f'/{self.container}/schemas/{schema_id}'
        res = self.connector.patchData(self.endpoint+path,
                              data=changes, headers=self.header)
        return res

    def putSchema(self, schema_id: str = None, changes: dict = None, **kwargs)->dict:
        """
        A PUT request essentially re-writes the schema, therefore the request body must include all fields required to create (POST) a schema.
        This is especially useful when updating a lot of information in the schema at once.
        Arguments:
            schema_id : REQUIRED : $id or meta:altId
            change : REQUIRED : dictionary of the new schema.
            It requires a allOf list that contains all the attributes that are required for creating a schema.
            #/Schemas/replace_schema
            More information on : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        path = f'/{self.container}/schemas/{schema_id}'
        if schema_id is None:
            raise Exception("Require an ID for the schema")
        if schema_id.startswith('https://'):
            from urllib import parse
            schema_id = parse.quote_plus(schema_id)
        res = self.connector.putData(self.endpoint+path,
                            data=changes, headers=self.header)
        return res

    def deleteSchema(self, schema_id: str = None, **kwargs)->str:
        """
        Delete the request
        Arguments:
            schema_id : REQUIRED : $id or meta:altId
            It requires a allOf list that contains all the attributes that are required for creating a schema.
            #/Schemas/replace_schema
            More information on : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        if schema_id is None:
            raise Exception("Require an ID for the schema")
        if schema_id.startswith('https://'):
            from urllib import parse
            schema_id = parse.quote_plus(schema_id)
        path = f'/{self.container}/schemas/{schema_id}'
        res = self.connector.deleteData(self.endpoint+path, headers=self.header)
        return res

    def createSchema(self, schema: dict = None)->dict:
        """
        Create a Schema based on the data that are passed in the Argument.
        Arguments:
            schema : REQUIRED : The schema definition that needs to be created.
        """
        path = f'/{self.container}/schemas/'
        if type(schema) != dict:
            raise TypeError("Expecting a dictionary")
        if "allOf" not in schema.keys():
            raise Exception(
                "The schema must include an ‘allOf’ attribute (a list) referencing the $id of the base class the schema will implement.")
        res = self.connector.postData(self.endpoint+path,
                             headers=self.header, data=schema)
        return res

    def getClasses(self, **kwargs):
        """
        return the classes of the AEP Instances.
        kwargs:
            debug : if set to True, will print result for errors
        """
        self.header.update({
            "Accept": "application/vnd.adobe.xdm-id+json"})
        start = kwargs.get("start", 0)
        params = {"start": start}
        path = f'/{self.container}/classes/'
        verbose = kwargs.get("verbose",False)
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params,verbose=verbose)
        self.header.update({
            "Accept": "application/json"})
        if kwargs.get('debug', False):
            if "results" not in res.keys():
                print(res)
        data = res['results']
        page = res['_page']
        while page['next'] is not None:
            data += self.getSchemas(start=page['next'])
        return data

    def getClass(self, class_id: str = None, full: bool = True, version: int = 1, save: bool = False):
        """
        Return a specific class.
        Arguments: 
            class_id : REQUIRED : the meta:altId or $id from the class
            full : OPTIONAL : True (default) will return the full schema.False just the relationships. 
            version : OPTIONAL : the version of the class to retrieve.
        """
        if class_id is None:
            raise Exception("Require a class_id")
        if class_id.startswith('https://'):
            from urllib import parse
            class_id = parse.quote_plus(class_id)
        self.header['Accept-Encoding'] = 'identity'
        self.header.update({
            "Accept": "application/vnd.adobe.xdm-full+json; version="+str(version)})
        path = f'/{self.container}/classes/{class_id}'
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        self.header.update({
            "Accept": "application/json"})
        if save:
            aepp.saveFile(module='schema', file=res,
                          filename=res['title'], type_file='json')
        return res

    def createClass(self, class_obj: dict = None, **kwargs):
        """
        Create a class based on the object pass. It should include the "allOff" element.
        Arguments:
            class_obj : REQUIRED : object to create a class, include a title and a "allOf" element.
        """
        path = f'/{self.container}/classes/'
        if type(class_obj) != dict:
            raise TypeError("Expecting a dictionary")
        if "allOf" not in class_obj.keys():
            raise Exception(
                "The class object must include an ‘allOf’ attribute (a list) referencing the $id of the base class the schema will implement.")
        res = self.connector.postData(self.endpoint+path,
                             headers=self.header, data=class_obj)
        return res

    def getMixins(self, **kwargs):
        """
        returns the mixin of the account
        kwargs:
            debug : if set to True, will print result for errors
        """
        path = f'/{self.container}/mixins/'
        start = kwargs.get("start", 0)
        params = {"start": start}
        verbose=kwargs.get("debug", False)
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params,verbose=verbose)
        if kwargs.get('debug', False):
            if "results" not in res.keys():
                print(res)
        data = res['results']
        page = res['_page']
        while page['next'] is not None:
            data += self.getSchemas(start=page['next'])
        return data

    def getMixin(self, mixin_id: str = None, version: int = 1, full: bool = True, save: bool = False):
        """
        Returns a specific mixin.
        Arguments:
            mixin_id : REQUIRED : meta:altId or $id
            version : OPTIONAL : version of the mixin
            full : OPTIONAL : True (default) will return the full schema.False just the relationships. 
        """
        if mixin_id.startswith('https://'):
            from urllib import parse
            mixin_id = parse.quote_plus(mixin_id)
        self.header['Accept-Encoding'] = 'identity'
        if full:
            accept_full = "-full"
        else:
            accept_full = ""
        update_accept = f"application/vnd.adobe.xed{accept_full}+json; version={version}"
        self.header.update({
            "Accept": update_accept})
        path = f'/{self.container}/mixins/{mixin_id}'
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        self.header.update({
            "Accept": "application/json"})
        if save:
            aepp.saveFile(module='schema', file=res,
                          filename=res['title'], type_file='json')
        return res

    def createMixin(self, mixin_obj: dict = None):
        """
        Create a mixin based on the dictionary passed.
        Arguments :
            mixin_obj : REQUIRED : the object required for creating the mixin.
            Should contain title, type, definitions
        """
        if mixin_obj is None:
            raise Exception("Require a mixin object")
        if "title" not in mixin_obj or "type" not in mixin_obj or "definitions" not in mixin_obj:
            raise AttributeError(
                "Require to have at least title, type, definitions set in the object.")
        path = f'/{self.container}/mixins/'
        res = self.connector.postData(self.endpoint + path,
                             data=mixin_obj, headers=self.header)
        return res

    def deleteMixin(self, mixin_id: str = None):
        """
        Arguments:
            schema_id : meta:altId or $id
        """
        if mixin_id is None:
            raise Exception("Require an ID")
        if mixin_id.startswith('https://'):
            from urllib import parse
            mixin_id = parse.quote_plus(mixin_id)
        path = f'/{self.container}/mixins/{mixin_id}'
        res = self.connector.deleteData(self.endpoint+path, headers=self.header)
        return res

    def updateMixin(self, mixin_id: str = None, changes: list = None):
        """
        Update the mixin with the operation described in the changes.
        Arguments:
            schema_id : REQUIRED : meta:altId or $id
            changes : REQUIRED : dictionary on what to update on that mixin.
        """
        if mixin_id is None or changes is None:
            raise Exception("Require an ID and changes")
        path = f'/{self.container}/mixins/{mixin_id}'
        if type(changes) == dict:
            changes = list(changes)
        res = self.connector.patchData(self.endpoint+path,
                              data=changes, headers=self.header)
        return res

    def getUnions(self, **kwargs):
        """
        Get all of the unions that has been set for the tenant.
        Returns a dictionary.

        Possibility to add option using kwargs
        """
        path = f'/{self.container}/unions'
        params = {}
        if len(kwargs) > 0:
            for key in kwargs.key():
                if key == 'limit':
                    if int(kwargs['limit']) > 500:
                        kwargs['limit'] = 500
                params[key] = kwargs.get(key, '')
        res = self.connector.getData(self.endpoint+path,
                            params=params, headers=self.header)
        data = res['results']  # issue when requesting directly results.
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
        if union_id.startswith('https://'):
            from urllib import parse
            union_id = parse.quote_plus(union_id)
        path = f'/{self.container}/unions/{union_id}'
        self.header.update({
            "Accept": "application/vnd.adobe.xdm-full+json; version="+str(version)})
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        self.header.update({
            "Accept": "application/json"})
        return res

    def getXDMprofileSchema(self):
        """
        Returns a list of all schemas that are part of the XDM Individual Profile.
        """
        path = "/tenant/schemas?property=meta:immutableTags==union&property=meta:class==https://ns.adobe.com/xdm/context/profile"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def getDataTypes(self, **kwargs):
        """
        Get the data types from a container.
        Possible kwargs:
            properties : str :limit the amount of properties return by comma separated list.
        """
        path = f"/{self.container}/datatypes/"
        if kwargs.get('properties', None) is not None:
            params = {'properties': kwargs.get('properties', 'title,$id')}
        self.header.update({
            "Accept": "application/vnd.adobe.xdm-id+json"})
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        self.header.update({
            "Accept": "application/json"})
        data = res['results']
        page = res['_page']
        while page['next'] is not None:
            data += self.getSchemas(start=page['next'])
        return data

    def getDataType(self, dataTypeId: str = None, version: str = "1", save: bool = False):
        """
        Retrieve a specific data type id
        Argument: 
            dataTypeId : REQUIRED : The resource meta:altId or URL encoded $id URI.
        """
        if dataTypeId is None:
            raise Exception("Require a dataTypeId")
        if dataTypeId.startswith('https://'):
            from urllib import parse
            mixin_id = parse.quote_plus(mixin_id)
        self.header.update({
            "Accept": "application/vnd.adobe.xdm-full+json; version="+version})
        path = f"/{self.container}/datatypes/{dataTypeId}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        self.header.update({
            "Accept": "application/json"})
        if save:
            aepp.saveFile(module='schema', file=res,
                          filename=res['title'], type_file='json')
        return res

    def createDataType(self, dataType_obj: dict = None):
        """
        Create Data Type based on the object passed.
        """
        if dataType_obj is None:
            raise Exception("Require a dictionary to create the Data Type")
        path = f"/{self.container}/datatypes/"
        res = self.connector.postData(self.endpoint + path,
                             data=dataType_obj, headers=self.header)
        return res

    def getDescriptors(self, type_desc: str = "xdm:descriptorIdentity", id_desc: bool = False, link_desc: bool = False, save: bool = False, **kwargs)->list:
        """
        Return a list of all descriptors contains in that tenant id.
        By default return a v2 for pagination.
        Arguments:
            type_desc : OPTIONAL : if you want to filter for a specific type of descriptor. (default : "xdm:descriptorIdentity")
            id_desc : OPTIONAL : if you want to return only the id.
            link_desc : OPTIONAL : if you want to return only the paths.
            save : OPTIONAL : Boolean that would save your descriptors in the schema folder. (default False)
        """
        path = f"/{self.container}/descriptors/"
        params = {'start': kwargs.get("start", 0)}
        if type_desc is not None:
            params['property'] = f"@type=={type_desc}"
        if id_desc:
            update_id = "-id"
        else:
            update_id = ""
        if link_desc:
            update_link = "-link"
        else:
            update_link = ""
        self.header['Accept'] = f"application/vnd.adobe.xdm-v2{update_link}{update_id}+json"
        res = self.connector.getData(self.endpoint + path,
                            params=params, headers=self.header)
        self.header.update({
            "Accept": "application/json"})
        data = res['results']
        page = res['_page']
        while page['next'] is not None:
            data += self.getSchemas(start=page['next'])
        if save:
            aepp.saveFile(module="schema", file=data,
                          filename='descriptors', type_file='json')
        return data

    def getDescriptor(self, descriptor_id: str = None, save: bool = False)->dict:
        """
        Return a specific descriptor
        Arguments:
            descriptor_id : REQUIRED : descriptor ID to return (@id).
            save : OPTIONAL : Boolean that would save your descriptors in the schema folder. (default False)
        """
        if descriptor_id is None:
            raise Exception("Require a descriptor id")
        path = f"/{self.container}/descriptors/{descriptor_id}"
        self.header['Accept'] = f"application/vnd.adobe.xdm+json"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        self.header.update({
            "Accept": "application/json"})
        if save:
            aepp.saveFile(module="schema", file=res,
                          filename=f'{res["@id"]}_descriptors', type_file='json')
        return res

    def createDescriptor(self, desc_type: str = "xdm:descriptorIdentity", sourceSchema: str = None, sourceProperty: str = None, namespace: str = None, xdmProperty: str = "xdm:code", primary: bool = False, **kwargs)->dict:
        """
        Create a descriptor attached to a specific schema.
        Arguments:
            desc_type : REQUIRED : the type of descriptor to create.(default Identity)
            sourceSchema : REQUIRED : the schema attached to your identity ()
            sourceProperty : REQUIRED : the path to the field
            namespace : REQUIRED : the namespace used for the identity
            xdmProperty : OPTIONAL : xdm code for the descriptor (default : xdm:code)
            primary : OPTIONAL : Boolean to define if it is a primary identity or not (default False).
        possible kwargs:
            version : version of the creation (default 1)
        """
        path = f"/{self.container}/descriptors"
        if sourceSchema is None or sourceProperty is None or namespace is None:
            raise Exception("Missing required arguments.")
        obj = {
            "@type": desc_type,
            "xdm:sourceSchema": sourceSchema,
            "xdm:sourceVersion": kwargs.get("version", 1),
            "xdm:sourceProperty": sourceProperty,
            "xdm:namespace":  namespace,
            "xdm:property": xdmProperty,
            "xdm:isPrimary": primary}
        res = self.connector.postData(self.endpoint+path, data=obj, headers=self.header)
        return res

    def deleteDescriptor(self, descriptor_id: str = None)->str:
        """
        Delete a specific descriptor.
        Arguments:
            descriptor_id : REQUIRED : the descriptor id to delete
        """
        if descriptor_id is None:
            raise Exception("Require a descriptor id")
        path = f"/{self.container}/descriptors/{descriptor_id}"
        self.header['Accept'] = f"application/vnd.adobe.xdm+json"
        res = self.connector.deleteData(self.endpoint + path, headers=self.header)
        self.header.update({
            "Accept": "application/json"})
        return res

    def putDescriptor(self, descriptor_id: str = None, desc_type: str = "xdm:descriptorIdentity", sourceSchema: str = None, sourceProperty: str = None, namespace: str = None, xdmProperty: str = "xdm:code", primary: bool = False)->dict:
        """
        Replace the descriptor with the new definition. It updates the whole definition.
        Arguments:
            descriptor_id : REQUIRED : the descriptor id to delete
            desc_type : REQUIRED : the type of descriptor to create.(default Identity)
            sourceSchema : REQUIRED : the schema attached to your identity ()
            sourceProperty : REQUIRED : the path to the field
            namespace : REQUIRED : the namespace used for the identity
            xdmProperty : OPTIONAL : xdm code for the descriptor (default : xdm:code)
            primary : OPTIONAL : Boolean to define if it is a primary identity or not (default False).
        """
        if descriptor_id is None:
            raise Exception("Require a descriptor id")
        path = f"/{self.container}/descriptors/{descriptor_id}"
        if sourceSchema is None or sourceProperty is None or namespace is None:
            raise Exception("Missing required arguments.")
        obj = {
            "@type": desc_type,
            "xdm:sourceSchema": sourceSchema,
            "xdm:sourceVersion": 1,
            "xdm:sourceProperty": sourceProperty,
            "xdm:namespace":  namespace,
            "xdm:property": xdmProperty,
            "xdm:isPrimary": primary}
        res = self.connector.putData(self.endpoint+path, data=obj, headers=self.header)
        return res
