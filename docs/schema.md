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
  - [FieldGroupManager](#fieldgroupmanager)

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

### Using different ConnectObject for different sandboxes

You can use the `connectInstance` parameter to load multiple sandbox configuration and save them for re-use later on, when instantiating the `Schema` class. 
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




