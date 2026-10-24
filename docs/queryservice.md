# QueryService module in aepp

This documentation will provide you some explanation on how to use the queryservice module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the Query Service API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/query-service/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu
- [QueryService module in aepp](#queryservice-module-in-aepp)
  - [Menu](#menu)
  - [Importing the module](#importing-the-module)
  - [Generating a QueryService instance](#generating-a-queryservice-instance)
    - [QueryService attributes](#queryservice-attributes)
    - [QueryService methods](#queryservice-methods)
      - [getResource](#getresource)
      - [connection](#connection)
      - [getQueries](#getqueries)
      - [createQuery](#createquery)
      - [postQueries](#postqueries)
      - [getQuery](#getquery)
      - [cancelQuery](#cancelquery)
      - [deleteQuery](#deletequery)
      - [getSchedules](#getschedules)
      - [getSchedule](#getschedule)
      - [getScheduleRuns](#getscheduleruns)
      - [getScheduleRun](#getschedulerun)
      - [createSchedule](#createschedule)
      - [deleteSchedule](#deleteschedule)
      - [disableSchedule](#disableschedule)
      - [enableSchedule](#enableschedule)
      - [updateSchedule](#updateschedule)
      - [getTemplates](#gettemplates)
      - [getTemplate](#gettemplate)
      - [deleteTemplate](#deletetemplate)
      - [createQueryTemplate](#createquerytemplate)
      - [getDatasetStatistics](#getdatasetstatistics)
      - [getAlertSubscriptions](#getalertsubscriptions)
      - [createAlertSubscription](#createalertsubscription)
      - [deleteAlertSubscription](#deletealertsubscription)
      - [getAlertSubscriptionsTypeId](#getalertsubscriptionstypeid)
      - [patchAlert](#patchalert)
      - [getUserAlerts](#getuseralerts)
      - [createAcceleratedQuery](#createacceleratedquery)
    - [Query Service use-cases](#query-service-use-cases)
    - [Query Service tips](#query-service-tips)
  - [Query Service CLI](#query-service-cli)
  - [InteractiveQuery and InteractiveQuery2](#interactivequery-and-interactivequery2)
    - [Differences between InteractiveQuery and InteractiveQuery2](#differences-between-interactivequery-and-interactivequery2)
      - [Instantiation of interactive query](#instantiation-of-interactive-query)
    - [Methods of Interactive Query](#methods-of-interactive-query)
      - [addConfig](#addconfig)
      - [close](#close)
      - [query](#query)
      - [queryHistoryMeta](#queryhistorymeta)
      - [queryProfilesTrend](#queryprofilestrend)
      - [queryNamespacesDistribution](#querynamespacesdistribution)
      - [queryNamespacesTrend](#querynamespacestrend)
      - [querySegmentPopulationTrend](#querysegmentpopulationtrend)
      - [queryAudiencePopulationTrend](#queryaudiencepopulationtrend)
      - [transformToDataFrame](#transformtodataframe)
      - [querySegmentPopulation](#querysegmentpopulation)
      - [queryAudiencePopulation](#queryaudiencepopulation)
      - [queryIdentity](#queryidentity)
    - [Tips for Interactive Query](#tips-for-interactive-query)

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `queryservice` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')

from aepp import queryservice
```

The queryservice module provide 2 classes that you can use for interacting with the Query Service API.\
The following documentation will provide you with more information on these.

## Generating a QueryService instance

The `QueryService` class is one the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling `QueryService()` from the `queryservice` module.

Following the previous method described above, you can realize this:

```python
qs = queryservice.QueryService(config=prod)
```

2 parameters are possible for the instantiation of the class:
* config : OPTIONAL : mostly used to pass a ConnectObject instance that is linked to one sandbox. 
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : A logging object that can be passed for debuging or logging elements, see [logging documentation](./logging.md)

### QueryService attributes

The QueryService instance will provide several attributes.
* sandbox : provide which sandbox is currently being used
* header : provide the default header which is used for the requests.
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods.

There are 3 additional attributes that you can use to help you create the dictionary data for your `createQuery` and `createSchedule` methods.\
The attributes are:\
* `QUERYSAMPLE`: for createQuery method
```JSON
{
        "dbName": "string",
        "sql": "SELECT $key from $key1 where $key > $key2;",
        "queryParameters": {
            "key": "value",
            "key1": "value1",
            "key2": "value2"
        },
        "templateId": "123",
        "name": "string",
        "description": "powered by aepp",
        "insertIntoParameters": {
            "datasetName": "string"
        },
        "ctasParameters": {
            "datasetName": "myDatasetName",
            "description": "powered by aepp",
            "targetSchemaTitle": "mySchemaName"
        }
    }
```

* `SCHEDULESAMPLE`: for createSchedule
```JSON
"query": {
            "dbName": "string",
            "sql": "SELECT $key from $key1 where $key > $key2;",
            "queryParameters": {
                "key": "value",
                "key1": "value1",
                "key2": "value2"
            },
            "templateId": "123",
            "name": "string",
            "description": "string",
            "insertIntoParameters": {
                "datasetName": "string"
            },
            "ctasParameters": {
                "datasetName": "string",
                "description": "string",
                "targetSchemaTitle": "mySchemaName"
            }
        },
        "schedule": {
            "schedule": "string",
            "startDate": "string",
            "endDate": "string",
            "maxActiveRuns": 0
        }
    }
```
* `TEMPLATESAMPLE`: To create a template.
```python
{
        "sql": "SELECT $key from $key1 where $key > $key2;",
        "queryParameters": {"key": "value", "key1": "value1", "key2": "value2"},
        "name": "string",
    }
```


### QueryService methods

below are all the different methods that are available to you once you have instantiated the `QueryService` class.

`getQueries`, `getSchedules` and `getTemplates` return lists, follow pagination links, and return at most `n_results` items (default: 1000). Set `n_results="inf"` to retrieve all available items. Missing pagination links mean the last page; malformed collection responses and API errors raise `ValueError` rather than returning an empty result. Ordering and filter values are URL-encoded by the connector and should be passed without manually escaping them.

#### getResource
Template for requesting data with a GET method.\
Arguments:
* endpoint : REQUIRED : The URL to GET
* params: OPTIONAL : dictionary of the params to fetch
* format : OPTIONAL : Type of response returned. Possible values:
  * json : default
  * txt : text file
  * raw : a response object from the requests module

#### connection
Create a connection for interactive interface.\
The result can be used in the `InteractiveQuery` and `InteractiveQuery2` classes. 

example:

```python
conn = qs.connection()
iqs = queryservice.InteractiveQuery2(conn)
```

#### getQueries
Retrieve the queries from your organization.\
Arguments:
* orderby : OPTIONAL : possibility to order by "created" or "updated".
  prepend with "+" for ASC and "-" for DESC. Automatically URL-encoded.
* limit : OPTIONAL : number of of records to fetch per page. (default 1000)
* start : OPTIONAL : when to start (depending on your orderby)
* property : OPTIONAL : Comma-separated filters. List of properties that allow filtering with all operators:
  * "created"
  * "updated"
  * "state"
  * "id"\
  with following operators >, <, >=, <=, ==, !=, ~\
  "referenced_datasets", "scheduleId", "templateId", and "userId" can only be used with ==. Multiple datasets ID with "||"\
  "SQL" can only be used with ~ (WITHOUT COMMA)
* n_results : OPTIONAL : total number of results returned (default 1000, set to "inf" to retrieve everything)\
possible kwargs:
* excludeSoftDeleted: Whether to include any queries that have been soft deleted. Defaults to true.
* excludeHidden : Whether to include any queries that have been found to be not interesting, as they were not user driven. Examples include CURSOR definitions, FETCH, and Metadata queries. Defaults to true.
* isPrevLink : Field indicating if the URI is a previous link.


#### createQuery
Create a query.\
Arguments:
* data : OPTIONAL : If you want to pass the full query statement.
* name : REQUIRED : Name of the query
* dbname : REQUIRED : the dataset name (default prod:all)
* sql: REQUIRED : the SQL query as a string.
* queryParameters : OPTIONAL : in case you are using template, providing the paramter in a dictionary.
* insertIntoParameters : OPTIONAL : in case you want to insert the result to an existing dataset\
      example : 
      ```python
      {
          "datasetName": "string"
      }
      ```
* ctasParameters: OPTIONAL : in case you want to create a dataset out of that query, dictionary is required with "datasetName" and "description".\
  example : 
  ```python
  {
      "datasetName": "string",
      "description": "string",
      "targetSchemaTitle":"string"
      }
  ```
  targetSchemaTitle if you want to use a precreated schema.

#### postQueries 
createQuery original method.(See above for parameters)

#### getQuery
Request the query status by ID.\
Argument :
* queryid : REQUIRED : the query id to check


#### cancelQuery
Cancel a specific query based on its ID.\
Argument:
* queryId : REQUIRED : the query ID to cancel

#### deleteQuery
Delete a specific query based on its ID.\
Argument:
* queryId : REQUIRED : the query ID to delete

#### getSchedules
Retrieve a list of scheduled queries for the AEP instance.\
Arguments:
* n_results : OPTIONAL : Total number of scheduled queries retrieved. To get them all, use "inf"\
possibile kwargs:
* orderby : Field to order by, prefixed with + for ASC or - for DESC. Automatically URL-encoded.
* limit : number of record to fetch
* start : specific start (use with orderby)
* property : Comma-separated filters.\
  created ; ex : created>2017-04-05T13:30:00Z\
  templateId ; ex : templateId==123412354\
  userId ; ex : userId==12341235\

#### getSchedule
Get a details about a schedule query.\
Arguments:
* scheduleId : REQUIRED : the schedule id

#### getScheduleRuns
Get the different jobs ran for this schedule\
Arguments:
* scheduleId : REQUIRED : the schedule id

#### getScheduleRun
Get the different jobs ran for this schedule\
Arguments:
* scheduleId : REQUIRED : the schedule id
* runId : REQUIRED : the run ID you want to retrieve.

#### createSchedule
Create a scheduled query.\
Arguments:
* scheduleQuery: REQUIRED : a dictionary containing the query and the schedule.
* name : OPTIONAL : Name of the query
* dbname : OPTIONAL : the dataset name (default prod:all)
* sql: OPTIONAL : the SQL query as a string.
* templateId : OPTIONAL : The Template ID to be used
* queryParameters : OPTIONAL : in case you are using template, providing the paramter in a dictionary.
* insertIntoParameters : OPTIONAL : in case you want to insert the result into an existing dataset.
* ctasParameters: OPTIONAL : in case you want to create a dataset out of that query, dictionary is required with "datasetName" and "description".
* schedule : OPTIONAL : Dictionary giving the instruction to schedule the query.
* description : OPTION : Description of the schedule query

The `schedule` object must contain `schedule` (a cron expression or shorthand such as `@daily` or `@once`) and `startDate` (a UTC timestamp). `endDate` and `maxActiveRuns` are optional. Cron schedules must not run more frequently than once per hour; schedules without an end date depend on organization availability.

Creation is asynchronous: the response includes the schedule `id` and normally `state="REGISTERING"`. Adobe automatically changes the state to `ENABLED` after registration. The SDK's default `dbname` remains `prod:all`; pass the connected sandbox explicitly when scheduling outside production. The CLI does this automatically.

```python
scheduled = qs.createSchedule(
    name="Daily accounts",
    dbname=f"{qs.sandbox}:all",
    sql="SELECT * FROM accounts",
    schedule={
        "schedule": "@daily",
        "startDate": "2026-11-01T00:00:00.000Z",
        "endDate": "2026-12-01T00:00:00.000Z",
    },
)
schedule_id = scheduled["id"]
```

Adjust the example dates before use. See Adobe's [Schedules endpoint documentation](https://experienceleague.adobe.com/en/docs/experience-platform/query/api/scheduled-queries) for full requirements.

#### deleteSchedule
Delete a scheduled query.\
Arguments:
* scheduleId : REQUIRED : id of the schedule.

#### disableSchedule
Disable a scheduled query.\
Arguments:
* scheduleId : REQUIRED : id of the schedule.

#### enableSchedule
Enable a scheduled query.\
Arguments:
* scheduleId : REQUIRED : id of the schedule.

`enableSchedule` and `disableSchedule` send a PATCH body containing a `replace` operation on `/state`, with value `enable` or `disable`. A successful response is `{"message": "Request to patch accepted", "statusCode": 202}`. This acknowledges an asynchronous request, not a completed state change. Use `getSchedule` or `getSchedules` to inspect `ENABLED`, `DISABLED` or a transitional state.

#### updateSchedule
Update the schedule query with the object pass.\
Arguments:
* scheduleId : REQUIRED : id of the schedule.
* update_obj : REQUIRED : List of patch operations

#### getTemplates
Retrieve a list of query template dictionaries for this instance, not the raw API envelope containing a `templates` key.\
Arguments:
* n_results : OPTIONAL : number of total results to retrieve. To get them all, use "inf".\
possible kwargs:
* limit : Hint on number of records to fetch per page. default (50)
* orderby : Field to order results by. Supported fields: created, updated. Prepend property name with + for ASC,- for DESC order. Default is -created.
* start : Start value of property specified using orderby.
* property : Comma-separated filters.List of properties that allow filtering:
  * name
  * userId
  * lastUpdatedBy\
  operations:
  * '~' (contains). This operator can only be used on the name property.
  * '==' (equal to). This operator can be used on both the userId and the lastUpdatedBy properties.
more details here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Query-Templates/get_query_templates

#### getTemplate
Retrieve a specific template ID.\
Arguments:
* templateId : REQUIRED : template ID to be retrieved.

#### deleteTemplate
Delete a template based on its ID.
Arguments:
* templateId : REQUIRED : template ID to be deleted.

#### createQueryTemplate
Create a query template based on the dictionary passed.\
Arguments:
* queryData : REQUIED : An object that contains "sql", "queryParameter" and "name" keys.
* name : OPTIONAL : Name of the template
* sql : OPTIONAL : SQL query as a string.
* queryParameters : OPTIONAL : in case you are using template, providing the paramter in a dictionary
more info : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Query-Templates/create_query_template

#### getDatasetStatistics
Returns statistics on the dataset size.\
Arguments:
* datasetId : REQUIRED : The dataset ID to look for.
* statisticType : OPTIONAL : The type of statistic to retrieve.

#### getAlertSubscriptions
Get the list of alerts subscriptions.\
Arguments:
* n_results : OPTIONAL : The total number of result you want.

#### createAlertSubscription
Create a subscription to an asset (queryID or scheduleID) for a list of predefined users.\
Arguments:
* assetId : REQUIRED : The schedule ID or query ID.
* alertType : REQUIRED : The type of alert to listen to. (start, success, failure)
* emails : REQUIRED : A list of email addresses that subscribes to that alert.
* inAEP : OPTIONAL : If the Alert should show up in AEP UI. (default True)
* inEmail : OPTIONAL : If the Alert should be sent via email. (default True)\
  NOTE: Consider setting your email address for notification via this tutorial:
  https://experienceleague.adobe.com/docs/experience-platform/observability/alerts/ui.html?lang=en#enable-email-alerts


#### deleteAlertSubscription
Delete a subscription for a specific alert on a specifc assetId.\
Arguments:
* assetId : REQUIRED : A query ID or a schedule ID that you want to delete the alert for.
* alertType : REQUIRED : The state of query execution that triggers the alert to be deleted. (start, success, failure).

#### getAlertSubscriptionsTypeId
Retrieve the subscriptions made about a specific asset ID and with or without alertType specification\
Arguments:
* assetId : REQUIRED : A query or schedule ID that you want the subscription information for.
* alertType : OPTIONAL : This property describes the state of query execution that triggers an alert.\
  (start, success, failure).

#### patchAlert
Disable or Enable an alert by providing the assetId and the alertType.\
Arguments:
* assetId : REQUIRED : A query or schedule ID that you want the subscription information for.
* alertType : REQUIRED : This property describes the state of query execution that triggers an alert.\
  (start, success, failure)
* action : OPTIONAL : the action to take on that Alert. "disable" (default) or "enable"

#### getUserAlerts
Get the alert that a specific user is subscribed to.\
Argument:
* email : REQUIRED : the email address of the user

#### createAcceleratedQuery
Create an accelerated query statement based on either an SQL statement or a template ID.
Arguments:
* name : REQUIRED : Name of your query
* dbName : REQUIRED : The name of the database you are making an accelerated query to. \
            The value for dbName should take the format of {SANDBOX_NAME}:{ACCELERATED_STORE_DATABASE}:{ACCELERATED_STORE_SCHEMA}
* sql : REQUIRED : Either this parameter with a SQL statement or a templateId in the "templateId" parameter.
* templateId : REQUIRED : Either this parameter with a template ID or a SQL statement in the "sql" parameter.
* description : OPTIONAL : An optional comment on the intent of the query to help other users understand its purpose. Max 1000 bytes.


### Query Service use-cases

1. Scheduling queries
 Query Service will be able to generate scheduled Query for your instance.
 At the moment (beginning 2021), this is not available through the UI options.

2. CTAS statement from analysis
 As you may be analysing your data in other application (CJA / non-adobe tool), you may want to request a new dataset creation without needing to connect to AEP UI.

3. Integrate within a pipeline outside AEP
 At some point, you may want to generate a query outside AEP.
 This option is possible from Query Service API but you still need to be aware of the dataset to used in your query and the schema definition.

4. Generate a connection object for interactive queries
 The module provides the possibility to use interactive queries but you will need to generate a connection object.\
 We will see the usage of InteractiveQuery in the next elements.

### Query Service tips

1. Query Service parameter can have a targetSchemaTitle
 The complete syntax for the CTAS statement in the `postQuery` method
 ```JSON
 "ctasParameters": {
    "datasetName": "datasetName",
    "description": "some description",
    "targetSchemaTitle":"schemaTitle"
  }
 ```


2. Time parameter are possible in the title of dataset.
 You can use `$schedule_time` in your query to name your table dynamically when using Schedule Query Service.


3. To follow a specific schema - use a Struct command
 In order to create a structured output for matching schema, use the struct() command

```SQL
 Select struct(visitor_id) as _tenantId from test
```

This will result in: `_tenantId.visitor_id`

4. Starting a Schedule Query
  You would normally need to pass a dictionary (JSON object) to the `updateSchedule` schedule method in order to start your scheduled Query.\
  This is using a PATCH request to inform AEP.\
  I have created an easier method that automatically set the dictionary, based on the scheduleQueryId you want to start: `enableSchedule`

* enableSchedule
  Enable a scheduled query.
  Arguments:
  * scheduleId : REQUIRED : id of the schedule.

5. Disabling a schedule Query
  Before you can delete a schedule Query, you need to disable it.\
  The same way than for starting a query. I have set up a shortcut method to pause a scheduled Query, based on its ID: `disableSchedule`

* disableSchedule
  Disable a scheduled query.
  Arguments:
  * scheduleId : REQUIRED : id of the schedule.

## Query Service CLI

The CLI wraps Query Service methods in the connected sandbox. All commands require a connection configured with `config` or CLI startup options.

| CLI command | SDK method | Output |
| --- | --- | --- |
| `get_queries` | `getQueries` | Filtered query history, console table and `<sandbox>_queries.csv` |
| `get_query <query_id>` | `getQuery` | Query metadata as JSON |
| `get_query_templates` | `getTemplates` | All templates in a console table |
| `get_query_template <template_id>` | `getTemplate` | JSON and `query_template_<template_id>.json` |
| `get_queries_scheduled` | `getSchedules` | All schedules in a console table and `queries_scheduled_<sandbox>.json` |
| `create_query_scheduled` | `createSchedule` | Creation response with schedule ID and initial state |
| `enable_query_scheduled <schedule_id>` | `enableSchedule` | Enable-request acceptance or an explicit error |
| `disable_query_scheduled <schedule_id>` | `disableSchedule` | Disable-request acceptance or an explicit error |
| `query "<sql>"` | `InteractiveQuery2.query` | CSV query results and a console sample |
| `query_audience_population <audience_id> ...` | `InteractiveQuery2.queryAudiencePopulation` | CSV audience population or count |
| `query_history_meta <table>` | `InteractiveQuery2.queryHistoryMeta` | Table snapshot history, console sample and `<sandbox>_history_meta.csv` |
| `query_profiles_trend` | `InteractiveQuery2.queryProfilesTrend` | Last 30 days of profile counts and `<sandbox>_profiles_trend.csv` |
| `query_namespaces_distribution` | `InteractiveQuery2.queryNamespacesDistribution` | Latest namespace counts and `<sandbox>_namespaces_distribution.csv` |
| `query_namespaces_trend [-ns <name>]` | `InteractiveQuery2.queryNamespacesTrend` | Namespace trends and `<sandbox>_namespaces_trend.csv` |
| `query_audience_population_trend [-a <name_or_id>]` | `InteractiveQuery2.queryAudiencePopulationTrend` | Audience population trends and `<sandbox>_audience_population_trend.csv` |

Run `help` to see the Queries command group, `help <command>` for a summary, or `<command> -h` for arguments. See the [CLI command reference](./cli.md#query-service-methods) for examples and the [CLI getting-started guide](./get-started-cli.md#query-service-quick-start) for setup and scheduling.

The five interactive query reports accept `-fn`, `--filename` to override their output filenames, display up to 10 rows and close the connection after fetching results, including when a query fails. Namespace and audience filters are case-insensitive.

Add `--plot` to `query_profiles_trend`, `query_namespaces_trend` or `query_audience_population_trend` for a Matplotlib line chart with dates on the X axis. The Y axis defaults to `COUNT_OF_PROFILES`; `--metric <column>` selects another numeric result column, matched case-insensitively. It requires `--plot`, and invalid names report the available metrics. Multiple namespaces or audiences are separate lines on a common scale. An interactive GUI backend is required; close the chart window to return to the CLI.

The same `--plot` flag on `query_namespaces_distribution` still displays Rich terminal bars of profile counts scaled to the largest namespace. Charting does not alter CSV exports. See the [interactive query report reference](./cli.md#interactive-query-reports) for examples.

## InteractiveQuery and InteractiveQuery2

**NOTE** : The `InteractiveQuery` and `InteractiveQuery2` class can be used if you have postegreSQL server install on your machine.
In order to install postGreSQL server, please follow the instruction here: https://www.postgresql.org/download/

The InteractiveQuery class is a way to directly request Query Service from your local environment.\
You can generate the instance of this class by passing the `connection()` result.

```python
import aepp
mysandbox = aepp.importConfigFile('myConfig_file.json',sandbox='mysandbox',connectInstance=True)

from aepp import queryservice
qs = queryservice.QueryService()
conn = qs.connection()

intQuery = queryservice.InteractiveQuery(conn,config=mysandbox)

#or

intQuery2 = queryservice.InteractiveQuery2(conn,config=mysandbox)
```

### Differences between InteractiveQuery and InteractiveQuery2

The `InteractiveQuery` class is using the `PyGreSQL` python module in the background. **This class will be deprecated in the future.**\
The `InteractiveQuery2` class is using the `psycopg2` python module in the background.

Most methods below are available on both classes. In version 0.6.0, audience population methods use different names:

| Operation | `InteractiveQuery` | `InteractiveQuery2` |
| --- | --- | --- |
| Export audience identities or retrieve counts | `querySegmentPopulation(segmentId=...)` | `queryAudiencePopulation(audienceId=...)` |
| Retrieve audience population trends | `querySegmentPopulationTrend(segment=...)` | `queryAudiencePopulationTrend(segment=...)` |

`InteractiveQuery2` no longer exposes `querySegmentPopulation`; update existing calls to `queryAudiencePopulation` and rename the `segmentId` argument to `audienceId`. There is no compatibility alias. The corresponding CLI command is now `query_audience_population`, replacing `query_segment_population`.

#### Instantiation of interactive query

Both class can be instantiated via the same method presented above.\
We recommend using `InteractiveQuery2` as it seems to be the more stable one.\

The parameter that you can pass during instantiation are: 
* conn_object : REQUIRED : The connection object you have generated via `QueryService` instance `connection` method.
* config : OPTIONAL : Configuration object from aepp ConnectObject instance. Requires if you want to use some advanced methods. 
* loggingObject : OPTIONAL : A logging object that can be passed for debuging or logging elements, see [logging documentation](./logging.md)
* sslmode : OPTIONAL : `InteractiveQuery2` only. The sslmode to use when connecting to the database. Default to "allow".

Initialization also reads the default merge policy and namespace mapping from `qsaccel.profile_agg.adwh_dim_merge_policies` and `qsaccel.profile_agg.adwh_dim_namespaces`. The connected sandbox must have accessible Profile reporting metadata and a row marked `IS_DEFAULT_MERGE_POLICY`. These reads happen on every instantiation, including for ordinary SQL and table-history queries; initialization fails if the metadata is unavailable or no default policy is returned.

Both classes expose `default_merge_policy_queryId` (the reporting `MERGE_POLICY_ID`) and `default_merge_policy_id` (the AEP merge-policy identifier from `MERGE_POLICY`). Reporting helpers use the reporting ID selected at initialization. Create a new instance to reload this metadata after changing the sandbox's default policy.

### Methods of Interactive Query

From the InteractiveQuery instances you can directly pass SQL query and receive either:
* dataframe
* object from the different module (`pyGreSQL` or `psycopg2`)

#### addConfig
Possibly to attach a configuration sandbox after the instantiation of the object.
Arguments:
* config : REQUIRED : Configuration object from aepp ConnectObject instance.

#### close
Close the underlying database connection. Available on both `InteractiveQuery` (PyGreSQL) and `InteractiveQuery2` (psycopg2). Takes no arguments and returns `None`.

Use `try`/`finally` to release the connection even if querying or processing the results raises an exception:

```python
intQuery2 = queryservice.InteractiveQuery2(conn, config=mysandbox)
try:
    df_result = intQuery2.query("SELECT * FROM myDataset LIMIT 100")
finally:
    intQuery2.close()
```

Consume or convert any raw query results before closing the connection. To run more queries after closing, create a new interactive-query instance.

The CLI's [`query` command](./cli.md#query) now closes its connection after retrieving and exporting the results on the successful execution path.

#### query
Query the database and return different type of data, depending the format parameters.\
Requests are limited to return 50 K rows by default.\
Arguments:
* sql : REQUIRED : the SQL request you want to realize.
* output : OPTIONAL : the format you would like to be returned.
* Possible format:
  * "raw" : return the instance of the query object.
  * "dataframe" : return a dataframe with the data. (default)\
  Returns empty dataframe when the query result is empty.

```python

sql = """
SELECT * 
FROM myDataset
LIMIT 100
"""

## returns a dataframe
df_result = intQuery.query(sql)

## returns an object
result = intQuery.query(sql,output= "raw")
```

#### queryHistoryMeta
Retrieve snapshot history metadata for a Query Service table as a dataframe. This does not return query execution history.

Arguments:
* `table` : Required Query Service table name.

#### queryProfilesTrend
Return `DATE_KEY` and `COUNT_OF_PROFILES` for the sandbox's default merge policy, sorted by `DATE_KEY`. The 30-day window is relative to the latest successful `FACT_TABLES_PROCESSING` process date, not the local clock.

#### queryNamespacesDistribution
Return the latest namespace distribution for the default merge policy. Includes namespace names, profile counts, identity counts and single-identity profile counts.

The namespace-name column is `NAMESPACE` for `InteractiveQuery` and `NAMESPACE_DESCRIPTION` for `InteractiveQuery2`. Both return `COUNT_OF_PROFILES`, `COUNT_OF_SINGLE_IDENTITY_PROFILES` and `COUNT_OF_IDENTITIES` from the latest reporting `DATE_KEY` for that policy.

#### queryNamespacesTrend
Return namespace trends for the default merge policy, sorted by `DATE_KEY`, with namespace names mapped from reporting IDs.

Arguments:
* `namespace` : Optional namespace name, matched exactly and case-insensitively. Defaults to all namespaces.

Returns `DATE_KEY`, `NAMESPACE`, `COUNT_OF_PROFILES`, `COUNT_OF_IDENTITIES` and `COUNT_OF_SINGLE_IDENTITY_PROFILES`. Unlike `queryProfilesTrend`, this method does not apply a 30-day filter.

#### querySegmentPopulationTrend
Available on `InteractiveQuery` only. Return segment population trends for the default merge policy, with `DATE_KEY`, `SEGMENT_NAME` and `AUDIENCE_ID` mapped from reporting IDs. Includes `COUNT_OF_PROFILES`, `COUNT_OF_IDENTITIES`, `COUNT_OF_CALCULATED_REALIZED_PROFILES`, `COUNT_OF_CALCULATED_EXISTING_PROFILES` and `COUNT_OF_CALCULATED_EXITED_PROFILES`.

Arguments:
* `segment` : Optional segment name or audience ID, matched exactly and case-insensitively. Defaults to all segments.

#### queryAudiencePopulationTrend
Available on `InteractiveQuery2` only. Return the same metrics as `querySegmentPopulationTrend`, with `AUDIENCE_NAME` instead of `SEGMENT_NAME`. The result also includes `DATE_KEY` and `AUDIENCE_ID`.

Arguments:
* `segment` : Optional audience name or ID, matched exactly and case-insensitively. The Python argument is still named `segment`; the CLI exposes it as `-a`, `--audience`. Defaults to all audiences.

Both audience trend methods map names and IDs from `adwh_dim_segments` entries in the `UPS` namespace. They return the available reporting history without a 30-day filter or explicit date sorting. The CLI sorts dates for plotting without changing the CSV row order.

The trend methods return an empty dataframe when the reporting query returns no rows. Namespace and audience filters with no matches also return an empty dataframe.

Example using the recommended `InteractiveQuery2` class:

```python
intQuery2 = queryservice.InteractiveQuery2(conn, config=mysandbox)
try:
    history = intQuery2.queryHistoryMeta(table="accounts")
    profiles = intQuery2.queryProfilesTrend()
    distribution = intQuery2.queryNamespacesDistribution()
    namespaces = intQuery2.queryNamespacesTrend(namespace="Email")
    audiences = intQuery2.queryAudiencePopulationTrend(segment="VIP Customers")
finally:
    intQuery2.close()
```

#### transformToDataFrame
In case you want to transform your result into a dataframe later on, you can use the `transformToDataFrame` method.\
This will return you a dataFrame.\
Argument:
* query : REQUIRED : The query result that you returned as "raw" in the query method.

```python
mydf = intQuery.transformToDataFrame(result)
```

#### querySegmentPopulation
Available on `InteractiveQuery` only. Retrieve the identities in the identityMap that are qualified to the segment ID passed.\
Arguments:
* segmentId : REQUIRED : Single or list of segment Ids
* extraFields : OPTIONAL : If you want to add more identities that are not in the IdentityMap
* count : OPTIONAL : If you just want to get the population count of the segment IDs, default `False`

This method will return a dataframe and will realize the following operations: 
1. Get the segments/audiences Id Profile Merge Policy ID 
2. Retrieve the profile snapshot specific for that merge policy
3. Query the identityMap and explode it, it will also add any additional fields that you have provided
4. Returns the result in a dataframe 

**Note**:\
If you specify `True` for the `count` parameter, the result will be a dataframe with the segments/audiences and the total profile population as reported via the Segmentation API. It will not do the calculation via Query Service but the UPS result. 

**Understanding the output**\
The returned dataframe may not have a similar count of rows as the profile population specified within the audience interface.\
As each identity contained in the identityMap is exploded, it creates additional row for each identities.\
In order to achieve the same count, you would need to deduplicate the rows by identities.\
This method is used to investigate and do advanced verification of segmentation population.\
This method is mostly using the Profile Snapshot for exporting data, which means that Real Time or Edge Segments population may not be represented correctly due to the asynchronous nature of the Profile Snapshot vs Profile Store. 

#### queryAudiencePopulation
The `InteractiveQuery2` counterpart to `querySegmentPopulation`, renamed in version 0.6.0.

Arguments:
* `audienceId` : Required audience ID or list of audience IDs.
* `extraFields` : Optional field name or list of additional fields to select. When a list of audiences is supplied, these fields are forwarded to each audience query.
* `count` : Optional boolean, default `False`. Requests the population count reported by the Segmentation API rather than counting identity rows.

Requires a sandbox configuration supplied at initialization or through `addConfig`. With `count=True`, returns one row per audience with `count` and `audienceId` columns, without looking up snapshot datasets or executing SQL. A missing population metric retains the existing `"No Data Yet"` value; a reported zero remains zero. The interactive-query initialization requirements still apply.

For identity exports, the method resolves each audience's merge policy and its Profile snapshot dataset. Identity exports label the audience identifier `audienceId`, replacing the old `segmentId` column. The snapshot timing and identity-expansion considerations described above also apply.


#### queryIdentity
Return the elements that you have passed in field list and return the output selected.\
Arguments:
* identityId : REQUIRED : The ID you want to retrieve
* fields : REQUIRED : a list of fields you want to return for that ID in your table.\
  example : ['person.name']
* tableName : REQUIRED : The dataset table name to use
* output : OPTIONAL : the format you would like to be returned.\
  Possible format:
  * "raw" : return the instance of the query object.
  * "dataframe" : return a dataframe with the data. (default)
* fieldId : OPTIONAL : If you want your selection to be based on another field than ECID in IdentityMap.
* limit : OPTIONAL : If you wish to set a LIMIT on number of row returned.
* save : OPTIONAL : will save a csv file
* verbose : OPTIONAL : will display some comment


### Tips for Interactive Query

1. Use the LIMIT parameter in your interactive query is recommended
 In any case, there is a limit of 50 000 rows from the API endpoint (enforced by Adobe API)

2. Using CTAS statement are possible in the Interactive Query as well
 The CTAS statement needs to be stated directly in the SQL statement.

3. I have created an easy method to retrieve a specific fields based on a condition: `queryIdentity`
  The main use-case is for debugging AEP Web SDK implementation so you can pass the ECID value and the different fields you want to retrieve with your table name.
  It will return the query result and can be saved in a csv with the identity value name.\
  Be careful however if you are using array of objects based Schema, you would need to deconstruct them before using this method.

* `queryIdentity`
  Return the elements that you have passed in field list and return the output selected.
  Arguments:
  * identityId : REQUIRED : The ID you want to retrieve
  * fields : REQUIRED : a list of fields you want to return for that ID in your table.
      example : ['person.name']
  * tableName : REQUIRED : The dataset table name to use
  * output : OPTIONAL : the format you would like to be returned.
  Possible format:
      "raw" : return the instance of the query object.
      "dataframe" : return a dataframe with the data. (default)
  * fieldId : OPTIONAL : If you want your selection to be based on another field than ECID.
  * limit : OPTIONAL : maximum number of elements returned in your query.
  * save : OPTIONAL : will save a csv file
  * verbose : OPTIONAL : will display some comment

example:

```python
import aepp
aepp.importConfigFile('config.json')
from aepp import queryservice

## using QueryService class to retrieve connection details
qs = queryservice.QueryService()
conn = qs.connection()

## Using interactive query
query = queryservice.InteractiveQuery(conn)
fields = ['_tenant.person.fullname','_tenant_.person.sex']
df = query.queryIdentity(identityId="21d67084-398e-4a48-8723-2fd",fields=fields,tableName='myTableName',verbose=True)

```
