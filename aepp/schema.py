# Internal Library
import aepp
from aepp import config
from copy import deepcopy
import re
import typing

json_extend = [{'op': 'replace',
                'path': '/meta:intendedToExtend',
                'value': ['https://ns.adobe.com/xdm/context/profile',
                          'https://ns.adobe.com/xdm/context/experienceevent']}]


class Schema:

    schemas = {}
    schemasPaths = {}
    schemaClasses = {
        "event": "https://ns.adobe.com/xdm/context/experienceevent",
        "profile": "https://ns.adobe.com/xdm/context/profile"
    }

    def __init__(self, **kwargs):
        self.header = aepp.config._header
        self.header['Accept'] = "application/vnd.adobe.xdm+json"
        self.header.update(**kwargs)
        self.endpoint = config._endpoint+config._endpoint_schema
        pass

    def _getPaths(self, myDict: dict, path: list = None, key: str = None, list_path: list = None, verbose: bool = False):
        "Function to find the different paths existing in a schema"
        if path is None:
            path = []
        if list_path is None:
            list_path = []
        if type(myDict) == dict:
            if "properties" in myDict.keys():  # have the properties in dict
                if key is not None:
                    path.append(key)
                res = self._getPaths(myDict['properties'],
                                     key=key, path=path, list_path=list_path, verbose=verbose)
            elif type(myDict) == dict:  # 2 have not the property option
                if myDict.get("type", 'object') == "object":
                    for key, value in myDict.items():
                        recurs = self._getPaths(value, path=path,
                                                key=key, list_path=list_path, verbose=verbose)
                        if key in path:
                            path.pop()
                else:  # last level Not object type.
                    path.append(key)
                    full_path = ".".join(path)
                    if verbose:
                        print(full_path)
                    list_path.append(full_path)
                    path.pop()
                    return path
            return list_path

    def getStats(self):
        """
        Returns a list of the last actions realized on the Schema for this instance of AEP. 
        """
        path = '/stats/'
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def getSchemas(self):
        """
        Returns a lit of the schemas hosted in this instance.
        """
        path = '/tenant/schemas/'
        res = aepp._getData(self.endpoint+path, headers=self.header)
        res = res['results']
        return res

    def getSchema(self, schema_id: str = None, version: int = 1, save: bool = False, findPaths: bool = False, **kwargs):
        """
        Get the Schema. Requires a schema id.
        Response provided depends on the header set, you can change the Accept header with kwargs.
        Arguments:
            schema_id : REQUIRED : $id or meta:altId
            version : OPTIONAL : Version of the Schema asked (default 1)
            save : OPTIONAL : save the result in json file (default False)
            findPaths : find the paths present in your schema.
        Possible kwargs:
            Accept : Accept header to change the type of response.
            # /Schemas/lookup_schema
            more details held here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        self.header["Accept"] = "application/vnd.adobe.xed-full+json; version=" + \
            str(version)
        if kwargs.get('Accept', None) is not None:
            header['Accept'] = kwargs.get('Accept', header['Accept'])
        self.header['Accept-Encoding'] = 'identity'
        if schema_id.startswith('https://'):
            from urllib import parse
            schema_id = parse.quote_plus(schema_id)
        path = f'/tenant/schemas/{schema_id}'
        res = aepp._getData(self.endpoint + path)
        del self.header['Accept-Encoding']
        self.header['Accept'] = "application/json"
        if save:
            with open(f'{res["title"]}.json', 'w') as f:
                f.write(aepp.json.dumps(res, indent=4))
        self.schemas[res['title']] = res
        if findPaths:
            paths = self._getPaths(res)
            self.schemasPaths[res['title']] = paths
        return res

    def patchSchema(self, schema_id: str = None, changes: list = None, **kwargs):
        """
        Enable to patch the Schema with operation.
        Arguments:
            schema_id : REQUIRED : $id or meta:altId
            change : REQUIRED : List of changes that need to take place.
        information : http://jsonpatch.com/
        """
        path = f'/ tenant/schemas/{schema_id}'
        if schema_id is None:
            raise Exception("Require an ID for the schema")
        if type(changes) == dict:
            changes = list(changes)
        if schema_id.startswith('https://'):
            from urllib import parse
            schema_id = parse.quote_plus(schema_id)
        res = aepp._patchData(self.endpoint+path,
                              data=changes, headers=self.header)
        return res

    def putSchema(self, schema_id: str = None, changes: dict = None, **kwargs):
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
        path = f'/ tenant/schemas/{schema_id}'
        if schema_id is None:
            raise Exception("Require an ID for the schema")
        if schema_id.startswith('https://'):
            from urllib import parse
            schema_id = parse.quote_plus(schema_id)
        res = aepp._putData(self.endpoint+path,
                            data=changes, headers=self.header)
        return res

    def deleteSchema(self, schema_id: str = None, **kwargs):
        """
        Delete the request
        Arguments:
            schema_id : REQUIRED : $id or meta:altId
            It requires a allOf list that contains all the attributes that are required for creating a schema.
            #/Schemas/replace_schema
            More information on : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        path = f'/ tenant/schemas/{schema_id}'
        if schema_id is None:
            raise Exception("Require an ID for the schema")
        if schema_id.startswith('https://'):
            from urllib import parse
            schema_id = parse.quote_plus(schema_id)
        res = aepp._deleteData(self.endpoint+path, headers=self.header)
        return res

    def createSchema(self, schema: dict = None):
        """
        Create a Schema based on the data that are passed in the Argument.
        Arguments:
            schema : REQUIRED : The schema definition that needs to be created.
        """
        path = '/ tenant/schemas/'
        if type(schema) != dict:
            raise TypeError("Expecting a dictionary")
        if "allOf" not in schema.keys():
            raise Exception(
                "The schema must include an ‘allOf’ attribute (a list) referencing the $id of the base class the schema will implement.")
        res = aepp._postData(self.endpoint+path,
                             headers=self.header, data=schema)
        return res

    def findPath(self, schema: typing.Union[str, dict] = None, filter: str = None):
        """
        Return a list of the paths containing your filter.
        Arguments:
            schema : Schema JSON or title reference
            filter : REQUIRED : element you would like to find in your path.
            paths : OPTIONAL : list of all of the paths.
        """
        if type(schema) == str:
            if schema in self.schemasPaths.keys():
                paths = self.schemasPaths[schema]
            elif schema in self.schemas.keys():
                schema = self.schemas[schema]
                paths = self._getPaths(schema)
            else:
                raise Exception(
                    "Schema reference doesn't exist.\nMake sure to retrieve the schema you want to use beforehand")
        elif type(schema) == dict:
            try:
                paths = self._getPaths(schema)
            except:
                print('Issue with the schema reading. Verifiy your schema structure.')
                return None
        if filter is None:
            return paths
        elements = (element for element in paths if re.search(
            f".*{filter}.*", str(element)) is not None)
        return list(elements)

    def getMixins(self):
        path = '/tenant/mixins/'
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def getMixin(self, mixin_id: str = None, version: int = 1):
        """
        Arguments:
            mixin_id : meta:altId or $id
            version : version of the mixin
        """
        header = self.header
        if mixin_id.startswith('https://'):
            from urllib import parse
            mixin_id = parse.quote_plus(mixin_id)
        self.header['Accept-Encoding'] = 'identity'
        self.header.update({
            "Accept": "application/vnd.adobe.xed-full+json; version="+str(version)})
        path = f'/tenant/mixins/{mixin_id}'
        res = aepp._getData(self.endpoint + path, headers=header)
        del header['Accept-Encoding']
        self.header.update({
            "Accept": "application/json"})
        return res

    def deleteMixin(self, mixin_id: str = None):
        """
        Arguments:
            schema_id : meta:altId or $id
        """
        if mixin_id is None:
            raise Exception("Require an ID")
        path = f'/tenant/mixins/{mixin_id}'
        if mixin_id.startswith('https://'):
            from urllib import parse
            mixin_id = parse.quote_plus(mixin_id)
        res = aepp._deleteData(self.endpoint+path, headers=self.header)
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
        path = f'/tenant/mixins/{mixin_id}'
        if type(changes) == dict:
            changes = list(changes)
        res = aepp._patchData(self.endpoint+path,
                              data=changes, headers=self.header)
        return res

    def getUnions(self, **kwargs):
        """
        Get all of the unions that has been set for the tenant.
        Returns a dictionary.

        Possibility to add option using kwargs
        """
        path = '/tenant/unions'
        params = {}
        if len(kwargs) > 0:
            for key in kwargs.key():
                if key == 'limit':
                    if int(kwargs['limit']) > 500:
                        kwargs['limit'] = 500
                params[key] = kwargs.get(key, '')
        res = aepp._getData(self.endpoint+path,
                            params=params, headers=self.header)
        res = res['results']
        return res

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
        path = '/tenant/unions/{union_id}'
        self.header['Accept-Encoding'] = 'identity'
        self.header.update({
            "Accept": "application/vnd.adobe.xed-full+json; version="+str(version)})
        res = aepp._getData(self.endpoint + path, headers=self.header)
        del self.header['Accept-Encoding']
        self.header.update({
            "Accept": "application/json"})
        return res
