# Edge module in aepp

This documentation will provide you some explanation on how to use the Edge module and the different methods supported by this module.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://experienceleague.adobe.com/en/docs/experience-platform/edge-network-server-api/overview).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu

- [What is the edge module in aepp](#What-is-the-edge-module-in-aepp)
- [Importing the module](importing-edgeserverside)
- [The Edge class](#instantiation)
  - [The Edge class attributes](#the-edge-class-attributes)
  - [The Edge methods](#the-edge-methods)
- [The IdentityMapHelper class](#the-identitymaphelper-class)

## What is the edge module in aepp

The edge module is not technically an AEP feature. It is part of the AEP Web SDK and App SDK data collection methods that are used for data ingestion on applications.\
The most famous library use is the AEP Web SDK, that helps tracking user behavior on the web.


## Importing edge

The `edge` module can be done directly via the normal `aepp` main module.

```python
import aepp
from aepp import edge

```

Note that the edge connection can work **with** or **without** authentication.\
It depends if your datastream has been setup to receive authenticated traffic or not.\
Most customers do not set authentication for Edge services.\

In case you need to use authenticated traffic you would need to import a config file to authenticate.\
For the sake of the example, we will use the authenticated calls in the example below.

```python
import aepp
from aepp import edge

prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')

```


## The Edge class

The `edge` module contains an `Edge` class that can be instantiated with or without a configuration. Contrary to most of the other module classes.\
However, there are other attributes that you need to specify or can specifiy to use the Edge capability.

The parameters available for instantiation of the class:
* dataStreamId : REQUIRED : The datastream ID that to be used for collecting data
* server : OPTIONAL : If you use a CNAME to send data, you can pass that CNAME server here. Default is `server.adobedc.net`
* config : OPTIONAL : If you need / want to authenticate the call to the Edge network
* version : OPTIONAL : By default the version `2` is used for Edge Server Side data collection. However, you can set the version to `1` to use client side data collection.

A default implementation would be: 

```py
import aepp
from aepp import edge

prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')

myEdge = edge.Edge('mydatastreamId',config=prod)

```

### The Edge class attributes

Once you have instantiated the class, you can access several attributes:

* versionEdge : which version of edge you are using
* server : which server is being used
* endpoint : which endpoint is used to send the requests
* params : The parameters that are used on each request. It contains mostly the `dataStreamId`
* origin : Use to identify the origin of the call for the Edge requests.   
* token : Available only if you are authenticated. Token used for the requests.


### The Edge methods

You can find the different methods available in the `Edge` instance.

#### interact
Send an interact calls. It usually return a response that can be used on the application.\
Arguments:
* payload : OPTIONAL : In case you want to pass the whole payload yourself
* xdm : OPTIONAL : In case you want to pass only XDM data
* data : OPTIONAL : In case you want to pass the data object (can be passed with xdm)
* scopes : OPTIONAL : In case you want to pass Target scopes/mbox in the request or the Offer Decisioning scope. It should be a list of strings. `["scopeId","__view__"]`
* surfaces : OPTIONAL : In case you want to pass AJO surfaces in the request. List of strings.
* params: OPTIONAL : If you want to pass additional query parameter. It takes a dictionary.
* assuranceToken : OPTIONAL : If you want to pass an assurance token value for debugging via a session\
  Usually one value, additional ones are separated by a pip such as: "dc9d59df-9b15-44d3-82d6-2f718ad5ec4a|7ddf4cc5-e304-4d95-991c-01359fe9a7de"


#### collect
In case you want to send multiple requests in one go. These are not returning response that can be used by the application.\
They are just sending data to AEP.\
You can send requests from different users.\
Arguments:
* payloads : OPTIONAL : A list of payload to be send via Edge.
* xdms : OPTIONAL : A list of xdm to be sent via Edge
* data : OPTIONAL : A list of data to attach to the xdms calls (note that the list of xdms and data should be in the same order)
* assuranceToken : OPTIONAL : If you want to pass an assurance token value for debugging via a session.\
  Usually one value, additional ones are separated by a pip such as: "dc9d59df-9b15-44d3-82d6-2f718ad5ec4a|7ddf4cc5-e304-4d95-991c-01359fe9a7de"


## IdentityMapHelper

One element that is always hard to conceptualize in the XDM body is the IdentityMap.\
In order to help the creation of such `identityMap` object, a class is offered to help : `IdentityMapHelper`

### Instantiation

The instantiation of the `IdentityMapHelper` can be realized with or without any parameter.\
Possible arguments:
* namespace : OPTIONAL : User namespace
* identity : OPTIONAL : User Value for that namespace
* primary : OPTIONAL : Default True.
* state : OPTIONAL : Default ambiguous. possible options: 'authenticated'

```python
import aepp
from aepp import edge

myIdMap = edge.IdentityMapHelper()

## or

myIdMap = edge.IdentityMap('CRMID','myCRMID1',True,'authenticated')

```

### IdentityMapHelper methods

Here are the different methods available for `IdentityMapHelper` class.

#### addIdentity
Add an identity to the identityMap.\
Arguments:
* namespace : REQUIRED : User namespace
* identity : REQUIRED : User Value for that namespace
* primary : OPTIONAL : Default False.
* state : OPTIONAL : Default "ambigous", possible state: "authenticated"


#### removePrimaryFlag
remove the primary flag from the identity map.\
Arguments:
* namespace : OPTIONAL : The namespace to remove the identity primary flag
* identity : OPTIONAL : The identity to remove the identity flag.

If nothing is provided, it will loop through all identities and remove the primary flag

#### setPrimaryFlag
Set an identity as primary identity.\
Arguments:
* namespace : OPTIONAL : If you want to specify the namespace to set the primary identity.\
  If no identity are provided and multiple identities are available, the first one is picked up to be primary.
* identity : OPTIONAL : the identity to be used as primary.

#### to_dict
Returns the identityMap as a dictionary (python compatible)

#### to_json
Returns the identityMap as a JSON string (JS compatible)