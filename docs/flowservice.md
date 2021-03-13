# Flow Service module in aepp

This documentation will provide you some explanation on how to use the Flow Service module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/flow-service.yaml).\
Alternatively, you can use the docstring in the methods to have more information.

## What is the Flow Service in AEP ?

The Flow Service create the different connectors for data ingestion inside Platform.\
It is true that you can ingest data directly into Adobe Experience Platform via the Data Insertion API.\
However, it is recommended and usually preferred to set up a pipeline from different data sources.\

The data sources available can be of different sort (Azure Blob, AWS S3, (S)FTP, HTTP streaming, etc...).\
In order to deal with all of that setup, the flow service has been created so it can scale to different type of source connector.\
Once you have setup the flow in the Adobe Experience platform API via a Source, but also a destination, you can run this flow in order for the pipeline to run.

In order to make the best of this API, it is preferred to have connection to one of the possible data source method cited previously.\
We will see later on how the process look like.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `flowservice` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import flowservice
```

The flowservice module provides a class that you can use for managing your connection to your Source and Destinations (see below).\
The following documentation will provide you with more information on its capabilities.

## The FlowService class

The FlowService class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instanciated by calling the `FlowService()` from the `flowservice` module.

Following the previous method described above, you can realize this:

```python
flw = flowservice.FlowService()
```

2 parameters are possible for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

## Use-cases

### Workflow for Flow Service

In order to use the Flow Service API, the different elements have dependencies and requires to be created in a specific order.\
The documentation of this API is a bit different from the other documentation as the use-case will be explained as you read through the process.

#### Create a connection setup

The first element you need to realize is to create a connection for your data to reference a specific setup.\
You can create a connection with the `createConnection` method. This will require some parameters to be filled.
The most important one is the `id` for the connectionSpec. This connectionSpec id can be retrieved from the list of available connectionSpec in Platform.\
As explained in the introduction, AEP supports lots of connection type (not everything) and each connection has specific paramaters that are required.\
You can find your connectionSpec Id by calling the `getConnectionSpecs` method in the module.\
This method will return the list of the different available connection ID and their specifications.

```python

import aepp
from aepp import flowservice

## importing the configuration
aepp.importConfigFile('myConfig.json')

## instantiate the 
flw = flowservice.FlowService()

## retrieving the possible connections specifications
conns = flw.getConnectionSpecs()

## Getting Streaming - Just an example
streaming = [spec for spec in specs if spec['name'] == "Streaming Connection"][0]
From there, you can find the different ID required.
## Provider ID would look like this : 'providerId': '521eee4d-8cbe-4906-bb48-fb6bd4450033'
## ID would look like this : 'id': 'bc7b00d6-623a-4dfc-9fdb-f1240aeadaeb'

newConnection = {
            "name": "My New Connection",
            "providerId": "521eee4d-8cbe-4906-bb48-fb6bd4450033",
            "description": "description",
            "connectionSpec": {
                "id": "bc7b00d6-623a-4dfc-9fdb-f1240aeadaeb",
                "version": "1.0"
            },
            "auth": {
                "specName": "Streaming Connection",
                "params": {
                    "sourceId": "AnIDString",
                    "dataType": "raw",
                    "name": "New Connection"
                }
            }
        }
```

### Connect to your Source connection

Once that you have created your global connection, you will receive an ID in return that you can use to connect new source (and target) connection.\
For your Source Connection, depending the connectionSpec that you have selected, you will need to create a dictionary that specify the different information requires.\
You can find the list of potential information requires in the [official documentation](https://experienceleague.adobe.com/docs/experience-platform/sources/home.html?lang=en#create).

For FTP per example, it will look like the following:

```JSON
{
        "name": "FTP connector with password",
        "description": "FTP connector password",
        "auth": {
            "specName": "Basic Authentication for FTP",
            "params": {
                "host": "{HOST}",
                "userName": "{USERNAME}",
                "password": "{PASSWORD}"
            }
        },
        "connectionSpec": {
            "id": "fb2e94c9-c031-467d-8103-6bd6e0a432f2",
            "version": "1.0"
        }
    }
```

Note that the `"fb2e94c9-c031-467d-8103-6bd6e0a432f2"` will be the ID attached to connection Spec (the FTP one in this case).

In the module you will need to use the ID on your request.\

```python
obj = {...}## your object with correct data 
res = flw.createSourceConnection(data=obj)
```

The *res* variable shloud then possess the ID of the source connection created.\

**Streaming Connection Source**
Creating a HTTP streaming connection source is pretty easy because you do not require any specific setup on your side.\
This the reason why I created an easy creation setup for that with the method: `createSourceConnectionStreaming`.\
This method takes 4 arguments:

* connectionId : REQUIRED : The Streaming connection ID (you have this from the previous step)
* name : REQUIRED : Name of the Connection.
* format : REQUIRED : format of the data sent (default : delimited) Possible to have it raw.
* description : OPTIONAL : Description of of the Connection Source.

### Connect to a Target Destination

Most of the case, you want to send data to the AEP datalake, therefore, there is a connection spec for that.\
The same way that you did for the Source Connection, you will need to pick the correct ConnectionSpec and assign it to the Target Connection.\
You can create a target connection by calling the `createTargetConnection` method.\
You will need to provide 4 elements:

* name : REQUIRED : The name of the target connection
* connectionSpecId : REQUIRED : The connectionSpecId to use.
* datasetId : REQUIRED : The dataset ID that is the target
* version : REQUIRED : version to be used (1.0 by default)
* format : REQUIRED : Data format to be used (parquet_xdm by default)
* description : OPTIONAL : description of your target connection

You can also pass the complete object in the data keyword.\
It is especially beneficial as you may need to pass additional information than the one I am providing in my easy setup (schema reference per example)\
If you cannot find a field predefined, you better pass the whole definition.\
Below, example with the Data Lake destination

```JSON
targetObj = {
  "name": "Test",
  "description": "",
  "data": {
    "format": "delimited",
    "schema": {
      "id": "https://ns.adobe.com/tenant/schemas/47ac873bdb0da54efa",
      "version": "application/vnd.adobe.xed-full+json;version=1.0"
    }
  },
  "params": {
    "dataSetId": "datasetId"
  },
  "connectionSpec": {
    "id": "feae26d8-4968-4074-b2ca-d182fc050729",
    "version": "1.0"
  }
}
```

**DataLake Target Connection**
Creating a destination for the datalake is a very common use-case.\
For this reason I created an easy creation setup for that with the method: `createTargetConnectionDataLake`.\
This method takes 4 arguments:

* name : REQUIRED : The name of your target Destination
* datasetId : REQUIRED : the dataset ID of your target destination.
* schemaId : REQUIRED : The schema ID of your dataSet. (NOT meta:altId)
* format : REQUIRED : format of your data inserted
* version : REQUIRED : version of your target destination
* description : OPTIONAL : description of your target destination.

### Creating a mapping

You may want to create a mapping for your incoming data and change the different values ingested.\
This is possible to setup via the mapping service.\
However, this is part of another API and I will recommend you to read the [mapper documentation for that](./mapping.md).

### Creating a Flow

Once you have finalized your Source, Target and Mapper service, you can combine all of them into a Flow that will serve as a pipeline for your data into or out of AEP.\
In order to create a flow, you need to first retrieve the different flowSpec ID and select the one associated with your flow.\
You can realize that with the `getFlowSpecs` method of the module.\
At the moment of that writing, it will provide you with these different options:

```python
flowSpecs = flw.getFlowSpecs()
[spec['name'] for spec in flowSpecs]
## output
['AudienceManagerToPlatform',
 'MockCloudStorage',
 'Analytics Classification Flow Spec',
 'OdiToAEP',
 'CloudStorageToAEP',
 'CRMToAEP',
 'FileUpload',
 'BizibleToPlatform',
 'BifrostFlowSpec',
 'dataset_to_ups',
 'dataset_to_uis',
 'Launch Flow Spec',
 'Mapper POC',
 'Live Streaming Flow',
 'Mapper POC Backfill Flow',
 'Backfill Flow',
 'UPStoGoogleDBM',
 'UPStoAppNexus',
 'UPStoProfileBasedDestination',
 'UPStoTradeDesk',
 'UPS to Mapper based Self Service Destination',
 'UPStoExactTargetFile',
 'UPStoSegmentBasedDestination',
 'DataLakeToOdiDestination',
 'UPStoGoogleMock',
 'upsToCampaign',
 'UPStoFacebookAudiences',
 'UPStoEloquaFile',
 'UPStoResponsysFile',
 'UPStoMicrosoftBing',
 'Stream data without transformation',
 'Steam data with transformation',
 'Stream data with optional transformation',
 'MarketoToPlatform']
```

You can see that there is some flowSpec with mapping and without mapping.\
Be mindful on the one you select.

By selecting the correct ID attached to your flow specification, you can then create the following object.\

```python
flowObj = {
    "name": "Test Flow",
    "description": "",
    "flowSpec": {
        "id": "<flowSpecId>",
        "version": "1.0"
    },
    "sourceConnectionIds": [
        "<sourceConnectionIds>"
    ],
    "targetConnectionIds": [
        "<targetConnectionIds>"
    ],
    "transformations": [
    {
      "name": "Mapping",
      "params": {
        "mappingId": "<mappingId>",
        "mappingVersion": "0"
      }
    }
  ],
  ,
  "scheduleParams": {
    "startTime": 1590091157,
    "frequency": "minute",
    "interval": "15",
    "backfill": "true"
  }
}
```

You can then use it on the `createFlow` method or use only the parameters if you prefer.

```python
myFlow = flw.createFlow(flowObj)
```
