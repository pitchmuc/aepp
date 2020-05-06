# Adobe Experience Platform Python Wrapper

This repository is the work in progress AEP wrapper on python.
It is focusing on helping accessing the different endpoint of Adobe Experience Platform API.
Documentation on the different endpoint can be found here : [AEP API doc](https://www.adobe.io/apis/experienceplatform/home/api-reference.html)
The wrapper is currently named **aepp**, it stands for Adobe Experience Platform Python.

## AEPP docs

At the moment the current wrapper is containing these modules:

### adobeio_auth

This module is used for management of the Adobe IO Authentication.
It is not meant to be used by the end user but it has a deep integration with all of the other modules.

### schema

The Schema module is containing 2 classes:

#### Schema Class

The Schema class is wrapping the different endpoint available and provide easy use of them around the Requests module.

### queryservice

The queryservice Module contains 2 classes:

#### QueryService

The QueryService class is the wrapper around the AEP Query Service API. It provides access to the different endpoint through a usage of the Requests module.

#### InteractiveQuery

This class is based on the pyGreSQL module for python. It requires that you possess this module to realize the query to AEP in an interactive mode.
You can instantiate this class by passing the response returned by the QueryService.connection method.
pypi doc : <https://pypi.org/project/PyGreSQL/>.
tutorial : <http://www.pygresql.org/contents/tutorial.html>.
