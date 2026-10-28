# Releases information

This page list all of the changes that came during the different release of the aepp module.

## version 0.6.0

* Add `queryHistoryMeta`, `queryProfilesTrend`, `queryNamespacesDistribution` and `queryNamespacesTrend` to both interactive Query Service classes. These return table snapshot history, daily profile counts for the last 30 days, the latest namespace distribution and namespace trends. Reporting queries use the default merge policy; namespace filtering is case-insensitive. [Query Service documentation](./queryservice.md#queryhistorymeta)
* Add `InteractiveQuery.querySegmentPopulationTrend` and `InteractiveQuery2.queryAudiencePopulationTrend` to retrieve profile, identity and calculated population trends, with optional case-insensitive filtering by audience name or ID. The two classes expose different method and name-column conventions. [Audience trend reference](./queryservice.md#queryaudiencepopulationtrend)
* Both interactive-query constructors now read default merge-policy and namespace metadata from `qsaccel.profile_agg`, exposing `default_merge_policy_queryId` and `default_merge_policy_id` as attributes.
* Add CLI reports `query_history_meta`, `query_profiles_trend`, `query_namespaces_distribution`, `query_namespaces_trend` and `query_audience_population_trend`. Each displays up to 10 rows, exports the full returned dataframe to CSV, supports a custom filename and closes its initialized connection even when report retrieval fails. [CLI report reference](./cli.md#interactive-query-reports)
* Add optional Matplotlib trend charts through `--plot`, with case-insensitive numeric-column selection through `--metric`. Namespace distributions use Rich terminal bars, including an ASCII fallback. Plotting leaves CSV contents unchanged; plotting errors are reported after export. [Examples and chart requirements](./cli.md#interactive-query-reports)
* **Breaking change:** Rename `InteractiveQuery2.querySegmentPopulation(segmentId=...)` to `queryAudiencePopulation(audienceId=...)` and CLI `query_segment_population` to `query_audience_population`. No compatibility aliases are provided. The identity export column becomes `audienceId`, and the default CLI filename becomes `audience_population_<first_audience_id>.csv`. `InteractiveQuery` retains its segment-named method. List requests now forward `extraFields` to each audience query. [Migration details](./queryservice.md#queryaudiencepopulation)
* Prevent schema synchronization from removing field-group references when the target schema is enabled for Profile or has associated datasets. References absent from the source can still be removed from schemas that meet neither condition; `force=True` does not bypass these safeguards. [Synchronizer behavior](./synchronizer.md#update)
* Extend offline CLI and Query Service regression coverage for reporting queries, filters, CSV exports, connection cleanup and chart behavior. [Testing guide](./tests.md#offline-cli-and-query-service-regression-tests)\
Patch: 
* adding verbose option for artifact extraction

## version 0.5.9
* Adding CLI destructive commands `delete_dataset`, `delete_schema`, `delete_dataflow` and `delete_audience`, wrapping the `deletion` module with an impact-warning panel and a type-to-confirm safeguard before anything is deleted. [documentation](./cli.md#deletion-methods)
* Fix `Deletion.deleteSchema` returning its field group results under the wrong key (`fieldGroupName` instead of `fieldGroup`).
* Extending Knowledge Graph `buildGraph` with Merge Policy nodes, linked to their schema and to the audiences that use them (`mergePolicy`, `totalProfiles`).
* Fix `KnowledgeGraph.buildSchemaRelationships` raising an `AttributeError` by calling the graph builder under its old name (`buildKnowledgeGraph` instead of `buildGraph`).
* Adding `KnowledgeGraph.query` to run a SPARQL query and get back a list of plain dictionaries (ready for `pandas.DataFrame`) instead of raw `rdflib` result rows. [documentation](./knowledge-graph.md#query)
* Requiring an active sandbox connection (`login_required`) on the Knowledge Graph CLI commands `load_graph`, `add_path_attributes`, `add_schema_attributes` and `add_dataset_attributes`, which could previously be called before connecting.
* `change_sandbox` in the CLI now falls back with a warning instead of crashing when the Sandboxes API isn't accessible with the current credentials.
* Fix `flexible_audience_evaluation` in the CLI raising an error because of an invalid `argparse` keyword.
* Fix `extract_artifacts` in the CLI not passing its artifact type filter through to `extractSandboxArtifacts` due to a flag name mismatch (`--artifact_type` vs `artifactTypes`).
* `sync` in the CLI no longer defaults `--localfolder` to `"extractions"`, avoiding an unintended local-folder sync when `--baseSandbox` is used instead.
* Fix `dateEnd` comparison when checking whether an audience is still actively shared to a destination flow.
* Adding `getDataSetExpiration` method in `catalog` module, and documenting the dataset TTL/`rowExpiration` example for `patchDataSet`.
* Adding `get_dataset_expiration` and `set_dataset_expiration` commands in the CLI, wrapping `Catalog.getDataSetExpiration` to read and update a dataset's TTL/`rowExpiration`. [documentation](./cli.md#dataset-methods)\
Patch: 
* Fixing `get_descriptors` behavior in the CLI 
* Fixing `upload_fieldgroup_definition_csv` and `importFieldGroupDefinition` to account when there is no `origin` columns
  * better support columns name when casing is loose
* adding `get_account_attributes` command in the CLI to retrieve account attributes for a specific user. [documentation](./cli.md#get_account_attributes)
* adding `upload_fieldgroup_definition_xlsx` command in the CLI to create or update a field group using an Excel XLSX file. [documentation](./cli.md#upload_fieldgroup_definition_xlsx)
* Adding params attribute to createRun in flowservice
* Adding `--ootb` and `--filter` options to the `get_fieldgroups` command in the CLI to include out-of-the-box field groups and filter field groups based on a string.
* Fixing knowledge graph build for Merge Policies.
* Fix normalization of dataType variable so it still works when using array notation (`[]`) and different casing.
* Adding CLI commands `get_descriptor` and `get_dataset` to retrieve individual definitions, with JSON export support. [Schema commands](./cli.md#get_descriptor), [Dataset commands](./cli.md#get_dataset).
* Adding Query Service CLI commands `get_query_templates`, `get_query_template`, `get_queries_scheduled`, `create_query_scheduled`, `enable_query_scheduled` and `disable_query_scheduled`, with grouped help, argument help and documentation. [Query Service CLI](./cli.md#query-service-methods).
* Scheduled-query creation now validates SQL/template selection, parameters and timezone-aware dates, uses the active sandbox's database, and reports Adobe's asynchronous activation behavior. The invalid, unused `--enabled` option is removed; schedules become enabled after registration, and subsequent enable/disable requests report acceptance rather than immediate completion.
* Fixing `get_queries` appending to the list it was iterating, ignoring the state filter, and using local timestamps marked as UTC. Query history now applies API state filters and encodes filters only once.
* Query Service query, template and schedule retrieval now follows complete pagination links (including string links and links without `orderby`), honors `n_results` exactly, and surfaces malformed/API error responses instead of silently returning empty results.

### Patch 0.5.9-5

* Extend `Catalog.getProfileSnapshotDatasets` to discover account and account-person snapshots in addition to profile snapshots. [Catalog documentation](./catalog.md#getprofilesnapshotdatasets)
* Add `flatten=True` to return snapshot definitions as a list with an `id` field, while preserving the default dictionary return format. Merge-policy lookup now adds `defaultPolicy` alongside `mergePolicyName`; `defaultOnly=True` enables lookup and filters out non-default policies. Unknown policies are currently retained, so the documentation includes an explicit filter for confirmed default policies.
* Extend the snapshot CLI listing with default-policy and row-count columns, a `-d` / `--defaultOnly` option, and CSV export using the list output. Fix the invalid `store_true` / `type=bool` combination: the option now accepts either a bare flag or an explicit, case-insensitive `True`/`False`, and defaults to `False` when omitted. [CLI reference](./cli.md#get_snapshot_datasets)
* Add `close()` to `InteractiveQuery` and `InteractiveQuery2` to release their database connections. The CLI `query` command now closes its connection after retrieving and exporting results on the successful execution path. [Connection cleanup](./queryservice.md#close)
* Document the local, mocked CLI and Query Service regression suites, covering scheduled queries, query history, definition exports, pagination, result limits and API error handling. Add snapshot CLI regression tests for optional boolean values, invalid input, help and CSV export. [Testing guide](./tests.md#offline-cli-and-query-service-regression-tests)

## version 0.5.8
* adding `get_flow_partial_success` in the CLI to export the partial success flows
* Improving docstring information on CLI 
* Adding `identityEnabled` as a column returned by `getDatasets` and `getDatasetsInfos` method in catalog
* enhance `ObservableSchema` and `to_dict` method to better support `map` type.
* adding knowledgegraph module [documentation](./knowledge-graph.md) and knowldege graph usage documentation [here](./knowledge-graph-usage.md)
* better supports in schemaManager around ootb field groups and data types.
* `getClassesGlobal` now also populate the `data` attributes regarding classes.
* Change the `extract_paths` logic in segmentation to be more robust. 
* Ensure that files created by `extractSandboxArtifact` and `extractSandboxArtifacts` are created with the lower case name to avoid duplicated name with different casing.\
Patch: 
* Fix issue when displaying sample for `query` command in CLI when the result is less than 5 rows.
* Extending CLI retrieval for segments to check if the segment used in Flow are still actively shared. 
* Extending KnowledgeGraph with destination Flows for `segments` and `profile attributes`
* Extending capability of `FlowManager` to better support destination flows and their attributes.
* Patch the name of the dataset created during extraction to reflect the name and not the table name. It means that the file name can evolve over time now. 
* Fix identification of audiences shares in destination when no end date provided in Graph.
* Fix that some descriptors were not created in the target schema when synchronizing between sandboxes.
* offer that we can pass a list of artifact types to extract in `extractSandboxArtifacts` method. It will allow to extract only specific artifacts instead of all of them.

## version 0.5.7
* adding the `create_b2b_artifacts` method in the CLI. 
* adding the possibility to pass command line arguments to the CLI module at instantiation time.[documentation](./cli.md#Non-interactive-mode-examples)
* adding the option to extend the number of events retrieve in `get_profile_events` method in the CLI module. Default is 1000 events but can be extended to 5000 events.
* adding the `flexible_audience_evaluation ` method in the CLI module to support flexible audience evaluation. [documentation](./segmentation.md#flexible-audience-evaluation)
* adding the `update_batch_evaluation_time` method in the CLI module to support update of batch evaluation time. [documentation](./segmentation.md#update-batch-evaluation-time)
* adding the `extract_audience_paths` method in the CLI module to support extraction of audience paths. [documentation](./segmentation.md#extract-audience-paths)
* adding the `extract_audience_ref` method in the CLI module to support extraction of audience references. [documentation](./segmentation.md#extract-audience-ref)

## version 0.5.6
* Adding the `ajo` module [documentation](./ajo.md)
Patch:
* optimizing synchronizer jobs runtime
* fixing `get_observable_schema_csv` and `get_observable_schema_json`
* adding `create_audiences_job` method
* enhancing header token replacement when private header are passed to the calls. Solving edge case of Token regeneration issue on some requests.
* adding `get_hygiene_works`, `get_hygiene_work` and `get_hygiene_quotas` methods in CLI module
* adding the PackageManager in the sandboxes module [documentation](./packageManager.md)
* adding safeguard for CLI `get_audiences`, fallback to `getSegments`
* adding the `get_merge_policies` method in the CLI. 
* Fix issue in schema manager `to_dataframe` and `to_dict` methods. Fixing map.
* Enhancing Audience sync by detecting existing reference to other segments. 
* Reduce limit for `getAudiences` method.

## version 0.5.5
* update the `createDescriptor` method in the `Schema` class.
* adding support for `labels` in the `createDescriptorOperation` in `SchemaManager`
* adding the `createDescriptorOperation` in the `Schema` class
* adding the `clear` method in the CLI
* supporting the new `adhoc-v2` schema in the `SchemaManager`.\
Patch:
* fixing the `SchemaManager` issue for regular schema due to adhoc-v2 schema patch.
* fixing issue with unwanted dependency 

## version 0.5.4
* Fix issues when synchronizer search for config.json file in local folders and they do not exist.
* Refactoring FieldGroupManager, SchemaManager and DataTypeManager to support better handling of local folder and synchronization.
* Refactoring FieldGroupManager to handle OOTB field groups without their full definition
* Changing the way the `synchronizer` module is handling the synchronization of schema, field groups and data types to support better handling of OOTB artefacts and local folder setup.\
* Fixing issue regarding handling data type reference for path that contains repetitive name (eg `_tenant.scroll.scroll`)\
Patch:
* Fixing recursion issue when trying to pull schema that reference themselves in extract_methods
* Fixing issue with datatype references in arrays in Field Group Manager
* Fix the handling of schema creation in synchronizer to better support B2B descriptors.
* Adding filtering options in datasets and audiences retrieval in CLI
* fixing CLI get_fieldgroup and get_datatype (json and csv) methods.
* Adding get_fieldgroup_xdm and get_datatype_xdm methods in CLI to export the XDM definition of a specific field group or data type.
* Changing behavior and now the query that do not return data will return empty dataframe instead of throwing an error.
* Adding filter parameter for extractSandboxArtifacts method to support filtering on schema and dataset name during extraction.
* Fix importing issue with unused library `tomlkit`
* Fix some issue related to `to_dataframe` method when doing union_event schema. 
* improve output for `analyzePath` method in `upsfieldanalyzer`
* Fixing issue with descriptor API that returns non case sensitive code for identity namespace and causing issue for synchronizer to find the correct descriptor to synchronize. 
* Fixing issue when syncing audiences between sandboxes when audience already exists.
* Optimizing the upsFieldAnalayzer for description and type
* adding exception for `meta:xedConverted` field in Schemas for `to_dict` and `to_dataframe` method in managers.
* Fixing that datasets were created with their ID and not table names when export artefacts. 

## version 0.5.3
* soft removing dependency to `region` in `Synchronizer` and `Identity` class
* adding `get_tags`, `get_profile_attributes`, `get_profile_events` method in the `cli` module
* supporting tags on export and synchronization of datasets, audiences
* adding `unifiedTags` support on dataset creation in `Catalog` module
* prioritization to `config` parameter in `Schema` class initialization
* Fixing issue on multiple localFolder support in `Synchronizer` class
* adding additional information (`string:date`, `string:date-time`, `int:long`, `int:short`, `int:byte`) in the `to_dict` methods for `SchemaManager`, `FieldGroupManager` and `DataTypeManager` to support better synchronization and understanding of the schema.\
* adding getSchemasGlobal in `Schema` class to support better synchronization and understanding of the schema.\
* changing persistence of values to add global field groups, schemas and datatypes in their normal respective data point, no more additional data point for global values. This will help better synchronization and simplification of attributes.\
* add support for creation of external audiences in the segmentation module.\
  * createExtenalAudience
  * getExternalAudienceStatus
  * runExternalAudienceJob
  * getExternalAudienceJob
* adding the `syncAll` method to support synchronization of multiple artifacts. Based of folders or sandbox.
* added `createConnectionToUPS` method in `flowservice` module to support connection to UPS for exporting data\
Patch:
* better handling of `config.json` file requirement or baseSandbox requirement for `Synchronizer` class.
* Optimization of code structure for `managers` with the manager_utils module.
* Better support of the `dataTypes` in the `FieldGroupManager` class and `DataTypeManager` class for Synchronizer.
* Fix some issues on the `to_dict` and `to_dataframe` method for `FieldGroupManager` and `DataTypeManager` class
* PR for fixing int issue with `getSchemaSample` in `Schema` class
* Optimization of artifact extraction in Managers to gain time during instantiation.
* adding retry capabilities in global methods, in the `connector`, in the `schema`, `fieldgroupmanager`, `schemamanager`, `classmanager` and `datatypemanager` module.
* adding `--version`, `-v` parameter for CLI to get the version of the module used.
* Removing `region` parameter in most sync and extraction methods as it is not needed anymore with the new API endpoint structure.
* fixing dependencies issues in Synchronizer related to OOTB datatypes and field groups handling.
* `syncAll` and `sync_all` methods now only works based on the local folder setup.
* Fix issue regarding missing folder when more than one folder is passed for `synchronization` and for `managers`.
* Adding the `force` parameter to sync in the CLI
* adding filter capabilities on get_schemas and get_datasets for name filtering. 
* fix issue on synchronization from local folder where tenantId was not correctly setup in schemaManager. 

## version 0.5.2
* adding support for multiple values for localFolder in `SchemaManager`, `FieldGroupManager`, `DataTypeManager` and `ClassManager`
* adding support for multiple values for localFolder in `Synchronizer` class
* Fixing incorrect logging with CLI when `None` values were passed.\
  Patch:
* adding methods in CLI (audiences, sandboxes, snapshots, observable schemas)
* update documentation for local file usage

## version 0.5.1
* changing the method name from `extractSandboxArtefacts` to `extractSandboxArtifacts` to follow the American English spelling.
* updating all references to the new method name in the documentation and code base.
* fixing parameters in CLI
* Updating CLI for mypy compliance

## version 0.5.0
* adding better support for the `saveFile` method.
* Starting integration of CLI capability
* Moving the project publishing from setup.py to pyproject.toml
* Adding better methods on some native methods for `schema`, `queryservice` and `flowservice`.
* Adding documentation on CLI module [here](./cli.md)
* Fixing some relative import issues for packaging.\
Patch:
* adding `partialSuccess` to flow analysis, and fixing typos
* adding new methods to CLI 
* fixing some case sensitivity issues in the `synchronizer` module
 

## version 0.4.2
* supporting segmentation in `extractSandboxArtefacts` and `extractSandboxArtefact` method
* supporting merge policies in `extractSandboxArtefacts` and `extractSandboxArtefact`  method
* supporting segmentation and merge policies in `Synchronizer` class. [See notes](.synchronizer.md#notes-on-merge-policies-synchronization)
* adding helper functions to `Synchronizer` class 
  * getSyncFieldGroupManager : Get the field group manager in the target or base sandbox
  * getDatasetName : Get the name of a dataset based on its id in the target or base sandbox
* extending capability of schema synchronization in `Synchronizer` class to support schema with hidden fields.\
Patch:
* Supporting update of segment via `synchronizer` module.
* improving parameterize support for template queries in `QueryService` module. 


## version 0.4.1
* extending support to export more elements from schemaManager, FieldGroupManager and DataTypeManager
  * Supporting Map capability for `addField` method
  * Support `minimum` and `maximum` for `integrer`
  * Supporting `minLength`, `maxLength`, `default` and `pattern` for `string`
  * Supporting the different options in synchronizer and in `importFieldGroupDefinition` and `importDataTypeDefinition` 
* establishing a `retry` parameter to try getting the Segments and Audiences a number of time if it returns empty.
  * Adding support for entityType for `getAudiences`
* Surfacing issue with `sandboxId` in an Error and in logs.\
Patch:
* Fixing the creation of descriptor for labels
* Upgrading capability of synchronizer to support deprecated fields\
* Fix some print statement left in the code
* Upgrading the extractArtefact method


## version 0.4.0
* removing the dependency to pyJWT and all references to JWT integration\
Patch:
* adapt to the change of the Data Hygiene API requirement.
* adding `getLinkedIdentities` in the Identity API
* adding `querySegmentPopulation` in the `InteractiveQueryService` instances
* fixing `getAudiences` method. 

## version 0.3.14
* adding the `deletion` module [documentation](./deletion.md)
* adding some parameters to make possible to create a HTTP Stream Flow for a dataset based on the `datasetId` [documentation](./flowservice.md#createflowstreaming)
* update the handling of responses for Access Control API
* adding `getEntityEvents` to the `customerprofile` module [documentation](./customerprofile.md)
* better handling of fieldgroup definition imported via `importFieldGroupDefinition`
* Update file name outputs used for `extractSandboxArtefacts` method
* adding `extractSandboxArtefact` method

## version 0.3.13
* adding `getWorkOrders` on the `hygiene` module
* enable to output pydantic data on managers. The `to_pydantic` method is now available.
  * building dependency with `datamodel-code-generator` module\
Patch:
* Fix pydantic references when using data type as array
* Fix `getAudiences` method that had a typo 
* Patch `copyFieldGroup` based on mdonke Fork to support customized OOTB field groups
* adding the `getUPSFlows`,`getUISFlows`, `getUPSFlow`,`getUISFlow`,`getUPSFlowRuns`,`getUISFlowRuns`. [see documentation](./flowservice.md#getUPSFlows)
* adding parameter for the OOTB artefacts from the `extractSandbox` method.
* changing the OOTB artefacts in their own folder for extractSandbox method and support in different classes (`Synchronizer`, `ClassManager`, `SchemaManager`, `FieldGroupManager`, `DataTypeManager`)   
* adding the `patchConnection` method in the `flowservice` module
* changing the output of `getConnection` to return the item directly.
* fixing the `params` setup for `interact` method in Edge module
* fixing reference to `getProfileSnapshotDatasets` due to API issue on AEP.
* adding a new method to download a resource URL directly to a file using CURL command in Python. (see [getResourceToFile](./catalog.md#getResourceToFile))
* adding the `getDatasetsInfos` in the `catalog` module
* adding the `getMergePolicyActiveOnEdge` in the `customerprofile` module
* better support of `datetime`, `pattern` and `enum` in pydantic
* adding several methods in `catalog` module regarding patch and put dataset
* fixing the `getParquetFilesToDataFrame` in `dataaccess` module


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
