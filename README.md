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

**NOTE TO PYTHON 3.10.X**

At the moment, not all packages are supported on python 3.10.X, therefore, please use this module with a python 3.9.X version.\
You can use pyenv to generate a local environment if required.

## Getting Started

In order to get started, I have compile a guide to help you initialize this module and what is required.
You can find this documentation [here](./docs/getting-started.md)

## AEPP docs

At the moment the current wrapper is containing the following sub modules:

* [schema](./docs/schema.md)
* [queryservice](./docs/queryservice.md) (see note below)
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
* accesscontrol
* sensei
* [privacyservice](./docs/privacyservice.md) (see 2nd note below)

Last but not least, the core methods are described here: [main](./docs/main.md)

## queryservice module

The queryservice Module contains 2 classes:

### QueryService class

The QueryService class is the wrapper around the AEP Query Service API.\
It provides access to the different endpoints available from the API.

Use-Case example : At the moment the capability to scheduled query is only accessible from the API.

[Detail documentation](./docs/queryservice.md)

#### InteractiveQuery  and InteractiveQuery2 classes

These classes are based on the pyGreSQL and psycopg2 module for python.\
It provides you the capability to realize query directly from your local Jupyter notebook and returns a dataframe.
In order to use these classes, you would need to install these module and a PSQL server.
On top of that, you would need to the psql server accessible in the environment path.

## PrivacyService module

The privacy service module is part of the AEP python wrapper but requires a different JWT connection in console.adobe.io.
Be careful that your JWT connection has the correct setup to access this API endpoints.

## Releases

Release notes are accessible [here](./docs/releases.md).
