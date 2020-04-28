# Adobe Experience Platform Python Wrapper

This repository is the work in progress AEP wrapper on python.
It is focusing on helping accessing the different endpoint of Adobe Experience Platform API.
Documentation on the different endpoint can be found here : [AEP API doc](https://www.adobe.io/apis/experienceplatform/home/api-reference.html)
The wrapper is currently named **aepp**, it stands for Adobe Experience Platform Python.

# AEPP docs
At the moment the current wrapper is containing these modules:

## adobeio_auth
This module is used for management of the Adobe IO Authentication.
It is not meant to be used by the end user but it has a deep integration with all of the other modules.

## schema
The Schema module is containing 2 classes:

### Schema Class
The Schema class is wrapping the different endpoint available and provide easy use of them around the Requests module.

### Helper
The Helper class is used in order to provide a wrapper around certain schema object that are being returned from the Schema.getSchema() method.
This will help you to find all of the possible schema paths that have been built.

## queryservice
The queryservice Module contains 2 classes:

### QueryService
The QueryService class is the wrapper around the AEP Query Service API. It provides access to the different endpoint through a usage of the Requests module.

### InteractiveQuery
