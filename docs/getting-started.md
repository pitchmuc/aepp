# Getting started with aepp

## Installing the module

You would need to install the module in your environment.\
You can use the pip command to do so.

```
pip install aepp --ugrade
```

You can use the upgrade argument when a release has been made.

## Create a JWT connection

The module create a connection to the API endpoints through a JWT integration.\
In order to use it, you would need to create this JWT integration directly in console.adobe.io.

Make sure you have developer rights and attaching the correct product profile to your integration.

Make sure to save the "private.key" file and write the information of your connection.

## Using the module

The following examples will be python code sample that shows you how to use the tool.

### Importing and create a config file

```python
import aepp
aepp.createConfigFile(filename='template_config.json',sandbox=True)
```

This line of code will create a config file where you will enter the different information related to your JWT integration.\
Normally your config file will look like this:

```JSON
{
    "org_id": "<orgID>",
    "client_id": "<client_id>",
    "tech_id": "<something>@techacct.adobe.com",
    "secret": "<YourSecret>",
    "pathToKey": "<path/to/your/privatekey.key>",
    "sandbox-name": "<your_sandbox_name>"
}
```

**Note** that you have the sandbox-name to fill. If you don't know what that is and what it means. You can drop the parameter `sandbox=True` in the createConfigFile function. The default will be set to "prod".

### Importing the config file and working with a sub module

Once your config file has been generated, you can import it in your script and use sub module.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')
```

You can then import the sub module and you will require to instantiate the class inside that module.\
The class has usually the same name than the sub module but with a capital letter.

Example with schema sub module and Schema class.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import schema

mySchemaCon = schema.Schema()

```

This works exactly the same for all of the sub modules mentioned in the [README page](../README.md).
Note the queryservice and privacyservice exception mentioned on the README.

### Help

You can always use the docstring definition to help you using the functions.\
I tried to give a clear documentation of what each function is capable of.

```python
help(mySchemaCon.getSchemas)
## returns

#getSchemas(**kwargs) -> list method of aepp.schema.Schema instance
#    Returns the list of schemas retrieved for that instances in a "results" list.
#    Kwargs:
#        debug : if set to true, will print the result when error happens
```
