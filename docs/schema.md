# Schema module in aepp

This documentation will provide you some explanation on how to use the schema module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/schema-registry/).\
Alternatively, you can use the docstring in the methods to have more information.


## Menu
- [Schema module in aepp](#schema-module-in-aepp)
  - [Menu](#menu)
  - [Importing the module](#importing-the-module)
  - [Generating a Schema instance](#generating-a-schema-instance)
    - [Connecting to different sandboxes](#connecting-to-different-sandboxess)
  - [Schema attributes](#schema-attributes)
  - [Schema methods](#schema-methods)
  - [Tips for schema requests](#tips-for-schema-requests)
    - [1. Generate Samples](#1-generate-samples)
    - [2. Using parameters in getSchema](#2-using-parameters-in-getschema)
    - [3. Hierarchy matters](#3-hierarchy-matters)
    - [4. Descriptors are important](#4-descriptors-are-important)
  - [Use Cases](#use-cases)
    - [Copying a mixin for ingestion](#copying-a-mixin-for-ingestion)
    - [Creating ExperienceEvent and Profile Schema](#creating-experienceevent-and-profile-schema)
    - [Get paths from schema](#get-paths-from-schema)
  - [SchemaManager](#schemamanager)
  - [FieldGroupManager](#fieldgroupmanager)
  - [Data Type Manager](#data-type-manager)

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `schema` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json', sandbox='prod', connectInstance=True)

from aepp import schema
```

## Generating a Schema instance

Because you can connect to multiple AEP instance at once, or multiple sandboxes, you would need to setup an instance of the `Schema` class from that module.\
Following the previous method described above, you can realize this:

```python
mySchemaConnection1 = schema.Schema(config=prod)
```

Several parameters are possibles when instantiating the class:\
* container_id : OPTIONAL : "tenant"(default) or "global"
* config : OPTIONAL : mostly used to pass a ConnectObject instance that is linked to one sandbox. 
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : A logging object that can be passed for debuging or logging elements, see [logging documentation](./logging.md)

### Connecting to different sandboxes

You can use the `connectInstance` parameter to load multiple sandbox configurations and save them for re-use later on, when instantiating the `Schema` class. 
As described above, it can be useful when you want to connect to multiple sandboxes with the same authentication.\
In that case, the 2 instances will be created as such:

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json', sandbox='prod', connectInstance=True)
dev = aepp.importConfigFile('myConfig_file.json', sandbox='dev', connectInstance=True)

from aepp import schema

mySchemaConnection1 = schema.Schema(config=prod)
mySchemaConnection2 = schema.Schema(config=dev)

```

## Schema attributes

Once you have instantiated the `Schema` class, you will have access to the following attributes.
* sandbox : provide which sandbox is currently being used
* header : provide the default header which is used for the requests.
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods.
* containerId : In case you have modified the default container.
* PATCH_OBJ : An example of Patch operation payload
* DESCRIPTOR_TYPES : A list of descriptor types
* data : an object that contains the following information depending the methods used **previously**
  * schemas_id : dictionary of {SchemaName:$id} when the `getSchemas` methods has been used
  * schemas_altId : dictionary of {SchemaName:altId} when the `getSchemas` methods has been used
  * fieldGroups_id : dictionary of {FieldGroupName:$id} when the `getFieldGroups` methods has been used
  * fieldGroups_altId : dictionary of {FieldGroupName:altId} when the `getFieldGroups` methods has been used
  * fieldGroupsGlobal_id : dictionary of Out of the box field groups such as {FieldGroupName:$id} when the `getFieldGroupsGlobal` methods has been used
  * fieldGroupsGlobal_altId : dictionary of Out of the box field groups such as {FieldGroupName:altId} when the `getFieldGroupsGlobal` methods has been used

## Schema methods

below are all the different methods that are available to you once you have instantiated the `Schema` class.

### getResource
Template for requesting data with a GET method.\
Arguments:
* endpoint : REQUIRED : The URL to GET
* params: OPTIONAL : dictionary of the params to fetch
* format : OPTIONAL : Type of response returned. Possible values:
  * json : default
  * txt : text file
  * raw : a response object from the requests module

### getStats
Returns a list of the last actions realized on the Schema for this instance of AEP.

### getTenantId
Return the tenantID for the AEP instance.

### getBehaviors
Return a list of behaviors.

### getBehavior
Retrieve a specific behavior for class creation.\
Arguments:
* behaviorId : REQUIRED : the behavior ID to be retrieved.

### getSchemas
Returns the list of schemas retrieved for that instances in a "results" list.\
Arguments:
* classFilter : OPTIONAL : filter to a specific class.\
  Example :
  * https://ns.adobe.com/xdm/context/experienceevent
  * https://ns.adobe.com/xdm/context/profile
  * https://ns.adobe.com/xdm/data/adhoc
* excludeAdhoc : OPTIONAL : exclude the adhoc schemas
* output : OPTIONAL : either "raw" for a list or "df" for dataframe\
Possible kwargs:
* debug : if set to true, will print the result when error happens
* format : if set to "xed", returns the full JSON for each resource (default : "xed-id" -  short summary)

### getSchema
Get the Schema. Requires a schema id.\
Response provided depends on the header set, you can change the Accept header with kwargs.\
Arguments:
* schemaId : REQUIRED : $id or meta:altId
* version : OPTIONAL : Version of the Schema asked (default 1)
* full : OPTIONAL : True (default) will return the full schema.False just the relationships.
* desc : OPTIONAL : If set to True, return the identity used as the descriptor.
* deprecated : OPTIONAL : Display the deprecated field from that schema
* flat : OPTIONAL : If set to True, return a flat schema for pathing.
* schema_type : OPTIONAL : set the type of output you want (xdm or xed) Default : xdm.
* save : OPTIONAL : save the result in json file (default False)\
Possible kwargs:
* Accept : Accept header to change the type of response.\
more details held here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html

### getSchemaPaths
Returns a list of the path available in your schema.\
Arguments:
* schemaId : REQUIRED : The schema you want to retrieve the paths for
* simplified : OPTIONAL : Default True, only returns the list of paths for your schemas.
* save : OPTIONAL : Save your schema paths in a file. Always the NOT simplified version.


### getSchemaSample
Generate a sample data from a schema id.\
Arguments:
* schema_id : REQUIRED : The schema ID for the sample data to be created.
* save : OPTIONAL : save the result in json file (default False)
* version : OPTIONAL : version of the schema to request

### patchSchema
Enable to patch the Schema with operation.
Arguments:
* schema_id : REQUIRED : $id or meta:altId
* change : REQUIRED : List of changes that need to take place.\
Example:
```python
    [
        {
            "op": "add",
            "path": "/allOf",
            "value": {'$ref': 'https://ns.adobe.com/emeaconsulting/mixins/fb5b3cd49707d27367b93e07d1ac1f2f7b2ae8d051e65f8d',
        'type': 'object',
        'meta:xdmType': 'object'}
        }
    ]
```
information : http://jsonpatch.com/

### putSchema
A PUT request essentially re-writes the schema, therefore the request body must include all fields required to create (POST) a schema.\
This is especially useful when updating a lot of information in the schema at once.\
Arguments:
* schemaId : REQUIRED : $id or meta:altId
* schemaDef : REQUIRED : dictionary of the new schema.\
  It requires a allOf list that contains all the attributes that are required for creating a schema.\
More information on : https://www.adobe.io/apis/experienceplatform/home/api-reference.html

### deleteSchema
Delete the request\
Arguments:
* schema_id : REQUIRED : $id or meta:altId to be deleted

### createSchema
Create a Schema based on the data that are passed in the Argument.\
Arguments:
* schema : REQUIRED : The schema definition that needs to be created.

### createExperienceEventSchema
Create an ExperienceEvent schema based on the list mixin ID provided.\
Arguments:
* name : REQUIRED : Name of your schema
* mixinIds : REQUIRED : dict of mixins $id and their type ["object" or "array"] to create the ExperienceEvent schema\
    Example `{'mixinId1':'object','mixinId2':'array'}`\
    if just a list is passed, it infers a 'object type'
* fieldGroupIds : REQUIRED : List of fieldGroup $id to create the Indiviudal Profile schema\
    Example `{'fgId1':'object','fgId2':'array'}`\
    if just a list is passed, it infers a 'object type'
* description : OPTIONAL : Schema description

### createProfileSchema
Create an IndividualProfile schema based on the list mixin ID provided.\
Arguments:
* name : REQUIRED : Name of your schema
* mixinIds : REQUIRED : List of mixins $id to create the Indiviudal Profile schema\
    Example `{'mixinId1':'object','mixinId2':'array'}`\
    if just a list is passed, it infers a 'object type'
* fieldGroupIds : REQUIRED : List of fieldGroup $id to create the Indiviudal Profile schema\
    Example `{'fgId1':'object','fgId2':'array'}`\
    if just a list is passed, it infers a 'object type'
* description : OPTIONAL : Schema description

### addFieldGroupToSchema
Take the list of field group ID to extend the schema.\
Return the definition of the new schema with added field groups.\
Arguments:
* schemaId : REQUIRED : The ID of the schema (alt:metaId or $id)
* fieldGroupIds : REQUIRED : The IDs of the fields group to add. It can be a list or dictionary.\
    Example `{'fgId1':'object','fgId2':'array'}`\
    if just a list is passed, it infers a 'object type'

### getClasses
Return the classes of the AEP Instances.\
Arguments:
* prop : OPTIONAL : A comma-separated list of top-level object properties to be returned in the response.\
  For example, `property=meta:intendedToExtend==https://ns.adobe.com/xdm/context/profile`
* oderBy : OPTIONAL : Sort the listed resources by specified fields. For example orderby=title
* limit : OPTIONAL : Number of resources to return per request, default 300 - the max.
* excludeAdhoc : OPTIONAL : Exlcude the Adhoc classes that have been created.
* output : OPTIONAL : type of output, default "raw", can be "df" for dataframe.\
kwargs:
* debug : if set to True, will print result for errors

### getClassesGlobal
Return the Out-of-the-box classes of the AEP Instances.
Arguments:
* prop : OPTIONAL : A comma-separated list of top-level object properties to be returned in the response.\
  For example, `property=meta:intendedToExtend==https://ns.adobe.com/xdm/context/profile`
* oderBy : OPTIONAL : Sort the listed resources by specified fields. For example orderby=title
* limit : OPTIONAL : Number of resources to return per request, default 300 - the max.
* output : OPTIONAL : type of output, default "raw", can be "df" for dataframe.\
kwargs:
* debug : if set to True, will print result for errors

### getClass
Return a specific class.\
Arguments:
* classId : REQUIRED : the meta:altId or $id from the class
* full : OPTIONAL : True (default) will return the full schema.False just the relationships.
* desc : OPTIONAL : If set to True, return the descriptors.
* deprecated : OPTIONAL : Display the deprecated field from that schema (False by default)
* xtype : OPTIONAL : either "xdm" (default) or "xed". 
* version : OPTIONAL : the version of the class to retrieve.
* save : OPTIONAL : To save the result of the request in a JSON file.


### createClass
Create a class based on the object pass. It should include the "allOff" element.\
Arguments:
* class_obj : REQUIRED : You can pass a complete object to create a class, include a title and a "allOf" element.
* title : REQUIRED : Title of the class if you want to pass individual elements
* class_template : REQUIRED : type of behavior for the class, either "https://ns.adobe.com/xdm/data/record" or "https://ns.adobe.com/xdm/data/time-series"\
Possible kwargs: 
* description : To add a description to a class.

### putClass
Replace the current definition with the new definition.\
Arguments:
* classId : REQUIRED : The class to be updated ($id or meta:altId)
* class_obj : REQUIRED : The dictionary defining the new class definition

### patchClass
Patch a class with the operation specified such as:\
```python
update = [{
    "op": "replace",
    "path": "title",
    "value": "newTitle"
}]
```
Possible operation value : "replace", "remove", "add"\
Arguments:
* classId : REQUIRED : The class to be updated  ($id or meta:altId)
* operation : REQUIRED : List of operation to realize on the class


### deleteClass
Delete a class based on the its ID.\
Arguments:
* classId : REQUIRED : The class to be deleted  ($id or meta:altId)


### getFieldGroups
returns the fieldGroups of the account.\
Arguments:
* format : OPTIONAL : either "xdm" or "xed" format\
kwargs:
* debug : if set to True, will print result for errors

### getFieldGroupsGlobal
returns the global fieldGroups of the account.\
Arguments:
* format : OPTIONAL : either "xdm" or "xed" format
* output : OPTIONAL : either "raw" (default) or "df" for dataframe\
kwargs:
* debug : if set to True, will print result for errors

### getFieldGroup
Returns a specific mixin / field group.\
Arguments:
* fieldGroupId : REQUIRED : meta:altId or $id
* version : OPTIONAL : version of the mixin
* full : OPTIONAL : True (default) will return the full schema.False just the relationships
* desc : OPTIONAL : Add descriptor of the field group
* type : OPTIONAL : Either "xed" (default) or "xdm"
* flat : OPTIONAL : if the fieldGroup is flat (false by default)
* deprecated : OPTIONAL : Display the deprecated fields from that schema
* save : Save the fieldGroup to a JSON file

### copyFieldGroup
Copy the dictionary returned by getFieldGroup to the only required elements for copying it over.\
Arguments:
* fieldGroup : REQUIRED : the object retrieved from the getFieldGroup.
* tenantId : OPTIONAL : if you want to change the tenantId (if None doesn't rename)
* name : OPTIONAL : rename your mixin (if None, doesn't rename it)

### createFieldGroup
Create a mixin based on the dictionary passed.\
Arguments :
* fieldGroup_obj : REQUIRED : the object required for creating the field group.\
  Should contain title, type, definitions

### deleteFieldGroup
Arguments:
* fieldGroupId : meta:altId or $id of the field group to be deleted

### patchFieldGroup
Update the mixin with the operation described in the changes.\
Arguments:
* fieldGroupId : REQUIRED : meta:altId or $id
* changes : REQUIRED : dictionary on what to update on that mixin.
Example:
```python
    [
        {
            "op": "add",
            "path": "/allOf",
            "value": {'$ref': 'https://ns.adobe.com/emeaconsulting/mixins/fb5b3cd49707d27367b93e07d1ac1f2f7b2ae8d051e65f8d',
        'type': 'object',
        'meta:xdmType': 'object'}
        }
    ]
```
information : http://jsonpatch.com/

### putFieldGroup
A PUT request essentially re-writes the schema, therefore the request body must include all fields required to create (POST) a schema.\
This is especially useful when updating a lot of information in the schema at once.\
Arguments:
* fieldGroupId : REQUIRED : $id or meta:altId
* fieldGroupObj : REQUIRED : dictionary of the new Field Group.
* It requires a allOf list that contains all the attributes that are required for creating a schema.


### getUnions
Get all of the unions that has been set for the tenant.\
Returns a dictionary.\
Possibility to add option using kwargs


### getUnion
Get a specific union type. Returns a dictionnary\
Arguments :
* union_id : REQUIRED :  meta:altId or $id
* version : OPTIONAL : version of the union schema required.


### getXDMprofileSchema
Returns a list of all schemas that are part of the XDM Individual Profile.


### getDataTypes
Get the data types from a container.\
Possible kwargs:
* properties : str :limit the amount of properties return by comma separated list.


### getDataType
Retrieve a specific data type id\
Argument:
* dataTypeId : REQUIRED : The resource meta:altId or URL encoded $id URI.
* full : OPTIONAL : If you want to retrieve the full setup of your data type.(default True)
* type : OPTIONAL : default 'xdm', you can also pass the 'xed' format
* version : OPTIONAL : The version of your data type
* save : OPTIONAL : Save the data type in a JSON file.


### createDataType
Create Data Type based on the object passed.\
Argument:
* dataTypeObj : REQUIRED : The data type definition


### patchDataType
Patch an existing data type with the operation provided.\
Arguments:
* dataTypeId : REQUIRED : The Data Type ID to be used
* operations : REQUIRED : The list of operation to be applied on that Data Type.
  Example : 
  ```python
  '[
    {
    "op": "replace",
    "path": "/loyaltyLevel/meta:enum",
    "value": {
        "ultra-platinum": "Ultra Platinum",
        "platinum": "Platinum",
        "gold": "Gold",
        "silver": "Silver",
        "bronze": "Bronze"
      }
    }
  ]'
  ```

### putDataType
Replace an existing data type definition with the new definition provided.\
Arguments:
* dataTypeId : REQUIRED : The Data Type ID to be replaced
* dataTypeObj : REQUIRED : The new Data Type definition.


### getDescriptors
Return a list of all descriptors contains in that tenant id.\
By default return a v2 for pagination.\
Arguments:
* type_desc : OPTIONAL : if you want to filter for a specific type of descriptor. None default.\
    (possible value : "xdm:descriptorIdentity")
* id_desc : OPTIONAL : if you want to return only the id.
* link_desc : OPTIONAL : if you want to return only the paths.
* save : OPTIONAL : Boolean that would save your descriptors in the schema folder. (default False)\
possible kwargs:
* prop : additional property that you want to filter with, such as "prop=f"xdm:sourceSchema==schema$Id"


### getDescriptor
Return a specific descriptor\
Arguments:
* descriptorId : REQUIRED : descriptor ID to return (@id).
* save : OPTIONAL : Boolean that would save your descriptors in the schema folder. (default False)


### createDescriptor
Create a descriptor attached to a specific schema.\
Arguments:
* descriptorObj : REQUIRED : If you wish to pass the whole object.
* desc_type : REQUIRED : the type of descriptor to create.(default Identity)
* sourceSchema : REQUIRED : the schema attached to your identity ()
* sourceProperty : REQUIRED : the path to the field
* namespace : REQUIRED : the namespace used for the identity
* primary : OPTIONAL : Boolean (True or False) to define if it is a primary identity or not (default None).\
possible kwargs:
* version : version of the creation (default 1)
* xdm:property : type of property

### deleteDescriptor
Delete a specific descriptor.
Arguments:
* descriptor_id : REQUIRED : the descriptor id to delete


### putDescriptor
Replace the descriptor with the new definition. It updates the whole definition.\
Arguments:
* descriptorId : REQUIRED : the descriptor id to replace
* descriptorObj : REQUIRED : The full descriptor object if you want to pass it directly.


### getAuditLogs
Returns the list of the changes made to a ressource (schema, class, mixin).\
Arguments:
* resourceId : REQUIRED : The "$id" or "meta:altId" of the resource.


### exportResource
Return all the associated references required for importing the resource in a new sandbox or a new Org.\
Argument:
* resourceId : REQUIRED : The $id or meta:altId of the resource to export.
* Accept : OPTIONAL : If you want to change the Accept header of the request.


### importResource
Import a resource based on the export method.\
Arguments:
* dataResource : REQUIRED : dictionary of the resource retrieved.


### extendFieldGroup
Patch a Field Group to extend its compatibility with ExperienceEvents, IndividualProfile and Record.\
Arguments:
* fieldGroupId : REQUIRED : meta:altId or $id of the field group.
* values : OPTIONAL : If you want to pass the behavior you want to extend the field group to.
  Examples: 
  ```python
  ["https://ns.adobe.com/xdm/context/profile",
  "https://ns.adobe.com/xdm/context/experienceevent"]
  ```
    by default profile and experienceEvent will be added to the FieldGroup.
* tenant : OPTIONAL : default "tenant", possible value 'global'


### enableSchemaForRealTime
Enable a schema for real time based on its ID.\
Arguments:
* schemaId : REQUIRED : The schema ID required to be updated


### FieldGroupManager
Generates a Field Group Manager instance using the information provided by the schema instance.\
Arguments:
* fieldGroup : OPTIONAL : the field group definition as dictionary OR the ID to access it OR nothing if you want to start from scratch
* title : OPTIONAL : If you wish to change the tile of the field group.


### SchemaManager
Generates a Schema Manager instance using the information provided by the schema instance.\
Arguments:
* schema : OPTIONAL : the schema definition as dictionary OR the ID to access it OR Nothing if you want to start from scratch
* fieldGroups : OPTIONAL : If you wish to add a list of fieldgroups.
* fgManager : OPTIONAL : If you wish to handle the different field group passed into a Field Group Manager instance and have additional methods available.

### DataTypeManager
Generates a Data Type Manager instance using the information provided by the schema instance.\
Arguments:
* dataType : OPTIONAL : The data Type definition, the reference Id or nothing if you want to start from scratch.

### compareDFschemas
Compare 2 schema dataframe returned by the SchemaManager `to_dataframe` method.\
Arguments:
* df1 : REQUIRED : the first schema dataframe to compare
* df2 : REQUIRED : the second schema dataframe to compare\
possible keywords:
* title1 : title of the schema used in the dataframe 1 (default df1)
* title2 : title of the schema used in the dataframe 2 (default df2)\
The title1 and title2 will be used instead of df1 or df2 in the results keys presented below.

Results: 
* Results are stored in a dictionary with these keys:
  * df1 (or title1) : copy of the dataframe 1 passed
  * df2 (or title2) : copy of the dataframe 2 passed
  * fielgroups: dictionary containing
    * aligned : boolean to define if the schema dataframes contain the same field groups
    * df1_missingFieldGroups : tuple of field groups missing on df1 compare to df2
    * df2_missingFieldGroups : tuple of field groups missing on df2 compare to df1
  * paths: dictionary containing
    * aligned : boolean to define if the schema dataframes contain the same fields.
    * df1_missing : tuple of the paths missing in df1 compare to df2
    * df2_missing : tuple of the paths missing in df2 compare to df1
  * type_issues: list of all the paths that are not of the same type in both schemas.


## Tips for schema requests

Here are a list of tips when using the aepp module to look at your schema.

### 1. Generate Samples

The API provide a way to generate sample schema for ingestion.\
Note that all of the fields will be used for the generation of the sample.\
The method is called `getSchemaSample` and requires a schemaId to be passed.\
My tip would be to generate 10 of them so I can modify them and create different ingestion files.

```python
mySchema = schema.Schema()
## schemaId = XXXXX

mySamples = [mySchema.getSchemaSample(XXXXX) for x in range(10)]
```

### 2. Using parameters in getSchema

When you retrieve a specific schema, you can use parameters to extract different views of your schemas.\
The available parameters:

* full : OPTIONAL : True (default) will return the full schema.False just the relationships
* desc : OPTIONAL : If set to True, return the identity used as the descriptor.
* schema_type : OPTIONAL : set the type of output you want (xdm or xed) Default : xdm.

With these parameters you may achieve returning a specific view fitting your needs.

### 3. Hierarchy matters

Knowing the relationships / hierarchy between the different component of schema constructors will help you on your pipeline.\
Example : You cannot delete a class if it is used in a schema and you cannot delete a mixin if it is used in a Schema.

From bottom to top, here is the list of elements.

1. Class : define the type of schema that will be built
2. Data Types : a single piece of data description
3. Mixins : can contains several data types
4. Schema : use class and mixins to build a data model

### 4. Descriptors are important

The descriptors methods are important as they are setting which elements of your schema are identities.\
These identities are important to build the data model on AEP for the Unified Profile setup.\
In addition to these identities, you need to enable the schema for unified profile.

## Use Cases

The module has some additional methods available to help you deal with schemas.\

### Copying a mixin for ingestion

The use-case was to be able to re-use an existing schema in a different sandbox or experience cloud in an easy manner.\
We all know that the API can help us with it but it can still be cumbersome to prepare the object for that.

The module provide a `copyMixin` capability that will trim down the object to the format needed for the `createMixin` method.\
This method takes 3 arguments:
* mixin : REQUIRED : the object retrieved from the getMixin.
* name : OPTIONAL : rename your mixin if you want (if None, it will take the same name)
* tenantId : OPTIONAL : if you want to change the tenantId (if None, it will take the same tenant)

### Creating ExperienceEvent and Profile Schema

I have included pre-made call for creating ExperienceEvents and IndividualProfile class in Schema.\
For these simplified methods, you would need to pass 2 required parameters, an additional one can also be passed.
* name : REQUIRED : Name of your schema
* mixinIds : REQUIRED : List of mixins $id to create the schema or a dictionary giving the mixin $id and the type you want to create (object or array)
    example of value `{"$id1":"object","$id2":"array"}` or `["$id1","$id2"]`
* description : OPTIONAL : Schema description

### Get paths from schema

One of the use-case that can be useful via schema API is to retrieve the different possible paths that you have created.\
The possible path can be used for Query Service or for Mapping service.\
The module provide a method `getSchemaPaths` that returns a list of the paths available.\
It takes the schemaId as parameter.

## SchemaManager

As using the schema and managing the field in your schema get more and more complicated over time. It became obvious that a set of methods would be required to fill the gap that the UI is not able to provide.\
For that reason, I created a [Schema Manager](./schemaManager.md) that will help you handling the schema composition and getting information out of your current implementation of XDM architecture.

One thing to know though, is that Schema is just a wrapping representation of Field Groups attached to a class in order to give a certain representation of your data.\
Is it a profile data ? (to give user attributes)\
Is it timestamp related ? (to give time-based context)\
Is it just a record of third party piece information ? (such as lookup) 

In reason of that, most of the most relevant method of the `SchemaManager` class are abstracted and aggregated representation of methods used in the `FieldGroupManager` class. 
The `SchemaManager` class is not an official Adobe schema manager and any method there needs to be tested before being used in production.

[The documentation around the Schema Manager](./schemaManager.md).

## FieldGroupManager

When creating and managing schema, what really happens is that you are managing the field groups that are contained in the schema.\
Therefore, managing a Field Group is actually the most important part of managing schemas.\
Schemas are "just" a container of field groups ids with an assigned class.\
For that reason, the [Field Group Manager](./fieldGroupManager.md) has been created and will provide your helper methods to understand and manage your schema architecture.

The `FieldGroupManager` is not an official Adobe AEP element or class, and any methods would need to be tested before used in production.

[The documentation around the Field Group Manager](./fieldGroupManager.md)


## Data Type Manager

The DataTypeManager is a class made to help you manage and analyze your custom data types that you have created in your sandbox.\
The same way than what the Field Group Manager and Schema Manager provide, you can manipulate and analyse the different elements that compose your data type.\
Any change that you are making to a Data Type has repercussion on all the elements that are using this Data Type (Schema or Field Groups).

To get to know more on the Data Type Manager, please read [the documentation](./dataTypeManager.md)

