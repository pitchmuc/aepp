# Releases information

This page list all of the changes that came during the different release of the aepp module.

## version 0.1.4

* adding queryTemplate endpoint (GET and DELETE)
* adding `cancelQuery` and `deleteQuery` method
* adding `property` parameter on `getQueries` method
* modifying `deleteBatch` method location. Now part of the `ingestion` module.
* adding `replayBatch` method to ingestion module.
* adding FieldGroup compatibility.
* adding logging capability (see [documentation](./logging.md))
Patch:
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
