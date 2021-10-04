# AEPP core methods

This documentation is focused on the methods available directly from the `aepp` module.

## Creating a config file

When starting with the `aepp` module, you will need to create a configuration file.\
The aepp module contains a method that will create a configuration file (JSON) as a template and you can just update the values.\
The method is : `createConfigFile`\
Arguments:

* destination : OPTIONAL : if you wish to save the file at a specific location.
* sandbox : OPTIONAL : You can directly set your sandbox name in this parameter.
* verbose : OPTIONAL : set to true, gives you a print stateent where is the location.

The JSON file is having this structure:

```python
{
    "org_id": "<orgID>",
    "client_id": "<client_id>",
    "tech_id": "<something>@techacct.adobe.com",
    "secret": "<YourSecret>",
    "pathToKey": "<path/to/your/privatekey.key>",
    "sandbox-name": "prod",
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

## Configure connection

The `configure` method directly available in the `aepp` module enables the possibility to pass all information required to connect to the AEP API without having to write them directly in a configuration file.\
This can be required when you are on the cloud on a stateless environment and you want to pass the connection info directly.

Arguments:

* org_id : REQUIRED : Organization ID
* tech_id : REQUIRED : Technical Account ID
* secret : REQUIRED : secret generated for your connection
* client_id : REQUIRED : The client_id (old api_key) provided by the JWT connection.
* path_to_key : REQUIRED : If you have a file containing your private key value.
* private_key : REQUIRED : If you do not use a file but pass a variable directly.
* sandbox : OPTIONAL : If not provided, default to prod

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
