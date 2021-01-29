# Data Access module in aepp

This documentation will provide you some explanation on how to use the Data Access module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/data-access-api.yaml).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `dataaccess` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import dataaccess
```

The catalog module provides a class that you can use for generating and retrieving the different catalog objects.\

The following documentation will provide you with more information on its capabilities.

## The DataAccess class

The Catalog class is the default API connector that you would encounter for any other submodules on this python module.\
This class can be instanciated by calling the `DataAcess()` from the `dataaccess` module.

Following the previous method described above, you can realize this:

```python
myData = dataaccess.DataAccess()
```

2 parameters are possible for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

## Data Access use-cases

The Data Access module will enable you to identify and download files that are holding your data.\
All data that you have previously ingested within Adobe Experience Platform can be downloaded from this API endpoint.

When working with Adobe Experience Platform, you work with Batch ingestion data. Due to that setup, you will also retrieve information regardings batch file.

### Retrieving Files from Platform

The `getBatchFiles` method will retrieve all the files ingested under a Batch.
```python
myData.getBatchFiles()
```

The important element is that the response will provide you with a link such as:
```JSON
{
    "href": "https://platform.adobe.io/data/foundation/export/files/{FILE_ID_1}"
}
```

This is the URL where you can have multiple files within a batch.
You can also retrieve the `FILE ID` from the response and use it with another method

### The getFiles method

From the `FILE ID` retrieved from the `getBatchFiles` method, you can directly use them with the `getFiles` method.

```python
myData.getFiles(dataSetFileId='fileId')
```

**IMPORTANT** : This method will provide either the complete file or a list of chunk for a file.
If a list of chunk data are exposed, you can download them separately by providing the path parameter.
Example:

```python
myData.getFiles(dataSetFileId='fileId',path='profile.csv')
```