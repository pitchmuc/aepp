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
    - [Using kwargs](#using-kwargs)
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
    - [Instantiation of Schema Manager](#instantiation-of-schema-manager)
    - [Methods of Schema Manager](#methods-of-schema-manager)
      - [searchField](#searchfield)
      - [searchAttribute](#searchattribute)
      - [addFieldGroup](#addfieldgroup)
      - [getFieldGroupManager](#getfieldgroupmanager)
      - [setTitle](#settitle)
      - [to\_dataframe](#to_dataframe)
      - [to\_dict](#to_dict)
      - [createSchema](#createschema)
      - [updateSchema](#updateschema)
      - [createDescriptorOperation](#createdescriptoroperation)
      - [createDescriptor](#createdescriptor)
  - [FieldGroupManager](#fieldgroupmanager)
    - [Field Group Manager instance](#field-group-manager-instance)
    - [Field Groups Manager methods](#field-groups-manager-methods)
      - [setTitle](#settitle-1)
      - [getField](#getfield)
      - [searchField](#searchfield-1)
      - [searchAttribute](#searchattribute-1)
      - [addFieldOperation](#addfieldoperation)
      - [addField](#addfield)
      - [removeField](#removefield)
      - [to\_dict](#to_dict-1)
      - [to\_dataframe](#to_dataframe-1)
    - [to\_xdm](#to_xdm)
    - [patchFieldGroup](#patchfieldgroup)
      - [updateFieldGroup](#updatefieldgroup)
      - [createFieldGroup](#createfieldgroup)

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `schema` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import schema
```

## Generating a Schema instance

Because you can connect to multiple AEP instance at once, or multiple sandboxes, you would need to setup an instance of the `Schema` class from that module.\
Following the previous method described above, you can realize this:

```python
mySchemaConnection1 = schema.Schema()
```

Several parameters are possibles when instantiating the class:\

* container_id : OPTIONAL : "tenant"(default) or "global"
* config : OPTIONAL : config object in the config module (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

### Using kwargs

Kwargs will be used to update the header used in the connection.\
As described above, it can be useful when you want to connect to multiple sandboxes with the same JWT authentication.\
In that case, the 2 instances will be created as such:

```python
mySchemaConnection1 = schema.Schema({"x-sandbox-name":"mySandbox1"})
```

```python
mySchemaConnection2 = schema.Schema({"x-sandbox-name":"mySandbox2"})
```

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
For that reason, I created a Schema Manager that will help you handling the schema composition and getting information out of your current implementation of XDM architecture.

One thing to know though, is that Schema is just a wrapping representation of Field Groups attached to a class in order to give a certain representation of your data.\
Is it a profile data ? (to give user attributes)\
Is it timestamp related ? (to give time-based context)\
Is it just a record of third party piece information ? (such as lookup) 

In reason of that, most of the most relevant method of the `SchemaManager` class are abstracted and aggregated representation of methods used in the `FieldManagerClass`. 
The `SchemaManager` class is not an official Adobe schema manager and any method there needs to be tested before being used in production.

### Instantiation of Schema Manager

The `SchemaManager` class can be instantiated with these parameters:
  * schemaId : OPTIONAL : Either a schemaId ($id or altId) or the schema dictionary itself.
        If schemaId is passed, you need to provide the schemaAPI connection as well.
        If no schema ID is passed, then it will create an empty schema.
  * fieldGroupIds : OPTIONAL : Possible to specify a list of fieldGroup. 
        Either a list of fieldGroupIds (schemaAPI should be provided as well) or list of dictionary definition 
  * schemaAPI : OPTIONAL : It is required if $id or altId are used. It is the instance of the Schema class or you should have import and/or pass the config object.
  * schemaClass : OPTIONAL : If you want to set the class to be a specific class.
        Default value is profile: "https://ns.adobe.com/xdm/context/profile", can be replaced with any class definition.
        Possible default value: "https://ns.adobe.com/xdm/context/experienceevent", "https://ns.adobe.com/xdm/context/segmentdefinition"
  * config : OPTIONAL : The config object in case you want to override the configuration.

By default, it will use the default config that has been used for the `Schema` class.\
However, you can use the `schemaAPI` parameter to pass an instance of the `Schema` class you want to use or you can pass the `config` object.


There are several attribute available from the instantiation of the schema:
* title : The title of the schema
* fieldGroups : A dictionary of the title and ID of the field groups
* fieldGroupTitles : A list of the field group titles
* fieldGroupIds : A list of the field groups Id
* fieldGroupsManagers : A list of Field Group Manager instances
* classId : The class assigned to that schema


### Methods of Schema Manager

The different methods available from the instantiation are:

#### searchField

The `searchField` method provide a way to search for a specific field name.\
It takes 3 arguments:
* string : REQUIRED : The string you are looking for
* partialMatch : OPTIONAL : If you want to use partial match (default True)
* caseSensitive : OPTIONAL : If you want to remove the case sensitivity.

The output will provide you with the element itself with additional attributes:
* path of the field with annotation if it is (in) a list
* the query path that you can use in Query Service
* the complete path that contains the complete path of that field
* the field group that contains that field

Example:
```python

mySchemaManagerInstance = schema.SchemaManager('<schemaId>')
mySchemaManagerInstance.searchField('myfield')

```

#### searchAttribute

The `searchAttribute` will search for any attribute that you have specified and will return either a list of the field that contains that field.\
You can also return the complete object description of the field matching your attributes search.

The parameter of that methods are:
* attr : REQUIRED : a dictionary of key value pair(s).  Example : {"type" : "string"} 
    NOTE : If you wish to have the array type, use the key "arrayType". Example : {"type" : "array","arrayType":"string"} 
* regex : OPTIONAL : if you want your value of your key to be matched via regex.
    Note that regex will turn every comparison value to string for a "match" comparison.
* extendedResults : OPTIONAL : If you want to have the result to contain all details of these fields. (default False)
* joinType : OPTIONAL : If you pass multiple key value pairs, how do you want to get the match.
    outer : provide the fields if any of the key value pair is matched.(default)
    inner : provide the fields if all the key value pair matched.

#### addFieldGroup

This method allows you to directly add a field group to the schema definition.\
It takes one argument:
* fieldGroup : REQUIRED : The fieldGroup ID or the dictionary definition connecting to the API.
                if a fieldGroup ID is provided, you should have added a schemaAPI previously.

#### getFieldGroupManager

This method will return the Field Group Manager instance used in the background of the `SchemaManager`.\
It takes one argument:
* fieldgroup : REQUIRED : The title or the $id of the field group to retrieve.

#### setTitle

This method will set a title for the Schema. It takes one argument:
* name : REQUIRED : a string to be used for the title of the FieldGroup

#### to_dataframe

This method returns a dataframe that shows you all available fields of your schema in a tabular format (dataframe from pandas).\
It also provide the type of the field itself and the field group of the field.\
It takes 2 arguments:
* save : OPTIONAL : If you wish to save it with the title used by the field group.
    save as csv with the title used. Not title, used "unknown_schema_" + timestamp.
* queryPath : OPTIONAL : If you want to have the query path to be used.

#### to_dict

This methods returns a dictionary representation of the schema, so you can better see the nested structure of your schema.\
You can then save that structure in a JSON file. It also provides the type of the fields.
No argument can be passed in that method.

#### createSchema

This method will try to create a Schema based on your different field group ids.\
NOTE: It removes the "$id" if one was provided to avoid overriding existing ID.\
Therefore you could generate 2 times the same schema.\
It is meant to be used for new schema creation, not for schema duplication.

#### updateSchema

Use the PUT method to replace the existing schema with the new definition.

#### createDescriptorOperation

Descriptor are an important part of the schema as it can define identity, lookup and so on.\
However, the descriptor are quite diverse and it can be a complicated operation to create the correct descriptor definition from scratch.\
This method helps you to prepare the descriptor to be used.\
You can see the type of descriptor available in the DESCRIPTOR_TYPES attribute and also on the official documentation: <https://experienceleague.adobe.com/docs/experience-platform/xdm/api/descriptors.html?lang=en#appendix>\
Many arguments are possible:
* descType : REQUIRED : The type to be used.
    it can only be one of the following value: "xdm:descriptorIdentity","xdm:alternateDisplayInfo","xdm:descriptorOneToOne","xdm:descriptorReferenceIdentity","xdm:descriptorDeprecated"
* completePath : REQUIRED : the complete path of the field you want to attach a descriptor.
* identityNSCode : OPTIONAL : if the descriptor is identity related, the namespace CODE  used.
* identityPrimary : OPTIONAL : If the primary descriptor added is the primary identity.
* alternateTitle : OPTIONAL : if the descriptor is alternateDisplay, the alternate title to be used.
* alternateDescription : OPTIONAL if you wish to add a new description.
* lookupSchema : OPTIONAL : The schema ID for the lookup if the descriptor is for lookup setup
* targetCompletePath : OPTIONAL : if you have the complete path for the field in the target lookup schema.

#### createDescriptor

Once you have prepare your descriptor with the `createDescriptorOperation` method. You can use the result in that method to attach that descriptor to the schema.\
Only one argument can be used:
* descriptor : REQUIRED : The operation to add a descriptor to the schema.


## FieldGroupManager

When creating and managing schema, what really happens is that you are managing the field groups that are contained in the schema.\
Therefore, I would believe that managing a Field Group is actually the most important part of managing schemas.\
Schemas are "just" a container of field groups ids with an assigned class.

### Field Group Manager instance

You can access a field group manager instance by 2 methods: 
* from `SchemaManager`, the `getFieldGroupManager` method will provide you with an instance of that class by passing the title or the $id of the field group you want.
* from instantiation of the `FieldGroupManager` class.

To instantiate the FieldGroupManager you can pass the following arguments:
* fieldGroup : OPTIONAL : the field group definition as dictionary OR the $id to access it.
    If you pass the $id or altId, you should pass the schemaAPI instance or have uploaded a configuration file.
    If you do not pass a field group (ID), an empty field group is created. 
* title : OPTIONAL : If you want to name the field group.
* fg_class : OPTIONAL : the class that will support this field group.
    by default events and profile, possible value : "record"
* schemaAPI : OPTIONAL : The instance of the Schema class. Provide a way to connect to the API.
* config : OPTIONAL : The config object in case you want to override the configuration.

Instantiation of the FieldGroupManager provide several attributes:
* fieldGroup : Definition of the field group
* title : Title of the field group
* id : ID of the field group
* altId : The alt:Id of the field group.

### Field Groups Manager methods

The different methods available, once the instantiation of the Field Group Manager is done, are:

#### setTitle

This method set the tile of the field group. It takes one argument:
* name : REQUIRED : a string to be used for the title of the FieldGroup


#### getField

This method return the field definition based on a dot notation.\
It takes one argument:
* path : REQUIRED : path with dot notation to which field you want to access


#### searchField

Search for a field name based on the string passed.\
By default, partial match is enabled and allow case sensitivity option.\
Arguments:
* string : REQUIRED : the string to look for for one of the field
* partialMatch : OPTIONAL : if you want to look for complete string or not. (default True)
* caseSensitive : OPTIONAL : if you want to compare with case sensitivity or not. (default False)

#### searchAttribute

Search for an attribute on the field of the field groups.\
Returns either the list of fields that match this search or their full definitions.\
Arguments:
* attr : REQUIRED : a dictionary of key value pair(s).  Example : {"type" : "string"} 
    NOTE : If you wish to have the array type on top of the array results, use the key "arrayType". Example : {"type" : "array","arrayType":"string"}
            This will automatically set the joinType to "inner". Use type for normal search. 
* regex : OPTIONAL : if you want your value of your key to be matched via regex.
    Note that regex will turn every comparison value to string for a "match" comparison.
* extendedResults : OPTIONAL : If you want to have the result to contain all details of these fields. (default False)
* joinType : OPTIONAL : If you pass multiple key value pairs, how do you want to get the match.
    outer : provide the fields if any of the key value pair is matched.
    inner : provide the fields if all the key value pair matched.

#### addFieldOperation

When adding a field to a field group, you can use a POST method to just add the additional fields.\
For that purpose, you need to provide a list of operation in that post method. The addFieldOperation method helps you to prepare this statement.\
Return the operation to be used on the field group with the Patch method (patchFieldGroup), based on the element passed in arguments.\
Arguments:
* path : REQUIRED : path with dot notation where you want to create that new field.
* dataType : REQUIRED : the field type you want to create
    A type can be any of the following: "string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object","array"
    NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
* title : OPTIONAL : if you want to have a custom title.
* objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.
    Example : {'field1':'string','field2':'double'}
* array : OPTIONAL : Boolean. If the element to create is an array. False by default.
* enumValues : OPTIONAL : If your field is an enum, provide a dictionary of value and display name, such as : {'value':'display'}\
possible kwargs:
* defaultPath : Define which path to take by default for adding new field on tenant. Default "property", possible alternative : "customFields"

Examples : *TBD*

#### addField

This method will add the field directly in the field group definition contained in the instance.\
You can then use the upgradeFieldGroup method to replace the existing definition with a new one.\
It returns False when the field could not be inserted.
Arguments:
* path : REQUIRED : path with dot notation where you want to create that new field. New field name should be included.
* dataType : REQUIRED : the field type you want to create
    A type can be any of the following: "string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object","array"
    NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
* title : OPTIONAL : if you want to have a custom title.
* objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.
    Example : {'field1:'string','field2':'double'}
* array : OPTIONAL : Boolean. If the element to create is an array. False by default.
* enumValues : OPTIONAL : If your field is an enum, provide a dictionary of value and display name, such as : {'value':'display'}\
possible kwargs:
* defaultPath : Define which path to take by default for adding new field on tenant. Default "property", possible alternative : "customFields"

#### removeField

Remove a field from the definition based on the path provided.
NOTE: A path that has received data cannot be removed from a schema or field group.
Argument:
* path : REQUIRED : The path to be removed from the definition.

#### to_dict
Generate a dictionary representing the field group constitution\
Arguments:
* typed : OPTIONAL : If you want the type associated with the field group to be given.
* save : OPTIONAL : If you wish to save the dictionary in a JSON file
    The title used. If no title, used "unknown_fieldGroup_" + timestamp.


#### to_dataframe

Generate a dataframe with the row representing each possible path.\
Arguments:\
* save : OPTIONAL : If you wish to save it with the title used by the field group.
    save as csv with the title used. If no title, used "unknown_fieldGroup_" + timestamp.
* queryPath : OPTIONAL : If you want to have the query path to be used.

### to_xdm

Returns the complete field group definition as XDM.

### patchFieldGroup

Use the POST method to patch the field group. It can be used with the result of the `addFieldGroupOperation` method.\
Patch the field group with the given operation.\
Arguments:
* operation : REQUIRED : The list of operation to realise

#### updateFieldGroup

Use the PUT method to push the current field group representation to AEP via API request.

#### createFieldGroup

Use the POST method to create the field group in the organization.

