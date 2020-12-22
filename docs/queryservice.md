# QueryService module in aepp

This documentation will provide you some explanation on how to use the queryservice module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/qs-api.yaml).\
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

## InteractiveQuery

The InteractiveQuery class is a way to directly request Query Service from your local environment.\
You can generate the instance of this class by passing the `connection()` result.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import queryservice
qs = queryservice.QueryService()
conn = qs.connection()

intQuery = queryservice.InteractiveQuery(conn)
```

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

### Tips for Interactive Query

1. Use the LIMIT parameter in your interactive query is recommended
 In any case, there is a limit of 50 000 rows from the API endpoint (enforced by Adobe API)

2. Using CTAS statement are possible in the Interactive Query as well
 The CTAS statement needs to be stated directly in the SQL statement.