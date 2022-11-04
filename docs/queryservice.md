# QueryService module in aepp

This documentation will provide you some explanation on how to use the queryservice module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/query-service/).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `queryservice` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import queryservice
```

The queryservice module provide 2 classes that you can use for interacting with the Query Service API.\
The following documentation will provide you with more information on these.

## QueryService class

The Query Service class is the default API connector that you would encounter for any other submodules on this python module.\
This class can be instanciated by calling the `QueryService()` from the `queryservice` module.

Following the previous method described above, you can realize this:

```python
qs = queryservice.QueryService()
```

2 parameters are possible for the instanciation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

### Using kwargs

Kwargs will be used to update the header used in the connection.\
As described above, it can be useful when you want to connect to multiple sandboxes with the same JWT authentication.\
In that case, the 2 instances will be created as such:

```python
qs1 = queryservice.QueryService({"x-sandbox-name":"mySandbox1"})
```

```python
qs2 = queryservice.QueryService({"x-sandbox-name":"mySandbox2"})
```

### Attributes

The QueryService instance will provide 2 attribute that you can use to help you create the dictionary data for your postQuery and createSchedule methods.\
The attributes are:\
`QUERYSAMPLE`: for postQuery method
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

`SCHEDULESAMPLE`: for createSchedule
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

### Difference between InteractiveQuery and InteractiveQuery2

The `InteractiveQuery` class is using the `PyGreSQL` python module in the background.\
The `InteractiveQuery2` class is using the `psycopg2` python module in the background.

Except for that change in the engine used in the background, all of the methods described below can be applied to either `InteractiveQuery` or `InteractiveQuery2` instances.

### usage of Interactive Query


From the Interactive Query instance you can directly pass SQL query and receive either:

* a dataframe (default return)
* an object

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

In case you want to transform your result into a dataframe later on, you can use the `transformToDataFrame` method.

```python
mydf = intQuery.transformToDataFrame(result)
```

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
