# internal library
import aepp
from aepp import config
from aepp import schema as aep_schema
from aepp import identity as aep_identity
from aepp import modules


def duplicateSchema(schema_obj: dict)->dict:
    """
    Duplication of schema requires you to pass an schema object WITH full parameter set to False.
    You would require to have the allOf in your keys of your object.
    Arguments:
        schema_obj : REQUIRED : the schema obj (not full).
    """
    copy_obj = modules.deepcopy(schema_obj)
    if schema_obj is None:
        raise Exception(
            "Expecting a dictionary to be copied (argument : schema_obj)")
    if 'allOf' not in copy_obj.keys():
        raise Exception("Expecting 'allOf' to be part of the schema")
    obj = {
        "type": "object",
        "title": copy_obj["title"],
        "description": copy_obj["description"],
        "allOf": [
            {
                "$ref": copy_obj["meta:class"]
            }
        ]
    }
    for element in copy_obj["allOf"]:
        if "$ref" in element.keys():
            obj['allOf'].append({"$ref": element['$ref']})
    return obj


def duplicateMixin(self, tenant_id: str = None, mixin_obj: dict = None)->dict:
    """
    Return an object ready to be ingested for creation.
    Arguments:
        tenant_id : REQUIRED : tenant id for root object.
        mixin_obj : REQUIRED : mixin object to duplicate.
    """
    if tenant_id is None:
        raise Exception(
            "Missing the tenant_id parameter")
    if mixin_obj is None:
        raise Exception(
            "Expecting a dictionary to be copied (argument : mixin_obj)")
    copy_obj = modules.deepcopy(mixin_obj)
    old_key = list(copy_obj['properties'].keys())[0]
    new_prop = {tenant_id:  copy_obj['properties'][old_key]}
    obj = {
        "title": copy_obj['title'],
        "description": copy_obj['description'],
        "type": copy_obj['type'],
        "meta:intendedToExtend": copy_obj['meta:intendedToExtend'],
        "definitions": {
            "customFields": {
                "properties":  new_prop}
        },
        "meta:resourceType": "mixins",
        "allOf": [{"$ref": "#/definitions/customFields"}]
    }
    return obj


def duplicateDataType(self, dt_obj: dict = None)->dict:
    """
    Returns an object ready to be used for Data Type creation, based on the data type given.
    Arguments:
        dt_obj : REQUIRED : Data Type object to be duplicated.
    """
    if dt_obj is None:
        raise Exception(
            "Expecting a dictionary to be copied (argument : dt_obj)")
    copy_obj = modules.deepcopy(dt_obj)
    obj = {
        "type": copy_obj["type"],
        "title": copy_obj["title"],
        "description": copy_obj["description"],
        "properties": copy_obj["properties"]
    }
    return obj


class Duplicator:
    """
    Duplicator class that will ingest your configuration file and start the duplication on your new instance.
    """

    def __init__(self):
        """
        Initialization of your duplicator.
        """
        self.CONFIG = {}

    def createConfigFile(self, n_duplicates: int = 1)->None:
        """
        Create a config file for your duplication job.
        The file will be later ingested with the importConfigFile method.
        Arguments:
            n_duplicates : OPTIONAL : Amount of duplicate you want to create.
        """
        duplicat_obj = {
            "config_file_location": "",
            "duplicate_id": ""
        }
        obj = {
            "original": {
                "original_id": "",
                "config_file_location": "",
            }
        }
        obj["duplicates"] = [duplicat_obj for n in range(n_duplicates)]
        with open('duplication_config.json', "w") as f:
            f.write(modules.json.dumps(obj, indent=4))

    def importConfigFile(self, file: object = None)->None:
        """
        ingest the configuration file and set some elements.
        Arguments:
            file : REQUIRED : filename or path to filename for config.
        """
        if file is None:
            raise Exception('Expecting a file as argument.')
        with open(modules.Path(file), 'r') as f:
            config = modules.json.loads(f.read())
        self.CONFIG = config

    def retrieveSchemas(self)->None:
        """
        Retrieve the schema and the mixin
        Arguments:
        """
        aepp.importConfigFile(
            self.CONFIG['original']['config_file_location'])
        schema_instance = aep_schema.Schema()
        tenant_id = schema_instance.getTenantId()
        schemas = schema_instance.getSchemas()
        obj_schema = {schema['title']: schema['meta:altId']
                      for schema in schemas if schema['title'].startswith("Adhoc") == False}
        for schema in obj_schema.values():
            schema = schema_instance.getSchema(schema, full=False, save=True)
            allOf = schema['allOf']
            allOf = [element for element in allOf if '$ref' in element.keys()]
            for element in allOf:
                if 'classes' in element['$ref']:
                    myClass = schema_instance.getClass(
                        element['$ref'], save=True)
                if 'mixins' in element['$ref']:
                    myMixin = schema_instance.getMixin(
                        element['$ref'], save=True)

    def retrieveIdentities(self)->None:
        """
        Retrieve the custom mixins.
        """
        aepp.importConfigFile(
            self.CONFIG['original']['config_file_location'])
        identity_instance = aep_identity.Identity(
            self.CONFIG['original']['instance_region'])
        custom_identities = identity_instance.getIdentities(
            only_custom=True, save=True)

    def retrieveDescriptors(self)->None:
        aepp.importConfigFile(
            self.CONFIG['original']['config_file_location'])
        schema_instance = aep_schema.Schema()
        descriptors = schema_instance.getDescriptors(
            type_desc="xdm:descriptorIdentity", save=True)

    def _readIdentities(self, folder: str = "Identity")->list:
        """
        Read the files on the specified folder, in the target duplicate instance.
        Arguments:
            folder : REQUIRED : Folder where the identities.json file can be found.(default : Identity)
        """
        here = modules.Path.cwd()
        if folder != "Identity":
            file_location = here.joinpath(f"{folder}/identities.json")
        else:
            file_location = here.joinpath(f"Identity/identities.json")
        with open(file_location, 'r') as f:
            identities = modules.json.loads(f.read())
        if type(identities) != list:
            identities = tuple(identities)
        return identities

    def _readDescriptors(self, folder: str = "Schema")->dict:
        """
        Read the files on the specified folder, in the target duplicate instance.
        Arguments:
            folder: REQUIRED: Folder where the identities.json file can be found.(default: Identity)
        """
        here = modules.Path.cwd()
        if folder != "Schema":
            file_location = here.joinpath(f"{folder}/descriptors.json")
        else:
            file_location = here.joinpath(f"Schema/descriptors.json")
        with open(file_location, 'r') as f:
            descriptors = modules.json.loads(f.read())
        if type(descriptors) != list:
            descriptors = tuple(descriptors)
        return descriptors

    def duplicateIdentities(self, folder: str = "Identity", save: bool = False, verbose: bool = False)->dict:
        """
        Create the identities in the duplicate instances placed in the config file.
        Expecting a file identities.json in a folder location. It returns a dictionary of the different duplicate_ids with identities created.
        Arguments:
            folder : OPTIONAL : if you have place the identities.json file in another folder. (default "Identity")
            save : OPTIONAL : if set to True, will generate a json file for your new identities.
            verbose : OPTIONAL : set to True, it will print comment during the processing.
        """
        identities = self._readIdentities(folder=folder)
        dict_identities = {}
        if verbose:
            print(f"Number of identities to create : {len(identities)}")
        for duplicate in self.CONFIG['duplicates']:
            if verbose:
                print(f"Selecting : {duplicate['duplicate_id']}")
            aepp.importConfigFile(
                duplicate['config_file_location'])
            schema_instance = aep_schema.Schema()
            tenant_id = schema_instance.getTenantId()
            identity_instance = aep_identity.Identity(
                duplicate['instance_region'])
            list_identities = []
            for identity in identities:
                if verbose:
                    print(f"Creating : {identity['name']}")
                try:
                    new_identity = identity_instance.createIdentity(name=identity['name'], code=identity['code'], idType=identity['idType'], description=identity.get(
                        'description', 'Python duplication tool'),)
                    list_identities.append(new_identity)
                except Exception as e:
                    print(
                        f"Error trying to create Identity : {identity['name']}, idType: {identity['idType']}")
                    print(e)
            if verbose and save:
                print(
                    f"creating a file in Identity Folder : {duplicate['duplicate_id']}_identities.json")
            aepp.saveFile(module='identity', file=list_identities,
                          filename=f"{duplicate['duplicate_id']}_identities.json")
            dict_identities[duplicate['duplicate_id']] = list_identities
        return dict_identities

    def _readSchemas(self, folder: str = "Schema", verbose: bool = False)->dict:
        """
        Read the files on the specified folder and returns the different elements found:
            - classes
            - mixins
            - schemas
            - dataTypes (not supported now)
        Arguments:
            folder : REQUIRED : Folder where the identities.json file can be found.(default : Schemas)
            verbose : OPTIONAL : set to True, it will print comment during the processing.
        """
        dict_elements = {'classes': {}, 'mixins': {},
                         'dataTypes': {}, 'schemas': {}}
        here = modules.Path.cwd()
        file_location = here.joinpath(f"{folder}")
        file_list = tuple([file_location.joinpath(file)
                           for file in modules.os.listdir(file_location)])
        for file in file_list:
            if verbose:
                print(f"{file}")
            with open(file, 'r') as f:
                data = modules.json.loads(f.read())
            if type(data) is dict:
                if data.get("meta:resourceType", 'unknown') == "classes":
                    dict_elements['classes'][data['title']] = {
                        "$id": data['$id'],
                        "type": data['type'],
                        "title": data['title'],
                        "description": data['description'],
                        "allOf": [{"$ref": data['meta:extends'][0]}],
                    }
                elif data.get("meta:resourceType", 'unknown') == "mixins":
                    dict_elements['mixins'][data['title']] = {
                        "$id": data['$id'],
                        "type": data['type'],
                        "title": data['title'],
                        "description": data['description'],
                        "meta:intendedToExtend": data['meta:intendedToExtend'],
                        "definitions": {
                            "customFields": {
                                "properties": data["properties"]
                            }
                        },
                        "allOf": [{"$ref": "#/definitions/customFields"}]
                    }
                elif data.get("meta:resourceType", 'unknown') == "schemas":
                    dict_elements['schemas'][data['title']] = {
                        "$id": data['$id'],
                        "type": data['type'],
                        "title": data['title'],
                        "description": data['description'],
                        "allOf": data['allOf']
                    }
                # no data types for now
        return dict_elements

    def _createClasses(self, class_elements: dict = None, header: dict = None, verbose: bool = False, save: bool = False)->dict:
        """
        Create the class based on the element given.
        Returns a dictionary of old $id with new $id.
        Arguments:
            class_elements : REQUIRED : Dictionary of classes to create.
            header : REQUIRED : header from the instance of AEP API to use.
            verbose : OPTIONAL : set to True, it will print comment during the processing.
        """
        if header is None:
            raise Exception("excepting the header to be passed")
        dict_ids = {}
        for key in class_elements:
            clas = modules.deepcopy(class_elements[key])
            if verbose:
                print(f"creating class : {clas['title']}")
            del clas['$id']
            schema_instance = aep_schema.Schema(**header)
            res = schema_instance.createClass(clas)
            if '$id' not in res:
                raise Exception(
                    f"issue creating the class : {clas['title']}")
                print(res)
                res['$id'] = res['title']
            dict_ids[class_elements[key]['$id']] = res['$id']
        return dict_ids

    def _createMixins(self, mixins: dict = None, header: dict = None, verbose: bool = False, save: bool = False)->dict:
        """
        Create the mixins based on the elements given.
        Returns a dictionary of old $id with new $id.
        Arguments:
            mixins : REQUIRED : Dictionary of mixins to create.
            header : REQUIRED : header from the instance of AEP API to use.
            verbose : OPTIONAL : set to True, it will print comment during the processing.
        """
        if header is None:
            raise Exception("excepting the header to be passed")
        dict_ids = {}
        for key in mixins:
            mixin = modules.deepcopy(mixins[key])
            if verbose:
                print(f"creating mixin : {mixin['title']}")
            del mixin['$id']
            #print(aepp.json.dumps(mixin, indent=4))
            schema_instance = aep_schema.Schema(**header)
            res = schema_instance.createMixin(mixin)
            # handling error
            if '$id' not in res:
                print(f"No Id found in response for {mixin['title']}")
                print(res)
                res['$id'] = res['title']
            dict_ids[mixins[key]['$id']] = res['$id']
        return dict_ids

    def _createSchemas(self, schemas: dict = None, header: dict = None, verbose: bool = False, save: bool = False)->dict:
        """
        Create the class based on the element given.
        Returns a dictionary of old $id with new $id.
        Arguments:
            schemas : REQUIRED : Dictionary of schemas to create.
            header : REQUIRED : header from the instance of AEP API to use.
            verbose : OPTIONAL : set to True, it will print comment during the processing.
        """
        if header is None:
            raise Exception("excepting the header to be passed")
        dict_ids = {}  # require for the descriptors.
        for key in schemas:
            schema = modules.deepcopy(schemas[key])
            if verbose:
                print(f"creating schema : {schema['title']}")
            old_id = schema['$id']
            del schema['$id']
            schema_instance = aep_schema.Schema(**header)
            res = schema_instance.createSchema(schema)
            # handling when issue creating schema
            if '$id' not in res:
                print(f"No Id found in response for {schema['title']}")
                print(res)
                res['$id'] = None
            dict_ids[old_id] = res['$id']
        return dict_ids

    def _retrieveEnabledSchemas(self, schema_instance: object = None, verbose: bool = False)->list:
        """
        Retrieve a list of the schema id that have been enabled for Union Profile.
        Returns a list.
        Arguments:
            schema_instance : REQUIRED : schema instance to make calls
            verbose : OPTIONAL : set to True, it will print comment during the processing.
        """
        schemas = schema_instance.getSchemas()
        enabled_schemas = [schema['$id'] for schema in schemas if schema.get(
            'meta:immutableTags', None) is not None]
        if verbose:
            print(
                f'There are {len(enabled_schemas)} Schema enabled with Union Profile')
        return enabled_schemas

    def _duplicateEnabledSchemas(self, schema_instance: object = None, list_original_enabledIds: list = None, matching_dict: dict = None, verbose: bool = False):
        """
        Enabled the schemas for union profile in the duplicate instance.
        Arguments:
            schema_instance : REQUIRED : schema instance to make calls
            list_original_enabledIds : REQUIRED : List returned by _retrieveEnabledSchemas.
            matching_dict : REQUIRED : dictionary containing old and new id.
            verbose : OPTIONAL : set to True, it will print comment during the processing.
        """
        updateObj = [
            {"op": "add", "path": "/meta:immutableTags", "value": ["union"]}]
        list_res = []
        for myId in list_original_enabledIds:
            new_id = matching_dict[myId]
            res = schema_instance.patchSchema(new_id, updateObj)
            if verbose:
                if 'meta:immutableTags' in res.keys():
                    print(f'Schema {new_id} has been enabled for Union Profle')
                else:
                    print(f'ERROR enabling schema {new_id} for Union Profile')
            list_res.append(res)
        return list_res

    def _createDescriptors(self, list_descriptors: list, header: dict = None, verbose: bool = False):
        """
        Takes the list of descriptors and create them.
        Arguments:
            list_descriptors : REQUIRED : List of all the descriptors to create with their fields required for creation.
        """
        if header is None:
            raise Exception("excepting the header to be passed")
        if verbose:
            print(f"creating descriptors")
        list_result = []
        for element in list_descriptors:
            schema_instance = aep_schema.Schema(**header)
            print(element['namespace'])
            res = schema_instance.createDescriptor(**element)
            if "xdm:sourceSchema" not in res.keys():
                print('Issue creating descriptor')
                print(res)
            list_result.append(res)
        return list_result

    def duplicateSchemas(self, folder: str = "Schema", enableProfile: bool = False, verbose: bool = False)->dict:
        """
        It will duplicate the schemas, mixins, classes from the original instance to the duplicates.
        Expecting a folder to exist with the different schema retrieved previously.
        Arguments:
            folder : OPTIONAL : if you have place the files in another folder. (default "Schema")
            enableProfile : OPTIONAL : If you want to enable schemas for Profile. 
            verbose : OPTIONAL : set to True, it will print comment during the processing.
        """
        dict_elements = self._readSchemas(folder=folder)
        list_descriptors = self._readDescriptors()
        aepp.importConfigFile(
            self.CONFIG['original']['config_file_location'])
        schema_instance = aep_schema.Schema()
        original_tenant = schema_instance.getTenantId()
        if enableProfile:
            if verbose:
                print('retrieving Enabled Schema for Union Profile')
            list_enabledSchemas = self._retrieveEnabledSchemas(
                schema_instance, verbose=verbose)
        if verbose:
            print(f"{len(dict_elements['classes'])} classes to create")
            print(f"{len(dict_elements['mixins'])} mixins to create")
            print(f"{len(dict_elements['schemas'])} schemas to create")
        duplicates_ids = {}
        for duplicate in self.CONFIG['duplicates']:
            if verbose:
                print(f"Selecting : {duplicate['duplicate_id']}")
            aepp.importConfigFile(
                duplicate['config_file_location'])
            schema_instance = aep_schema.Schema()
            tenant_id = schema_instance.getTenantId()
            # starting creating classes
            classes_translate = self._createClasses(
                class_elements=dict_elements['classes'], header=schema_instance.header, verbose=verbose)
            # need to change tenant_id for mixins
            old_mixins = dict_elements['mixins']
            new_mixins = {}
            for mixin in old_mixins:
                obj = modules.deepcopy(old_mixins[mixin])
                new_def = {
                    "customFields": {
                        "properties": {
                            f"_{tenant_id}":  old_mixins[mixin]['definitions']['customFields']['properties'][f"_{original_tenant}"]}
                    }
                }
                obj["definitions"] = new_def
                # translate classes
                meta_extends = []
                for clas in obj["meta:intendedToExtend"]:
                    if clas in classes_translate.keys():
                        meta_extends.append(classes_translate[clas])
                    else:
                        meta_extends.append(clas)
                obj["meta:intendedToExtend"] = meta_extends
                new_mixins[mixin] = obj
            mixins_translate = self._createMixins(
                new_mixins, header=schema_instance.header, verbose=verbose)
            # need to translate the schemas
            translat = {**classes_translate, **mixins_translate}
            old_schemas = dict_elements['schemas']
            new_schemas = {}
            for schema in old_schemas:
                obj = modules.deepcopy(old_schemas[schema])
                allOf = []
                for element in obj['allOf']:
                    if "$ref" in element.keys():
                        if element['$ref'] in translat.keys():
                            allOf.append(
                                {'$ref': translat[element['$ref']]})
                        else:
                            allOf.append({'$ref': element['$ref']})
                obj['allOf'] = allOf
                new_schemas[schema] = obj
                # creating schemas
            trans_schemas = self._createSchemas(
                schemas=new_schemas, header=schema_instance.header, verbose=verbose)
            new_descriptors = []
            if verbose:
                print('translating descriptors')
            for desc in list_descriptors:
                new_sourceProperty = desc["xdm:sourceProperty"].replace(
                    f'_{original_tenant}/', f'_{tenant_id}/')
                new_descriptors.append({
                    "desc_type": "xdm:descriptorIdentity",
                    "sourceSchema": trans_schemas[desc['xdm:sourceSchema']],
                    "sourceProperty": new_sourceProperty,
                    "namespace": desc["xdm:namespace"],
                    "xdmProperty": "xdm:code",
                    "primary": desc["xdm:isPrimary"]
                })
            res = self._createDescriptors(
                new_descriptors, schema_instance.header, verbose=verbose)
            duplicates_ids[duplicate['duplicate_id']] = trans_schemas
            if enableProfile:
                if verbose:
                    print(
                        f'Enabling {len(list_enabledSchemas)} Schemas for Union Profile')
                self._duplicateEnabledSchemas(
                    schema_instance, list_enabledSchemas, trans_schemas, verbose=verbose)

        return duplicates_ids  # return old id and new id for schema

    def completeDuplication(self, enableSchemas: bool = False, verbose: bool = False)->dict:
        """
        This will completely duplicate an original configuration (AEP Experience Cloud Instance or Sandbox) to the new sandbox.
        Return a dictionary containing new identities and a dictionary of old and new schemas id.
        Arguments:
            enableSchemas : OPTIONAL : Boolean to duplicate Schema enablement to Union Profile.
            verbose : OPTIONAL : set to True, it will print comment during the processing.
        """
        # retrieving information from base property
        self.retrieveIdentities()
        self.retrieveSchemas()
        self.retrieveDescriptors()
        # creating new identities
        new_identities = self.duplicateIdentities(verbose=verbose)
        # create new schema and descriptors
        translate_schemas = self.duplicateSchemas(
            enableProfile=enableSchemas, verbose=verbose)
        data = {
            'identities': new_identities,
            'schemas': translate_schemas
        }
        return data
