# Access Control module in aepp

This documentation will provide you an overview on how to use the `accesscontrol` module and different methods supported by this module.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/access-control/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu
- [Access Control module in aepp](#access-control-module-in-aepp)
  - [Menu](#menu)
  - [Importing the module](#importing-the-module)
  - [The AccessControl class](#the-accesscontrol-class)
  - [AccessControl methods](#accesscontrol-methods)
    - [getPermissions](#getpermissions)
    - [getEffectivePolicies](#geteffectivepolicies)
    - [getRoles](#getroles)
    - [getRole](#getrole)
    - [deleteRole](#deleterole)
    - [patchRole](#patchrole)
    - [putRole](#putrole)
    - [getSubjects](#getsubjects)
    - [patchSubjects](#patchsubjects)
    - [getPolicies](#getpolicies)
    - [getPolicy](#getpolicy)
    - [deletePolicy](#deletepolicy)
    - [createPolicy](#createpolicy)
    - [putPolicy](#putpolicy)
    - [patchPolicy](#patchpolicy)
    - [getProducts](#getproducts)
    - [getPermissionCategories](#getpermissioncategories)
    - [getPermissionSets](#getpermissionsets)

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `destination` keyword.

```python
import aepp
sandbox = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='my-sandbox')

from aepp import accesscontrol
```

The accesscontrol module provides a class that you can use to list out permissions, list out resource types, and list all the effective policies for a user on given resources within a sandbox.\
The following documentation will provide you with more information on its capabilities.

## The AccessControl class

You can instantiate an `AccessControl` class by using these parameters.
Arguments:
* config : OPTIONAL : it could be the instance of the ConnectObject class (preferred) or a dictionary containing the config information. Default will take the latest configuration loaded.
* header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
* loggingObject : OPTIONAL : logging object to log messages.\
kwargs :
* header options that you want to append to the header. Such as {"Accept":"accepted-value"}


## AccessControl methods

### getPermissions
List all available permission names and resource types.


### getEffectivePolicies
List all effective policies for a user on given resources within a sandbox.\
Arguments:
* listElements : REQUIRED : List of resource urls. Example url : /resource-types/{resourceName} or /permissions/{highLevelPermissionName}\
    example: "/permissions/manage-dataset" "/resource-types/schema" "/permissions/manage-schemas"


### getRoles
Return all existing roles in the Company.


### getRole
Retrieve a specific role based on the ID.\
Arguments:
* roleId : REQUIRED : Role ID to be retrieved


### deleteRole
Delete a role based on its ID.\
Argument:
* roleId : REQUIRED : The role ID to be deleted


### patchRole
PATCH the role with the attribute passed.\
Attribute can have the following action "add" "replace" "remove".\
Arguments:
* roleId : REQUIRED : The role ID to be updated
* roleDict : REQUIRED : The change to the role


### putRole
PUT the role with the new definition passed.\
As a PUT method, the old definition will be replaced by the new one.\
Arguments:
* roleId : REQUIRED : The role ID to be updated
* roleDict : REQUIRED : The change to the role\
example:
```JSON
{
"name": "Administrator Role",
"description": "Role for administrator type of responsibilities and access.",
"roleType": "user-defined"
}
```

### getSubjects
Get the subjects attached to the role specified in the roleId.\
Arguments:
* roleId : REQUIRED : The roleId for which the subjects should be extracted


### patchSubjects
Manage the subjects attached to a specific role\
Arguments:
* roleId : REQUIRED : The role ID to update
* subjectId : REQUIRED : The subject ID to be updated
* operation : REQUIRED : The operation could be either "add" "replace" "remove"


### getPolicies
Returns all the policies applying in your organization


### getPolicy
Returns a specific policy based on its ID.\
Arguments:
* policyId : REQUIRED : The policy ID to be retrieved


### deletePolicy
Delete a specific policy based on its ID.
Arguments:
* policyId : REQUIRED : The policy ID to be deleted


### createPolicy
Create a policy based on the definition passed
Arguments:
* policyDef : REQUIRED : The policy definition requires


### putPolicy
Replace the policyID provided by the new definition passed. \
Arguments:
* policyId : REQUIRED : The policy ID to replaced
* policyDef : REQUIRED : The new definition of the policy ID.


### patchPolicy
Patch the policyID provided with the operation provided\
Arguments:
* policyId : REQUIRED : The policy ID to be updated
* operation : REQUIRED : The operation to realise ("add" "replace" "remove")
* attribute : REQUIRED : The attribute to be updated. Ex : "/description"
* value : REQUIRED : The new value to be used


### getProducts
List all entitled products


### getPermissionCategories
Retrieve the permissions categories for a specific product\
Arguments:
* productId : REQUIRED : The product you are looking for


### getPermissionSets
Retrieve the permissions set of the product ID you want to acces.\
Arguments:
* productId : REQUIRED : The product ID permissions set you want to retrieve