# Access Control module in aepp

This documentation will provide you an overview on how to use the `accesscontrol` module and different methods supported by this module.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/access-control/).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `destination` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import accesscontrol
```

The accesscontrol module provides a class that you can use to list out permissions, list out resource types, and list all the effective policies for a user on given resources within a sandbox.\
The following documentation will provide you with more information on its capabilities.

## The AccessControl class

The AccessControl class allows you to:

* List names of permissions and resource types
* Lists all the effective policies for a user on given resources within a sandbox
  
This class can be instantiated by calling the `AccessControl()` from the `accesscontrol` module.

Following the previous method described above, you can realize this:

```python
myAccess = accesscontrol.AccessControl()
```

2 parameters are possible for the instantiation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

## AccessControl use-cases

The existing methods of modules listed below are self explanatory.\
In case of doubt, please refer to the docstring or the API documentation shared above.

* getReferences - List all available permission names and resource types.
* postEffectivePolicies - List all effective policies for a user on given resources within a sandbox.
