# Flow Service module in aepp

This documentation will provide you some explanation on how to use the Flow Service module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/flow-service/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu

- [What is the Flow Service module in AEP](#What-is-the-flow-service-module-in-aep)
- [Importing the module](importing-the-module)
- [The Flow Service class](#the-flow-service-class)
  - [The Flow Service class attributes](#the-flow-service-attributes)
  - [The Flow Service methods](#flow-service-methods)
- [The FlowManager class](#the-flowmanager-class)

## What is the Flow Service module in AEP

The Flow Service create the different connectors for data ingestion inside Platform.\
It is true that you can ingest data directly into Adobe Experience Platform via the Data Insertion API.\
However, it is recommended and usually preferred to set up a pipeline from different data sources.

The data sources available can be of different sort (Azure Blob, AWS S3, (S)FTP, HTTP streaming, etc...).\
In order to deal with all of that setup, the flow service has been created so it can scale to different type of source connector.\
Once you have setup the flow in the Adobe Experience platform API via a Source, but also a destination, you can run this flow in order for the pipeline to run.

In order to make the best of this API, it is preferred to have connection to one of the possible data source method cited previously.\
We will see later on how the process look like.

## Importing the module & the FlowService class
To use the module, you must first set up the configuration. This can be done in one of two ways:

1. Import the configuration file directly.
2. Use the configure method to manually provide the information required for the API connection.

For detailed instructions, refer to the [Getting Started guide](./getting-started.md).\

The `flowservice` module includes the FlowService class, which is designed to help you manage connections to both your Source and Destination systems (see example below).

This documentation will provide detailed information on the class’s capabilities and how to utilize them effectively.

The FlowService class relies on the default API connector, which is consistent across other submodules within this Python package. To instantiate the class, simply call `FlowService()` from the flowservice module.


```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')

from aepp import flowservice
flw = flowservice.FlowService(prod)
```

3 parameters are possible for the instantiation of the class:

* config : OPTIONAL : mostly used to pass a ConnectObject instance that is linked to one sandbox. 
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : A logging object that can be passed for debuging or logging elements, see [logging documentation](./logging.md)

## The Flow Service attributes

You can access some attributes once you have instantiated the class.\
These following elements would be available:

* sandbox : provide which sandbox is currently being used
* header : provide the default header which is used for the requests.
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods.
* data.flowId : a dictionary of flow name and flow ID.
* data.flowSpecId : a dictionary of flow name and flow spec ID.

### The data attributes 

The `data` attributes is populated once you have used the `getFlows` methods at least once.\
If you are using the `getFlows` method with parameters to filters it (`onlyDestinations` and `onlySources`), it will only get restricted the data into the data attributes. 

## Flow Service Methods

You can find below the different methods available once you have instantiated the class.

#### getResource
Template for requesting data with a GET method.\
Arguments:
* endpoint : REQUIRED : The URL to GET
* params: OPTIONAL : dictionary of the params to fetch
* format : OPTIONAL : Type of response returned. Possible values:
  * json : default
  * txt : text file
  * raw : a response object from the requests module


#### getConnections
Returns the list of connections available.\
Arguments:
* limit : OPTIONAL : number of result returned per request (default 20)
* n_results : OPTIONAL : number of total result returned (default 100, set to "inf" for retrieving everything)
* count : OPTIONAL : if set to True, just returns the number of connections
kwargs will be added as query parameters

#### createConnection
Create a connection based on either the data being passed or the information passed.\
Arguments:
* data : REQUIRED : dictionary containing the different elements required for the creation of the connection.

In case you didn't pass a data parameter, you can pass different information.
* name : REQUIRED : name of the connection.
* auth : REQUIRED : dictionary that contains "specName" and "params"
  * specName : string that names of the the type of authentication to be used with the base connection.
  * params : dict that contains credentials and values necessary to authenticate and create a connection.
* connectionSpec : REQUIRED : dictionary containing the "id" and "verison" key.
  * id : The specific connection specification ID associated with source
  * version : Specifies the version of the connection specification ID. Omitting this value will default to the most recent version\
Possible kwargs:
* responseType : by default json, but you can request 'raw' that return the requests response object.

#### createStreamingConnection
Create a Streaming connection based on the following connectionSpec :\
```py
"connectionSpec": {
  "id": "bc7b00d6-623a-4dfc-9fdb-f1240aeadaeb",
  "version": "1.0",
  }
```
with provider ID : `521eee4d-8cbe-4906-bb48-fb6bd4450033`\
Arguments:
* name : REQUIRED : Name of the Connection.
* sourceId : REQUIRED : The ID of the streaming connection you want to create (random string possible).
* dataType : REQUIRED : The type of data to ingest (default xdm)
* paramName : REQUIRED : The name of the streaming connection you want to create.
* description : OPTIONAL : if you want to add a description\
kwargs possibility:
* specName : if you want to modify the specification Name.(Default : "Streaming Connection")
* responseType : by default json, but you can request 'raw' that return the requests response object.

#### getConnection
Returns a specific connection object.\
Argument:
* connectionId : REQUIRED : The ID of the connection you wish to retrieve.


#### connectionTest
Test a specific connection ID.\
Argument:
* connectionId : REQUIRED : The ID of the connection you wish to test.

#### deleteConnection
Delete a specific connection ID.\
Argument:
* connectionId : REQUIRED : The ID of the connection you wish to delete.

#### getConnectionSpecs
Returns the list of connectionSpecs in that instance.\
If that doesn't work, return the response.

#### getConnectionSpecsMap
Returns the detail for a specific connection.\
Arguments:
* specId : REQUIRED : The specification ID of a connection

#### getConnectionSpecIdFromName
Returns the connection spec ID corresponding to a connection spec name.\
Arguments:
* name : REQUIRED : The specification name of a connection

#### getFlows
Returns the flows set between Source and Target connection.\
Arguments:
* limit : OPTIONAL : number of results returned
* n_results : OPTIONAL : total number of results returned (default 100, set to "inf" for retrieving everything)
* prop : OPTIONAL : comma separated list of top-level object properties to be returned in the response.
    Used to cut down the amount of data returned in the response body.
    For example, prop=id==3416976c-a9ca-4bba-901a-1f08f66978ff,6a8d82bc-1caf-45d1-908d-cadabc9d63a6,3c9b37f8-13a6-43d8-bad3-b863b941fedd.
* filterMappingSetId : OPTIONAL : returns only the flow that possess the mappingSetId passed in a list.
* filterSourceIds : OPTIONAL : returns only the flow that possess the sourceConnectionIds passed in a list.
* filterTargetIds : OPTIONAL : returns only the flow that possess the targetConnectionIds passed in a list.
* onlyDestinations : OPTIONAL : Filter to only destinations flows (max 100)
* onlySources : OPTIONAL : Filter to only source flows (max 100)

#### getFlow
Returns the details of a specific flow.\
Arguments:
* flowId : REQUIRED : the flow ID to be returned

#### deleteFlow
Delete a specific flow by its ID.\
Arguments:
* flowId : REQUIRED : the flow ID to be returned


#### createFlow
Create a flow with the API.\
Arguments:
* obj : REQUIRED : body to create the flow service.
  Details can be seen at <https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Flows/postFlow>
  requires following keys : name, sourceConnectionIds, targetConnectionIds.

#### createFlowDataLakeToDataLandingZone
Create a Data Flow to move data from Data Lake to the Data Landing Zone.\
Arguments:
* name : REQUIRED : The name of the Data Flow.
* source_connection_id : REQUIRED : The ID of the source connection tied to Data Lake.
* target_connection_id : REQUIRED : The ID of the target connection tied to Data Landing Zone.
* schedule_start_time : REQUIRED : The time from which the Data Flow should start running.
* schedule_frequency : OPTIONAL : The granularity of the Data Flow. Currently only "hour" supported.
* schedule_interval : OPTIONAL : The interval on which the Data Flow runs. Either 3, 6, 9, 12 or 24. Default to 3.
* transformation_mapping_id : OPTIONAL : If a transformation is required, its mapping ID.
* transformation_name : OPTIONAL : If a transformation is required, its name.
* transformation_version : OPTIONAL : If a transformation is required, its version.
* version : OPTIONAL : The version of the Data Flow.
* flow_spec_name : OPTIONAL : The name of the Data Flow specification. Same for all customers.

#### createFlowDataLandingZoneToDataLake
Create a Data Flow to move data from Data Lake to the Data Landing Zone.\
Arguments:
* name : REQUIRED : The name of the Data Flow.
* source_connection_id : REQUIRED : The ID of the source connection tied to Data Lake.
* target_connection_id : REQUIRED : The ID of the target connection tied to Data Landing Zone.
* schedule_start_time : REQUIRED : The time from which the Data Flow should start running.
* schedule_frequency : OPTIONAL : The granularity of the Data Flow. Can be "hour" or "minute". Default to "minute".
* schedule_interval : OPTIONAL : The interval on which the Data Flow runs. Default to 15
* transformation_mapping_id : OPTIONAL : If a transformation is required, its mapping ID.
* transformation_name : OPTIONAL : If a transformation is required, its name.
* transformation_version : OPTIONAL : If a transformation is required, its version.
* version : OPTIONAL : The version of the Data Flow.
* flow_spec_name : OPTIONAL : The name of the Data Flow specification. Same for all customers.

#### updateFlow
update the flow based on the operation provided.\
Arguments:
* flowId : REQUIRED : the ID of the flow to Patch.
* etag : REQUIRED : ETAG value for patching the Flow.
* updateObj : REQUIRED : List of operation to realize on the flow.

Follow the following structure:
```JSON
[
    {
        "op": "Add",
        "path": "/auth/params",
        "value": {
        "description": "A new description to provide further context on a specified connection or flow."
        }
    }
]
```

#### getFlowSpecs
Returns the flow specifications.\
Arguments:
* prop : OPTIONAL : A comma separated list of top-level object properties to be returned in the response.
* Used to cut down the amount of data returned in the response body.\
For example, prop=id==3416976c-a9ca-4bba-901a-1f08f66978ff,6a8d82bc-1caf-45d1-908d-cadabc9d63a6,3c9b37f8-13a6-43d8-bad3-b863b941fedd.

#### getFlowSpecIdFromNames
Return the Flow specification ID corresponding to some conditions.\
Arguments:
* flow_spec_name : REQUIRED : The flow specification name to look for
* source_spec_name : OPTIONAL : Additional filter to only return a flow with a source specification ID.
* target_spec_name : OPTIONAL : Additional filter to only return a flow with a target specification ID.

#### getFlowSpec
Return the detail of a specific flow ID Spec\
Arguments:
* flowSpecId : REQUIRED : The flow ID spec to be checked

#### getUPSFlows
Returns the flows that are uploading data from datasets to UPS.\
Retuns a list of flows.\
Arguments:
* resolveSourceDataset : OPTIONAL : Use the catalog API to resolve the name of the dataset used in that Flow.\
    Adding attributes in the flow "datasetName" and "datasetId". Adding "unknown" for unresolved datasetName.

#### getUISFlows
Returns the flows that are uploading data from dataset to UIS.\
Returns a list of flows\
Arguments:
* resolveSourceDataset : OPTIONAL : Use the catalog API to resolve the name of the dataset used in that Flow\
  Adding attributes in the flow "datasetName" and "datasetId". Adding "unknown" for unresolved datasetName.

#### getUPSFlow
Return the UPS Flow for a specific dataset ID or name.\
Required at least a datasetId or datasetName.\
Argument: 
* datasetId : OPTIONAL : datasetId to check
* datasetName : OPTIONAL : dataset name to check

#### getUISFlow
Return the UIS Flow for a specific dataset ID or name.\
Required at least a datasetId or datasetName.\
Argument: 
* datasetId : OPTIONAL : datasetId to check
* datasetName : OPTIONAL : dataset name to check

#### getUPSFlowRuns
Returns a list of UPS runs for a specific dataset. You can also refine by state.\
Required at least a datasetId or datasetName.\
Arguments:
* datasetId : OPTIONAL : datasetId to check
* datasetName : OPTIONAL : dataset name to check 
* state : OPTIONAL : the state of the flow runs (possible values : "failed","success")

#### getUISFlowRuns
Returns a list of UIS runs for a specific dataset. You can also refine by state.\
Required at least a datasetId or datasetName.\
Arguments:
* datasetId : OPTIONAL : datasetId to check
* datasetName : OPTIONAL : dataset name to check
* state : OPTIONAL : the state of the flow runs (possible values : "failed","success")


#### getRuns
Returns the list of runs. Runs are instances of a flow execution.\
Arguments:
* limit : OPTIONAL : number of results returned per request
* n_results : OPTIONAL : total number of results returned (default 100, set to "inf" for retrieving everything)
* prop : OPTIONAL : comma separated list of top-level object properties to be returned in the response.
    Used to cut down the amount of data returned in the response body.
    For example, prop=id==3416976c-a9ca-4bba-901a-1f08f66978ff,6a8d82bc-1caf-45d1-908d-cadabc9d63a6,3c9b37f8-13a6-43d8-bad3-b863b941fedd.

#### createRun
Generate a run based on the flowId.\
Arguments:
* flowId : REQUIRED : the flow ID to run
* status : OPTIONAL : Status of the flow

#### getRun
Return a specific runId.\
Arguments:
* runId : REQUIRED : the run ID to return


#### getSourceConnections
Return the list of source connections\
Arguments:
* n_results : OPTIONAL : total number of results returned (default 100, set to "inf" for retrieving everything)\
kwargs will be added as query parameterss

#### getSourceConnection
Return detail of the sourceConnection ID\
Arguments:
* sourceConnectionId : REQUIRED : The source connection ID to be retrieved


#### deleteSourceConnection
Delete a sourceConnection ID\
Arguments:
* sourceConnectionId : REQUIRED : The source connection ID to be deleted


#### createSourceConnection
Create a sourceConnection based on the dictionary passed.\
Arguments:
* obj : REQUIRED : the data to be passed for creation of the Source Connection.\

Details can be seen at <https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Source_connections/postSourceConnection>\
requires following keys : name, data, connectionSpec.


#### createSourceConnectionStreaming
Create a source connection based on streaming connection created.\
Arguments:
* connectionId : REQUIRED : The Streaming connection ID.
* name : REQUIRED : Name of the Connection.
* format : REQUIRED : format of the data sent (default : delimited)
* description : REQUIRED : Description of of the Connection Source.
* spec_name : OPTIONAL : The name of the source specification corresponding to Streaming.


#### createSourceConnectionDataLandingZone
Create a new data landing zone connection.\
Arguments:
* name : REQUIRED : A name for the connection
* format : REQUIRED : The type of data type loaded. Default "delimited". Can be "json" or "parquet" 
* path : REQUIRED : The path to the data you want to ingest. Can be a single file or folder.
* type : OPTIONAL : Use "file" if path refers to individual file, otherwise "folder".
* recursive : OPTIONAL : Whether to look for files recursively under the path or not.
* spec_name : OPTIONAL : The name of the source specification corresponding to Data Landing Zone.

#### createSourceConnectionDataLake
Create a new data lake connection.\
Arguments:
* name : REQUIRED : A name for the connection
* format : REQUIRED : The type of data type loaded. Default "delimited". Can be "json" or "parquet"
* dataset_ids : REQUIRED : A list of dataset IDs acting as a source of data.
* spec_name : OPTIONAL : The name of the source specification corresponding to Data Lake.


#### updateSourceConnection
Update a source connection based on the ID provided with the object provided.\
Arguments:
* sourceConnectionId : REQUIRED : The source connection ID to be updated
* etag: REQUIRED : A header containing the etag value of the connection or flow to be updated.
* updateObj : REQUIRED : The operation call used to define the action needed to update the connection. Operations include add, replace, and remove.

#### getTargetConnections
Return the target connections\
Arguments:
* n_results : OPTIONAL : total number of results returned (default 100, set to "inf" for retrieving everything)\
kwargs will be added as query parameters


#### getTargetConnection
Retrieve a specific Target connection detail.\
Arguments:
* targetConnectionId : REQUIRED : The target connection ID is a unique identifier used to create a flow.

#### deleteTargetConnection
Delete a specific Target connection detail\
Arguments:
* targetConnectionId : REQUIRED : The target connection ID to be deleted


#### createTargetConnection
Create a new target connection\
Arguments:
* name : REQUIRED : The name of the target connection
* connectionSpecId : REQUIRED : The connectionSpecId to use.
* datasetId : REQUIRED : The dataset ID that is the target
* version : REQUIRED : version to be used (1.0 by default)
* format : REQUIRED : Data format to be used (parquet_xdm by default)
* description : OPTIONAL : description of your target connection
* data : OPTIONAL : If you pass the complete dictionary for creation\
Details can be seen at <https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Target_connections/postTargetConnection>\
requires following keys : name, data, params, connectionSpec.

#### createTargetConnectionDataLandingZone
Create a target connection to the Data Landing Zone\
Arguments:
* name : REQUIRED : The name of the target connection
* format : REQUIRED : Data format to be used
* path : REQUIRED : The path to the data you want to ingest. Can be a single file or folder.
* type : OPTIONAL : Use "file" if path refers to individual file, otherwise "folder".
* version : REQUIRED : version of your target destination
* description : OPTIONAL : description of your target destination.
* spec_name : OPTIONAL : The name of the target specification corresponding to Data Lake.


#### createTargetConnectionDataLake
Create a target connection to the AEP Data Lake.\
Arguments:
* name : REQUIRED : The name of your target Destination
* datasetId : REQUIRED : the dataset ID of your target destination.
* schemaId : REQUIRED : The schema ID of your dataSet. (NOT meta:altId)
* format : REQUIRED : format of your data inserted
* version : REQUIRED : version of your target destination
* description : OPTIONAL : description of your target destination.
* spec_name : OPTIONAL : The name of the target specification corresponding to Data Lake.


#### updateTargetConnection
Update a target connection based on the ID provided with the object provided.\
Arguments:
* targetConnectionId : REQUIRED : The target connection ID to be updated
* etag: REQUIRED : A header containing the etag value of the connection or flow to be updated.
* updateObj : REQUIRED : The operation call used to define the action needed to update the connection. Operations include add, replace, and remove.

#### updatePolicy
By passing the policy IDs as a list, we update the Policies apply to this Flow.\
Arguments:
* flowId : REQUIRED : The Flow ID to be updated
* policies : REQUIRED : The list of policies Id to add to the Flow\
    example of value: "/dulepolicy/marketingActions/06621fe3q-44t3-3zu4t-90c2-y653rt3hk4o499"
* operation : OPTIONAL : By default "replace" the current policies. It can be an "add" operation.


#### getLandingZoneContainer
Returns a dictionary of the available Data Landing Zone container information.\
Arguments:
* dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"


#### getLandingZoneStorageName
Returns the name of the DLZ storage corresponding to this type.\
Arguments:
* dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"


#### getLandingZoneStorageTTL
Returns the TTL in days of the DLZ storage corresponding to this type.\
Arguments:
* dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"


#### getLandingZoneCredential
Returns a dictionary with the credential to be used in order to create a new zone\
Arguments:
* dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"

#### getLandingZoneSASUri
Returns the SAS URI of the DLZ container corresponding to this type.\
Arguments:
* dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"


#### getLandingZoneSASToken
Returns the SAS token of the DLZ container corresponding to this type.\
Arguments:
* dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"


#### getLandingZoneNamespace
Returns either:
* 'storage account name' of the DLZ storage if provisioned on Azure\
or
* 's3 bucket name' of the DLZ storage if provisioned on Amazon\
Arguments:
* dlz_type : OPTIONAL : The type of DLZ container - default to "user_drop_zone" but can be "dlz_destination"

#### exploreLandingZone
Return the structure of your landing zones\
Arguments:
* objectType : OPTIONAL : The type of the object you want to access.(root (default), folder, file)
* fileType : OPTIONAL : The type of the file to see. (delimited, json, parquet )
* object : OPTIONAL : To be used to defined the path when you are using the "folder" or "file" attribute on objectType

#### getLandingZoneContent
Return the structure of your landing zones\
Arguments:
* fileType : OPTIONAL : The type of the file to see.\
  Possible option : "delimited", "json" or "parquet"
* file : OPTIONAL : the path to the specific file.
* determineProperties : OPTIONAL : replace other parameter to auto-detect file properties.
* preview : OPTIONAL : If you wish to see a preview of the file.

#### postFlowAction
Define a flow action to realize.\
Arguments:
* flowId : REQUIRED : The flow ID to pass the action
* action : REQUIRED : The type of action to pass

#### createFlowStreaming
Create a streaming flow with or without transformation\
Arguments:
* name : REQUIRED : The name of the Data Flow.
* description : OPTIONAL : description of the Flow
* source_connection_id : REQUIRED : The ID of the source connection tied to Data Lake.
* target_connection_id : REQUIRED : The ID of the target connection tied to Data Landing Zone.
* transformation : OPTIONAL : if it is using transformation step. If Optional, set to True.
* transformation_mapping_id : OPTIONAL : If a transformation is required, its mapping ID.
* transformation_name : OPTIONAL : If a transformation is required, its name.
* transformation_version : OPTIONAL : If a transformation is required, its version.

#### createTargetConnectionDatasetToDataLandingZone
Create a target connection to the Data Landing Zone\
Arguments:
* name : REQUIRED : The name of the target connection
* baseConnectionId : REQUIRED : The base connection ID you have used which define the dataset to export.
* path : REQUIRED : The path to the data you want to ingest. Can be a single file or folder.
* datasetFileType : OPTIONAL : Default JSON compressed data, other possible value "PARQUET".
* compression : OPTIONAL : If you wish to compress the file (default: GZIP, other value : NONE). JSON file cannot be sent uncompressed.
* version : REQUIRED : version of your target destination
* description : OPTIONAL : description of your target destination.

#### getExportableDatasets
Retrieve the exportable dataset\
Arguments:
* connectionSpec : REQUIRED : The connection Spec used for the flo

#### getExportableDatasetsDLZ
Return the exportable dataset to Data Landing Zone

#### createBaseConnectionS3Target
Create a base connection for S3 storage as Target.\
Arguments:
* name : REQUIRED : Name of the connectionBase
* s3AccessKey : REQUIRED : The S3 Access Key to access the storage
* s3SecretKey : REQUIRED : The S3 Secret Key to access the storage

#### createBaseConnectionBlobTarget
Create a base connection for Blob Storage as Target.\
Use the connection string auth passed by Azure Blob Storage.\
Arguments:
* name : REQUIRED : Name of your base connection
* connectionString : REQUIRED : Connection string used to authenticate to Blob Storage

#### createBaseConnectionDLZTarget
Create a Connection for Data Landing Zone as Target\
Arguments:
* name : REQUIRED : The name of your Data Landing Zone


#### exportDatasetToDLZ
Create a Flow to export a specific dataset to your data landing zone.\
Taking care of creating a base, source, target and the related specification in DLZ.\
Arguments:
* datasetIds : REQUIRED : The list of datasetId that needs to be exported.
* path : REQUIRED : The path that will be used in DLZ to export the data (default:aepp)
* fileType : REQUIRED : can be JSON (default),PARQUET or DELIMITED (CSV)
* compression : REQUIRED : JSON are automatically compressed. Only PARQUET can not be compressed.
* exportMode: REQUIRED : Can be "FIRST_FULL_THEN_INCREMENTAL" (default) or "DAILY_FULL_EXPORT"
* scheduleStart : REQUIRED : The UNIX seconds when to start the flow runs
* scheduleEnd : OPTIONAL : The UNIX seconds when to end the flow runs
* scheduleUnit : OPTIONAL : The unit used to define intervals to send new files, by default "day", "hour" supported
* scheduleInterval : OPTIONAL : Interval between 2 export.
* baseConnection : OPTIONAL : Base Connection name, by default "base-dataset-export-dlz" + date
* sourceConnection : OPTIONAL : Source Connection name, by default "source-dataset-export-dlz" + date
* targetConnection : OPTIONAL : Target Connection name, by default "target-dataset-export-dlz" + date
* flowname : OPTIONAL : Name of your flow, by default "flow-dataset-export-dlz" + date


## The FlowManager class

On top of the `FlowService` class, another class is provided in this module. The `FlowManager` class.\
The FlowManager class provide a way to group information on a specific flow.\
A flow is always a grouping of a `targetConnection` and `sourceConnection` with some specification.\
It takes several parameters as arguments:

* flowId : REQUIRED : the flow ID to use for gathering all relationships.

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
## From there, you can find the different ID required.
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

You will then need to create a connection for your application.\
You will need to use the `createConnection` with the object created before.

Example:
```python
flw.createConnection(newConnection)

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
