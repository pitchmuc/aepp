# Data Hygiene in AEP

The data hygiene API is not yet officially presented in the AEP API catalog.\
You can find the details of the API in the [Experience League](https://experienceleague.adobe.com/en/docs/experience-platform/data-lifecycle/api/overview)\
The module is therefore relying on the information of Experience League and is here to help users of the AEP product to automate their Data Hygiene calls directly from `aepp`

**NOTE** : All functionalities of the data hygiene setup is not yet provided to all customers. Some requires migration of your data platform, some are available after a licence purchase.\
Contact your adobe representative to know what can be used in your organization.

## Menu

- [Data Hygiene in AEP](#data-hygiene-in-aep)
  - [Menu](#menu)
  - [Importing the module](#importing-the-module)
  - [Generating a Hygiene instance](#generating-a-hygiene-instance)
    - [Using different ConnectObject for different sandboxes](#using-different-connectobject-for-different-sandboxes)
  - [Data Hygiene Methods](#data-hygiene-methods)
    - [getQuotas](#getquotas)
    - [getDatasetsExpirations](#getdatasetsexpirations)
    - [getDatasetExpiration](#getdatasetexpiration)
    - [createDatasetExpiration](#createdatasetexpiration)
    - [deleteDatasetExpiration](#deletedatasetexpiration)
    - [createRecordDeleteRequest](#createrecorddeleterequest)
    - [getWorkOrderStatus](#getworkorderstatus)
    - [updateWorkOrder](#updateworkorder)


## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `hygiene` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json', sandbox='prod', connectInstance=True)

from aepp import hygiene
```

## Generating a Hygiene instance

Because you can connect to multiple AEP instance at once, or multiple sandboxes, you would need to setup an instance of the `Hygiene` class from that module.\
Following the previous method described above, you can realize this:

```python
myHygieneSandbox = hygiene.Hygiene(config=prod)
```

Several parameters are possibles when instantiating the class:\

* config : OPTIONAL : mostly used to pass a ConnectObject instance that is linked to one sandbox as described in the example above.
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

### Using different ConnectObject for different sandboxes

You can use the `connectInstance` parameter to load multiple sandbox configuration and save them for re-use later on, when instantiating the `Hygiene` class. 
As described above, it can be useful when you want to connect to multiple sandboxes with the same authentication.\
In that case, the 2 instances will be created as such:

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json', sandbox='prod', connectInstance=True)
dev = aepp.importConfigFile('myConfig_file.json', sandbox='dev', connectInstance=True)

from aepp import hygiene

myHygieneSandbox1 = hygiene.Hygiene(config=prod)
myHygieneSandbox2 = hygiene.Hygiene(config=dev)

```

## Data Hygiene Methods

In the below section, we will document all methods available for the Hygene class

### getQuotas

Returns a list of quota types and their status.\
It allows you to monitor your Advanced data lifecycle management usage against your organization's quota limits for each job type.\
Arguments:
* quotaType : OPTIONAL : If you wish to restrict to specific quota type.\
  Possible values:
  * expirationDatasetQuota (Dataset expirations)
  * deleteIdentityWorkOrderDatasetQuota (Record delete)
  * fieldUpdateWorkOrderDatasetQuota (Record updates)

### getDatasetsExpirations

allows you to schedule expiration dates for datasets in Adobe Experience Platform.\
A dataset expiration is only a timed-delayed delete operation. The dataset is not protected in the interim, so it may be be deleted by other means before its expiry is reached.\
It can take up to 24h after the date specified before the dataset is deleted from AEP.\
It can take up to 7 days for all services (UIS, UPS, CJA, etc...) to reflect the deletion impact.\
Arguments:\
Possible keywords:\
* author : Matches expirations whose created_by (ex: author=LIKE %john%, author=John Q. Public)
* datasetId : Matches expirations that apply to specific dataset.    (ex : datasetId=62b3925ff20f8e1b990a7434)
* datasetName : Matches expirations whose dataset name contains the provided search string. The match is * case-insensitive. (ex : datasetName=Acme)
* createdDate : Matches expirations that were created in the 24-hour window starting at the stated time. (ex : createdDate=2021-12-07)
* createdFromDate : Matches expirations that were created at, or after, the indicated time. (ex : createdFromDate=2021-12-07T00:00:00Z)
* createdToDate : Matches expirations that were created at, or before, the indicated time. (ex : createdToDate=2021-12-07T23:59:59.00Z)
* completedToDate : Matches expirations that were completed during the specified interval. (ex: completedToDate=2021-11-11-06:00)
* status : A comma-separated list of statuses. When included, the response matches dataset expirations whose current status is among those listed. (ex : status=pending,cancelled)
* updatedDate : matches against a dataset expiration's update time instead of creation time. (updatedDate=2022-01-01)
* full list : https://experienceleague.adobe.com/en/docs/experience-platform/data-lifecycle/api/dataset-expiration#appendix

### getDatasetExpiration

To retrieve the specify dataset deletion.\
One of the 2 parameters is required.\
Arguments:
* datasetId : OPTIONAL : the datasetId to look for
* ttlId : OPTIONAL : The ttlId returned when setting the ttl.


### createDatasetExpiration

Create or update an expiration date for a dataset through a PUT request.\
The PUT request uses either the datasetId or the ttlId.\
One of the 2 first parameters is required.\
Arguments:
* datasetId : OPTIONAL : the datasetId to set expiration for
* ttlId : OPTIONAL : The ID of the dataset expiration.
* expiry : REQUIRED : the expiration in date such as "2024-12-31T23:59:59Z"
* name : REQUIRED : name of the ttl setup
* description : OPTIONAL : description of the ttl setup

### deleteDatasetExpiration

You can cancel a dataset expiration by making a DELETE request.\
Arguments:
* ttlId : REQUIRED : The ttlId of the dataset expiration that you want to cancel.


### createRecordDeleteRequest

Delete records from a specific identity.\
**NOTE** : You should use the maximum number of identities in one request. Max is 100 K identities in the list.\
Argument:
* datasetId : REQUIRED : default "ALL" for all dataset, otherwise a specific datasetId.
* name : REQUIRED : Name of the deletion request job
* namespacesIdentities : REQUIRED : list of namespace code and id to be deleted.\
    example :
    ```py
    [
        {
            "namespace": {
            "code": "email"
        },
        "IDs": [
            "alice.smith@acmecorp.com",
            "bob.jones@acmecorp.com",
            "charlie.brown@acmecorp.com"
            ]
        }
    ]
    ``` 
* description : OPTIONAL : Description of the job
* recordDeletionDict : OPTIONAL : dictionary containing the full deletion request payload (not passing other arguments)

### getWorkOrderStatus

Return the status of a work order.\
Arguments:
* workorderId : REQUIRED : The workorderId return by the job creation

### updateWorkOrder

Update the work order\
Arguments:
* workorderId : REQUIRED : The workorderId return by the job creation 
* name : REQUIRED : the new name of the work order
* description : OPTIONAL : Description of the work order

