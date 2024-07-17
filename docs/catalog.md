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
    - [Catalog methods](#catalog-methods)
  - [Observable Schema Manager](#observable-schema-manager)
    - [Observable Schema Manager Methods](#observable-schema-manager-methods)
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

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md).\
Note that I am using the `connectInstance` parameter to save the configuration imported.

To import the module you can use the import statement with the `catalog` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')

from aepp import catalog
```

The catalog module provides a class that you can use for generating and retrieving the different catalog objects.\
The following documentation will provide you with more information on its capabilities.

## The Catalog class

The `Catalog` class is the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `Catalog()` from the `catalog` module.

Following the previous method described above, you can realize this:

```py
import aepp
from aepp import catalog

mySandbox = aepp.importConfigFile('config.json',connectInstance=True,sandbox='prod')
myCat = catalog.Catalog(config=mySandbox)
```

3 parameters are possible for the instantiation of the class:

* config : OPTIONAL : the connect object instance created when you use `importConfigFile` with connectInstance parameter. Default to latest loaded configuration.
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : logging object to provide log of the application.

## Catalog methods

On the elements below, you can find all methods existing and that you can query when instantiating the `Catalog` class.

#### getResource
Template for requesting data with a GET method.\
Arguments:
* endpoint : REQUIRED : The URL to GET
* params: OPTIONAL : dictionary of the params to fetch
* format : OPTIONAL : Type of response returned. Possible values:
  * json : default
  * txt : text file
  * raw : a response object from the requests module


#### decodeStreamBatch
Decode the full txt batch via the codecs module.\
Usually the full batch is returned by the getResource method with format == "txt".\
Arguments:
* message: REQUIRED : the text file return from the failed batch message.

return None when issue is raised


#### jsonStreamMessages
Try to create a list of dictionary messages from the decoded stream batch extracted from the decodeStreamBatch method.\
Arguments:
* message : REQUIRED : a decoded text file, usually returned from the decodeStreamBatch method
* verbose : OPTIONAL : print errors and information on the decoding.

return None when issue is raised


#### getLastBatches
Returns the last batch from a specific datasetId.\
Arguments:
* dataSetId : OPTIONAL : the datasetId to be retrieved the batch about
* limit : OPTIONAL : number of batch per request\
Possible kwargs:
* created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
* lastBatchStatus : Filter by the status of the last related batch of the dataset [success, inactive, replay]
* properties : A comma separated allowlist of top-level object properties to be returned in the response. Used to cut down the number of properties and amount of data returned in the response bodies.


#### getBatches
Retrieve a list of batches.\
Arguments:
* limit : Limit response to a specified positive number of objects. Ex. limit=10 (max = 100)
* n_results : OPTIONAL :  number of result you want to get in total. (will loop - "inf" to get as many as possible)
* output : OPTIONAL : Can be "raw" response (dict) or "dataframe".\
Possible kwargs:
* created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
* createdAfter : Exclusively filter records created after this timestamp. 
* createdBefore : Exclusively filter records created before this timestamp.
* start : Returns results from a specific offset of objects. This was previously called offset. (see next line)\
    offset : Will offset to the next limit (sort of pagination)        
* updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
* createdUser : Filter by the ID of the user who created this object.
* dataSet : Used to filter on the related object: &dataSet=dataSetId.
* version : Filter by Semantic version of the account. Updated when the object is modified.
* status : Filter by the current (mutable) status of the batch.\
possible values:"processing","success","failure","queued","retrying","stalled","aborted","abandoned","inactive","failed","loading","loaded","staged","active","staging","deleted"
* orderBy : Sort parameter and direction for sorting the response.\ 
    Ex. orderBy=asc:created,updated. This was previously called sort.
* properties : A comma separated whitelist of top-level object properties to be returned in the response.\
    Used to cut down the number of properties and amount of data returned in the response bodies.
* size : The number of bytes processed in the batch.\
/Batches/get_batch, more details : https://www.adobe.io/apis/experienceplatform/home/api-reference.html


#### getFailedBatchesDF
Abstraction of getBatches method that focus on failed batches and return a dataframe with the batchId and errors.\
Also adding some meta data information from the batch information provided.\
Arguments:
* limit : Limit response to a specified positive number of objects. Ex. limit=10 (max = 100)
* n_results : OPTIONAL :  number of result you want to get in total. (will loop)
* orderBy : OPTIONAL : The order of the batch. Default "desc:created"\
Possible kwargs: Any additional parameter for filtering the requests


#### getBatch
Get a specific batch id.\
Arguments:
* batch_id : REQUIRED : batch ID to be retrieved.


#### createBatch
Create a new batch.\
Arguments:
* object : REQUIRED : Object that define the data to be onboarded.\
see reference here: https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Batches/postBatch


#### getResources
Retrieve a list of resource links for the Catalog Service.\
Possible kwargs:
* limit : Limit response to a specified positive number of objects. Ex. limit=10
* orderBy : Sort parameter and direction for sorting the response.\
  Ex. orderBy=asc:created,updated. This was previously called sort.
* property : A comma separated whitelist of top-level object properties to be returned in the response.\
  Used to cut down the number of properties and amount of data returned in the response bodies.


#### getDataSets
Return a list of a datasets.\
Arguments:
* limit : REQUIRED : amount of dataset to be retrieved per call. 
* output : OPTIONAL : Default is "raw", other option is "df" for dataframe output\
Possible kwargs:
* state : The state related to a dataset.
* created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
* updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
* name : Filter by the a descriptive, human-readable name for this DataSet.
* namespace : One of the registered platform acronyms that identify the platform.
* version : Filter by Semantic version of the account. Updated when the object is modified.
* property : Regex used to filter objects in the response. Ex. property=name~^test.\
  /Datasets/get_data_sets, more possibilities : https://www.adobe.io/apis/experienceplatform/home/api-reference.html


#### getProfileSnapshotDatasets
Return a dictionary of Profile Snapshot datasetId, containing the information related to them.\
Arguments:
  * explicitMergePolicy : OPTIONAL : Provide a mergePolicyName attribute for the dataset to explain.


#### createDataSets
Create a new dataSets based either on preconfigured setup or by passing the full dictionary for creation.\
Arguments:
* data : REQUIRED : If you want to pass the dataset object directly (not require the name and schemaId then)\
    more info: https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Datasets/postDataset
* name : REQUIRED : if you wish to create a dataset via autocompletion. Provide a name.
* schemaId : REQUIRED : The schema $id reference for creating your dataSet.
* profileEnabled : OPTIONAL : If the dataset to be created with profile enbaled
* identityEnabled : OPTIONAL : If the dataset should create new identities
* upsert : OPTIONAL : If the dataset to be created with profile enbaled and Upsert capability.
* tags : OPTIONAL : set of attribute to add as tags.
* systemLabels : OPTIONAL : A list of string to attribute system based label on creation.\
possible kwargs:
* requestDataSource : Set to true if you want Catalog to create a dataSource on your behalf; otherwise, pass a dataSourceId in the body.


#### getDataSet
Return a single dataset.\
Arguments:
* datasetId : REQUIRED : Id of the dataset to be retrieved.


#### getDataSetObservableSchema
Return a single dataset observable schema.\
Which means that the fields that has been used in that dataset.\
Arguments:
* datasetId : REQUIRED : Id of the dataset for which the observable schema should be retrieved.
* appendDatasetInfo : OPTIONAL : If set to True, it will append the "datasetId" into the dictionary return


#### deleteDataSet
Delete a dataset by its id.\
Arguments:
* datasetId : REQUIRED : Id of the dataset to be deleted.


#### getDataSetViews
Get views of the datasets.\
Arguments:
* datasetId : REQUIRED : Id of the dataset to be looked down.\
Possible kwargs:
* limit : Limit response to a specified positive number of objects. Ex. limit=10
* orderBy : Sort parameter and direction for sorting the response. Ex. orderBy=asc:created,updated.
* start : Returns results from a specific offset of objects. This was previously called offset. Ex. start=3.
* property : Regex used to filter objects in the response. Ex. property=name~^test.


#### getDataSetView
Get a specific view on a specific dataset.\
Arguments:
* datasetId : REQUIRED : ID of the dataset to be looked down.
* viewId : REQUIRED : ID of the view to be look upon.


#### getDataSetViewFiles
Returns the list of files attached to a view in a Dataset.\
Arguments:
* datasetId : REQUIRED : ID of the dataset to be looked down.
* viewId : REQUIRED : ID of the view to be look upon.


#### enableDatasetProfile
Enable a dataset for profile with upsert.\
Arguments:
* datasetId : REQUIRED : Dataset ID to be enabled for profile
* upsert : OPTIONAL : If you wish to enabled the dataset for upsert.


#### enableDatasetIdentity
Enable a dataset for profile with upsert.\
Arguments:
* datasetId : REQUIRED : Dataset ID to be enabled for Identity


#### enableDatasetUpsert
Enable a dataset for upsert on profile.
        The dataset is automatically enabled for profile as well.
        Arguments:
            datasetId : REQUIRED : Dataset ID to be enabled for upsert


#### disableDatasetProfile
Disable the dataset for Profile ingestion.\
Arguments:
* datasetId : REQUIRED : Dataset ID to be disabled for profile


#### disableDatasetIdentity
Disable a dataset for identity ingestion\
Arguments:
* datasetId : REQUIRED : Dataset ID to be disabled for Identity


#### createUnionProfileDataset
Create a dataset with an union Profile schema.


#### getMapperErrors
Get failed batches for Mapper errors, based on error code containing "MAPPER".\
Arguments:
* limit : OPTIONAL : Number of results per requests
* n_results : OPTIONAL : Total number of results wanted.\
Possible kwargs:
* created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
* createdAfter : Exclusively filter records created after this timestamp. 
* createdBefore : Exclusively filter records created before this timestamp.
* start : Returns results from a specific offset of objects. This was previously called offset. (see next line)\
  offset : Will offset to the next limit (sort of pagination)        
* updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
* createdUser : Filter by the ID of the user who created this object.
* dataSet : Used to filter on the related object: &dataSet=dataSetId.
* version : Filter by Semantic version of the account. Updated when the object is modified.
* status : Filter by the current (mutable) status of the batch.
* orderBy : Sort parameter and direction for sorting the response.\
  Ex. orderBy=asc:created,updated. This was previously called sort.
*properties : A comma separated whitelist of top-level object properties to be returned in the response.\
  Used to cut down the number of properties and amount of data returned in the response bodies.
* size : The number of bytes processed in the batch.


#### findActiveBatch
Recursive function to find the active batch from any batch.\
In case the active batch is part of a consolidation job, it returns the batch before consolidation.\
Argument:
* batchId : REQUIRED : The original batch you want to look.
* predecessor : OPTIONAL : The predecessor


## Observable Schema Manager

The `ObservableSchemaManager` is a class that will allow you to take the observable schema returned by the `getDataSetObservableSchema` method and construct a similar element that is the [Schema Manager](./schemaManager.md).\
This would allow you to use the `to_dataframe` or `to_dict` in order to build visual representation of the data being ingested in that dataset. 
You can then compare the defined schema with the observable schema in order to see which fields is used or not.

### Instantiation 

In order to instantiate the `ObservableSchemaManager`, you would need to provide the response of the `getDataSetObservableSchema` method.
Argument:
* observableSchema : dictionary of the data stored in the "observableSchema" key

### Observable Schema Manager Methods

#### searchField
Search a field in the observable schema.\
Arguments:
* string : REQUIRED : the string to look for for one of the field
* partialMatch : OPTIONAL : if you want to look for complete string or not. (default True)
* caseSensitive : OPTIONAL : if you want to compare with case sensitivity or not. (default False)


#### to_dataframe
Generate a dataframe with the row representing each possible path.\
Arguments:
* save : OPTIONAL : If you wish to save it with the title used by the field group.\
  save as csv with the title used. Not title, used "unknown_fieldGroup_" + timestamp.
* queryPath : OPTIONAL : If you want to have the query path to be used.
* description : OPTIONAL : If you want to have the description used


#### to_dict
Generate a dictionary representing the field group constitution\
Arguments:
* typed : OPTIONAL : If you want the type associated with the field group to be given.
* save : OPTIONAL : If you wish to save the dictionary in a JSON file


#### compareSchemaAvailability
A method to compare the existing schema with the observable schema and find out the difference in them.\
It output a dataframe with all of the path, the field group, the type (if provided) and the part availability (in that dataset)\
Arguments:
* SchemaManager : REQUIRED : the SchemaManager class instance for that schema.



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