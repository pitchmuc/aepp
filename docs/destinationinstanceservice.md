# Destination Instance module in aepp

This documentation will provide you some explanation on how to use the `destinationinstanceservice` module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the destination instance API, please refer to this [API documentation](https://experienceleague.adobe.com/docs/experience-platform/destinations/api/ad-hoc-activation-api.html?lang=en).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `destinationinstanceservice` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import destinationinstanceservice
```

The destinationinstanceservice module provides a class that you can use to create adhoc export tasks.\
The following documentation will provide you with more information on its capabilities.

## The Instance class

The Authoring class is the default API connector that you would encounter for any other submodules on this python module.\
This class can be instanciated by calling the `Instance()` from the `destinationinstanceservice` module.

Following the previous method described above, you can realize this:

```python
mySDK = destinationinstanceservice.Instance()
```

3 parameters are possible for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : logging object to provide log of the application.

## Destination Instance Service module use-cases
The Destination module will enable you to create adhoc request for export segments/datasets

## Destination Instance Service methods
This part is describing the different methods available from that module, once you have generated your instance.

* createAdhocTask
create adhoc task for export segments/datasets