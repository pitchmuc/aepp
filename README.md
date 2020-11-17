# Adobe Experience Platform Python Wrapper

This repository is the work in progress AEP wrapper on python.
It is focusing on helping accessing the different endpoint of Adobe Experience Platform API.
Documentation on the different endpoint can be found here : [AEP API doc](https://www.adobe.io/apis/experienceplatform/home/api-reference.html)
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

## AEPP docs

At the moment the current wrapper is containing the following sub modules:

* schema
* queryservice (see note below)
* dule
* customerprofile
* catalog
* accesscontrol
* flowservice
* identity
* sandboxes
* segmentation
* sensei
* privacyservice**

## queryservice module

The queryservice Module contains 2 classes:

#### QueryService

The QueryService class is the wrapper around the AEP Query Service API.\
It provides access to the different endpoints available from the API.

At the moment the capability to scheduled query is only accessible from the API.

#### InteractiveQuery

This class is based on the pyGreSQL module for python.\
It provides you the capability to realize query directly from your local Jupyter notebook and returns a dataframe.

## privacyservice module

The privacy service module is part of the AEP python wrapper but requires a different JWT connection in console.adobe.io.
Be careful that your JWT connection has the correct setup to access this API endpoints.

## Getting Started

In order to get started, I have compile a guide to help you initialize this module and what is required.
You can find this documentation [here](./docs/getting-started.md)

## Releases

Release note will be added once the version 0.1.0. has been reached.
Release notes will be accessible [here](./docs/releases.md).
