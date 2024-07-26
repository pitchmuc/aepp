# Ingestion module in aepp

This documentation will provide you some explanation on how to use the `ingestion` module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
This module is containing 2 main method to ingest data into AEP, the batch upload and the HTTP Stream.\
To have a full view on the different API endpoints specific to the schema API, please refer to these documentations:
* [Batch Upload](https://developer.adobe.com/experience-platform-apis/references/batch-ingestion/)
* [HTTP Stream](https://developer.adobe.com/experience-platform-apis/references/streaming-ingestion/)

Alternatively, you can use the docstring in the methods to have more information.

## What is the Data Ingestion in AEP ?

The Data Ingestion endpoints allows you to send data to AEP data lake directly (through your datasets).\
You can ingest the data through Batch or via Streaming.\
Batch ingestion lets you import data in batch, from any number of data sources.\
Streaming ingestion lets users send data to Platform in real time from client and server-side devices.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `ingestion` keyword.

```python
import aepp
dev = aepp.importConfigFile('myConfig_file.json',sandbox='dev',connectInstance=True)

from aepp import ingestion
```

The ingestion module provides a class that you can use for ingesting data into your datasets (see below).\
The following documentation will provide you with more information on its capabilities.

## The DataIngestion class

The `DataIngestion` class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `DataIngestion()` class from the `ingestion` module.\
As you can see, it is one of the only class that is not directly named after its submodule.

Following the previous method described above, you can realize this:

```python
import aepp
dev = aepp.importConfigFile('myConfig_file.json',sandbox='dev',connectInstance=True)

from aepp import ingestion
myConnector = ingestion.DataIngestion(dev)
```

2 parameters are possible for the instantiation of the class:

2 parameters are possible for the instantiation of the class:
* config : OPTIONAL : mostly used to pass a ConnectObject instance that is linked to one sandbox. 
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : A logging object that can be passed for debuging or logging elements, see [logging documentation](./logging.md)

### DataIngestion attributes

You can access some attributes once you have instantiated the class.\
These following elements would be available:

* sandbox : provide which sandbox is currently being used
* header : provide the default header which is used for the requests.
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods.
* STREAMING_REFERENCE : A Payload example on how to ingest data with HTTP API (single message)
* TAG_BATCH_MAPPING : A Template on how to setup a tag for BATCH creation with mapping

### DataIngestion methods
On the elements below, you can find all methods existing and that you can query when instantiating the `DataIngestion` class.

#### createBatch
Create a new batch in Catalog Service. This batch will be used to upload files with other methods.\
You will receive the new batch ID to use.
Arguments:
* datasetId : REQUIRED : The Dataset ID for the batch to upload data to.
* format : REQUIRED : the format of the data send.(default json)
* multiline : OPTIONAL : If you wish to upload multi-line JSON.
* tags : OPTIONAL : In case some additional tags needs to be specified.\
Possible kwargs:
* replay : the replay object to replay a batch.
https://experienceleague.adobe.com/docs/experience-platform/ingestion/batch/api-overview.html?lang=en#replay-a-batch


#### deleteBatch
Delete a batch by applying the revert action on it.\
Argument:
* batchId : REQUIRED : Batch ID to be deleted


#### replayBatch
You can replay a batch that has already been ingested. You need to provide the datasetId and the list of batch to be replay.\
Once specify through that action, you will need to re-upload batch information via uploadSmallFile method with JSON format and then specify the completion.\
You will need to re-use the batchId provided for the re-upload.\
Arguments:
* dataSetId : REQUIRED : The dataset ID attached to the batch
* batchIds : REQUIRED : The list of batchID to replay.

#### uploadSmallFile
Upload a small file (<256 MB) to the filePath location in the dataset.\
You need to have created a batch before using this action.
Arguments:
* batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
* datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
* filePath : REQUIRED : the filePath that will store the value.
* data : REQUIRED : The data to be uploaded (following the type provided). List or Dictionary, depending if multiline is enabled.\
    You can also pass a JSON file path. If the element is a string and ends with ".json", the file will be loaded and transform automatically to a dictionary. 
* verbose: OPTIONAL : if you wish to see comments around the ingestion

#### uploadLargeFileStartEnd
**DEPRECATED**
Start / End the upload of a large file with a POST method defining the action (see parameter)\
Arguments:
* batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
* datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
* filePath : REQUIRED : the filePath that will store the value.
* action : REQUIRED : Action to either INITIALIZE or COMPLETE the upload.

#### uploadLargeFilePart
**DEPRECATED**
Continue the upload of a large file with a PATCH method.\
Arguments:
* batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
* datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
* filePath : REQUIRED : the filePath that will store the value.
* data : REQUIRED : The data to be uploaded (in bytes)
* contentRange : REQUIRED : The range of bytes of the file being uploaded with this request.

#### headFileStatus
Check the status of a large file upload.\
Arguments:
* batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
* datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
* filePath : REQUIRED : the filePath that reference the file.

#### getPreviewBatchDataset
Generates a data preview for the files uploaded to the batch so far. The preview can be generated for all the batch datasets collectively or for the selected datasets.\
Arguments:
* batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
* datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
* format : REQUIRED : Format of the file ('json' default)
* delimiter : OPTIONAL : The delimiter to use for parsing column values.
* quote : OPTIONAL : The quote value to use while parsing data.
* escape : OPTIONAL : The escape character to use while parsing data.
* charset : OPTIONAL : The encoding to be used (default utf-8)
* header : OPTIONAL : The flag to indicate if the header is supplied in the dataset files.
* nrow : OPTIONAL : The number of rows to parse. (default 5) - cannot be 10 or greater

#### streamMessage
Send a dictionary to the connection for streaming ingestion.\
Arguments:
* inletId : REQUIRED : the connection ID to be used for ingestion
* data : REQUIRED : The data that you want to ingest to Platform.
* flowId : OPTIONAL : The flow ID for the stream inlet.
* syncValidation : OPTIONAL : An optional query parameter, intended for development purposes.\
    If set to true, it can be used for immediate feedback to determine if the request was successfully sent.

#### streamMessages
Send a dictionary to the connection for streaming ingestion.\
Arguments:
* inletId : REQUIRED : the connection ID to be used for ingestion
* data : REQUIRED : The list of data that you want to ingest to Platform.
* flowId : OPTIONAL : The flow ID for the stream inlet.
* syncValidation : OPTIONAL : An optional query parameter, intended for development purposes.\
    If set to true, it can be used for immediate feedback to determine if the request was successfully sent.


## Use-cases

### Streaming Use-case

By having an inlet available for your connection, you can use it with either:

* the `StreamMessage` method to send a single message to your dataSet.
* the `StreamMessages` method to send multiple messages to your dataSet (batch streaming). This one take a list as main parameter.

**NOTE**: In order to have an inlet you can either create one via the UI or via the API (use the [flowservice](./flowservice.md) module)

I find it particularly useful to use these methods when you want to debug your ingestion process.\
You can find a template of a message with the `STREAMING_REFERENCE` attribute of the class.\
Accessing it like this:

```python
myConnector.STREAMING_REFERENCE
## will return
{
"header": {
    "schemaRef": {
    "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
    "contentType": "application/vnd.adobe.xed-full+json;version={SCHEMA_VERSION}"
    },
    "imsOrgId": "{IMS_ORG_ID}",
    "datasetId": "{DATASET_ID}",
    "createdAt": "1526283801869",
    "source": {
    "name": "{SOURCE_NAME}"
    }
},
"body": {
    "xdmMeta": {
    "schemaRef": {
        "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
        "contentType": "application/vnd.adobe.xed-full+json;version={SCHEMA_VERSION}"
    }
    },
    "xdmEntity": {
    "person": {
        "name": {
        "firstName": "Jane",
        "middleName": "F",
        "lastName": "Doe"
        },
        "birthDate": "1969-03-14",
        "gender": "female"
    },
    "workEmail": {
        "primary": True,
        "address": "janedoe@example.com",
        "type": "work",
        "status": "active"
    }
    }
}
}
```

### Batch use case


#### Importing a small batch

You can ingest batch into the datset by using the different batch method.\
It is recommended to use this API for small files.\
Uploading large file is a method that will not be supported in the future and is deprecated.

The first thing you will need to do is to identify the dataset you want to upload the batch to, more importantly the `datasetId` is the element to know.\
In order to do that, you will need to use the `catalog` module.\
You can find details on the catalog module [here](./catalog.md)\

```python

import aepp
from aepp import catalog, ingestion

dev = aepp.importConfigFile('myConfig_file.json',sandbox='dev',connectInstance=True)

cat = catalog.Catalog(dev)
mydatasets = cat.getDatasets()

mydatasetId = cat.data.ids['my dataset name']

```

Once you have your datasetId, you can create your batch.\
Note that you can add a mapping capability during batch ingestion, for the sake of demontration we will use a mapping in this example.\
You can create a mappingSetFile via the [dataprep capability](./dataprep.md)\
We will create the batch to ingest JSON data and with multiline as well.

It means that the format of the data will be as : 

```JSON
[
    {/*data*/},
    {/*data*/},
]
```

I will then retrievethe batchId that has been created to load the file.\
It is part of the response from the `createBatch` method.


```python

myMappingFileSetId = "mappingFileSetId" ## example
tags = {
    "aep_sip_mapper": [f"mapping-set-id:{myMappingFileSetId}","mapping-set-version:0"]
}

myIng = ingestion.DataIngestion(dev) ## instantiate the class

myNewbatch = myIng.createBatch(mydatasetId,multiline=True,tags=tags,format='json')
myBatchId = myNewbatch['id']

```

Once we have save the `batchId`, we can use it to send the data via the `uploadSmallFile` method.\
You can either send the data as a `dictionary` (for single-line upload), `list` (for multi-line upload), or just send the path to the file for upload.\
Once the upload is done, you would need to use the `uploadSmallFileFinish` to complete the batch so it is promoted to the DataLake and all other services (UIS, UPS).

```python
import json
with open('myfilewithdata.json','r') as f:
    myData = json.load(f)

myIng.uploadSmallFile(batchId=myBatchId,datasetId=mydatasetId,data=myData,filePath='path_test.json')

myIng.uploadSmallFileFinish(myBatchId) ## complete the upload

```
