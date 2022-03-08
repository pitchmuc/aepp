# Datasets module in aepp

This documentation will provide you some explanation on how to use the Datasets module and different methods supported by this module.\
Contrary to the other documentation, due to the limited methods available, all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/dataset-service/).\
Alternatively, you can use the docstring in the methods to have more information.

## What is the Datasets in AEP ?

The Dataset Service API provides several endpoints to help you manage data usage labels for existing datasets within the Data Lake.\
Data usage labels are part of Adobe Experience Platform Data Governance, which allows you to manage customer data and ensure compliance with regulations, restrictions, and policies applicable to data use.\
Dataset Service is separate from Catalog Service, which manages other dataset metadata.\
If you wish to create datasets and manage datasets elements, you should then refer to the [catalog documentation](./catalog.md)

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `datasets` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import datasets
```

The datasets module provides a class that you can use for managing your labels on your datasets.

## The Datasets class

The Datasets class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instanciated by calling the `Datasets()` from the `datasets` module.

Following the previous method described above, you can realize this:

```python
datasetslabels = datasets.Datasets()
```

2 parameters are possible for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

## Datasets methods

* `getLabels`
  Return the labels assigned to a dataSet
  Argument:
  * dataSetId : REQUIRED : the dataSet ID to retrieve the labels

* `headLabels`
  Return the head assigned to a dataSet. You would required the ETAG parameter to modify or delete the labels.
  Argument:
  * dataSetId : REQUIRED : the dataSet ID to retrieve the head data

* `deleteLabels`
  Delete the labels of a dataset.
  Arguments:
  * dataSetId : REQUIRED : The dataset ID to delete the labels for.
  * ifMatch : REQUIRED : the value is from the header etag of the headLabels. (use the headLabels method)

* `createLabels`
  Assign labels to a dataset.
  Arguments:
  * dataSetId : REQUIRED : The dataset ID to delete the labels for.
  * data : REQUIRED : Dictionary setting the labels to be added.
    more info https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Datasets/postDatasetLabels

* `updateLabels`
  Update the labels (PUT method)
  * dataSetId : REQUIRED : The dataset ID to delete the labels for.
  * data : REQUIRED : Dictionary setting the labels to be added.
        more info https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Datasets/postDatasetLabels
  * ifMatch : REQUIRED : the value is from the header etag of the headLabels.(use the headLabels method)

On top of these methods, you will have access to an attribute of your instance that will provide you a dictionary sample for creation of labels for a dataset.\
The name of the attribute is `REFERENCE_LABELS_CREATION`\
The output will be:

```JSON
{
    "labels": [
        [
        "C1",
        "C2"
        ]
    ],
    "optionalLabels": [
        {
        "option": {
            "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
            "contentType": "application/vnd.adobe.xed-full+json;version=1",
            "schemaPath": "/properties/repositoryCreatedBy"
        },
        "labels": [
            [
            "S1",
            "S2"
            ]
        ]
        }
    ]
}
```