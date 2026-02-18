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
  - [Flow Service](#flow-service)
  - [Identities methods](#identities-methods)
  - [Query Service Methods](#query-service-methods)
  - [Tools & Migration](#tools--migration)
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
* `-f`, `--full` : Boolean. Get full details (default: False, possible values: True, False).

### Dataset Methods

#### get_datasets
List all datasets in the current sandbox (Basic info).

#### get_datasets_infos
List all datasets with detailed storage and row count statistics.

#### do_get_datasets_tableNames
Get the table names associated with dataset names and ID.\


#### get_observable_schema_json
Retrieve the observable schema JSON for a specific dataset.\
Arguments:
* `dataset` : The Dataset ID or Name.

#### get_observable_schema_csv
Retrieve the observable schema CSV for a specific dataset.\
Arguments:
* `dataset` : The Dataset ID or Name.

#### get_snapshot_datasets
Get the list of snapshot datasets in the current sandbox.\

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

#### get_queries
List top 1000 queries from the last 24 hours (configurable).\
Arguments:
* `-ds`, `--dataset` : Filter by Dataset ID.
* `-st`, `--state` : Filter by state (e.g., running, completed, failed).
* `-mn`, `--minutes` : Lookback window in minutes.
* `-H`, `--hours` : Lookback window in hours.
* `-d`, `--days` : Lookback window in days.

#### query
Execute a raw SQL query against the Data Lake.\
Arguments:
* `sql_query` : The SQL string to execute.
* `-sv`, `--save` : Path to save the query results as a CSV file.


### Profile API 

#### get_profile_attributes
Retrieve the profile attributes for a specific user, saving it in a JSON file.\
Arguments:
* `-uid`,`--user_id` : User ID of the user.
* `-ns`,`--namespace` : Namespace of the user.

#### get_profile_events
Retrieve all UPS events for a specific user, saving it in a JSON file.\
Arguments:
* `-uid`,`--user_id` : User ID of the user.
* `-ns`,`--namespace` : Namespace of the user.


### Tools & Migration

#### extract_artifacts
Bulk extract sandbox components to a local folder.\
Arguments:
* `-lf`, `--localfolder` : Destination folder (default: ./extractions).
* `-rg`, `--region` : Source region (default: 'ndl2').

#### extract_artifact
Extract a single specific artifact.\
Arguments:
* `artifact` : Name or ID of the artifact.
* `-at`, `--artifactType` : Type (e.g., schema, dataset, etc.).
* `-lf`, `--localfolder` : Destination folder.
* `-rg`, `--region` : Source region.


#### sync
Synchronize or copy artifacts between sandboxes.\
Arguments:
* `artifact` : Name or ID of the component to sync.
* `-at`, `--artifactType` : Type of component.
* `-t`, `--targets` : list of target sandboxes.
* `-lf`, `--localfolder` : Local staging folders.
* `-b`, `--baseSandbox` : The source sandbox name.
* `-rg`, `--region` : Region.
* `-v`, `--verbose` : Enable verbose logging (default: True).


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