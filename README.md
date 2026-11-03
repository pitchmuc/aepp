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
You can find this documentation [here](./docs/getting-started.md)\
Some notebooks are already available in the `notebooks` folder to help you get started with the module and its different functionalities.\
For the CLI, you can find a specific documentation to get started with it [here](./docs/get-started-cli.md)

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
  * [PackageManager](./docs/packageManager.md)
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
* [ajo](./docs/ajo.md)
* [som](./docs/som.md) (see note below)
* [synchronizer](./docs/synchronizer.md)
* [Knowledge Graph](./docs/knowledge-graph.md) (see note below)

Last but not least, the core methods are described here: [main](./docs/main.md)

## CLI

The CLI module allows you to interact with the AEP services directly from your terminal. You can perform various operations such as managing schemas, querying data, and handling sandboxes without writing Python code.\
The CLI encompass the different modules in a single interface, allowing you to manage various aspects of the AEP services efficiently from the command line.\
It abstracts the requirements of the different modules, and provide more advanced use-cases that would otherwise require direct interaction with the individual APIs.\
This allows users to focus on their business logic rather than the intricacies of each individual service.
For more information on how to use the CLI, refer to the [CLI documentation](./docs/cli.md).

Do not hesitate to raise a ticket / request in case you have a very common task or feature that you would like to see implemented in the CLI.

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

### Knowledge Graph module

The knowledge graph module is a module that allows you to build a Knowledge Graph from a specific sandbox.
You can then export it and use it in your own AI setup. It would work as an AI assistant that will use the graph knowledge to answer questions regarding your data model and its relationships.\

To use the Knowledge Graph, I recommend you to read the graph knowledge usage documentation [here](./knowledge-graph-usage.md)

## Releases

Release notes are accessible [here](./docs/releases.md).
