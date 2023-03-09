# Getting started with aepp

## Installing the module

You would need to install the module in your environment.\
You can use the pip command to do so.

```shell
pip install aepp --upgrade
```

You can use the upgrade argument when a release has been made.

## Create a JWT connection

The module create a connection to the API endpoints through a JWT integration.\
In order to use it, you would need to create this JWT integration directly in console.adobe.io.

Make sure you have developer rights and attaching the correct product profile to your integration.

Make sure to save the "private.key" file and write the information of your connection.

## Using the module

The following examples will be python code sample that shows you how to use the tool.

### Authentication methods

There are 2 ways to authenticate with `aepp`:
- JWT-based authentication
- OAuth-based authentication

By default we use JWT-based authentication. This is appropriate for users who have developer access to their AEP instance. This requires the following information:
- Client ID
- Client secret
- Technical Account ID
- Private key

The other method of authentication is based on the OAuth protocol. This is more intended for services and internal developer. This requires the following information:
- Client ID
- Client secret
- Authorization code - note that this can be either a permanent or temporary code.

### Importing and create a config file

To create a config file for JWT-based authentication, use the code below:

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
    "sandbox-name": "prod",
    "environment": "prod"
}
```

If you want to use OAuth-based authentication, use the following code:

```python
import aepp
aepp.createConfigFile(destination='template_config.json', auth_type="oauth")
```

The resulting file will have different fields:

```JSON
{
    "org_id": "<orgID>",
    "client_id": "<client_id>",
    "secret": "<YourSecret>",
    "sandbox-name": "prod",
    "environment": "prod",
    "auth_code": "<auth_code>"
}
```

**Note** By default, we are setting the sandbox name to "prod". If you don't know what that value, you can override it via a parameter.

### Environments

By default, the environment is set to `prod`. This is different from the sandbox, as it refers to the physical environment where the organization was setup.

For all AEP customers "prod" is what should be used, but for internal accounts it can be set to "stage" or "int".

### Importing the config file and working with a sub module

Once your config file has been generated, you can import it in your script.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')
```

By default, this will only configure using the JWT information from your config file. If you have a config with OAuth information, instead use the following:

```python
import aepp
aepp.importConfigFile('myConfig_file.json', auth_type="oauth")
```

### Alternative method for cloud configuration

You can also use the configure method to setup the connection directly on the aepp setup.\
This approach is better if you don't want to use a file in your system.\
In that case, you can directly pass the elements in the configure method.

```python
import aepp
aepp.configure(
    org_id=my_org_id,
    tech_id=my_tech_id, 
    secret=my_secret,
    path_to_key=my_path_to_key,
    client_id=my_client_id,
    environment="prod"
)
```

In case you do not want to use a private.key file, you can also provide the private key as a string.

```python
import aepp
aepp.configure(
    org_id=my_org_id,
    tech_id=my_tech_id, 
    secret=my_secret,
    private_key=my_key_as_string,
    client_id=my_client_id,
    environment="prod"
)
```

If you instead want to use OAuth-based authentication, simply use different parameters when calling `configure`:

```python
import aepp
aepp.configure(
    org_id=my_org_id,
    secret=my_secret,
    client_id=my_client_id,
    auth_code=my_auth_code,
    environment="prod"
)
```

**NOTE** : In both case, I didn't provide a `sandbox` parameter but this parameter does exist and can be used to setup a specific sandbox.\
By default, the prod sandbox will be used. To use that, use the code below:

```python
import aepp
aepp.configure(
    org_id=my_org_id,
    tech_id=my_tech_id, 
    secret=my_secret,
    private_key=my_key_as_string,
    client_id=my_client_id,
    environment="prod",
    sandbox=my_sandbox_id
)
```

**NOTE** The `environment` parameter is optional and defaults to "prod".


### Importing a module to work with

You can then import the sub module and you will require to instantiate the class inside that module.\
The class has usually the same name than the sub module but with a capital letter.

Example with schema sub module and Schema class.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import schema

mySchemaInstance = schema.Schema()

```

This works exactly the same for all of the sub modules mentioned in the [README page](../README.md).
Note the queryservice and privacyservice have exceptions mentioned on the README.

The idea to have a class instanciated for each submodule has been made in order to allow to work with several sandboxes (or organization) in the same environment.\
You can always access the sandbox used by using the instance `sandbox` attribute.\
Following the previous example:

```python
mySchemaInstance.sandbox ## will return which sandbox is configured in that environment.
```

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
