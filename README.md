# Adobe Experience Platform API made for humans

This repository will document the AEP wrapper on python.
It is focusing on helping accessing the different endpoints of Adobe Experience Platform API.
Documentation on the different endpoints can be found here : [AEP API doc](https://www.adobe.io/apis/experienceplatform/home/api-reference.html)
The wrapper is currently named **aepp**, it stands for Adobe Experience Platform Python.

## Installation

You can install the module directly from a pypi command:

```shell
pip install aepp
```

The version of the wrapper can be seen by the following command (once loaded):

```python
import aepp
aepp.__version__

```

**Consider upgrading regulary**

```shell
pip install aepp --upgrade
```

## Getting Started

In order to get started, I have compiled a guide to help you initialize this module and what is required.
You can find this documentation [here](./docs/getting-started.md)

## AEPP docs

At the moment the current wrapper is containing the following sub modules:

* [schema](./docs/schema.md)
  * [SchemaManager](./docs/schemaManager.md)
  * [FieldGroupManager](./docs/fieldGroupManager.md)
  * [DataTypeManager](./docs/dataTypeManager.md)
  * [ClassManager](./docs/classManager.md)
* [queryservice](./docs/queryservice.md) (see note below for Interactive Queries)
* [identity](./docs/identity.md)
* [sandboxes](./docs/sandboxes.md)
* [dataaccess](./docs/dataaccess.md)
* [catalog](./docs/catalog.md)
* [customerprofile](./docs/customerprofile.md)
* [segmentation](./docs/segmentation.md)
* [dataprep](./docs/dataprep.md)
* [flowservice](./docs/flowservice.md)
* [policy](./docs/policy.md)
* [datasets](./docs/datasets.md)
* [ingestion](./docs/ingestion.md)
* [destination Authoring](./docs/destination.md)
* [destination Instance](./docs/destinationinstanceservice.md)
* [observability](./docs/observability.md)
* [accesscontrol](./docs/accesscontrol.md)
* [privacyservice](./docs/privacyservice.md) (see note below)
* [data hygiene](./docs/hygiene.md)
* [edge](./docs/edge.md)
* [som](./docs/som.md) (see note below)
* [synchronizer](./docs/synchronizer.md)(BETA)

Last but not least, the core methods are described here: [main](./docs/main.md)

## Special classes

The wrapper is having a class in all submodule in order to connect to the different service APIs.\
In addition to that, there are other classes that are provided in order to help you working with the API.

### Simple Object Manager

In order to simplify the management of objects via python, especially when dealing with XDM object, we provide an abstraction that aim to simplify the manipulation of complex objects.\
The Simple Object Manager (SOM) is aiming at supporting the creation, manipulation or analysis of XDM messages.\
You can find all information about the methods available of that class (`Som`) in the related documentation.

The Simple Object Manager documentation is located here: [SOM documentation](./docs/som.md)

### InteractiveQuery  and InteractiveQuery2 classes

These classes are implemented in the `queryservice` modulebased on the `pyGreSQL` and `psycopg2` module for python.\
It provides you the capability to realize query directly from your local Jupyter notebook and returns a dataframe.
In order to use these classes, you would need to install these module and a PSQL server.
On top of that, you would need to the psql server accessible in the environment path.

### SchemaManager, FieldGroupManager and DataTypeManager

Since version 0.3.9, these classes are available from their respective modules, previously they were available from the `schema` module and alloy you to handle the different elements of the schema definition.\
You can use them to extract information on your schema definition.

### FlowManager

The FlowManager is part of the `flowservice` module and allows you to group every aspect of a flow in a single class and simplify the search for the relationship between `sourceFlows`, `targetFlow` and the main flow elements.

### PrivacyService module

The privacy service module is part of the AEP python wrapper (`aepp`) but requires a different API connection in console.adobe.io.
Be careful that your developer project has the correct setup to access this API endpoints.

## Releases

Release notes are accessible [here](./docs/releases.md).
