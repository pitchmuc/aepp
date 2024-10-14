# Data Access module in aepp

This documentation will provide you some explanation on how to use the Data Access module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/data-access/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu

- [Data Access module in aepp](#data-access-module-in-aepp)
- [Importing the module](#importing-the-module)
- [The DataAccess class](#the-dataaccess-class)
    - [The Profile class attributes](#the-profile-attributes)
    - [The Profile methods](#the-profile-methods)
- [Use Cases](#customer-profile-use-cases)


## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `dataaccess` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',sandbox='prod',connectInstance=True)

from aepp import dataaccess
```

The dataaccess module provides a class that you can use for generating and retrieving the different catalog objects.\

The following documentation will provide you with more information on its capabilities.

## The DataAccess class

The Data Access class is the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `DataAcess()` from the `dataaccess` module.

Following the previous method described above, you can realize this:

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',sandbox='prod',connectInstance=True)

from aepp import dataaccess
myData = dataaccess.DataAccess(config=prod)
```

There are 3 possible parameters when intantiating the class:

* config : OPTIONAL : mostly used to pass a ConnectObject instance that is linked to one sandbox. 
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : A logging object that can be passed for debuging or logging elements, see [logging documentation](./logging.md)

### Data Access Methods
Here you can find the different methods available once you have instantiated the data access class.

#### getBatchFiles
List all dataset files under a batch.\
Arguments:
* batchId : REQUIRED : The batch ID to look for.\
Possible kwargs:
* limit : A paging parameter to specify number of results per page.
* start : A paging parameter to specify start of new page. For example: page=1


#### getBatchFailed
Lists all the dataset files under a failed batch.\
Arguments:
* batchId : REQUIRED : The batch ID to look for.
* path : OPTIONAL : The full name of the file. The contents of the file would be downloaded if this parameter is provided.\
    For example: path=profiles.csv\
Possible kwargs:
* limit : A paging parameter to specify number of results per page.
* start : A paging parameter to specify start of new page. For example: page=1


#### getBatchMeta
Lists files under a batch's meta directory or download a specific file under it. The files under a batch's meta directory may include the following:
* row_errors: A directory containing 0 or more files with parsing, conversion, and/or validation errors found at the row level.
* input_files: A directory containing metadata for 1 or more input files submitted with the batch.
* row_errors_sample.json: A root level file containing the sampled set of row errors for the UX.\
Arguments:
* batchId : REQUIRED : The batch ID to look for.
* path : OPTIONAL : The full name of the file. The contents of the file would be downloaded if this parameter is provided.\
  Possible values for this query include the following:
  * row_errors
  * input_files
  * row_errors_sample.json\
Possible kwargs:
* limit : A paging parameter to specify number of results per page.
* start : A paging parameter to specify start of new page. For example: page=1

#### getHeadFile
Get headers regarding a file.\
Arguments:
* dataSetFileId : REQURED : The ID of the dataset file you are retrieving.
* path : REQUIRED : The full name of the file identified.\
For example: path=profiles.json


#### getFiles
Returns either a complete file or a directory of chunked data that makes up the file.\
The response contains a data array that may contain a single entry or a list of files belonging to that directory.\
Arguments:
* dataSetFileId : REQUIRED : The ID of the dataset file you are retrieving.
* path : OPTIONAL : The full name of the file. The contents of the file would be downloaded if this parameter is provided.\
  For example: path=profiles.csv\
  if the extension is .parquet, it will try to return the parquet data decoded (returns a io.BytesIO). 
* range : OPTIONAL : The range of bytes requested. For example: Range: bytes=0-100000
* start : OPTIONAL : A paging parameter to specify start of new page. For example: start=fileName.csv
* limit : OPTIONAL : A paging parameter to specify number of results per page. For example: limit=10

#### getPreview
Give a preview of a specific dataset\
Arguments:
* datasetId : REQUIRED : the dataset ID to preview

#### getResource
Template for requesting data with a GET method.\
Arguments:
* endpoint : REQUIRED : The URL to GET
* params: OPTIONAL : dictionary of the params to fetch
* format : OPTIONAL : Type of response returned. Possible values:\
  * json : default
  * txt : text file
  * raw : a response object from the requests module

#### getParquetFilesToDataFrame
Get a list of paths and download all of the files, transform them into dataframe and return the aggregated dataframe\
Arguments:
* dataSetFileId : REQUIRED : The ID of the dataset file you are retrieving.
* path : REQUIRED : the list of name of the files. The contents of the files will be downloaded if this parameter is provided.\
For example of value: ["YWGJ48C8R3QWPPQ_part-00001-93b3f57d-a7e5-4887-8832-f6ab1d1706b1-c0000.snappy.parquet"]\
It is intended for data that has been saved as snappy.parquet file in AEP.

#### transformDataToDataFrame
By passing the result of the getFiles with the parquet file path in the parameter, tries to return a pandas dataframe of the records.\
Argument:
* data : REQUIRED : The _io.BytesIO data format returned by the getFiles method. 

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