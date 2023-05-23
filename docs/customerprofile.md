# Customer Profile in aepp

This documentation will provide you some explanation on how to use the Customer Profile module and different methods supported by this module.\
*Note*: The real name within AEP is Real Time Customer Profile.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/profile/).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `customerprofile` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import customerprofile
```

The customerprofile module provides a class that you can use for accessing your (unified) user profile.\
The following documentation will provide you with more information on its capabilities.

## The Profile class

The customerprofile class will use the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `Profile()` from the `customerprofile` module.

Following the previous method described above, you can realize this:

```python
myProfiles = customerprofile.Profile()
```

2 parameters are possible for the instantiation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

## Preequisites before using the customer profile module

Before using the Real Time Customer Profile API, you should have an understanding of the Merge Policies and the process of the unified profile within Adobe Experience Platform.\
The Customer Profile API is giving you the capability to access the unified profile of a user and other capabilities but the underlying condition is the understanding of the the Unified Profile logic.

The different merging rule option available through the API should be carefully considered before enabling them or modifying the existing ones.\
For more information about the Customer Profile and Merging rules, please read this documentation:\

* [Link to Customer Profile Overview](https://experienceleague.adobe.com/docs/experience-platform/profile/profile-overview.html?lang=en)
* [Link to Merge Rule article](https://experienceleague.adobe.com/docs/experience-platform/profile/ui/merge-policies.html?lang=en#merge-methods)

## Customer Profile use-cases

### Fetching information for a profile

The most obvious use-case for the the real time customer profile API, it is to retrieve a specific user data.\
This can be achieved by using the `getEntity()` method from the API.

The method takes 4 mandatory arguments:

* schema_name: class name of the schema to be retrieved. (Default: _xdm.context.profile)
* entityId:  identity ID
* entityIdNS: Identity Namespace code. Required if entityId is used.
* mergePoliciyId: Id of the merge policy.

There are also additional keywords that can be used with that method.\
Please refer to the docstring for more information.

However, we will mention the `relatedEntityId` and `relatedSchema.name` that can define identities related to the Experience Events data.\
As explained before, the API call will retrieve the data for unified profile by default but the Experience Events data are not merged and therefore you can request all of them by passing this argument.

At the end, a simple call will look like this:

```python
profile = myProfiles.getEntity(entityId="09237308232164398232158732346",entitiyIdNS='ecid')
```

A more complex call with Experience Event and Profile:

```python
profile = myProfiles.getEntity(schema_name="_xdm.context.experienceevent", relatedEntityId="09237308232164398232158732346",relatedEntityIdNS='ecid',relatedSchema.name="_xdm.context.profile")
```

#### Multiple entities

You can also fetch information for multiple entities with the `getEntities()` method.\
This method takes a whole dictionary / object to define the parameters. 

Example of an call using this method:

```python
myDict = {
        "schema": {
            "name": "_xdm.context.profile"
        },
        "relatedSchema": {
            "name": "_xdm.context.profile"
        },
        "fields": [
            "person.name.firstName"
        ],
        "identities": [
            {
            "entityId": "69935279872410346619186588147492736556",
            "entityIdNS": {
                "code": "CRMID"
            }
            }
        ],
        "timeFilter": {
            "startTime": 1539838505,
            "endTime": 1539838510
        },
        "limit": 10,
        "orderby": "-timestamp",
        "withCA": True
    }
profiles = myProfiles.getEntities(request_data=myDict)
```

#### Delete Entities

You can use this method to delete an entitty:

The method takes 4 arguments:

* schema_name: class name of the schema to be retrieved. (Default: _xdm.context.profile)
* entityId:  identity ID
* entityIdNS: Identity Namespace code. Required if entityId is used.

Example:

```python
profile = myProfiles.deleteEntity(schema_name="_xdm.context.experienceevent", entityId="09237308232164398232158732346",entityIdNS='ecid'")
```

### Get the Merge policies & create Merge policies

One other use-case for the endpoint is to retrieve your different Merge Policies inplace, in order to analyze or modify them.\
This can also help you change the call to the `getEntity` as you can pass a different `mergePolicyId` as a parameter.

```python
myProfiles.getMergePolicies()
```

You can also create merge policies through that endpoint.\
This can be achieved with the `createMergePolicy` method.

This method takes a dictionary such as this one in the example:

```python
myDict = {
            "name": "real-time-customer-profile-default",
            "imsOrgId": "1BD6382559DF0C130A49422D@AdobeOrg",
            "schema": {
                "name": "_xdm.context.profile"
            },
            "default": False,
            "identityGraph": {
                "type": "pdg"
            },
            "attributeMerge": {
                "type": "timestampOrdered",
                "order": [
                "string"
                ]
            },
            "updateEpoch": 1234567890
        }
```

The attributeMerge can takes 2 types:

* "timestampOrdered" : see example above.
* "dataSetPrecedence" : In that case, provide a list of dataSetId on "order".

More information with [official documentation on merge policy](https://experienceleague.adobe.com/docs/experience-platform/profile/api/merge-policies.html?lang=en#access-merge-policies)

### See distribution of profiles

An interesting use-case for this endpoint is to have a look at the distribution of the profile recorded in your AEP instance through different views.\
You can see the number of profiles globally, by dataSet or by NameSpace through these different methods:

* `getPreviewStatus()`
* `getPreviewDataSet()`
* `getPreviewNamespace()`

**Note**: you can retrieve a dataframe by passing "df" in the `output` parameter for `getPreviewDataSet` and `getPreviewNamespace`.

### Delete a Batch or a DataSet

An unexpected application of this endpoint is the capability to delete a batch or a dataset based on their ID.\
Both elements can be deleted with the same method, it is a matter of the parameter used in the method.

`createDeleteSystemJob` method takes 2 parameters:

* dataSetId : dataSetId to be deleted
* batchId : batchId to be deleted

Use one of them to delete its respective element.\
Example:

```python
myProfiles.createDeleteSystemJob(batchId="Sa2143saW")

```

You can see the job done by calling the `getDeleteSystemJobs()` method.

### Destinations

TBD

### Projections

TBD

### Computed Attributes

TBD
