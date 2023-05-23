# Policy module in aepp

This documentation will provide you some explanation on how to use the Policy module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/policy-service/).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `policy` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import policy
```

The policy module provides a class that you can use for managing your data governance.\
The following documentation will provide you with more information on its capabilities.

## The Policy class

The Policy class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `Policy()` from the `policy` module.

Following the previous method described above, you can realize this:

```python
mySegs = segmentation.Segmentation()
```

2 parameters are possible for the instantiation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

## Policy use-cases

TBD