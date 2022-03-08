# Sandboxes module in aepp

This documentation will provide you some explanation on how to use the sandboxes module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/sandbox/).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `sandboxes` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import sandboxes
```

The sandboxes module provides a class that you can use for generating and retrieving sandboxes.\
The following documentation will provide you with more information on its usage.

## The Sandbox class

The Sandbox class is generating a connection to use the different methods directly on your AEP sandbox / instance.\
This class can be instanciated by calling the `Sandboxes()` from the `sandboxes` module.

Following the previous method described above, you can realize this:

```python
mySands = sandboxes.Sandboxes()
```

3 parameters can be provided for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

**Note**: Kwargs can be used to update the header used in the connection.

## Sandboxes use-cases

The usage of that module is pretty straight forward as you can use it to identify your sandboxes set on your AEP instance.\
You will need to have set the correct access right on your API connection in order to be able to manage the sandboxes.\
It requires extensive access to your AEP instance and can result in the deletion of your data so be mindful of that access.

The existing methods of that modules can be listed and are self explanatory.\
In case of doubt, please refer to the docstring or the API documentation shared above.

* getSandboxes
* getSandbox
* deleteSandbox
* createSandbox
* resetSandbox
