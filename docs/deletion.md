# Deletion module in aepp

This documentation will provide you some explanation on how to use the `deletion` module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
This module is NOT an existing module in Adobe Experience Platform.\
It has been created as many customers do not know how to delete artefacts in Adobe Experience Platform. Also, it covers the deletion of dependencies if you want to delete more than the artefacts.\
Example: Deleting the Schema may not be enough, but you would like to also delete all the associated Field Groups and Data Types associated.  

## Menu
- [Deletion module in aepp](#deletion-module-in-aepp)
  - [Menu](#menu)
  - [Importing the module](#importing-the-module)
  - [The Deletion class](#the-deletion-class)
    - [The Deletion class attributes](#the-deletion-class-attributes)
    - [Methods available on the deletion class](#methods-available-on-the-deletion-class)
      - [deleteAudience](#deleteaudience)
      - [deleteSchema](#deleteschema)
      - [deleteDataFlow](#deletedataflow)
      - [deleteDataset](#deletedataset)

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `deletion` keyword.

```python
import aepp
sandbox = aepp.importConfigFile('myConfig_file.json',sandbox='mysandbox',connectedInstance=True)
from aepp import deletion
```
The destination module provides a class that you can use to generate a SDK taking care of transfering some information to specific destination endpoints.\
The following documentation will provide you with more information on its capabilities.

## The Deletion class

The `Deletion` class exist in the `deletion` module. It regroups methods existing in the different other modules of `aepp`. They are based on existing deletion methods from the Adobe Experience Platform APIs.


**NOTE**: 
* The Adobe Privacy Service API, to delete records from GDPR or CCPA requests remains in its own module ([privacyservice](./privacyservice.md)) 
* The Data Hygiene service to delete records from Adobe Experience Platform remains in its own module ([data hygiene](./hygiene.md))

Both of these modules are solely created to delete records and bringing them in the deletion module would confuse non-experience users in the correct module to use.  

In order to load the Deletion class, you can use the following: 

```py
import aepp
sandbox = aepp.importConfigFile('myConfig_file.json',sandbox='mysandbox',connectedInstance=True)
from aepp import deletion
mydeletion = deletion.Deletion(config=sandbox)
```

### The Deletion class attributes

Some attributes are available once you have instantiated the deletion class.
Accessible attributes: 
* header : The header that contains the token for connecting to the different API
* config : The `config` object that will be used to log into different API Service

### Methods available on the deletion class

Here are the different method available on this special module.

#### deleteAudience
Delete an audience/segment.\
Arguments:
* audienceId : REQUIRED : The identifier of the audience to delete.

The deletion of an audience can be quite challenging task, as it requires you to make sure that the audience is not mapped to any destination before deleting it.\
By using this method, this process is automated. 


#### deleteSchema
Delete a schema and possibly all associated artefacts.\
Arguments:
* schemaId : REQUIRED : The identifier of the schema to delete.
* associatedArtefacts : OPTIONAL : If set to True, all associated artefacts (fieldGroup, datatype) will also be deleted (default False).\
  **Note** : Deleting associated arterfacts option will be pass down to other methods called within this method. So Field Groups, Data Type could be impacted.\
  In case, it is not possible to delete artefacts, it will be silently ignored and returns in the output dictionary.

You may sometimes want to delete not only the schema but also all of their children (field groups and data type). This method provide the possibility to go down the different elements and try delete all of them.

#### deleteDataFlow
Delete a dataflow and possibly all associated artefacts.\
Arguments:
* flowId : REQUIRED : The identifier of the dataflow to delete.
* associatedArtefacts : OPTIONAL : If set to True, all associated artefacts (source and target) will also be deleted (default False).\
  **Note** : The base connection will be identified and returned but not deleted. It can contains other dataflows still actives."""

The deletion of the datalflow can be generated and all associated source and target connection can also be deleted.\
The base connection, that serves as an Account in the UI, will be identified but not deleted. You would still need to do that manually if you want to. 

#### deleteDataset
Delete a dataset and all associated artefacts (dataflows, schemas, data connections).\
Arguments:
* datasetId : REQUIRED : The identifier of the dataset to delete.
* associatedArtefacts : OPTIONAL : If set to True, all associated artefacts (dataflows, schemas) will also be deleted (default False).\
  **Note** : Deleting associated arterfacts option will be pass down to other methods called within this method. So Field Groups, Data Type could be impacted.\
  In case, it is not possible to delete artefacts, it will be silently ignored and returns in the output dictionary.

This method for the dataset can also help deleting all associated elements to it, if possible. 
It means that the associated elements can be deleted:
- Schema
- Field Groups 
- DataFlow
