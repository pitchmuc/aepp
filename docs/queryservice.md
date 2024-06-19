# QueryService module in aepp

This documentation will provide you some explanation on how to use the queryservice module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/query-service/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu
- [QueryService module in aepp](#queryservice-module-in-aepp)
  - [Menu](#menu)
  - [Importing the module](#importing-the-module)
  - [Generating a QueryService instance](#generating-a-queryservice-instance)
  - [QueryService attributes](#schema-attributes)
  - [QueryService methods](#schema-methods)
  - [Use Cases](#use-cases)
  - [InteractiveQuery and InteractiveQuery2](#interactivequery-and-interactivequery2)
    - [Differences between InteractiveQuery and InteractiveQuery2](#differences-between-interactivequery-and-interactivequery2)
    - [Methods of Interactive Query](#methods-of-interactive-query)
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
  prepend with "+" for ASC and "-" for DESC. To be escaped (default: -)
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

### deleteQuery
Delete a specific query based on its ID.\
Argument:
* queryId : REQUIRED : the query ID to delete

#### getSchedules
Retrieve a list of scheduled queries for the AEP instance.\
Arguments:
* n_results : OPTIONAL : Total number of scheduled queries retrieved. To get them all, use "inf"\
possibile kwargs:
* orderby : + for ASC and - for DESC
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

#### updateSchedule
Update the schedule query with the object pass.\
Arguments:
* scheduleId : REQUIRED : id of the schedule.
* update_obj : REQUIRED : List of patch operations

#### getTemplates
Retrieve the list of template for this instance.\
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
* queryData : REQUIED : An object that contains "sql", "queryParameter" and "name" keys.\
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

## InteractiveQuery and InteractiveQuery2

**NOTE** : The `InteractiveQuery` and `InteractiveQuery2` class can be used if you have postegreSQL server install on your machine.
In order to install postGreSQL server, please follow the instruction here: https://www.postgresql.org/download/

The InteractiveQuery class is a way to directly request Query Service from your local environment.\
You can generate the instance of this class by passing the `connection()` result.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import queryservice
qs = queryservice.QueryService()
conn = qs.connection()

intQuery = queryservice.InteractiveQuery(conn)

#or

intQuery2 = queryservice.InteractiveQuery2(conn)
```

### Differences between InteractiveQuery and InteractiveQuery2

The `InteractiveQuery` class is using the `PyGreSQL` python module in the background.\
The `InteractiveQuery2` class is using the `psycopg2` python module in the background.

Except for that change in the engine used in the background, all of the methods described below can be applied to either `InteractiveQuery` or `InteractiveQuery2` instances.

### Methods of Interactive Query

From the InteractiveQuery instances you can directly pass SQL query and receive either:

#### query
Query the database and return different type of data, depending the format parameters.\
Requests are limited to return 50 K rows by default.\
Arguments:
* sql : REQUIRED : the SQL request you want to realize.
* output : OPTIONAL : the format you would like to be returned.
* Possible format:
  * "raw" : return the instance of the query object.
  * "dataframe" : return a dataframe with the data. (default)

```python

sql = """
SELECT * 
FROM myDataset
LIMIT 100
"""

## returns a dataframe
df_result = intQuery.query(sql,output= "dataframe")

## returns an object
result = intQuery.query(sql,output= "raw")
```

#### transformToDataFrame
In case you want to transform your result into a dataframe later on, you can use the `transformToDataFrame` method.\
This will return you a dataFrame.\
Argument:
* query : REQUIRED : The query result that you returned as "raw" in the query method.

```python
mydf = intQuery.transformToDataFrame(result)
```

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
