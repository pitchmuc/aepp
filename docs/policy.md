# Policy module in AEP

This documentation will provide you some explanation on how to use the Policy module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/policy-service/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu

- [Policy module in AEP](#policy-module-in-aep)
- [Importing the module](importing-the-module)
- [The Policy class](#the-policy-class)
  - [The Policy methods](#the-policy-methods)

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `policy` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',sandbox='prod',connectInstance=True)

from aepp import policy
```

The policy module provides a class that you can use for managing your data governance.\
The following documentation will provide you with more information on its capabilities.

## The Policy class

The Policy class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `Policy()` from the `policy` module.

Following the previous method described above, you can realize this:

```python
import aepp 
from aepp import policy

prod = aepp.importConfigFile('myConfig_file.json',sandbox='prod',connectInstance=True)

mypolicy = policy.Policy(config=prod)
```

3 parameters are possible for the instantiation of the class:

* config : OPTIONAL : mostly used to pass a ConnectObject instance that is linked to one sandbox. 
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : A logging object that can be passed for debuging or logging elements, see [logging documentation](./logging.md)

### The Policy Methods

In this part we will review the different methods available once you have instantiated the policy class.

#### getEnabledCorePolicies
Retrieve a list of all enabled core policies.

#### createEnabledCorePolicies
Create or update the list of enabled core policies. (PUT method)\
Argument:
* policyIds : REQUIRED : list of core policy ID to enable

#### bulkEval
Enable to pass a list of policies to check against a list of dataSet.\
Argument:
* data : REQUIRED : List/Array describing the set of label and datasets.\
    see <https://developer.adobe.com/experience-platform-apis/references/policy-service/#operation/bulkEval>

Example:

```py

evaluations = [
  {
    "evalRef": "https://platform.adobe.io:443/data/foundation/dulepolicy/marketingActions/core/emailTargeting/constraints",
    "includeDraft": false,
    "labels": [
      "C1",
      "C2",
      "C3"
    ]
  },
  {
    "evalRef": "https://platform.adobe.io:443/data/foundation/dulepolicy/marketingActions/core/emailTargeting/constraints",
    "includeDraft": false,
    "entityList": [
      {
        "entityType": "dataSet",
        "entityId": "5b67f4dd9f6e710000ea9da4",
        "entityMeta": {
          "fields": [
            "address"
          ]
        }
      }
    ]
  }
]

mypolicy.bulkEval(evaluations)
```

#### getPoliciesCore
Returns the core policies in place in the Organization.\
Possible kwargs:
* limit : A positive integer, providing a hint as to the maximum number of resources to return in one page of results.
* property : Filter responses based on a property and optional existence or relational values.\
    Only the 'name' property is supported for core resources.\
    For custom resources, additional supported property values include 'status', 'created', 'createdClient','createdUser', 'updated', 'updatedClient', and 'updatedUser'
* orderby : A comma-separated list of properties by which the returned list of resources will be sorted.
* start : Requests items whose 'orderby' property value are strictly greater than the supplied 'start' value.
* duleLabels : A comma-separated list of DULE labels. Return only those policies whose "deny" expression references any of the labels in this list
* marketingAction : Restrict returned policies to those that reference the given marketing action.


#### getPoliciesCoreId
Return a specific core policy by its id.\
Arguments:
* policy_id : REQUIRED : policy_id to retrieve.

#### getPoliciesCustoms
Returns the custom policies in place in the Organization.\
Possible kwargs:
* limit : A positive integer, providing a hint as to the maximum number of resources to return in one page of results.
* property : Filter responses based on a property and optional existence or relational values.\
    Only the 'name' property is supported for core resources.\
    For custom resources, additional supported property values include 'status', 'created', 'createdClient', 'createdUser', 'updated', 'updatedClient', and 'updatedUser'
* orderby : A comma-separated list of properties by which the returned list of resources will be sorted.
* start : Requests items whose 'orderby' property value are strictly greater than the supplied 'start' value.
* duleLabels : A comma-separated list of DULE labels. Return only those policies whose "deny" expression references any of the labels in this list
* marketingAction : Restrict returned policies to those that reference the given marketing action.

#### getPoliciesCustom
Return a specific custom policy by its id.
Arguments:
* policy_id: REQUIRED: policy_id to retrieve.


#### createPolicy
Create a custom policy.\
Arguments:
* policy : REQUIRED : A dictionary contaning the policy you would like to implement.


#### getCoreLabels
Retrieve a list of core labels.\
Arguments:
* prop : OPTIONAL : Filters responses based on whether a specific property exists, or whose value passes a conditional expression\
    Example: prop="name==C1".\
    Only the "name" property is supported for core resources.
* limit : OPTIONAL : number of results to be returned. Default 100


#### getCoreLabel
Returns a specific Label by its name.\
Argument:
* labelName : REQUIRED : The name of the core label.


#### getCustomLabels
Retrieve a list of custom labels.\
Arguments:
* prop : OPTIONAL : Filters responses based on whether a specific property exists, or whose value passes a conditional expression\
    Example: prop="name==C1".\
    Property values include "status", "created", "createdClient", "createdUser", "updated", "updatedClient", and "updatedUser".
* limit : OPTIONAL : number of results to be returned. Default 100

#### getCustomLabel
Returns a specific Label by its name.\
Argument:
* labelName : REQUIRED : The name of the custom label.

#### updateCustomLabel
Update a specific Label by its name. (PUT method)\
Argument:
* labelName : REQUIRED : The name of the custom label.
* data : REQUIRED : Data to replace the old definition
    Example:
    ```python
    {
        "name": "L2",
        "category": "Custom",
        "friendlyName": "Purchase History Data",
        "description": "Data containing information on past transactions"
    }
    ```

#### getMarketingActionsCores
Retrieve a list of core marketing actions.\
Arguments:
* prop : OPTIONAL : Filters responses based on whether a specific property exists, or whose value passes a conditional expression (e.g. "prop=name==C1").\
    Only the "name" property is supported for core resources.
* limit : OPTIONAL : number of results to be returned.

#### getMarketingActionsCore
Get a specific marketing action core by marketing Action Name.\
Arguments:
* mktActionName : REQUIRED : The marketing action name to be provided.


#### getCustomMarketingActions
Retrieve a list of custom Marketing Actions\
Arguments:
* prop : OPTIONAL : Filters responses based on whether a specific property exists, or whose value passes a conditional expression (e.g. ?property=name==C1).\ 
    Only the name property is supported for core resources. \
    For custom resources, additional supported property values include "status", "created", "createdClient", "createdUser", "updated", "updatedClient", and "updatedUser"\
Possible kwargs:
* orderby : A comma-separated list of properties by which the returned list of resources will be sorted.
* start : Indicates 

#### getCustomMarketingAction
Return a specific marketing action\
Arguments:
* mktActionName : REQUIRED : The marketing action name to be returned.


#### createOrupdateCustomMarketingAction
Create or update a custom marketing action based on the parameter provided.\
Arguments:
* name : REQUIRED : The name of the custom marketing action
* description : OPTIONAL : the description for that custom marketing action.


#### deleteCustomMarketingAction
Delete a specific custom Marketing action\
Arguments:
* mktActionName : REQUIRED : The marketing action name to be deleted.

#### evaluateMarketingActionDataset
Evaluate either Marketing Action core or custom based on parameter again some field on a datasetId.\
Arguments
* typeMktAction : REQUIRED : Default to "core", can be "custom"
* mktActionName : REQUIRED : The name of the marketing action to be evaluated
* entityType : REQUIRED : The type of entity to be tested against. Usually "dataSet", so set as default.
* entityId : REQUIRED : The Id of the entity to be tested.
* entityMeta : REQUIRED : A list of field to be tested for the marketing action in case of a dataset.
* draftEvaluation : OPTIONAL : If true, the system checks for policy violations among policies with DRAFT status as well as ENABLED status. Otherwise, only ENABLED policies are checked.

#### evaluateMarketingActionUsageLabel
This call returns a set of constraints that would govern an attempt to perform the given marketing action on a hypothetical source of data containing specific data usage labels.\
Arguments:
* typeMktAction : REQUIRED : Default to "core", can be "custom"
* mktActionName : REQUIRED : The name of the marketing action to be evaluated
* duleLabels : REQUIRED: A comma-separated list of data usage labels that would be present on data that you want to test for policy violations.
* draftEvaluation : OPTIONAL : If true, the system checks for policy violations among policies with DRAFT status as well as ENABLED status. Otherwise, only ENABLED policies are checked.


## Policy use-cases

TBD