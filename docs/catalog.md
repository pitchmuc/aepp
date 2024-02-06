# Catalog module in aepp

This documentation will provide you some explanation on how to use the catalog module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/catalog/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu
- [Catalog module in aepp](#catalog-module-in-aepp)
  - [Menu](#menu)
  - [What is the catalog capability in AEP](#what-is-the-catalog-capability-in-aep)
  - [Importing the module](#importing-the-module)
  - [The Catalog class](#the-catalog-class)
    - [Using kwargs](#using-kwargs)
  - [Catalog use-cases](#catalog-use-cases)
    - [1. Listing the current datasets](#listing-the-current-datasets)
      - [The data attribute](#The-data-attribute)
    - [2. Monitor batch ingestion](#monitor-batch-ingestion)
    - [3. Retrieve failed batches as DataFrame](#retrieve-failed-batches-as-dataframe)
    - [4. Create DataSet](#create-dataset)
  - [Use Cases](#use-cases)

## What is the catalog capability in AEP

Catalog is the system of record for data location and lineage within Adobe Experience Platform. Catalog Service does not contain the actual files or directories that contain the data. Instead, it holds the metadata and description of those files and directories.

Catalog acts as a metadata store or "catalog" where you can find information about your data within Experience Platform.\
Simply put, Catalog acts as a metadata store or "catalog" where you can find information about your data within Experience Platform. You can use Catalog to answer the following questions:

* Where is my data located?
* At what stage of processing is this data?
* What systems or processes have acted on my data?
* How much data was successfully processed?
* What errors occurred during processing?

The data can be represented through different types of object depending the state of the data. Catalog is an exhaustive endpoint to fetch the status of these different objects:

* accounts
* batches
* connections
* connectors
* dataSets
* dataSetFiles
* dataSetViews

You can find more information on the [official documentation of the catalog](https://experienceleague.adobe.com/docs/experience-platform/catalog/home.html?lang=en#catalog-and-experience-platform-services)

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `catalog` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import catalog
```

The catalog module provides a class that you can use for generating and retrieving the different catalog objects.\

The following documentation will provide you with more information on its capabilities.

## The Catalog class

The Catalog class is the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `Catalog()` from the `catalog` module.

Following the previous method described above, you can realize this:

```py
import aepp
from aepp import catalog

mySandbox = aepp.importConfigFile('config.json',connectInstance=True,sandbox='prod')
myCat = catalog.Catalog(config=mySandbox)
```

### Using kwargs
2 parameters are possible for the instantiation of the class:

* config : OPTIONAL : the connect object instance created when you use `importConfigFile` with connectInstance parameter. Default to latest loaded configuration.
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : logging object to provide log of the application.


## Catalog use-cases

Important amount of use-cases are covered in the [Official documentation on catalog endpoints](https://experienceleague.adobe.com/docs/experience-platform/catalog/api/getting-started.html?lang=en#api).\
However, we can cover some with our module so you can see how it translates within python.

### Listing the current datasets

You have the possibility to list all of the datasets that are existing within your AEP instance or sandbox.\
In order to realize that, you can `getDatasets()` method.

This will return the list of the dataset with all information attached to them.\
The data returned could be overwhelming if you just want to have the basic information.\
For that reason, the realization of that method will feed 3 data attributes on your instance.\
You can access them by using the `data` attribute on that instance:

### The data attribute

* `catalogInstance.data.table_names`: gives you the dataSet names & Query Service names
* `catalogInstance.data.schema_ref`: gives you the dataSet names & their schema reference
* `catalogInstance.data.ids` : gives you the dataSet name and their Ids

```python
import aepp
from aepp import catalog

mySandbox = aepp.importConfigFile('config.json',connectInstance=True,sandbox='prod')
myCat = catalog.Catalog(config=mySandbox)

DataSets = myCat.getDatasets()

## table names
myCat.data.table_names

## Schema ref
myCat.data.schema_ref

## DataSet Ids
myCat.data.ids

```

### Monitor batch ingestion

The catalog module can help you identify the batches that help build the dataset. \
This can help you identify or monitor a specific dataSet for batch failure.\
Several options exist to filter for specific dataSet or specific status.
The options are kwargs parameters and are available in the docstring.

Monitoring batch for a specific dataSet:
```python
batches = myCat.getBatches(dataSet="60103d1b49bb4f194a5be4c9")
```

Monitoring failed batch:
```python
batches = myCat.getBatches(status='failed')
```

Monitoring failed batch for a specific dataSet:
```python
batches = myCat.getBatches(status='failed',dataSet="60103d1b49bb4f194a5be4c9")
```

### Retrieve failed batches as DataFrame

It is common to monitor only the batches that have failed during ingestion.\
In order to realize that, you can use one of the methods that I presented above in the documentation for batch monitoring.\
I have also created a specific failed batches monitoring method that will return you some data required for investigation.\
Name of that method : `getFailedBatchesDF`\
More data can be found by the `getBatch` method but this simplified method can be useful as reporting.\
It will provide you the following information:

* batchId
* timestamp
* recordsSize
* invalidRecordsProfile
* invalidRecordsIdentity
* invalidRecordCount
* invalidRecordsStreamingValidation
* invalidRecordsMapper
* invalidRecordsUnknown
* errorCode
* errorMessage
* flowId (if available)
* dataSetId
* sandboxId

This method is useful as it returns a dataframe that you can save for reporting or passing along to your adobe representative.

Arguments:
* limit : Limit response to a specified positive number of objects. Ex. limit=10 (max = 100)
* n_results : OPTIONAL :  number of result you want to get in total. (will loop)

```python
failedBatches = myCat.getFailedBatchesDF(limit=50,n_results=200)
```

### Create DataSet

The Catalog endpoints allows you to create DataSet programatically.\
You will need to pass the schemaRef $id to be used and set some options required (format, persistence,containerFormat).\
Example of a request type (with createDataSource set to `True`):\

```JSON
{
    "name":"Example Dataset",
    "schemaRef": {
        "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
        "contentType": "application/vnd.adobe.xed+json;version=1"
    },
    "fileDescription": {
        "persisted": true,
        "containerFormat": "parquet",
        "format": "parquet"
    }
}
```

Note that you can create dataSet for parquet or JSON format data type.

## Catalog Methods

### Get Methods

The get methods are GET HTTP protocole.\

**getResource** : Template for requesting data with a GET method.\
It is using the Header of the `Catalog` instance in order to acces some resource / URL.\
Arguments:
  * endpoint : REQUIRED : The URL to GET
  * params: OPTIONAL : dictionary of the params to fetch
  * format : OPTIONAL : Type of response returned. Possible values:\
        json : default\
        txt : text file\
        raw : a response object from the requests module

**getLastBatches** : Returns the last batch from a specific datasetId.\
Arguments:
  * dataSetId : OPTIONAL : the datasetId to be retrieved the batch about

**getBatches** : Retrieve a list of batches.\
Arguments:
  * limit : Limit response to a specified positive number of objects. Ex. limit=10 (max = 100)
  * n_results : OPTIONAL :  number of result you want to get in total. (will loop)
  * output : OPTIONAL : Can be "raw" response (dict) or "dataframe".
  Possible kwargs:
  * created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
  * createdAfter : Exclusively filter records created after this timestamp. 
  * createdBefore : Exclusively filter records created before this timestamp.
  * start : Returns results from a specific offset of objects. This was previously called offset. (see next line)
  *  offset : Will offset to the next limit (sort of pagination)        
  * updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
  * createdUser : Filter by the ID of the user who created this object.
  * dataSet : Used to filter on the related object: &dataSet=dataSetId.
  * version : Filter by Semantic version of the account. Updated when the object is modified.
  * status : Filter by the current (mutable) status of the batch.
  * orderBy : Sort parameter and direction for sorting the response. 
        Ex. orderBy=asc:created,updated. This was previously called sort.
  * properties : A comma separated whitelist of top-level object properties to be returned in the response.\
    Used to cut down the number of properties and amount of data returned in the response bodies.
  * size : The number of bytes processed in the batch.

**getFailedBatchesDF** :  Abstraction of getBatches method that focus on failed batches and return a dataframe with the batchId and errors.\
Also adding some meta data information from the batch information provided.\
Arguments:
  * limit : Limit response to a specified positive number of objects. Ex. limit=10 (max = 100)
  * n_results : OPTIONAL :  number of result you want to get in total. (will loop)
  * orderBy : OPTIONAL : The order of the batch. Default "desc:created"\
    Possible kwargs: Any additional parameter for filtering the requests



### Create Methods

The create methods are POST HTTP protocole.\


## Other methods

The other methods can be PUT, PATCH or wrapping methods.

**decodeStreamBatch** : Decode the full txt batch via the codecs module.\
Usually the full batch is returned by the getResource method with format == "txt".\
Arguments:
  * message: REQUIRED : the text file return from the failed batch message.
  
return `None` when issue is raised

**jsonStreamMessages** : Try to create a list of dictionary messages from the decoded stream batch extracted from the decodeStreamBatch method.\  Arguments:
  * message : REQUIRED : a decoded text file, usually returned from the decodeStreamBatch method
  * verbose : OPTIONAL : print errors and information on the decoding.
        
return `None` when issue is raised