# AEPP core methods

This documentation is focused on the methods available directly from the `aepp` module.

## Creating a config file

When starting with the `aepp` module, you will need to create a configuration file.\
The aepp module contains a method that will create a configuration file (JSON) as a template and you can just update the values.\
The method is : `createConfigFile`\
Arguments:

* destination : OPTIONAL : if you wish to save the file at a specific location.
* sandbox : OPTIONAL : You can directly set your sandbox name in this parameter. Default : `prod`
* environment : OPTIONAL : This element is only for AEP core developer. **NOT TO BE CHANGED BY CLIENTS**.
* auth_type : OPTIONAL : Default is OauthV2, but you can also use OauthV1 (**for Internal only!**)
* verbose : OPTIONAL : set to true, gives you a print statement where is the location.

The JSON file is having this structure:

```python
{
    "org_id": "<orgID>",
    "client_id": "<client_id>",
    "tech_id": "<something>@techacct.adobe.com",
    "secret": "<YourSecret>",
    "scopes": "scope",
    "sandbox-name": "prod",
    "environment" : "prod"
    }
```

Example:

```python
import aepp
aepp.createConfigFile(destination='myConfigFile.json')
```

## Importing a config file

Once you have created and updated the configuration file, you can (or need) to import it in order to have the information required for connecting to AEP.\
The method is the `importConfigFile`\
Argument:

* path: REQUIRED : path to the configuration file. Can be either a fully-qualified or relative.
* connectInstance : OPTIONAL : If you want to return an instance of the ConnectObject class. (default False)

**NOTE**: `connectInstance` is default to `False`, but we strongly recommend to use it as best practice when you are having multiple sandbox environment.

Example: 

```py
import aepp
from aepp import schema ## to manipulate schema definition

## here I will create a connect instance to prod2 sandbox
prod2 = aepp.importConfigFile('myconfig.json',sandbox='prod2',connectInstance=True)

mySchema = schema.Schema(config=prod)
```

## Configure connection

The `configure` method directly available in the `aepp` module enables the possibility to pass all information required to connect to the AEP API without having to write them directly in a configuration file.\
This can be required when you are on the cloud on a stateless environment and you want to pass the connection info directly.

Arguments:

* org_id : REQUIRED : Organization ID
* tech_id : REQUIRED : Technical Account ID
* secret : REQUIRED : secret generated for your connection
* client_id : REQUIRED : The client_id (old api_key).
* scopes : REQUIRED : The scope used in the OauthV2 connection.
* sandbox : OPTIONAL : If not provided, default to prod
* connectInstance : OPTIONAL : If you want to return an instance of the ConnectObject class (default False)
* environment : OPTIONAL : If not provided, default to prod

### The `connectInstance` parameter

In an environment when you have multiple organization and / or multiple sandboxes to manage via `aepp`, it would be cumbersome to import the new environment any time you want to switch the Organization or the sandbox.\
For that use-case, we provide a way for you to save your configuration in an instance of a `ConnectObject` class.\
This class will save your organization, your sandbox and any information related to your configuration setup.\
Therefore, in instantiation of any class later on, such as Schema class per example, you can pass the appropriate instance to connect to the right organization.

Example: 

```python
import aepp
myOrg1 = aepp.importConfigFile('org1_config.json',connectInstance=True)
myOrg2 = aepp.importConfigFile('org1_config.json',connectInstance=True)

from aepp import catalog, schema

### conecting to the schema Registry endpoint for the org 1
schema1 = schema.Schema(config=myOrg1)
## connecting for org 2 
schema2 = schema.Schema(config=myOrg2)

### Same for Catalog
catalog2 = catalog.Catalog(config=myOrg2)
catalog1 = catalog.Catalog(config=myOrg1)

```

## Generating the logging object

With the different submodule of `aepp`, you can generate logs information to monitor the state of your application running aepp.\
In order to pass how you want the log to be structured and which file to create for the log, you can create a logging object.
The method is: `generateLoggingObject`

A complete description of its usage is available on the [logging documentation](./logging.md)

## Home

This method (`home`) provides information from your AEP setup.\
Arguments:

* product : OPTIONAL : specify one or more product contexts for which to return containers. If absent, containers for all contexts that you have rights to will be returned. The product parameter can be repeated for multiple contexts. An example of this parameter is product=acp
* limit : OPTIONAL : Optional limit on number of results returned (default = 50).

Example:

```python
import aepp
aepp.importConfigFile('myConfig.json')

conf = aepp.home()
```

## Retrieve Users Log events

The `getPlatformEvents` is a method that should return you with the information of what has been done during the last 90 days on your AEP instance by your users.\
Arguments:

* limit : OPTIONAL : Number of events to retrieve per request (50 by default)
* n_results : OPTIONAL : Number of total event to retrieve per request.
* prop : OPTIONAL : An array that contains one or more of a comma-separated list of properties (prop="action==create,assetType==Sandbox")
    If you want to filter results using multiple values for a single filter, pass in a comma-separated list of values. (prop="action==create,update")

## extractSandboxArtefacts

The `extractSandboxArtefacts` method is a way to extract the different artefacts that are available on your sandbox in a local folder.\
This method is taking 2 arguments:
* sandbox: REQUIRED: the instance of a ConnectObject that contains the sandbox information and connection.
* localFolder: OPTIONAL: the local folder where to extract the sandbox. If not provided, it will use the current working directory and name the    folder the name of the sandbox.
* region: OPTIONAL: the region of the sandbox (default: nld2). This is used to fetch the correct API endpoints for the identities. 
    Possible values: "va7","aus5", "can2", "ind2"
* ootb : OPTIONAL : If you want to also download the OOTB elements

Example of usage: 

```py
import aepp

prod = aepp.importConfigFile('myconfig.json',sandbox='prod',connectInstance=True)
aepp.extractSandboxArtefacts(prod,localFolder='prodFolder',region='va7')
```
as of today, the following artefacts are exported:
* behavior
* class
* schema
* fieldgroup
* datatype
* descriptors
* identities
* datasets

The reason to use that extractSandboxArtefacts methods is documented on [Local File Usage](./localfilesusage.md)

## extractSandboxArtefact
Export a single artefact and its dependencies from the sandbox.\
Arguments:
* sandbox: REQUIRED: the instance of a ConnectObject that contains the sandbox information and connection.
* localFolder: OPTIONAL: the local folder where to extract the sandbox. If not provided, it will use the current working directory and name the * folder the name of the sandbox.
* artefact: REQUIRED: the id or the name of the artefact to export.
* artefactType: REQUIRED: the type of artefact to export. Possible values are: 'class','schema','fieldgroup','datatype','descriptor','dataset','identity'
* region: OPTIONAL: the region of the sandbox (default: nld2). This is used to fetch the correct API endpoints for the identities. 
    Possible values: "va7","aus5", "can2", "ind2"

The reason to use that extractSandboxArtefacts methods is documented on [Local File Usage](./localfilesusage.md)