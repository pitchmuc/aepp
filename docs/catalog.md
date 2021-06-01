# Catalog module in aepp

This documentation will provide you some explanation on how to use the catalog module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/catalog.yaml).\
Alternatively, you can use the docstring in the methods to have more information.

## What is the catalog capability in AEP ?

Catalog is the system of record for data location and lineage within Adobe Experience Platform. Catalog Service does not contain the actual files or directories that contain the data. Instead, it holds the metadata and description of those files and directories.

Catalog acts as a metadata store or “catalog” where you can find information about your data within Experience Platform.\
Simply put, Catalog acts as a metadata store or “catalog” where you can find information about your data within Experience Platform. You can use Catalog to answer the following questions:

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
This class can be instanciated by calling the `Catalog()` from the `catalog` module.

Following the previous method described above, you can realize this:

```python
myCat = catalog.Catalog()
```

2 parameters are possible for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

## Catalog use-cases

Important amount of use-cases are covered in the [Official documentation on catalog endpoints](https://experienceleague.adobe.com/docs/experience-platform/catalog/api/getting-started.html?lang=en#api).\
However, we can cover some with our module so you can see how it translates within python.

### Listing the current datasets

You have the possibility to list all of the datasets that are existing within your AEP instance or sandbox.\
In order to realize that, you can `getDatasets()` method.

This will return the list of the dataset with all information attached to them.\
The data returned could be overwhelming if you just want to have the basic information.\
For that reason, the realization of that method will feed 3 data attributes on your instance.\
You can access them by using:

* `data.table_names`: gives you the dataSet names & Query Service names
* `data.schema_ref`: gives you the dataSet names & their schema reference
* `data.ids` : gives you the dataSet name and their Ids

```python
myCat = catalog.Catalog()

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
