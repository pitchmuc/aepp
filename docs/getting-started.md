# Getting started with aepp

## Menu
- [Installing the module](#installing-the-module)
- [Create a Developer Project ](#create-a-developer-project)
    - [JWT connection](#jwt-connection)
    - [Oauth Server-to-Server](#oauth-server-to-server)
    
- [Using the module](#using-the-module)
    - [Create a Config file](#create-a-config-file)
    - [Environments](#environments)
    - [Importing the config file](#importing-the-config-file)
    - [Alternative method for cloud configuration](#alternative-method-for-cloud-configuration)
    - [The ConnectInstance parameter](#the-ConnectInstance-parameter)
- [Importing a sub module to work with](#importing-a-sub-module-to-work-with)
- [Help](#help)

## Installing the module

You would need to install the module in your environment.\
You can use the pip command to do so.

```shell
pip install aepp --upgrade
```

You can use the upgrade argument when a release has been made.

## Create a Developer Project

You will need to have a developer project that has access to the Adobe Experience Platform API.\
When creating a project you have the possibility to use 2 authentication methods.

* JWT-based authentication (**_LEGACY_**)
* OAuth-based authentication

### JWT connection

Originally, the module create a connection to the API endpoints using a JWT integration.\
**IMPORTANT**: This integration is now legacy and will be replaced by the oauth token integration. See [Oauth server part](#oauth-server).\

In order to use it, you would need to create this JWT integration directly in developer.adobe.com.\
Make sure you have developer rights and attaching the correct product profile to your integration.\
Make sure to save the "private.key" file and write the information of your connection.

To use the JWT integration, it requires the following information to be passed later on:
- Client ID
- Client secret
- Technical Account ID
- Private key (saved as a `private.key` file per example)
- IMS Org

### Oauth Server-to-Server

In 2023, the Oauth Server token has been introduced in the API environment of Adobe.\
`aepp` is now supporting this capabiliy and you can create an `Oauth Server-to-Server` integration.

in developer.adobe.com, make sure you have developer rights and attaching the correct product profile to your integration.\
You will need to have the following information saved to be used later:
- Client ID
- Client secret
- Technical Account ID
- Scopes
- IMS Org


## Using the module

Once you have created the developer project in developer.adobe.com, you can start using the module.\
In order to start using the module, you will need to import it on your environment.\
This is where the `import` keyword is used for that module.


```python
import aepp
```

### Create a config file

Once you have imported the module in your environment, you probably want to create a config file for authentication.\
The `createConfigFile` is the method directly available out of aepp module to help you create the configuration file needed.\

As explained above, there are 2 options:

* JWT config file (Legacy)
* Oauth config file (New)

To create a config file for JWT, use the code below:

```python
import aepp
aepp.createConfigFile(destination='template_config.json',auth_type='jwt')
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
    "scopes": "<scopes>"
}
```

In both cases, remove the `<placeholder>` and replace them with your information.\
All information are available on your project page on developer.adobe.com

**Note** By default, we are setting the sandbox name to "prod". If you don't know what that value, you can override it via a parameter.

**Note** The default behavior has been changed starting June 2023, where oauth is the default type of configuration file created in case you omit the parameter.

Parameter for `createConfigFile` method:

* destination : OPTIONAL : The name of the file to be created (with a dedicated path if needed)
* sandbox : OPTIONAL : You can directly set your sandbox name in this parameter.
* auth_type : OPTIONAL : type of authentication, either "jwt" or "oauth" (default oauth)
* verbose : OPTIONAL : set to true, gives you a print stateent where is the location.


### Environments

By default, the environment is set to `prod`. This is different from the sandbox, as it refers to the physical environment where the organization was setup.

For all AEP customers "prod" is what should be used, but for internal accounts it can be set to "stage" or "int".

### Importing the config file

Once your config file has been generated, you can import it in your script by using the `importConfigFile` method.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')
```

The type of authentication will be automatically determined based on the keys provided by the JSON config file. Be careful to not mix JWT and Oauth on the same config file.\

Parameter for `importConfigFile` method:
* path: REQUIRED : path to the configuration file. Can be either a fully-qualified or relative.
* connectInstance : OPTIONAL : If you want to return an instance of the ConnectObject class
* auth_type : OPTIONAL : type of authentication, either "jwt" or "oauth". Detected based on keys present in config file.
* sandbox : OPTIONAL : The sandbox to connect it.

The `connectInstance` parameter is described below. see [Tip for multi sandbox work](#tip-for-multi-sandbox-work)\
The `sandbox` paramter is to facilitate your life, in case you want to use the same config file for multiple sandboxes.

### Alternative method for cloud configuration

You can also use the configure method to setup the connection directly on the aepp setup.\
This approach is better if you don't want to use a file in your system.\
In that case, you can directly pass the elements in the configure method.

For a JWT connection, you can use this code:

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
    scopes=my_scopes,
    environment="prod"
)
```

**NOTE** : In both case, I didn't provide a `sandbox` parameter but this parameter does exist and can be used to setup a specific sandbox.\
By default, the `prod` sandbox will be used. To use that, use the code below:

```python
import aepp
aepp.configure(
    org_id=my_org_id,
    tech_id=my_tech_id, 
    secret=my_secret,
    private_key=my_key_as_string,
    client_id=my_client_id,
    environment="prod",
    sandbox=my_sandbox
)
```

**NOTE** The `environment` parameter is optional and defaults to "prod".

### The ConnectInstance parameter

The `aepp` module contains a parameter named `connectInstance` for `importConfig` and `configure` methods that provide a way to store the configuration setup.\
As you import the config file, you will default any instantiation of the sub module to the latest loaded configuration.\
Using this parameter will make the methods returning an instance of the `ConnectObject` class.\
That will store the information required to connect to your IMS or sandbox setup (secret, client_id, tech_id, IMSorg, etc...)

You can use that instance then in any of the sub module that is provided with the aepp package and that are related to the AEP API.\
You will be able to pass that instance to the `config` parameter of any submodule (see next section)

Example:

```python
import aepp
myOrg1 = aepp.importConfigFile('org1_config.json',connectInstance=True)
```


## Importing a sub module to work with

You can then import the sub module and you will require to instantiate the class inside that module.\
The class has usually the same name than the sub module but with a capital letter.

Example with schema sub module and Schema class.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')
## using the connectInstance parameter
config1 = aepp.importConfigFile('myConfig_file.json',connectInstance=True)

from aepp import schema

mySchemaInstance = schema.Schema()
## using the instance of config use 
mySchemaInstance = schema.Schema(config=config1)

```

This works exactly the same for all of the sub modules mentioned in the [README page](../README.md).
Note the queryservice and privacyservice have exceptions mentioned on the README.

The idea to have a class instanciated for each submodule has been made in order to allow to work with several sandboxes (or organization) in the same environment.\
You can always access the sandbox used by using the instance `sandbox` attribute.\
Following the previous example:

```python
mySchemaInstance.sandbox ## will return which sandbox is configured in that environment.
```

## Help

You can always use the docstring definition to help you using the functions.\
I tried to give a clear documentation of what each function is capable of.

```python
help(mySchemaInstance.getSchemas)
## returns

#getSchemas(**kwargs) -> list method of aepp.schema.Schema instance
#    Returns the list of schemas retrieved for that instances in a "results" list.
#    Kwargs:
#        debug : if set to true, will print the result when error happens
```
