# Data Prep module in aepp

This documentation will provide you some explanation on how to use the Data Prep module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/data-prep.yaml).\
Alternatively, you can use the docstring in the methods to have more information.

## What is the Data Prep in AEP ?

The `dataprep` module contains the Mapping Service in AEP and it is a service happening during  the data ingestion in AEP.\
It is linked to the Flow Service capability and you can have more information about that by reading the [corresponding documentation](./flowservice.md).

In order to make the best of this API, it is preferred to have knowledge on how the flow service is being setup.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `dataprep` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import dataprep
```

The `dataprep` module provides a class that you can use for managing your connection to your different Mappings and MappingsSet (see below).\
The following documentation will provide you with more information on its capabilities.

## The DataPrep class

The DataPrep class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instanciated by calling the `DataPrep()` from the `dataprep` module.

Following the previous method described above, you can realize this:

```python
mapper = dataprep.DataPrep()
```

2 parameters are possible for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

Any additional parameters in the kwargs will be updating the header content.

## Use-cases

The Data Prep Service enables you to use the mapping service. This service is used in order to map the incoming data to match specific field expectation in your schema (type / value).\
It can be used in 2 different ways:

* `text/x.schema-path` when you want to map a specific path to a new path
* `text/x.aep-xl` when you are doing calculation or applying function on a field.

### Mapping is used with Flow Service

To use the `mapper`, you would need to attach it to a connection flow.\
Please reference to the [FlowService documentation for this](./flowservice.md).

### Create a mapping

When creating a mapping you need to pass (a list of) object that will define the transformation happening to your `source` data and the `destination` of that data.\
An empty example of mapping would be:

```JSON
MyMapping = {
    "sourceType": "",
    "source": "",
    "destination": ""
}
```

You can find this element in the `REFERENCE_MAPPING` attribute of the `Mapping` instance.\
The different elements means the following:
* sourceType : as explained above it can be either `text/x.schema-path` or `text/x.aep-xl`.
* source : the path to your value
* destination : the path of your destination (where the data should go after transformation)

You can then use that object in a list and pass it to a dictionary, specifying your outputSchema reference:

```JSON
obj = {
    "outputSchema": {
       "schemaRef": {
            "id": "https://ns.adobe.com/tenant/schemas/e0b7cba00da86d10c0774a337",
            "contentType": "application/vnd.adobe.xed-full+json;version=1"
        }
    },
    "mappings": [MyMapping]
}
```

Note : In this example above, I only had one object so I pass it in a list.\
You can pass that object directly into the `createMappingSet` method as the following:
```python
mapper.createMappingSet(obj,validate=True,verbose=True)
```

What can also be done is to use the optional parameter to only pass the schema `$Id` and the list of mapping.

```python
mapper.createMappingSet(schemaId="https://ns.adobe.com/tenant/schemas/e0b7cba00da86d10c0774a337",mappingList=[MyMapping],validate=True,verbose=True)
```

### Update a Mapping

At some point, when you want to update a Mapping, the way to achieve this is to update the whole MappingSet.\
You can then directly update the MappingSet by using the `updateMappingSet` method.

```python
updateObject = {
  "id": "string",
  "mappings": [
        {
        "sourceType": "text/x.aep-xl" or "text/x.schema-path",
        "source": "",
        "destination": ""
        }
  ],
  "name": "string",
  "schemaRef": {
    "contentType": "string",
    "id": "string"
  },
  "transformScript": "string",
  "version": X
}
mapper.updateMappingSet('MappingId',mappingSet=updateObject)
```

### Detect where the mapping is used

Detecting where your mapping is currently being used can be important if you have several mapping and data flows running.\
However, the module doesn't support this search directly.\
You can achieve this use-case by using the `flowservice` module.
