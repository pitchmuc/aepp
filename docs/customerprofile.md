# Customer Profile in AEP

This documentation will provide you some explanation on how to use the Customer Profile module and different methods supported by this module.\
*Note*: The real name within AEP is Real Time Customer Profile.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/profile/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu

- [Customer Profile in AEP](#customer-profile-in-aepp)
- [What is the customer profile API](#what-is-the-customer-profile-api)
- [Prerequisite before using customerprofile module](#preequisites-before-using-the-customer-profile-module)
- [Importing the module](#importing-the-module)
- [The Profile class](#the-profile-class)
    - [The Profile class attributes](#the-profile-attributes)
    - [The Profile methods]()
- [Use Cases](#customer-profile-use-cases)

## What is the Customer Profile API

The Customer Profile API is providing your to request data directly from the profile store.\
This API is the one recommended when you to fetch the projected 360° view of your customer, once all of your data has been aggregated.\
It also contains capability to manipulate the following elements:
* Computed Attributes: They are profile attributes that are created based on some event data logic
* Destinations: They are the RTCDP destinations that are sending profile attributes
* Projections: They are Edge Projection setup. They are used for Target, Offer Decisioning or AJO. It allows to get fast delivery of experiences.

### Preequisites before using the customer profile module

Before using the Real Time Customer Profile API, you should have an understanding of the Merge Policies and the process of the unified profile within Adobe Experience Platform.\
The Customer Profile API is giving you the capability to access the unified profile of a user and other capabilities but the underlying condition is the understanding of the the Unified Profile logic.

The different merging rule option available through the API should be carefully considered before enabling them or modifying the existing ones.\
For more information about the Customer Profile and Merging rules, please read this documentation:\

* [Link to Customer Profile Overview](https://experienceleague.adobe.com/docs/experience-platform/profile/profile-overview.html?lang=en)
* [Link to Merge Rule article](https://experienceleague.adobe.com/docs/experience-platform/profile/ui/merge-policies.html?lang=en#merge-methods)


## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `customerprofile` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',sandbox='prod',connectInstace=True)
from aepp import customerprofile
```

The customerprofile module provides a class that you can use for accessing your (unified) user profile.\
The following documentation will provide you with more information on its capabilities.

## The Profile class

The customerprofile sub module contains a `Profile` class.\
There are 3 possible parameters when intantiating the class:

* config : OPTIONAL : mostly used to pass a ConnectObject instance that is linked to one sandbox. 
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : A logging object that can be passed for debuging or logging elements, see [logging documentation](./logging.md)

Example

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',sandbox='prod',connectInstace=True)
from aepp import customerprofile

myProfiles = customerprofile.Profile(prod)

```

### The Profile attributes

Once you have instantiated the `Profile` class, you can have access to several attributes.
* sandbox : provide which sandbox is currently being used
* header : provide the default header which is used for the requests.
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods.

### The Profile methods

Once you have instantiated the `Profile` class, you can have access to the following methods.

#### getEntity
Returns an entity by ID or Namespace.\
Arguments:
* schema_name : REQUIRED : class name of the schema to be retrieved. default : `_xdm.context.profile`
* entityId : OPTIONAL : identity ID
* entityIdNS : OPTIONAL : Identity Namespace code. Required if entityId is used (except for native identity)
* mergePoliciyId : OPTIONAL : Id of the merge policy.
* n_events : OPTIONAL : Maximum number of event returned\
Possible kwargs:
* fields : path of the elements to be retrieved, separated by comma. Ex : "person.name.firstName,person.name.lastName"
* relatedSchema_name : If schema.name is `_xdm.context.experienceevent`, this value must specify the schema for the profile entity that the time series events are related to.
* relatedEntityId : ID of the entity that the ExperienceEvents are associated with. Used when looking up ExperienceEvents. For Native XID lookup, use relatedEntityId=<XID> and leave relatedEntityIdNS absent;
For ID:NS lookup, use both relatedEntityId and relatedEntityIdNS fields.
* relatedEntityIdNS : Identity Namespace code of the related entity ID of ExperienceEvent. Used when looking up ExperienceEvents. If this field is used, entityId cannot be empty.
* startTime : Start time of Time range filter for ExperienceEvents. Should be at millisecond granularity. Included. Default: From beginning.
* endTime : End time of Time range filter for ExperienceEvents. Should be at millisecond granularity. Excluded. Default: To the end.
* limit : Number of records to return from the result. Only for time-series objects. Default: 1000

Example: 

```python

myProfile = customerprofile.Profile(prod)

## Get Profile attributes information
myentity = myProfile.getEntity(entityId="80283329115095239723254388905762951649",entityIdNS='ECID')
## Get Profile events information
myentity = myProfile.getEntity(entityId="80283329115095239723254388905762951649",entityIdNS='ECID',schema_name='_xdm.context.experienceevent')

```

#### getEntities
Get a number of different identities from ID or namespaces.\
Argument:
* request_data : Required : A dictionary that contains fields for the search.

Example
```python
{
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
        },
        ,
    {
        "entityId":"89149270342662559642753730269986316900",
        "entityIdNS":{
            "code":"ECID"
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
```

#### deleteEntity
Delete a specific entity\
Arguments:
* schema_name : REQUIRED : Name of the associated XDM schema.
* entityId : REQUIRED : entity ID
* entityIdNS : OPTIONAL : entity ID Namespace
* mergePolicyId : OPTIONAL : The merge Policy ID

#### createExportJob
Create an export of the profile information of the user.\
You can pass directly the payload or you can pass different arguments to create that export job.\
Documentation: <https://experienceleague.adobe.com/docs/experience-platform/profile/api/export-jobs.html?lang=en>\
Arguments: 
* exportDefinition : OPTIONAL : The complete definition of the export
  If not provided, use the following parameters:
* fields : OPTIONAL : Limits the data fields to be included in the export to only those provided in this parameter. 
        Omitting this value will result in all fields being included in the exported data.
* mergePolicyId : OPTIONAL : MergePolicyId to use for data combination.
* additionalFields : OPTIONAL : Controls the time-series event fields exported for child or associated objects by * providing one or more of the following settings:
* datasetId : OPTIONAL : the datasetId to be used for the export.
* schemaName : OPTIONAL : Schema associated with the dataset.
* segmentPerBatch : OPTIONAL : A Boolean value that, if not provided, defaults to `False`. A value of `False` exports all segment IDs into a single batch ID. A value of true exports one segment ID into one batch ID.

#### getExportJobs
Returns all export jobs\
Arguments:
* limit : OPTIONAL : Number of jobs to return

#### getExportJob
Returns an export job status\
Arguments:
* exportId : OPTIONAL : The id of the export job you want to access.

#### deleteExportJob
Delete an export job\
Arguments:
* exportId : OPTIONAL : The id of the export job you want to delete.


#### getMergePolicies
Returns the list of merge policies hosted in this instance.\
Arguments:
* limit : OPTIONAL : amount of merge policies returned by pages.

#### getMergePolicy
Return a specific merge policy.\
Arguments:
* policy_id : REQUIRED : id of the the policy id to be returned.

#### createMergePolicy
Create a Merge Policy.\
Arguments:
* policy: REQUIRED : The dictionary defining the policy\

Refer to the documentation : https://experienceleague.adobe.com/docs/experience-platform/profile/api/merge-policies.html

Example of a dictionary:

```python
{
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

#### updateMergePolicy
Update a merge policy by replacing its definition. (PUT method)\
Arguments:
* mergePolicyId : REQUIRED : The merge Policy Id
* policy : REQUIRED : a dictionary giving the definition of the merge policy

Refer to the documentation : https://experienceleague.adobe.com/docs/experience-platform/profile/api/merge-policies.html

Example of a dictionary:

```python
{
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

**NOTE**: `attributeMerge` can be `"dataSetPrecedence"` or `"timestampOrdered"`.\
Please provide a list of dataSetId with the correct"order" when using the first option.

#### patchMergePolicy
Update a merge policy by replacing its definition.\
Arguments:
* mergePolicyId : REQUIRED : The merge Policy Id
* operations : REQUIRED : a list of operations to realize on the merge policy

Refer to the documentation : https://experienceleague.adobe.com/docs/experience-platform/profile/api/merge-policies.html\

Example of operation:
```python
[
{
    "op": "add",
    "path": "/identityGraph.type",
    "value": "pdg"
}
]
```

#### deleteMergePolicy
Delete a merge policy by its ID.\
Arguments:
* mergePolicyId : REQUIRED : The merge Policy to be deleted

#### getPreviewStatus
View the details for the last successful sample job that was run for the IMS Organization.

#### getPreviewDataSet
View a report showing the distribution of profiles by dataset.\
Arguments:
* date : OPTIONAL : Format: YYYY-MM-DD.
  * If multiple reports were run on the date, the most recent report for that date will be returned.
  * If a report does not exist for the specified date, a 404 error will be returned.
  * If no date is specified, the most recent report will be returned.\
   Example: date=2024-12-31
* output : OPTIONAL : if you want to have a dataframe returns. Use "df", default "raw"

#### getPreviewDataSetOverlap
Method to find the overlap of identities with datasets.\
Arguments:
* date : OPTIONAL : Format: YYYY-MM-DD.
  * If multiple reports were run on the date, the most recent report for that date will be returned.
  * If a report does not exist for the specified date, a 404 error will be returned.
  * If no date is specified, the most recent report will be returned.\
  Example: date=2024-12-31
* output : OPTIONAL : if you want to have a dataframe returns. Use "df", default "raw"

#### getPreviewNamespace
View a report showing the distribution of profiles by namespace.\
Arguments:
* date : OPTIONAL : Format: YYYY-MM-DD.
  * If multiple reports were run on the date, the most recent report for that date will be returned.
  * If a report does not exist for the specified date, a 404 error will be returned.
  * If no date is specified, the most recent report will be returned.\
  Example: date=2024-12-31
* output : OPTIONAL : if you want to have a dataframe returns. Use "df", default "raw"

#### createDeleteSystemJob
Delete all the data for a batch or a dataSet based on their ids.\
**Note**: you cannot delete batch from record type dataset. You can overwrite them to correct the issue.\
Only Time Series and record type datasets can be deleted.\
Arguments:
* dataSetId : REQUIRED : dataSetId to be deleted
* batchId : REQUIRED : batchId to be deleted.

More info: <https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Profile_System_Jobs/createDeleteRequest>

#### getDeleteSystemJobs
Retrieve a list of all delete requests (Profile System Jobs) created by your organization.\
Arguments:
* page : OPTIONAL : Return a specific page of results, as per the create time of the request. For example, page=0
* limit : OPTIONAL : Limit response to a specific number of objects. Must be a positive number. For example, limit=10
* n_results : OPTIONAL : Number of total result to retrieve.


#### getDeleteSystemJob
Get a specific delete system job by its ID.\
Arguments:
* jobId : REQUIRED : Job ID to be retrieved.


#### deleteDeleteSystemJob
Delete a specific delete system job by its ID.\
Arguments:
* jobId : REQUIRED : Job ID to be deleted.


#### getComputedAttributes
Retrieve the list of computed attributes set up in your organization.


#### getComputedAttribute
Returns a single computed attribute.\
Arguments:
* attributeId : REQUIRED : The computed attribute ID.


#### deleteComputedAttribute
Delete a specific computed attribute.\
Arguments:
* attributeId : REQUIRED : The computed attribute ID to be deleted.


#### createComputedAttribute
Create a specific computed attribute.\
Arguments:
definition : REQUIRED : The definition of the computed attribute to be created.

#### patchComputedAttribute
Patch an existing computed attribute with the new status\
Arguments:
* attributeId : REQUIRED : The computed attribute ID to be deleted.
* definition : REQUIRED : the new definition of the attribute\
example:
```python
{
"description": "Sample Description",
"expression": {
    "type": "PQL",
    "format": "pql/text",
    "value": "xEvent[(commerce.checkouts.value > 0.0 or commerce.purchases.value > 1.0 or commerce.order.priceTotal >= 10.0) and (timestamp occurs <= 7 days before now)].sum(commerce.order.priceTotal)"
},
"status": "NEW"
}'
```

#### getDestinations
Retrieve a list of edge projection destinations. The latest definitions are returned.

#### createDestination
Create a new edge projection destination. Assume that there is time between creation and propagation of this information to the edge.\
Arguments:
* destinationConfig : REQUIRED : the destination configuration


#### getDestination
Get a specific destination based on its ID.\
Arguments:
* destinationId : REQUIRED : The destination ID to be retrieved


#### deleteDestination
Delete a specific destination based on its ID.\
Arguments:
* destinationId : REQUIRED : The destination ID to be deleted


#### updateDestination
Update a specific destination based on its ID. (PUT request)\
Arguments:
* destinationId : REQUIRED : The destination ID to be updated
* destinationConfig : REQUIRED : the destination config object to replace the old one.


#### getProjections
Retrieve a list of edge projection configurations. The latest definitions are returned.\
Arguments:
* schemaName : OPTIONAL : The name of the schema class associated with the projection configuration you want to access.\
example : `_xdm.context.profile`
* name : OPTIONAL : The name of the projection configuration you want to access.\
  if name is specified, schemaName is also required.


#### getProjection
Retrieve a single projection based on its ID.\
Arguments:
* projectionId : REQUIRED : the projection ID to be retrieved.


#### deleteProjection
Delete a single projection based on its ID.\
Arguments:
* projectionId : REQUIRED : the projection ID to be deleted.


#### createProjection
Create a projection\
Arguments:
* schemaName : REQUIRED : XDM schema names
* projectionConfig : REQUIRED : the object definiing the projection


#### updateProjection
Update a projection based on its ID.(PUT request)\
Arguments:
* projectionId : REQUIRED : The ID of the projection to be updated.
* projectionConfig : REQUIRED : the object definiing the projection


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

