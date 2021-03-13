# Ingestion module in aepp

This documentation will provide you some explanation on how to use the ingestion module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/ingest-api.yaml).\
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
aepp.importConfigFile('myConfig_file.json')

from aepp import ingestion
```

The ingestion module provides a class that you can use for ingesting data into your datasets (see below).\
The following documentation will provide you with more information on its capabilities.

## The DataIngestion class

The DataIngestion class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instanciated by calling the `DataIngestion()` from the `ingestion` module.\
As you can see, it is one of the only class that is not directly named after its submodule.

Following the previous method described above, you can realize this:

```python
myConnector = ingestion.DataIngestion()
```

2 parameters are possible for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

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

### Batch

TBD