# Observability module in aepp

This documentation will provide you some explanation on how to use the `observability` module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/observability-insights/).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `destination` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import observability
```

The destination module provides a class that you can use to generate a SDK taking care of transferring some information to specific destination endpoints.\
The following documentation will provide you with more information on its capabilities.

## The Observability class

The Observability class allows you to discover statistics on the AEP processing.\
This class can be instantiated by calling the `Observability()` from the `observability` module.

Following the previous method described above, you can realize this:

```python
obs = observability.Observability()
```

2 parameters are possible for the instantiation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : logging object to provide log of the application.
