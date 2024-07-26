# Data Prep module in aepp

This documentation will provide you some explanation on how to use the Data Prep module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/data-prep/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu
- [Data Prep module in aepp](#data-prep-module-in-aepp)
  - [Menu](#menu)
  - [What is the Data Prep in AEP](#what-is-the-data-prep-in-aep)
  - [Importing the module](#importing-the-module)
  - [The DataPrep class](#the-dataingestion-class)
  - [DataPrep attributes](#dataingestion-attributes)
  - [DataPrep methods](#dataingestion-methods)
  - [The data prep use-cases](#use-cases)

## What is the Data Prep in AEP ?

The `dataprep` module contains the Mapping Service in AEP and it is a service happening during  the data ingestion in AEP.\
It is linked to the Flow Service capability and you can have more information about that by reading the [corresponding documentation](./flowservice.md).

In order to make the best of this API, it is preferred to have knowledge on how the flow service is being setup.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `dataprep` keyword.

```python
import aepp
dev = aepp.importConfigFile('myConfig_file.json',sandbox='dev',connectInstance=True)

from aepp import dataprep
```

The `dataprep` module provides a class that you can use for managing your connection to your different Mappings and MappingsSet (see below).\
The following documentation will provide you with more information on its capabilities.

## The DataPrep class

The DataPrep class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `DataPrep()` from the `dataprep` module.

Following the previous method described above, you can realize this:

```python
import aepp
from aepp import dataprep

dev = aepp.importConfigFile('myConfig_file.json',sandbox='dev',connectInstance=True)
mapper = dataprep.DataPrep(dev)

```

3 parameters are possible for the instantiation of the class:

* config : OPTIONAL : mostly used to pass a ConnectObject instance that is linked to one sandbox. 
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : A logging object that can be passed for debuging or logging elements, see [logging documentation](./logging.md)


Any additional parameters in the kwargs will be updating the header content.

## DataPrep attributes
* sandbox : provide which sandbox is currently being used
* header : provide the default header which is used for the requests.
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods.
* containerId : In case you have modified the default container.
* REFERENCE_MAPPING : An example of mapping definition
* SOURCETYPE : A list of source types for mapping


## DataPrep methods

On the elements below, all methods are documented.\
You can access these methods once you have instantiated the DataPrep class.

#### getXDMBatchConversions
Returns all XDM conversions\
Arguments:
* dataSetId : OPTIONAL : Destination dataSet ID to filter for.
* property : OPTIONAL : Filters for dataSetId, batchId and Status.
* batchId : OPTIONAL : batchId Filter
* status : OPTIONAL : status of the batch.
* limit : OPTIONAL : number of results to return (default 100)


#### getXDMBatchConversion
Returns XDM Conversion info.\
Arguments:
* conversionId : REQUIRED : Conversion ID to be returned


#### getXDMBatchConversionActivities
Returns activities for a XDM Conversion ID.\
Arguments:
* conversionId : REQUIRED : Conversion ID for activities to be returned


#### getXDMBatchConversionRequestActivities
Returns conversion activities for given request\
Arguments:
* requestId : REQUIRED : the request ID to look for
* activityId : REQUIRED : the activity ID to look for


#### createXDMConversion
Create a XDM conversion request.\
Arguments:
* dataSetId : REQUIRED : destination dataSet ID
* batchId : REQUIRED : Source Batch ID
* mappingSetId : REQUIRED : Mapping ID to be used


#### copyMappingRules
Create a copy of the mapping based on the mapping information passed.\
Argument:
* mapping : REQUIRED : either the list of mapping or the dictionary returned from the getMappingSetMapping
* tenantid : REQUIRED : in case tenant is present, replace the existing one with new one.

#### cleanMappingRules
Create a clean copy of the mapping based on the mapping list information passed.\
Argument:
* mapping : REQUIRED : either the list of mapping or the dictionary returned from the getMappingSetMapping

#### getMappingSets
Returns all mapping sets for given IMS Org Id and sandbox.\
Arguments:
* name : OPTIONAL : Filtering by name
* prop : OPTIONAL : property filter. Supported fields are: xdmSchema, status.
  * Example : prop="status==success"
* limit : OPTIONAL : number of result to retun. Default 100.

#### getMappingSuggestions
Returns non-persisted mapping set suggestion for review\
Arguments:
* dataSetId : OPTIONAL : Id of destination DataSet. Must be a DataSet with schema.
* batchId : OPTIONAL : Id of source Batch.
* excludeUnmapped : OPTIONAL : Exclude unmapped source attributes (default True)

#### getMappingSet
Get a specific mappingSet by its ID.\
Arguments:
* mappingSetId : REQUIRED : mappingSet ID to be retrieved.
* save : OPTIONAL : save your mapping set defintion in a JSON file.
* saveMappingRules : OPTIONAL : save your mapping rules only in a JSON file
* mappingRulesOnly : OPTIONAL : If set to True, return only the mapping rules.\
optional kwargs:
* encoding : possible to set encoding for the file.

#### deleteMappingSet
Delete a specific mappingSet by its ID.\
Argument:
* mappingSetId : REQUIRED : mappingSet ID to be deleted.


#### createMappingSet
Create a mapping set.\
Arguments:
* schemaId : OPTIONAL : schemaId to map to.
* mappingList: OPTIONAL : List of mapping to set.
* validate : OPTIONAL : Validate the mapping.\
if you want to provide a dictionary for mapping set creation, you can pass the following params:
* mappingSet : REQUIRED : A dictionary that creates the mapping info.\
  see info on https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Mappings/createMappingSetUsingPOST

#### updateMappingSet
Update a specific Mapping set based on its Id.\
Arguments:
* mappingSetId : REQUIRED : mapping Id to be updated
* mappingRules : REQUIRED : the list of different rule to map
* outputSchema : OPTIONAL : If you wish to change the destination output schema. By default taking the same one.


#### getMappingSetMappings
Returns all mappings for a mapping set\
Arguments:
* mappingSetId : REQUIRED : the mappingSet ID to retrieved

#### createMappingSetMapping
Create mappings for a mapping set\
Arguments:
* mappingSetId : REQUIRED : the mappingSet ID to attached the mapping
* mapping : REQUIRED : a dictionary to define the new mapping.

#### getMappingSetMapping
Get a mapping from a mapping set.\
Arguments:
* mappingSetId : REQUIRED : The mappingSet ID
* mappingId : REQUIRED : The specific Mapping


#### deleteMappingSetMapping
Delete a mapping in a mappingSet\
Arguments:
* mappingSetId : REQUIRED : The mappingSet ID
* mappingId : REQUIRED : The specific Mapping

#### updateMappingSetMapping
Update a mapping for a mappingSet (PUT method)\
Arguments:
* mappingSetId : REQUIRED : The mappingSet ID
* mappingId : REQUIRED : The specific Mapping
* mapping : REQUIRED : dictionary to update

#### previewDataOutput
The data you want to run through as a preview, which will be transformed by the mapping sets within the body.\
Arguments:
* data : REQUIRED : A dictionary containing the data to test.
* mappingSet : REQUIRED : The mappingSet to test.

Example:
```JSON
{
    "data": {
        "id": 1234,
        "firstName": "Jim",
        "lastName": "Seltzer"
    },
    "mappingSet": {
        "outputSchema": {
        "schemaRef": {
            "id": "https://ns.adobe.com/stardust/schemas/89abc189258b1cb1a816d8f2b2341a6d98000ed8f4008305",
            "contentType": "application/vnd.adobe.xed-full+json;version=1"
        }
        },
        "mappings": [
        {
            "sourceType": "ATTRIBUTE",
            "source": "id",
            "destination": "_id",
            "name": "id",
            "description": "Identifier field"
        },
        {
            "sourceType": "ATTRIBUTE",
            "source": "firstName",
            "destination": "person.name.firstName"
        },
        {
            "sourceType": "ATTRIBUTE",
            "source": "lastName",
            "destination": "person.name.lastName"
        }
        ]
    }
}
```

#### getMappingSetFunctions
Return list of mapping functions.

#### getMappingSetOperators
Return list of mapping operators.

#### validateExpression
Check if the expression that you have passed is valid.\
Arguments:
* expression : REQUIRED : the expression you are trying to validate.
* mappingSetId : OPTIONAL : MappingSetId to integrate this expression.
* sampleData : OPTIONAL : Sample Date to validate
* sampleDataType : OPTIONAL : Data Type of your Sample data.


## Use-cases

The Data Prep Service enables you to use the mapping service. This service is used in order to map the incoming data to match specific field expectation in your schema (type / value).\
It can be used in 2 different ways:

* `text/x.schema-path` when you want to map a specific path to a new path
* `text/x.aep-xl` when you are doing calculation or applying function on a field.

### Mapping is used with Flow Service

To use the `mapper`, you would need to attach it to a connection flow.\
Please reference to the [FlowService documentation for this](./flowservice.md).

### Create a mapping

When creating a mapping you need to pass (a list of) object that will define the transformation happening to your `source` data and the `destination` of that data.\
An empty example of mapping would be:

```JSON
MyMapping = {
    "sourceType": "",
    "source": "",
    "destination": ""
}
```

You can find this element in the `REFERENCE_MAPPING` attribute of the `Mapping` instance.\
The different elements means the following:
* sourceType : as explained above it can be either `text/x.schema-path` or `text/x.aep-xl`.
* source : the path to your value
* destination : the path of your destination (where the data should go after transformation)

You can then use that object in a list and pass it to a dictionary, specifying your outputSchema reference:

```JSON
obj = {
    "outputSchema": {
       "schemaRef": {
            "id": "https://ns.adobe.com/tenant/schemas/e0b7cba00da86d10c0774a337",
            "contentType": "application/vnd.adobe.xed-full+json;version=1"
        }
    },
    "mappings": [MyMapping]
}
```

Note : In this example above, I only had one object so I pass it in a list.\
You can pass that object directly into the `createMappingSet` method as the following:
```python
mapper.createMappingSet(obj,validate=True,verbose=True)
```

What can also be done is to use the optional parameter to only pass the schema `$Id` and the list of mapping.

```python
mapper.createMappingSet(schemaId="https://ns.adobe.com/tenant/schemas/e0b7cba00da86d10c0774a337",mappingList=[MyMapping],validate=True,verbose=True)
```

### Update a Mapping

At some point, when you want to update a Mapping, the way to achieve this is to update the whole MappingSet.\
You can then directly update the MappingSet by using the `updateMappingSet` method.

```python
updateObject = {
  "id": "string",
  "mappings": [
        {
        "sourceType": "text/x.aep-xl" or "text/x.schema-path",
        "source": "",
        "destination": ""
        }
  ],
  "name": "string",
  "schemaRef": {
    "contentType": "string",
    "id": "string"
  },
  "transformScript": "string",
  "version": X
}
mapper.updateMappingSet('MappingId',mappingSet=updateObject)
```

### Detect where the mapping is used

Detecting where your mapping is currently being used can be important if you have several mapping and data flows running.\
However, the module doesn't support this search directly.\
You can achieve this use-case by using the `flowservice` module.
