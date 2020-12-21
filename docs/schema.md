# Schema module in aepp

This documentation will provide you some explanation on how to use the schema module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/schema-registry.yaml).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `schema` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import schema
```

## Generating an instance

Because you can connect to multiple AEP instance at once, or multiple sandboxes, you would need to setup an instance of the `Schema` class from that module.\
Following the previous method described above, you can realize this:

```python
mySchemaConnection1 = schema.Schema()
```

Several paramters are possibles when instanciating the class:\

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

Knowning the relationships / hierarchy between the different component of schema constructors will help you on your pipeline.\
Example : You cannot delete a class if it is used in a schema and you cannot delete a mixin if it is used in a Schema.

From bottom to top, here is the list of elements.

1. Data Types : a single piece of data description
2. Mixins : can contains several data types
3. Class : define the type of schema that will be built
4. Schema : use class and mixins to build a data model

### 4. Descriptors are important

The descriptors methods are important as they are setting which elements of your schema are identities.\
These identities are important to build the data model on AEP for the Unified Profile setup.\
In addition to these identities, you need to enable the schema for unified profile.

