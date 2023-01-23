# Releases information

This page list all of the changes that came during the different release of the aepp module.

## version 0.2.4
* Supporting out of the box schema and field groups for `SchemaManager` & `FieldGroupManager`
* fix `FlowManager` instanciation when no update available for a mapping.
* adding a parameter (`mappingRulesOnly`) to extract only the rule out of a mappingSet.\
* adding querypath output for dataframe in `FieldGroupManager`
* support `property` and `customFields` having the same object construction\
PATCH : 
* moving from `customField` to `property` per default.
* adding method `getMapping` to get detail on mappings from FlowManager
* changing methods to extract MappingSet rules by `cleanMappingRules` and `copyMappingRules`

## version 0.2.2

* adding `FieldGroupManager` and `SchemaManager` class in the `schema` submodule
* adding support for more parameter on `getFailedBatches` in `catalog` submodule
* adding the new method `getMapperErrors` to access mapper errors and provide cleanse data to analyze.
* adding the `FlowManager` class to gather all information from one flow Id.
* improving the method to fetch unique component of the Flow. Avoiding additional clean up to end result.
* import `updateMappingSet` method so only the mapping list is required to be provided.\
Patch:
* fix searchField, getField by accessing `properties` and `customField` attributes.
* adding possibility to modify schema output when updating mapping.
* adding timestamp information and updating date for mapping in Flow service.
* deduplicating path for SchemaManager dataframe output
* improve when path used for title on FieldGroup manager `addField` operation is not cleaned.
* adding Enum support for `addField` operations
* adding `createFieldGroup` method on `FieldGroupManager`
* changing the requirement to instantiate `FieldGroupManager` and `SchemaManager`. No requirement to pass the Schema instance if a config file has been provided.
* supporting operation on out-of-the-box fieldgroups

## version 0.2.1

* remove requirement for `PyGreSQL` and `psycopg2`\
Patch
* Fixing looping for Schemas / Field Groups and Data Type

## version 0.2.0

* create a new interactive query class `InteractiveQuery2` that uses `psycopg2` as module.
  * supports all methods used by the `InteractiveQuery` class
* adding `getAlertSubscriptions`, `createAlertSubscription` and all methods related to alerts in `queryservice` module
* adding the `createAcceleratedQuery` method in the `queryservice` module
* adding new methods for `segmentation` module
  * all audiences methods (GET, POST, PUT, DELETE)
  * Bulk Definition
  * Convert segment definition
  * rename `searchEntity` to `searchEntities`
* adding more logger log in schema

## version 0.1.8

* improve `getClasses` in the schema module.
* Adding some classes methods:
  * putClass
  * patchClass
  * deleteClass
* adding shortcuts for
  * enabling a schema for union profile : `enableSchemaForRealTime`
  * extend a FieldGroup / Mixin to multiple class support (ExperienceEvent/Record/Profile) : `extendFieldGroup`
* adding several methods for profile and identity enablement of datasets:
  * `enableDatasetProfile`
  * `enableDatasetIdentity`
  * `disableDatasetProfile`
  * `disableDatasetIdentity`
  * `createUnionProfileDataset`
* adding `createExportJob` fin the `customerprofile` module
* adding `getExportJobs`,`getExportJob` and `deleteExportJob`\
Patch:
* improving `schema` internal module work
* adding new option for `getFieldGroup` method 
* fix issue with `getDataType` method
* fixing typo in documentation
* Improving descriptor methods with primary support
* fixing getDescriptors loop
* adding deprecated option for schema, fieldGroup and class
* fixing `SyncValidation` parameter in data ingestion.
* adding option to get raw request response object
* Fixing sandbox attribute update when using `updateSandbox` method
* Fix `getAuditEvent` pagination
* Improving `copyFieldGroup` method
* Fixing `extendFieldGroup`
* supporting parquet file download from data access API
* supporting replace operation when creating batch.

## version 0.1.7

* adding statistics endpoint to retrieve dataset size in the `QueryService` class in the `queryservice` module. Method: `getDatasetStatistics`.
* adding the destination SDK capability in the `destination` module. Documentation on [Destination Authoring](https://developer.adobe.com/experience-platform-apis/references/destination-authoring/) or [internal documentation](https://github.com/pitchmuc/aepp/blob/master/docs/destination.md)
* adding the capability to enable a dataset for profile directly from API: `catalog` module and method `enableDatasetProfile`
* Improving the `createClass` method with simpler parameters.
* Updating links to Adobe documentation
* Change `Accept` parameter for `application/json` in `identity` submodule for certain methods.\
Patch:
* typo on the `getIdentity` parameter check conditions.

## version 0.1.6

* update `queryservice` module to avoid PostgreSQL server installation when not using `InteractiveQuery`.
* update query service module documentation.
* adding `export` and `import` method to the schema module.
* adding behavior methods to schema module.
* parametarize the `generateLoggingObject` method.

## version 0.1.5

* improve `segmentation` methods

## version 0.1.4

* adding queryTemplate endpoint (GET and DELETE)
* adding `cancelQuery` and `deleteQuery` method
* adding `property` parameter on `getQueries` method
* modifying `deleteBatch` method location. Now part of the `ingestion` module.
* adding `replayBatch` method to ingestion module.
* adding FieldGroup compatibility.
* adding logging capability (see [documentation](./logging.md))

Patches:

* fix an issue on logging data when using `GET` method.
* adding more endpoints in the `dataprep` module
* adding the `updateSchedule` on the `segmentation` module

## version 0.1.3

* adding manifest file to include pickle files
* changing setup file to include pickle files
* adding overlap report endpoint in `customerprofile`

Patch:

* Fix `getRuns` and `getRun` in `flowService` module
* adding *n_results* parameter in most of global calls
* fix `streamMessage` and `streamMessages` methods wrong capitalization
* adding docstring to `flowservice` elements

## version 0.1.2

* handling pagination on `getConnections` method in `flowService`
* fix `getRun` and `getRuns` methods
* adding `getResource` method on `schema`, `queryService`, `flowservice` and `catalog` module
* exposing encoding capability on the `saveFile` method
* adding `decodeStreamBatch` to the catalog module to decode the message returned by failed batch.
* adding `jsonStreamMessages` to the catalog module to transform the output `decodeStreamBatch` into list of dictionary.
* adding `getFailedBatchesDF` method to catalog module

Patch :

* fix `getFailedBatchesDF` when no Flow or no Tag is used
* adding deprecated `deleteBatch` method.

## version 0.1.1

* adding `observability` submodule
* adding Query Service Template template as attribute: `TEMPLATESAMPLE`.
* update `catalog` parameters for standardization.
* fix Stream batch
* rename `mapping` to `dataprep`
* fix sandbox switch on `importConfigFile`
* change `Sandbox` class to `Sandboxes` for consistency.

PATCH

* fixing *`limit`* parameter for `queryIdentity` method
* fixing verbose f string method.

## version 0.1.0

* official release of the aepp module as beta python module with support.\
  The module include:
  * Automatic token generation and maintenance
  * Documentation on use-cases for the modules (with a star)
  * Support to most endpoints described on the [AEP API documentation](https://www.adobe.io/apis/experienceplatform/home/api-reference.html) (as January 2021).
    * Schema *
    * Query Service *
    * Identity *
    * Privacy Service
    * Sandboxes *
    * Segmentation *
    * Sensei
    * Flow Service *
    * Dule
    * Customer Profile *
    * Catalog *
    * Data Access *
    * Mapping Service *
    * Datasets *
    * Ingestion *
  
Patches:

* fix `save` option in `getSchemaSample`
* add `save` option to `getSchemaPaths`
* change `getBatches` method parameters to add "dataframe" and "raw" ouputs options
* upgrading the docstring for `postQuery` method
* changing `exportJobs` to `getExportJobs`
* removing some duplicate attributes in `QueryService` class
* fix verification issue on queryService `createQueryTemplate` method.

Return to [README](../README.md)
