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
aepp.createConfigFile(destination='template_config.json',)
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
    "sandbox-name": "prod"
}
```

**Note** By default, we are setting the sandbox name to "prod". If you don't know what that value, you can override it via a paramter.

### Importing the config file and working with a sub module

Once your config file has been generated, you can import it in your script.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')
```

### Alternative method for cloud configuration

You can also use the configure method to setup the connection directly on the aepp setup.\
This approach is better if you don't want to use a file in your system.\
In that case, you can directly pass the elements in the configure method.

```python
import aepp
aepp.configure(org_id=my_org_id,tech_id=my_tech_id, secret=my_secret,path_to_key=my_path_to_key,client_id=my_client_id)
```

In case you do not want to use a private.key file, you can also provide the private key as a string.

```python
import aepp
aepp.configure(org_id=my_org_id,tech_id=my_tech_id, secret=my_secret,private_key=my_key_as_string,client_id=my_client_id)
```

**NOTE** : In both case, I didn't provide a `sandbox` parameter but this parameter does exist and can be used to setup a specific sandbox.\
By default, the prod sandbox will be used.

### Importing a module to work with

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
