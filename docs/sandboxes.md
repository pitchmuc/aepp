# Sandboxes module in aepp

This documentation will provide you some explanation on how to use the sandboxes module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/sandbox/).\
Alternatively, you can use the docstring in the methods to have more information.\

To be noted, some documentation about the sandbox tooling can be found here:[sandbox tooling documentation](https://experienceleague.adobe.com/en/docs/experience-platform/sandbox/troubleshooting-guide)

## Menu
- [Sandboxes module in aepp](#sandboxes-module-in-aepp)
  - [Menu](#menu)
  - [What is the segmentation capability in AEP](#what-is-the-segmentation-capability-in-aep)
  - [Importing the module](#importing-the-module)
  - [The Sandboxes class](#the-sandboxes-class)
  - [Sandboxes attributes](#sandboxes-attributes)
  - [Sandboxes methods](#sandboxes-methods)
  - [Sandboxes use-cases](#segmentation-use-cases)
    - [1. List all of your sandboxes](#list-all-of-your-sandboxes)



## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `sandboxes` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')

from aepp import sandboxes
```

The sandboxes module provides a class that you can use for generating and retrieving sandboxes.\
The following documentation will provide you with more information on its usage.

## The Sandboxes class

The Sandboxes class is generating a connection to use the different methods directly on your AEP sandbox / instance.\
This class can be instantiated by calling the `Sandboxes()` from the `sandboxes` module.

Following the previous method described above, you can realize this:

```python
import aepp
from aepp import sandboxes

prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')
mySandboxes = sandboxes.Sandboxes(config=prod)
```

3 parameters are possible for the instantiation of the class:

* config : OPTIONAL : the connect object instance created when you use `importConfigFile` with connectInstance parameter. Default to latest loaded configuration.
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : logging object to provide log of the application.

**Note**: Kwargs can be used to update the header used in the connection.

## Sandboxes attributes

Once you have instantiated the `Sandboxes` class, you have access to some attributes:

* sandbox : provide which sandbox is currently being used
* header : provide the default header which is used for the requests.
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods.
* ARTIFACS_TYPE : The type of artefact you can use to migrate between sandboxes


## Sandboxes methods

### getSandboxes
Return a list of all the sandboxes

### getSandboxTypes
Return the list of all the sandboxes types.

### createSandbox
Create a new sandbox in your AEP instance.\
Arguments:
* name : REQUIRED : name of your sandbox
* title : REQUIRED : display name of your sandbox
* type_sandbox : OPTIONAL : type of your sandbox. default : development.

### getSandbox
retrieve a Sandbox information by name\
Argument:
* name : REQUIRED : name of Sandbox

### getSandboxId
Retrieve the ID of a sandbox by name.\
Argument:
* name : REQUIRED : name of Sandbox

### deleteSandbox
Delete a sandbox by its name.\
Arguments:
* name : REQUIRED : sandbox to be deleted.

### resetSandbox
Reset a sandbox by its name. Sandbox will be empty.\
Arguments:
* name : REQUIRED : sandbox name to be deleted.

### updateSandbox
Update the Sandbox with the action provided.\
Arguments:
* name : REQUIRED : sandbox name to be updated.
* action : REQUIRED : dictionary defining the action to realize on that sandbox.

### getPackages
Returns the list of packages available.\
Arguments:
* prop : OPTIONAL : A list of options to filter the different packages.
    Ex: ["status==DRAFT,PUBLISHED","createdDate>=2023-05-11T18:29:59.999Z","createdDate<=2023-05-16T18:29:59.999Z"]
* limit : OPTIONAL : The number of package to return per request\
Possible kwargs:
* see https://experienceleague.adobe.com/docs/experience-platform/sandbox/sandbox-tooling-api/appendix.html?lang=en

### getPackage
Retrieve a single package.\
Arguments:
* packageId : REQUIRED : The package Id to be retrieved

### deletePackage
Delete a specific package.\
Argument:
* packageId : REQUIRED : The package ID to be deleted


### createPackage
Create a package.\
Arguments:
* name : REQUIRED : Name of the package.
* description : OPTIONAL : Description of the package
* fullPackage : OPTIONAL : If you want to copy the whole sandbox. (default False)
* artefacts : OPTIONAL : If you set fullPackage to False, then you need to provide a dictionary of items with their type.\
example :
```JS
    {"27115daa-c92b-4f17-a077-d65ffeb0c525":"PROFILE_SEGMENT",
    "d8d8ed6d-696a-40bd-b4fe-ca053ec94e29" : "JOURNEY"}
```
For more types, refers to ARTIFACS_TYPE
* expiry : OPTIONAL : The expiry of that package in days (default 90 days)

### updatePackage
Update a package ID.\
Arguments:
* packageId : REQUIRED : The package ID to be updated
* operation : OPTIONAL : Type of update, either "UPDATE", "DELETE","ADD"
* name : OPTIONAL : In case you selected UPDATE and want to change the name of the package.
* description : OPTIONAL : In case you selected UPDATE and want to change the description of the package.
* artifacts : OPTIONAL : In case you used DELETE or ADD, the dictionary of artifacts such as {"id":"type"}\
    example : {"27115daa-c92b-4f17-a077-d65ffeb0c525":"PROFILE_SEGMENT",\
    "d8d8ed6d-696a-40bd-b4fe-ca053ec94e29" : "JOURNEY"}


### publishPackage
Publish a package. Requires step before importing the package.\
Argument:
* package ID : REQUIRED : The package to be published


### importPackageCheck
Try to import a specific package in a sandbox, returns the conflicts.\
Argument:
* packageId : REQUIRED : The package ID to be imported
* targetSandbox : REQUIRED : The Target sandbox to be used.

### importPackage
This will import the different artifacts into the targetSandbox.\
You can provide a map of artifacts that are already in the targeted sandbox and should be avoided to be imported.\
Arguments:
* packageId : REQUIRED : The package ID to be imported
* targetSandbox : REQUIRED : The Target sandbox to be used
* alternatives : OPTIONAL : A dictionary, a map, of artifacts existing in your package that already exists in the targeted sandboxes.\
    example of alternative dictionary:
    ```python 
        {"artifactIdInPackage": {
            "id": "targetSandboxArtifactId"
            "type" : "REGISTRY_SCHEMA" (refer to ARTIFACS_TYPE for more types)
            }
        }
    ```
  
### getPackageDependencies
List all of the dependencies for the package specified\
Arguments:
* packageId : REQUIRED : the package ID to evaluate

### getImportExportJobs
Returns all of the jobs done or prepared\
Arguments:
* importsOnly : OPTIONAL : Boolean if you want to return the import jobs only (default False)
* exportsOnly : OPTIONAL : Boolean if you want to return the export jobs only (default False)

### checkPermissions
Check the type of access the client ID has.\
Arguments:
* packageId : REQUIRED : The package you want to copy over.
* targetSandbox : REQUIRED : The Target sandbox to be used

## Sandboxes use-cases

The usage of that module is pretty straight forward as you can use it to identify your sandboxes set on your AEP instance.\
You will need to have set the correct access right on your API connection in order to be able to manage the sandboxes.\
It requires extensive access to your AEP instance and can result in the deletion of your data so be mindful of that access.

### List all of your sandboxes and create a connector for each

```python 

import aepp
from aepp import sandboxes

prod = aepp.importConfigFile('config_oauth.json',sandbox='prod',connectInstance=True)

sand = sandboxes.Sandboxes(config=prod)

mysandboxes = sand.getSandboxes()

sandNames = [s['name'] for s in mysandboxes]

dict_sandbox = {}
for name in sandNames:
    dict_sandbox[name] = aepp.importConfigFile('config_oauth.json',sandbox=name,connectInstance=True)

```

The `dict_sandbox` will be a dictionary that use the sandbox name as key and the value will be an instance to use for the different modules `config` parameter. 