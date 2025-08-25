# Releases information

This page list all of the changes that came during the different release of the aepp module.


## version 0.3.13
* adding `getWorkOrders` on the `hygiene` module
* enable to output pydantic data on managers. The `to_pydantic` method is now available.
  * building dependency with `datamodel-code-generator` module

## version 0.3.12
* adding the `extractSandboxArtefacts` methods in aepp module [documentation on methods](./main.md), [documentation on local file usage](./localfilesusage.md) 
* refactoring `SchemaManager`, `FieldGroupManager`, `DataTypeManager` and `ClassManager` to support local file setup.
* refactoring `addField` operation to support more type of DataType and Field Group. Removing some safeguard.
* adding capabilities for `synchronizer` module to support local file setup.
* refactoring the `to_dict` and `to_dataframe` to support extended OOTB Field Group
* better support for `enum` and `map` in `to_dict` method\
Patch:
* improve `map` representation in dict for FieldGroupManager
* improve `enum` export in dict for FieldGroupManager
* support custom fieldgroups not following `customFields` setup
* `synchronizer` fix for reference to localFolder setup
* patch creation of synchronizer without using the `localFolder` capability
* adding the `getDatasets` method in `schemaManager`
* fixing issue on `to_dataframe` and `to_dict` `__simpleMerge__` usage
* fixing issue on `searchField` for edge-case fieldgroup definitions

## version 0.3.11
* adding the better compatibility for data type in `FieldgroupManager`
  * The new attributes `dataTypeManagers` is returning dict of `{'title':'__DataTypeManager__class'}`
  * the attribute `dataTypes` is returning a dict of `{'id':'title'}`
  * the new method `getDataTypePaths` path is returning a dict of `{'path':'dataType'}`
  * the `to_dict` and `to_dataframe` methods are now resoving dependency on data type instead of querying the resolved field groups.
  * Fixing issue on `addField` capacity on `DataTypeManager`
  * Adding `importDataTypeDefinition` method on `DataTypeManager`
  * Better support of legacy data type definition with `property`
* adding the `classes_id` and `classes_altId` attributes in the `Schema` instance.
* adding new capabilities to send data via `ingestion` module `streamMessage` method. 
* adding the `remove` and `clear` method in `som`
* adding `targetSchema` and `xdm:descriptorRelationship` to the descriptor support
* change the `createDataSets` to `createDataSet` to better reflect the behavior.
* adding new `descriptors` supports on `SchemaManager` class.
* better support on `createIdentity` method
* supporting creation of descriptors on the `FieldGroupManager` to accomodate to `xdm:descriptorLabel`
* adding the `to_som()` to `SchemaManager`, `FieldGroupManager` and `DataTypeManager`\
Patch: 
* fixing an issue on providing the dataframe for Schema, FieldGroup and DataType when objectArrays were not marked correctly on the path
* improving the `to_dataframe` capability by providing the custom required fields.
* better support for `getBehavior` method
* adding `updateDescriptor` in `FieldGroupManager`
* better handling of custom class in `ClassManager`
* fix issue handling dataTypes for `to_dict()`and `to_som()` methods
* Supporting B2B identities in `Identity` module
* adding the `createB2Bschemas` method in `schema` module [doc](./schema.md#createB2Bschemas)
* release of the `synchronizer`(BETA version) [documentation](./synchronizer.md)

## version 0.3.10
* refactor the `createPackage` and `updatePackage` methods ([documentation](./sandboxes.md#createPackage)).
Patch:
* fixing typo in `getFailedBatchesDF` method in catalog
* change of default parameter `xtype` to `type` for getClass method. Should be backward compatible. No impact.
* Preventing null assignment to some variable during init of classes.
* Changing some string (`''`) to raw string (`r''`) for regex to avoid potential escape errors

## version 0.3.9

* refactor `SchemaManager`, `FieldGroupManager` and `DataTypeManager` for better maintenance
* adding the `classManager` class. [documentation](./classmanager.md)
* change the default `addField` path to `customFields` instead of `property` in FieldGroupManager.
* fixing the refresh of token with new data class for token.
* supporting custom classes for FieldGroupManager creation
* change the requirement for `importSchemaDefinition` and `importFieldGroupDefinition` to `xdmType` and not `type`.
* adding multiple parameter supports in some  flowservice methods
* adding Once dataset export capability via community push\
Patch:
* added option to return expanded schema in MappingSet retrieval
* fix so that credential properties are not case sensitive
* set max limit to 100 for segment retrieval to avoid 400 errors
* better support of native class in `ClassManager`
* fix looping for `getTags` method
* Supporting a new descriptor in `SchemaManager`
* Fixing customer profile typo
* Enhancing `Identity` class connection for AEP developer
* Adding new reference for descriptors in `SchemaManager`.
* Patch invalid escape sequence in `catalog` and `fieldgroupmanager`
* Patch the `from_dataframe` in the `som` module 
* adding capability to request ssl connection in `InteractiveQuery2`


## Version 0.3.8

* creating the `som` module [documentation](./som.md)
* expanding hints for additional server on `identity` and `sandbox`
* fix support for `title` parameter in custom `dataType` for `fieldGroupManager`
* adding the `getDataTypeGlobal` method in the schema module
* adding dataTypes in the `data` object when querying `getDataTypes` and `getDataTypesGlobal`
* Fixing issues on API spec for `Tags` and adding `Folders` endpoints\
Patch:
* adding the `excludeObjects` parameter in `to_dataframe` methods for `FieldGroups` and `SchemaManager`


## Version 0.3.7

* adding support for assurance token on Edge methods
* adding following methods to flowservice
  * `createFlowStreaming`
  * `createTargetConnectionDatasetToDataLandingZone`
  * `getExportableDatasets`
  * `getExportableDatasetsDLZ`
  * `createBaseConnectionS3Target`
  * `createBaseConnectionBlobTarget`
  * `createBaseConnectionDLZTarget`
  * `exportDatasetToDLZ`
  * [see documentation](./flowservice.md#createFlowStreaming)
* adding methods to package ([see sandbox methods](./sandboxes.md))
  * `createShareRequest`
  * `approvingShareRequest`
  * `getShareRequests`
  * `transferPackage`
  * `getTransfer`
  * `getTransfers`
  * `importPublicPackage`



## Version 0.3.6
* Adding the `edge` module. [Documentation](./edge.md)
* adding better docstring and documentation for `catalog` module [here](./catalog.md)
* adding `enableDatasetUpsert` specific method in `catalog` to enable a profile for upsert.
* fixing methods for `customerprofile` in order to retrieve destinations and projections.
* adding complete documentation for `ingestion` module.
* Deprecated `uploadLargeFilePart` & `uploadLargeFileStartEnd` in `ingestion` module.\
Patch: 
* adding `getParquetFilesToDataFrame` and `transformDataToDataFrame` methods in `dataaccess` 


## Version 0.3.5

Deprecate:
* Deprecated `getLandingZoneContainerName` method in `flowservice`, new `getLandingZoneStorageName` should be used instead
* Deprecated `getLandingZoneContainerTTL` method in `flowservice`, new `getLandingZoneStorageTTL` should be used instead
* Deprecated `getLandingZoneStorageAccountName` method in `flowservice`, new `getLandingZoneNamespace` should be used instead\
Patch:
* fix on Data Hygiene method `createRecordDeleteRequest`
* fix some typo on `customerProfile` docstring and methods


## Version 0.3.4

* add `Hygiene` module ([documentation](./hygiene.md))
* adding `datasetId` key to Observable Schemas
* add the `findInactiveBatch` method on the catalog
* fix schema class filtering on `getSchemas` methods\
Patch:
* fix `UploadSmallFile` method in `ingestion` module
* adding `extractPaths` method to `Segmentation` class ([doc](https://github.com/adobe/aepp/blob/main/docs/segmentation.md#extractpaths))
* adding `extractAudiences` method in `Segmentation` class ([doc](https://github.com/adobe/aepp/blob/main/docs/segmentation.md#extractaudiences))
* fixing the `updateFlowMapping` in FlowManager class.
* fixing the `policy` module
* adding the `tags` module
* improving the `schema` documentation
* improving docstring in `DataPrep`
* improving batch ingestion in `ingestion` module.
* Improve documentation for Schema and dropping mixins related methods
* Improving `FieldGroupManager` to handle `dataType` & fix on typo
* Improving `QueryService` documentation and setup a new method `createQuery` that is a copy of `postQueries`
* Adding support for edge case scenario when data type are added as array.

## Version 0.3.3
* add Access Control new methods
  * getRoles
  * getRole
  * createRoles
  * patchRole
  * putRole
  * deleteRole
  * getSubjects
  * updateSubjects
  * getPermissionSets
  * getPermissionCategories
  * getProducts
  * createPolicy
  * getPolicy
  * getPolicies
  * deletePolicy
* rename `getReferences` to `getPermissions` in Access control
* rename `postEffectivePolicies` to `getEffectivePolicies`, even if POST method, it returns a list that cannot be changed.
* change `updateSegment` from POST method to PATCH\
Patch:
* Fix the `deleteEntity` in `customerprofile` with `mergePolicyId` Support
* Fix reference and header used in the Computed Attributes methods in `customerprofile` 
* Making Field Group Manager supporting more default field groups.
* Fix `getDescriptors` when only one property is passed as parameter
* add `getDescriptors` in `SchemaManager`
* add `getProfileSnapshotDatasets` method to catalog
* fix `disableDatasetIdentity` and `disableDatasetProfile` methods


## Version 0.3.2

* fix `getSchemas` and `getFieldGroups` because of Adobe AEP API change.
* adding a __str__ and __repr__ method to all Classes. 
* `enableSchemaForRealTime` now also supports the schema `$id`
* abstracting HTTP methods for the `ConnectObject`
* providing a parameter to setup SSL verify in HTTP methods.
* providing `title` column on `to_dataframe` method for `SchemaManager` instances.
* adding the different methods available for sandbox tooling in the `sandboxes` module:
  * getPackages
  * getPackage
  * deletePackage
  * createPackage
  * updatePackage
  * importPackageCheck
  * importPackage
  * getImportExportJobs
  * getPackageDependencies
  * checkPermissions
* providing `DataTypeManager` class in the schema module\
Patch:
* fixing `title` for array and array of objects in `to_dataframe()` methods for SchemaManager and FieldGroupManager.
* dropping reference to `pathlib` as required module in `requirements.txt` and `setup.py` file
* adding the new methods `importSchemaDefinition` and `importFieldGroupDefinition` in the Schema and Field Group Manager.
* adding support for Data Type Manager in the Field Group Manager instance (`getDataTypeManager()` method and `dataTypes` attribute)
* adding the `DataTypeManager` class instantiation from `Schema` instance
* fixing `getAudiences` method in Segmentation
* extending flowManager
* fixing `importSchemaDefinition` and `importFieldGroupDefinition` first bugs.

## Version 0.3.1

* adding methods for Policy module.
  * `evaluateMarketingActionUsageLabel`
  * `evaluateMarketingActionDataset`
  * `createOrupdateCustomMarketingAction`
  * `getCustomMarketingAction`
* Fixing issue on Schema Manager when multiple sandboxes are used.
* adding `compareDFschemas` method in schema module and `Schema` class.
* removing & renaming parameters for `SchemaManager` methods in `Schema` class.
* Fixing `schemaAPI` reference in `FieldGroupManager` instantiation
* adding exportDatasetToDataLandingZone module.
  * `createDataFlowIfNotExists`
  * `createDataFlow`
  * `createBaseConnection`
  * `createSourceConnection`
  * `createSourceConnection`
  * `createTargetConnection`
  * `createFlow`
  * `createFlowRun`
  * `checkIfRetry`
* Fixing addFieldGroupToSchema\
Patches: 
* Changing return type of `compareDFschemas` method to dataFrame
* Fixing `FieldGroupManager` discovery of custom data type
* More robust `getFailedBatchDF` method
* Supporting pandas > 2.0 by replacing `append` with `concat`
* Fixing support to `getEntity` method in `customerProfile` for experienceEvents data.
* Fixing `start` parameter that is not supported for `getSchemas` anymore.
* default the getSchemas to not get the adhoc schema.
* Fixing the FieldGroupManager intantiation.
* adding documentation on the Catalog
* Adding `onlyDestinations` and `onlySources` as parameter for the `getFlows` method.
* Fixing the `createDataset` method when wanting to have a dataset enabled for Profile and Identity Service. 

## version 0.3.0

* Supporting Oauth V2 token for authentication in the config file and configure methods.See [getting-started](./getting-started.md).
* Change in the default config file creation. It is now automatically creating a config file giving information for Oauth Server-to-Server integration
* Change for Oauth V1, the parameter value is now `oauthV1` instead of `oauth` when importing the config file. Automatically, the type of authentication is detected but you can still force the type of authentication to be done via the `auth_type` parameter.

## version 0.2.11

* Supporting the disabling SSL certificate disablement capability

## version 0.2.9

* adding a new module : `destinationInstanceService`
  * The new module will help provide destination support.
* logging some errors when identified in the connector `getData` operation
* returning errors for getSchemas operation
* Fixing `getRuns` in `FlowService` class when there are no runs to fetch.
* adding the possibility to extract `description` field when running `to_dataframe` in Schema and Field Group Managers
* adding the `getDataSetObservableSchema` method to retrieve all fields that contains data.

## version 0.2.8

* support for Service Token
  * refactoring of token generation to support user-based-token
  * Use `DataClass` for better abstraction of Token endpoint response.
  * sandbox management for JW and Service Token
* fix issue on `SchemaManager` and `FieldGroupManager` for searching for fields at root.
* adding first set of test 
* support JSON file for `uploadSmallFile` method in `ingestion` module
* fixing header `'Content-Type'` header param for `enableDatasetIdentity` in `catalog` module.

## version 0.2.7

* adding environment for AEP API endpoints for non-prod endpoints
* Update the `flowservice` module to support dataset egress
  * `createFlowDataLakeToDataLandingZone` method has been added
  * `createTargetConnectionDataLandingZone` method has been added
* Update the `flowservice` module to look the connection spec IDs from API instead of hardcoding them
  * method `getConnectionSpecIdFromName` has been added
  * method `getFlowSpecIdFromNames` has been added (not to be used for Destination SDK flows)
* `createFlow`method has been improved with additional parameters
* `createFlowDataLandingZoneToDataLake` has been created to simplify Data Landing Zone ingestion
  * `createSourceConnectionDataLandingZone` has been created

## version 0.2.6
* adding an `updateFlow` and `updateFlowMapping` method to `FlowManager` class.
* adding the `ConnectObect` class that will provide a more dynamic way to switch between orgs or sandboxes.
* adding `sandbox` param in class instantiation for supporting sandbox definition at instantiation time.
* adding support for `patchDataType` and `putDataType` operation in `Schema` class.
* Supporting the class `Formatter` type in the logging capability.
* updating the `createDataSet` method in `Catalog` to allow better parameterization.
* Changing Content-type for `enablingDatasetProfile` method. Undocumented issue for AEP.
* adding `getLandingZoneContainer` , `exploreLandingZone`, `getLandingZoneCredential` and `getLandingZoneContent` in `FlowService` class.
* adding `createSourceConnectionDataLandingZone` in `FlowService` class
* adding support for `systemLabels` parameters in DataSet creation.
* fixing issue on Query Service when you can only pass the `templateId` parameter\
Patch 
* fix query service endpoints reference

## version 0.2.5
* adding the `completePath` attribute for search result of `searchField` method in `SchemaManager`
* fix the `getField` method and support any field type.
* adding the `updatePolicy` method in the flow.
* fixing typo on `pathFieldGroup` method for `FieldGroupManager`.
* updating the field group will automatically update the local copy of the definition.
* adding the searchAttribute for `SchemaManager` and `FieldGroupManager` class.
* add a `createSchema` method from the `SchemaManager` class.\
Patch:
* fix when root component where search via searchField and searchAttribute
* fix when strings were passed to add Fieldgroup to SchemaManager
* adding the `updateSchema` method in `SchemaManager` class.
* adding a method to return all available default field groups (`getFieldGroupsGlobal`)
* adding `output` param or `getSchemas` and `getFieldGroups` methods
* adding a `fieldGroups` attribute to `SchemaManager` instance with `$id` and `title`

## version 0.2.4
* Supporting out of the box schema and field groups for `SchemaManager` & `FieldGroupManager`
* fix `FlowManager` instantiation when no update available for a mapping.
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
