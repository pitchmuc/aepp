# AEPP Command Line Interface (CLI)

The AEPP Command Line Interface (CLI) is a powerful tool that allows developers to interact with the Adobe Experience Platform directly from their terminal. This guide provides an overview of the CLI commands and how to use them effectively.

## Table of content

[Menu](#table-of-content)
- [Installation](#installation)
- [Initializing the CLI](#initializing-the-cli)
- [Available Commands](#available-commands)
  - [Configs](#configs)
  - [Schema Methods](#schema-methods)
  - [Dataset Methods](#dataset-methods)
  - [Audience Methods](#audience-methods)
  - [Flow Service](#flow-service)
  - [Deletion Methods](#deletion-methods)
  - [Identities methods](#identities-methods)
  - [Query Service Methods](#query-service-methods)
  - [Tools & Migration](#tools--migration)
  - [Knowledge Graph](#knowledge-graph)
  - [Other methods](#other-methods)


## Installation

This package can be accessible directly after installing the AEPP SDK. To install the SDK, follow the instructions in the [Getting Started Guide](./getting-started.md).\
I provide a guide to get started with the CLI, see the [getting started with the CLI section](./getting-started-cli.md).

## Initializing the CLI

To start using the CLI, you need to initialize it in your terminal. You can do this by running the following command:

```bash

python -m aepp.cli

```

At the start of your instantiation, you can provide optional parameters that would be used to directly connect to your Adobe Experience Platform instance. These parameters include:
* `--client-id` or `-cid` : Your Adobe I/O Client ID
* `--secret` or `-s` : Your Adobe I/O Client Secret
* `--org-id` or `-o` : Your Adobe I/O Organization ID
* `--sandbox` or `-sx` : Your Adobe I/O Sandbox name
* `--scopes` or `-sc` : Your Adobe I/O Scopes (comma-separated if multiple)
* `--region` or `-r` : The region of your Adobe Experience Platform instance (default is 'nld2'). Available regions are: "va7", "aus5", "can2", "ind2".
* `--config-file` or `-cf` : Path to a JSON configuration file containing connection parameters.
* `--command` or `-cmd` : Run a single CLI command non-interactively and exit immediately after. The value is a string containing the command name followed by its arguments, using the same syntax as the interactive prompt. This is useful for scripting or automation workflows.

### Non-interactive mode examples

The `-cmd` flag lets you connect to AEP and execute one command in a single call, without entering the interactive shell. The command string follows the exact same syntax as the interactive prompt.

```bash
# List all schemas in the prod sandbox, filtered by "client"
python -m aepp.cli -cf config_api.json -sx prod -cmd "get_schemas -f client"

# Export all datasets to CSV from the dev sandbox
python -m aepp.cli -cf config_api.json -sx dev -cmd "get_datasets"

# List all audiences filtered by name and save them
python -m aepp.cli -cf config_api.json -sx prod -cmd "get_audiences -f loyalty"

# Get all identities from a specific region
python -m aepp.cli -cf config_api.json -sx prod -cmd "get_identities -r va7"

# Export a specific schema as a CSV file
python -m aepp.cli -cf config_api.json -sx prod -cmd "get_schema_csv _tenant.schemas.abc123"
```

> **Note:** Any command available in the interactive shell can be used with `-cmd`. The arguments accepted by each command are the same as described in the [Available Commands](#available-commands) section below.


## Available Commands
The CLI provides a variety of commands to manage and interact with Adobe Experience Platform resources. Below is a list of available commands:

### Configs

#### create_config_file
Generate a JSON configuration file with your connection parameters for future use.\
Arguments:
* `-fn`, `--file_name` : File name for your config file (default: "aepp_config.json")


#### config
In case you did not provide the connection parameters at the start of the CLI, you can use this command to set up your connection configuration.
Parameters:
* `--client-id` or `-cid` : Your Adobe I/O Client ID
* `--secret` or `-s` : Your Adobe I/O Client Secret
* `--org-id` or `-o` : Your Adobe I/O Organization ID
* `--sandbox` or `-sx` : Your Adobe I/O Sandbox name
* `--scopes` or `-sc` : Your Adobe I/O Scopes (comma-separated if multiple)
* `--region` or `-r` : The region of your Adobe Experience Platform instance (default is 'nld2'). Available regions are: "va7", "aus5", "can2", "ind2".
* `--config-file` or `-cf` : Path to a JSON configuration file containing connection parameters.

#### change_sandbox
Switch the active sandbox session after initial configuration.\
Arguments:
* `sandbox` : The name of the sandbox to switch to.

The command first tries to validate the sandbox name against the list returned by the Sandboxes API. If that API is not accessible with your current credentials (e.g. your service account lacks the "Manage Sandboxes" permission), a yellow warning is shown and the switch proceeds unvalidated instead of being blocked.

#### get_sandboxes
List all sandboxes available in the current organization.

#### create_sandbox
Create a new sandbox in the current organization.\
Arguments:
* `-n`, `--name` : Name for the new sandbox. It must be unique and not contain spaces (use - instead of space).
* `-t`, `--type` : Type for the new sandbox. Possible values: [development, production].
* `-tl`, `--title` : Title for the new sandbox.


### Schema Methods

#### get_schemas
List all schemas in the current sandbox.\
Arguments:
* `-sv`, `--save` : Save the list of schemas to a CSV file.
* `-f`, `--filter`: filter the schema returned based on title and on lower case and partial match of that string

#### get_classes
List all classes in the current sandbox.\
Arguments:
* `-sv`, `--save` : Save the list of classes to a CSV file.
* `-f`, `--filter`: filter the classes returned based on title and on lower case and partial match of that string
  
#### get_ups_schemas
List all schemas enabled for Unified Profile in the current sandbox.\
Arguments:
* `-sv`, `--save` : Save the list of enabled schemas to a CSV file.

#### get_profile_schemas
Get schemas specifically filtered for the Profile class (https://ns.adobe.com/xdm/context/profile).\

#### get_event_schemas
Get schemas specifically filtered for the Experience Event class (https://ns.adobe.com/xdm/context/experienceevent).\
Arguments:
* `-sv`, `--save` : Save the list of event schemas to a CSV file.

#### get_schema_xdm
Get the raw JSON (XDM) definition of a specific schema.\
Arguments:
* `schema` : The Schema Title, $id, or alt:Id.
* `-f`, `--full` : Boolean. Get full schema details (default: False, possible values: True, False).

#### get_schema_csv
Get the structure of a specific schema exported as a CSV file.\
Arguments:
* `schema` : The Schema $id or alt:Id.
* `-f`, `--full` : Boolean. Get full schema details (default: False, possible values: True, False).

#### get_schema_json
Get the JSON representation of a specific schema manager object.\
Arguments:
* `schema` : The Schema $id or alt:Id.

#### enable_schema_for_ups
Enable a specific schema for the Unified Profile Service.\
Arguments:
* `schema_id` : The Schema ID to enable.

#### get_union_profile_json
Export the current Profile Union Schema to a JSON file.

#### get_union_profile_csv
Export the current Profile Union Schema to a CSV file.\
Arguments:
* `-f`, `--full` : Boolean. Get full schema information (default: False, possible values: True, False).

#### get_union_event_json
Export the current Experience Event Union Schema to a JSON file.

#### get_union_event_csv
Export the current Experience Event Union Schema to a CSV file.\
Arguments:
* `-f`, `--full` : Boolean. Get full schema information (default: False, possible values: True, False).

#### get_fieldgroups
List all field groups in the current sandbox.\
Arguments:
* `-ootb`, `--ootb` : Boolean. Include out-of-the-box field groups (default: False, possible values: True, False).
* `-f`, `--filter` : Filter the field groups based on the string.
* `-sv`, `--save` : Save the list of field groups to a CSV file.

#### get_ups_fieldgroups
List all field groups enabled for Profile in the current sandbox.\
Arguments:
* `-sv`, `--save` : Save the list of enabled field groups to a CSV file.

#### get_fieldgroup_json
Get the JSON definition of a specific field group.\
Arguments:
* `fieldgroup` : Field Group Name, $id, or alt:Id.

#### get_fieldgroup_csv
Get the structure of a specific field group exported as a CSV file.\
Arguments:
* `fieldgroup` : Field Group Name, $id, or alt:Id.
* `-f`, `--full` : Boolean. Get full field group details (default: False, possible values: True, False).

#### get_fieldgroup_xdm
Get the XDM definition of a specific field group exported as a JSON file.\
Arguments:
* `fieldgroup` : Field Group Name, $id, or alt:Id.

#### delete_fieldgroup
Delete a field group from the current sandbox.\
Arguments:
* `fieldgroup` : Field Group Name, $id, or alt:Id to delete.

#### upload_fieldgroup_definition_csv
Create or Update a field group using a CSV definition file.\
Arguments:
* `csv_path` : Path to the CSV file.
* `-ts`, `--test` : Boolean. Test the upload locally without sending to AEP (default: False, possible values: True, False).

#### create_fieldgroup_definition_template
Create a CSV template for defining a field group.\
Arguments:
* `-tl`, `--title` : Name of the field group (default: "MyFieldGroup").
* `-d`, `--description` : Description of the field group (default: "").
* `-fn`, `--file_name` : Name of the output CSV file (default: None).

#### upload_fieldgroup_definition_xdm
Create or Update a field group using a JSON XDM file.\
Arguments:
* `xdm_path` : Path to the JSON file.
* `-ts`, `--test` : Boolean. Test the upload locally without sending to AEP (default: False, possible values: True, False).


#### upload_fieldgroup_definition_xlsx
Create or Update a field group using an Excel XLSX file.\
Arguments:
* `xlsx_path` : Path to the XLSX file.
* `-sh`, `--sheet` : Name of the sheet in the XLSX file to use (default: "Sheet1").
* `-ts`, `--test` : Boolean. Test the upload locally without sending to AEP (default: False, possible values: True, False).


#### get_descriptors
List all descriptors in the current sandbox.\
Arguments:
* `-sv`, `--save` : Save the list of descriptors to a CSV file.

#### get_descriptor
Display the JSON definition of a specific descriptor in the current sandbox.\
Arguments:
* `descriptor_id` : Required descriptor ID (`@id`).
* `-sv`, `--save` : Also save the definition to `descriptor_<descriptor_id>.json`.

#### get_datatypes
List all data types in the current sandbox.\

#### get_datatype_csv
Export a specific Data Type structure to a CSV file.\
Arguments:
* `datatype` : Data Type Name, $id, or alt:Id.
* `-f`, `--full` : Boolean. Get full details (default: False, possible values: True, False).

#### get_datatype_json
Export a specific Data Type definition to a JSON file.\
Arguments:
* `datatype` : Data Type Name, $id, or alt:Id.

#### get_datatype_xdm
Export a specific Data Type XDM definition to a JSON file.\
Arguments:
* `datatype` : Data Type Name, $id, or alt:Id.

#### create_b2b_artifacts
Create the B2B identities and schema and relationship for the current sandbox.\
combination of `createB2BIdentities` in the `identity` module and `createB2Bschemas` in `schema` module. 

### Dataset Methods

#### get_datasets
List all datasets in the current sandbox.\
Also save the result in a CSV file.\
* `-f`, `--filter`: filter the dataset returned based name and on lower case and partial match of that string

#### get_dataset
Display a single dataset's JSON definition and save it to `dataset_<dataset_id>.json`.\
Arguments:
* `dataset` : Required Dataset ID or exact, case-sensitive Dataset Name. Quote names containing spaces.

Example:
```text
prod> get_dataset "Customer events"
```

#### get_datasets_infos
List all datasets with detailed storage and row count statistics.

#### do_get_datasets_tableNames
Get the table names associated with dataset names and ID.
Arguments:
* `-f`, `--filter`: filter the dataset returned based name and on lower case and partial match of that string

#### get_observable_schema_json
Retrieve the observable schema JSON for a specific dataset.\
Arguments:
* `dataset` : The Dataset ID or Name.

#### get_observable_schema_csv
Retrieve the observable schema CSV for a specific dataset.\
Arguments:
* `dataset` : The Dataset ID or Name.

#### get_snapshot_datasets
List profile, account and account-person snapshot datasets in the current sandbox, including merge-policy metadata. The command uses [`Catalog.getProfileSnapshotDatasets`](./catalog.md#getprofilesnapshotdatasets) with `explicitMergePolicy=True` and `flatten=True`.\
Arguments:
* `-d`, `--defaultOnly` : Optional boolean, default `False`. Request default-merge-policy snapshots. Passing the flag alone sets it to `True`; an explicit `True` or `False` is also accepted, case-insensitively. See the Catalog documentation for the current handling of unknown merge policies.

The console table includes:
* Dataset ID
* Query Service table name
* Merge policy name and ID
* Default policy indicator
* Data Lake row count from `extensions.adobe_lakeHouse.metrics.rowCount`, or `N/A` when unavailable

Dataset records are exported to `<sandbox>_snapshot_datasets.csv`, including a top-level `id` field. Nested metadata remains nested in the records passed to the CSV export.

Examples:

```text
dev> get_snapshot_datasets
dev> get_snapshot_datasets --defaultOnly
dev> get_snapshot_datasets --defaultOnly True
dev> get_snapshot_datasets --defaultOnly=False
dev> get_snapshot_datasets -d False
```

Invalid boolean values are rejected before any API request or export. The existing boolean converter also accepts `yes`/`no`, `t`/`f`, `y`/`n` and `1`/`0`.

The CLI's merge-policy ID display assumes each snapshot has a `mergePolicyId` entry in its `unifiedProfile` tags. For snapshots without this metadata, use the [Python Catalog examples](./catalog.md#getprofilesnapshotdatasets).

#### get_dataset_expiration
Get the TTL (Time To Live) / `rowExpiration` setting for a dataset. ONLY WORKS ON Experience Event Datasets.\
Arguments:
* `dataset` : The Dataset ID or Name.

#### set_dataset_expiration
Set the TTL (Time To Live) / `rowExpiration` setting for a dataset. ONLY WORKS ON Experience Event Datasets.\
Arguments:
* `dataset` : The Dataset ID or Name.
* `-t`, `--ttl` : TTL value in days.

#### createDataset
Create a new dataset.\
Arguments:
* `dataset_name` : The name for the new dataset.
* `schema_id` : The Schema ID to associate with the dataset.


#### enable_dataset_for_ups
Enable a specific dataset for the Unified Profile Service.\
Arguments:
* `dataset` : The Dataset ID or Name.

### Audience Methods

#### get_audiences
List all audiences in the current sandbox.
If the `getAudiences` method fails, it will fallback to `getSegments` method, which might not include external audiences.\
The result will be saved in a CSV with more information than what is being displayed in the terminal. 
Arguments:
* `-f`, `--filter`: filter the audience returned based name and on lower case and partial match of that string

The results displayed in the Terminal will have the following columns: 
- ID : Audience ID
- Name : Audience Name
- Evaluation : Evaluation Method, Batch, Streaming or Edge
- Total Profiles : The total profile of that audience if available 
- In Flow : If the audience has been shared (`True` or `False`)
- Active in Flow : If the audience expiration date for actively being shared is below today (`True` or `False`)

#### create_audiences_job
Create a job for audience segmentation. Only 50 jobs available per year for production sandboxes.
Arguments:
* `audience_ids` : list of audience IDs such as `"audienceId1"` `"audienceId2"` `"audienceId3"`

#### flexible_audience_evaluation
Trigger an on-demand evaluation job for one or more specific audiences, outside of the regular batch schedule.
This is useful when you need to refresh audience membership immediately without waiting for the next scheduled batch run.\
Arguments:
* `audience_ids` : One or more audience IDs to evaluate. Pass them space-separated, e.g. `"audienceId1"` `"audienceId2"`.

Example:
```bash
# Evaluate a single audience
flexible_audience_evaluation "a1b2c3d4-0000-0000-0000-111111111111"

# Evaluate multiple audiences at once
flexible_audience_evaluation "a1b2c3d4-0000-0000-0000-111111111111" "e5f6a7b8-0000-0000-0000-222222222222"

# Non-interactive mode
python -m aepp.cli -cf config_api.json -sx prod -cmd "flexible_audience_evaluation \"a1b2c3d4-0000-0000-0000-111111111111\""
```

#### get_batch_evaluation
Retrieve the current batch segmentation job definition for the sandbox, including its cron schedule and status.\
No arguments.

#### update_batch_evaluation_time
Update the cron schedule that controls when the daily batch segmentation job runs for the current sandbox.
The schedule uses the standard six-field cron format: `seconds minutes hours day-of-month month day-of-week`.\
Arguments:
* `schedule` : The cron expression to apply. Example: `"0 0 1 * * ?"` runs the job daily at 01:00 UTC.

Example:
```bash
# Run batch segmentation daily at 01:00 UTC
update_batch_evaluation_time "0 0 1 * * ?"

# Run batch segmentation daily at 03:30 UTC
update_batch_evaluation_time "0 30 3 * * ?"

# Non-interactive mode
python -m aepp.cli -cf config_api.json -sx prod -cmd "update_batch_evaluation_time \"0 0 1 * * ?\""
```

##### extract_audience_paths
Get the list of paths used in audience definitions.\
Arguments:
* `audience` : Audience ID or audience name to get paths for.
* `-r`, `--recursive` : Boolean. Get paths recursively from segment references. Default False. Possible values: True, False.

##### extract_audience_ref
Get the list of audience references used in audience definitions.\
Arguments:
* `audience` : Audience ID or audience name to get references for.

### Flow Service

#### create_dataset_http_source
Create an HTTP streaming endpoint for a specific dataset.\
Arguments:
* `dataset` : Name or ID of the Dataset.

#### get_DLZ_credential
Get Data Lake Zone credentials for the current sandbox.\
Arguments:
* `type` : (Optional) Credential type: 'user_drop_zone' (default) or 'dlz_destination'.

#### get_flows
List flows in the sandbox. Supports filtering by source/destination and time. Default last 24h.\
Arguments:
* `-i`, `--internal_flows` : Include internal flows (default: False).
* `-t`, `--type` : Filter by flow type (source, destination, internal, all).
* `-adv`, `--advanced` : Fetch run metrics (success/fail rates) (default: False).
* `-ao`, `--active_only` : List only flows active in the time period (default: True).
* `-mn`, `--minutes` : Lookback window in minutes (default: 0).
* `-H`, `--hours` : Lookback window in hours (default: 0).
* `-d`, `--days` : Lookback window in days (default: 0).

#### get_flow_errors
Export failed run details for a specific flow to a JSON file Default is last 24h.\
Arguments:
* `flow_id` : The Flow ID.
* `-mn`, `--minutes` : Lookback window in minutes.
* `-H`, `--hours` : Lookback window in hours.
* `-d`, `--days` : Lookback window in days (default: 0).

### Deletion Methods

These commands wrap the [`deletion`](./deletion.md) module to let you remove artifacts directly from the sandbox you are connected to.\
Every command resolves the artifact by name or ID, prints a warning panel describing exactly what will be impacted (and, when `--associated_artifacts` is used, a `Summary` line totaling every artifact that will be deleted across the full cascade), and requires you to type the artifact's name back to confirm before anything is deleted. Pass `-y true` to skip the confirmation prompt (useful for scripting).\
**These operations are irreversible.**

#### delete_dataset
Delete a dataset from the current sandbox.\
Arguments:
* `dataset` : Dataset name or ID to delete.
* `-a`, `--associated_artifacts` : Boolean. Also delete the associated dataflows and schema (which itself cascades to that schema's field groups and data types). Default False.
* `-y`, `--yes` : Boolean. Skip the confirmation prompt. Default False.

#### delete_schema
Delete a schema from the current sandbox.\
Arguments:
* `schema` : Schema title, `$id`, or `alt:Id` to delete.
* `-a`, `--associated_artifacts` : Boolean. Also delete the field groups and data types used by this schema. Default False.
* `-y`, `--yes` : Boolean. Skip the confirmation prompt. Default False.

#### delete_dataflow
Delete a dataflow from the current sandbox.\
Arguments:
* `flow` : Dataflow name or ID to delete.
* `-a`, `--associated_artifacts` : Boolean. Also delete the associated source and target connections. Default False.
* `-y`, `--yes` : Boolean. Skip the confirmation prompt. Default False.

#### delete_audience
Delete an audience/segment from the current sandbox.\
If the audience is activated to any destination, it is first removed from those destination flows (shown in an "Impacted Destination Flows" table) before being deleted.\
Arguments:
* `audience` : Audience name or ID to delete.
* `-w`, `--waittime` : Seconds to wait for destination flow updates to propagate before deleting. Default 30.
* `-y`, `--yes` : Boolean. Skip the confirmation prompt. Default False.

Example:
```bash
# Delete a dataset only (leave its schema and dataflows untouched)
delete_dataset "my_dataset_name"

# Delete a dataset and cascade to its dataflows and schema
delete_dataset "my_dataset_name" -a true

# Delete a schema and its field groups/data types without being prompted
delete_schema "_tenant.schemas.abc123" -a true -y true

# Non-interactive mode
python -m aepp.cli -cf config_api.json -sx dev -cmd "delete_audience \"my_audience_name\" -y true"
```

### Identities Methods

#### get_identities
List all identities in the current sandbox.\
Arguments:
* `-r`, `--region` : Region code (e.g., 'ndl2', 'va7', 'aus5'. Default: 'ndl2').
* `-co`, `--custom_only` : Boolean. List only custom namespaces (default: False, possible values: True, False).

#### create_identity
Create a new identity namespace.\
Arguments:
* `-c`,`--code` : Code for the new identity namespace (e.g., crmId, uid)
* `-n`,`--name` : Display name for the new identity namespace
* `-t`,`--type` : Type for the new identity namespace. Possible Values: COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE or PHONE
* `-d`,`--description` : Description for the new identity namespace

### Query Service Methods

All Query Service commands require an active sandbox connection. Run `help <command>` for a summary or `<command> -h` for its arguments.

#### get_queries
Retrieve up to 1000 queries from the last 24 hours (configurable), keep queries from the Query Service UI and Generic PostgreSQL clients, display the first 10, and export them to `<sandbox>_queries.csv`.\
Arguments:
* `-ds`, `--dataset` : Filter by Dataset ID.
* `-st`, `--state` : Filter by API state: `SUBMITTED`, `IN_PROGRESS`, `SUCCESS`, `FAILED`, `KILLED`, or `TIMEOUT` (case-insensitive). Aliases `running`, `completed`, and `failed` are also accepted.
* `-mn`, `--minutes` : Non-negative lookback window in minutes.
* `-H`, `--hours` : Non-negative lookback window in hours.
* `-d`, `--days` : Non-negative lookback window in days.

The three lookback options are added together. If all are zero or omitted, the lookback is 24 hours. Time filters use UTC.

#### get_query
Display a query's metadata, SQL and execution state as JSON. This does not execute the query or retrieve its result rows.\
Arguments:
* `query_id` : Required ID of the query to retrieve.

#### get_query_templates
List all query templates in the current sandbox, following pagination. Displays each template's ID, name and creation date.

#### get_query_template
Display a query template as JSON and save it to `query_template_<template_id>.json`.\
Arguments:
* `template_id` : Required ID of the query template to retrieve.

#### get_queries_scheduled
List all scheduled queries in the current sandbox, following pagination, and save their full definitions to `queries_scheduled_<sandbox>.json`.

Displays the schedule ID, query name, start date, cron expression and activation state. The Enabled column shows `True` for `ENABLED`, `False` for `DISABLED`, and the state name for a transition such as `REGISTERING`.

#### create_query_scheduled
Create a scheduled query using either SQL or an existing query template. The query runs against `<current_sandbox>:all`, not a hard-coded production database.\
Arguments:
* `-q`, `--query` : SQL string. Required unless `--template_id` is provided.
* `-t`, `--template_id` : Query template ID. Required unless `--query` is provided. The two options are mutually exclusive.
* `-sch`, `--schedule` : Required five-field cron expression, such as `"0 */2 * * *"`, or a shorthand: `@once`, `@hourly`, `@daily`, `@weekly`, `@monthly`, or `@yearly`.
* `-sd`, `--start_date` : Required ISO 8601 start timestamp with a timezone, such as `"2026-11-01T00:00:00Z"`.
* `-ed`, `--end_date` : Optional ISO 8601 end timestamp with a timezone. Must be later than the start date.
* `-n`, `--name` : Optional query name.
* `-d`, `--description` : Optional query description.
* `-a`, `--arguments` : Optional comma-separated SQL/template parameters in `key1=value1,key2=value2` format. Values may contain `=`; commas separate parameters.

Dates are normalized to UTC before submission. Adjust the example dates before use. Adobe validates the cron expression; scheduled runs must not be more frequent than once per hour. For recurring schedules, omitting an end date depends on your organization's support for schedules without an end date.

Adobe accepts creation asynchronously and returns the schedule ID and initial state, normally `REGISTERING`. It automatically transitions to `ENABLED` after registration. There is no `--enabled` flag; use the commands below to change an existing schedule after registration.

Examples:
```text
dev> create_query_scheduled -n "Daily accounts" -q "SELECT * FROM accounts" -sch "@daily" -sd "2026-11-01T00:00:00Z" -ed "2026-12-01T00:00:00Z"
dev> create_query_scheduled -n "Template run" -t template-id -a "table=accounts,minimum=10" -sch "0 */2 * * *" -sd "2026-11-01T00:00:00Z" -ed "2026-12-01T00:00:00Z"
```

#### enable_query_scheduled
Request enabling an existing query schedule.\
Arguments:
* `schedule_id` : Required schedule ID.

#### disable_query_scheduled
Request disabling an existing query schedule.\
Arguments:
* `schedule_id` : Required schedule ID.

Both commands report that Adobe accepted the request, not that the state change has finished. Use `get_queries_scheduled` to inspect the resulting state. Adobe can reject changes while a schedule is still registering or already in the requested state.

See the [Query Service module documentation](./queryservice.md#query-service-cli) and Adobe's [Schedules endpoint reference](https://experienceleague.adobe.com/en/docs/experience-platform/query/api/scheduled-queries) for API details.

#### query
Execute a raw SQL query against the Data Lake, save the results as CSV and display a sample.\
Arguments:
* `sql_query` : The SQL string to execute.
* `-fn` : Optional output filename. The `.csv` extension is added if omitted. Defaults to `query_result_<timestamp>.csv`.

After the query results have been retrieved and exported, the command closes its `InteractiveQuery2` database connection before displaying the sample. For Python usage, see [`close`](./queryservice.md#close).

#### query_segment_population
Query the population of specific segment(s).\
Arguments:
* `segment_id` : Segment ID(s) to query population for. It can be multiple segment | audience IDs separated by spaces.
* `-ef`, `--extra_fields` : Extra fields to include in the query, comma-separated.
* `-c`, `--count_only` : If you want to get only the count of the segment population. (default: `False`). If set to `True`, the query will return only the count of profiles in the segment(s) instead of the full list.
* `-fn`, `--filename` : If you want to save it to a specific filename.

Example:
```bash
prod> query_segment_population "segmentId1" "segmentId2" -ef "email,_tenant.fieldname" -fn "segment_population.csv"
```

### Profile API 

#### get_profile_attributes
Retrieve the profile attributes for a specific user, saving it in a JSON file.\
Arguments:
* `-uid`,`--user_id` : User ID of the user.
* `-ns`,`--namespace` : Namespace of the user.

#### get_account_attributes
Retrieve the account attributes for a specific user, saving it in a JSON file.\
Arguments:
* `-uid`,`--user_id` : User ID of the user.
* `-ns`,`--namespace` : Namespace of the user (default: `b2b_account`).

#### get_profile_events
Retrieve all UPS events for a specific user, saving it in a JSON file.\
Arguments:
* `-uid`,`--user_id` : User ID of the user.
* `-ns`,`--namespace` : Namespace of the user.
* `-l`, `--limit` : Number of events returned by the response (max 5000, default 1000) 

The output in the terminal will give you an aggregated view of these different informations: 
- "eventTypes": the different types and their numbers
- "primaryIdentities": the different primary identities used during the requests
- "totalEvents": the total events attached to that profile
- "firstEventTimestamp": The first event timestamp recorded of that profile
- "lastEventTimestamp": The last event timestamp recorded of that profile

#### get_merge_policies
Retrieve all merge policies in the current sandbox.\
Save the list of merge policies in a JSON file. 


### Hygiene API

#### get_hygiene_works
List all hygiene works in the current sandbox and save it in a JSON file.\
Arguments:
* `-f`, `--filter`: filter the works returned based name and on lower case and partial match of that string
* `-d`, `--days`: filter the works by creation date based on a lookback window in days (default: 0, no filter)

#### get_hygiene_work
Get details of a specific hygiene work and save it in a JSON file.\
Arguments:
* `workOrderId` : The Hygiene Work ID.


### Tools & Migration

#### extract_artifacts
Bulk extract sandbox components to a local folder.\
Arguments:
* `-lf`, `--localfolder` : Destination folder (default: ./extractions).
* `-f`, `--filters`: filter the artifacts to extract based on name and on lower case and partial match of that string

#### extract_artifact
Extract a single specific artifact.\
Arguments:
* `artifact` : Name or ID of the artifact.
* `-at`, `--artifactType` : Type (e.g., schema, dataset, etc.).
* `-lf`, `--localfolder` : Destination folder.


#### sync
Synchronize or copy artifacts between sandboxes.\
Arguments:
* `artifact` : Name or ID of the component to sync.
* `-at`, `--artifactType` : Type of component. Can be from this list: "schema","fieldgroup","datatype","descriptor","dataset","identity","mergepolicy","audience"
* `-t`, `--targets` : list of target sandboxes.
* `-lf`, `--localfolder` : Local staging folders.
* `-b`, `--baseSandbox` : The source sandbox name.
* `-v`, `--verbose` : Enable verbose logging (default: True).


### Knowledge Graph

#### build_graph
Build a graph of all artifacts in the current sandbox and save it in memory for the session.\
Arguments:
* `-hd`, `--has_data` : Boolean. Retrieve information for all schemas and datasets. Default True.
* `-d`, `--detail` : Boolean. Retrieve the path information for the schema and field groups. Default True.
* `-e`, `--enabled` : Boolean. Build the knowledge graph based on enabled datasets only. Default False.
* `-ex`, `--export` : Boolean. Export the graph to a turtle file (named `<sandbox>.ttl`) once built. Default False.
* `-v`, `--verbose` : Boolean. If you want to see the progress of the graph building. Default `False`.

#### export_graph
Export the previously built graph (via `build_graph`) to a turtle file.\
Arguments:
* `filename` : Filename to export the graph to (e.g., `graph.ttl`).

#### load_graph
Load a graph from a turtle file into memory for the session.\
Arguments:
* `filename` : Filename to load the graph from (e.g., `graph.ttl`).

#### add_path_attributes
Add path attributes to the previously built graph. Requires a graph to have been built (`build_graph`) or loaded (`load_graph`) first.\
Arguments:
* `-p`, `--path` : Path to add the attributes to.
* `-a`, `--attributes` : Attributes to add, in the form `predicate1=value1 predicate2=value2 ...`.

#### add_schema_attributes
Add schema attributes to the previously built graph. Requires a graph to have been built (`build_graph`) or loaded (`load_graph`) first.\
Arguments:
* `-s`, `--schema` : Schema `$id` to add the attributes to.
* `-a`, `--attributes` : Attributes to add, in the form `predicate1=value1 predicate2=value2 ...`.

#### add_dataset_attributes
Add dataset attributes to the previously built graph. Requires a graph to have been built (`build_graph`) or loaded (`load_graph`) first.\
Arguments:
* `-d`, `--dataset` : Dataset ID to add the attributes to.
* `-a`, `--attributes` : Attributes to add, in the form `predicate1=value1 predicate2=value2 ...`.

### Other methods

#### get_tags
Get the tag associated with your organization.

#### get_profile_attributes_lineage
Get usage details for all Profile paths.\
No arguments.\
**This will take a long time.**

#### get_event_attributes_lineage
Get the information details for all Experience Event paths.\
No arguments. 
**This will take a long time.**

#### get_profile_attribute_lineage
Get usage details for a specific Profile path.\
Arguments:
* `path` : The Profile path to analyze.

#### get_event_attribute_lineage
Get usage details for a specific Experience Event path.\
Arguments:
* `path` : The Experience Event path to analyze.

#### exit
Exit the CLI.

#### help
Display help information about available commands.