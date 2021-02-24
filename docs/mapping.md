# Mapping module in aepp

This documentation will provide you some explanation on how to use the Mapping module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/mapping-service-api.yaml).\
Alternatively, you can use the docstring in the methods to have more information.

## What is the Mapping Service in AEP ?

The Mapping module is based on the Mapping Service in AEP and it is part of the data ingestion or data preparation process in AEP.\
It is linked to the Flow Service capability and you can have more information about that by reading the [corresponding documentation](./flowservice.md).

In order to make the best of this API, it is preferred to have knowledge on how the flow service is being setup.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `flowservice` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import mapping
```

The mapping module provides a class that you can use for managing your connection to your different Mappings and MappingsSet (see below).\
The following documentation will provide you with more information on its capabilities.

## The Mapping class

The Mapping class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instanciated by calling the `Mapping()` from the `mapping` module.

Following the previous method described above, you can realize this:

```python
mapper = mapping.Mapping()
```

2 parameters are possible for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

Any additional parameters in the kwargs will be updating the header content.

## Use-cases

The Mapping Service is used in order to map the incoming data to match specific field expectation.\
