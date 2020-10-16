# Internal Library
import aepp
from aepp import config
from aepp import modules
from aepp import connector
from pg import DB


class QueryService:
    """
    QueryService class is to be used in order to generate queries, scheduled queries or retrieve past queries.
    """
    QUERYSAMPLE = {
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
    SCHEDULESAMPLE = {
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

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        """
        Instanciate the class for Query Service call.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        kwargs:
            kwargs will update the header
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        #self.header.update({"Accept": "application/json"})
        self.header.update(**kwargs)
        self.endpoint = aepp.config.endpoints["global"]+aepp.config.endpoints["query"]
        self.TEMPLATES = {
            'post': {
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
                    "description": "string"
                }
            },
            'schedule': {
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
                        "description": "string"
                    }
                },
                "schedule": {
                    "schedule": "string",
                    "startDate": "string",
                    "endDate": "string",
                    "maxActiveRuns": 0
                }
            }
        }

    def connection(self):
        """
        Create a connection for interactive interface. 
        """
        path = "/connection_parameters"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def getQueries(self, orderby: str = None, limit: int = 1000, start: int = None, **kwargs):
        """
        Retrieve the queries from your organization.
        Arguments:
            orderby : OPTIONAL : possibility to order by "created" or "updated".
            prepend with "+" for ASC and "-" for DESC. To be escaped (default: -)
            limit : OPTIONAL : number of of records to fetch per page. (default 1000)
            start: OPTIONAL : when to start (depending on your orderby)

        possible kwargs:
            excludeSoftDeleted: Whether to include any queries that have been soft deleted. Defaults to true.
            excludeHidden : Whether to include any queries that have been found to be not interesting, as they were not user driven. Examples include CURSOR definitions, FETCH, and Metadata queries. Defaults to true.
            isPrevLink : Field indicating if the URI is a previous link.
        """
        path = '/queries'
        arguments = {'limit': 1000}
        if orderby is not None:
            if orderby == "+":
                orderby = "%2B"
            arguments['orderby'] = orderby
        if start is not None:
            arguments['start'] = start
        if limit is not None:
            arguments['limit'] = limit
        if len(kwargs.keys()) > 0:
            arguments['excludeSoftDeleted'] = kwargs.get(
                "excludeSoftDeleted", True)
            arguments['excludeHidden'] = kwargs.get(
                "excludeHidden", True)
            arguments['isPrevLink'] = kwargs.get(
                "isPrevLink", '')
        res = self.connector.getData(self.endpoint+path, params=arguments, headers=self.header)
        return res

    def postQueries(self, data: dict = None, name: str = None, dbname: str = "prod:all", sql: str = None, templateId: str = None, queryParameters: dict = None, insertIntoParameters: dict = None, ctasParameters: dict = None, description: str = "", **kwargs):
        """
        Create a query.
        Arguments:
            data : OPTIONAL : If you want to pass the full query statement. 
            name : REQUIRED : Name of the query
            dbname : REQUIRED : the dataset name (default prod:all)
            sql: REQUIRED : the SQL query as a string.
            queryParameters : OPTIONAL : in case you are using template, providing the paramter in a dictionary.
            ctasParameters: OPTIONAL : in case you want to create a dataset out of that query, dictionary is required with "datasetName" and "description".
        """
        path = '/queries'
        if data is None:
            if sql is None or name is None:
                raise AttributeError("You are missing required arguments.")
            if type(ctasParameters) is dict:
                if "datasetName" not in ctasParameters.keys() or "description" not in ctasParameters.keys():
                    raise KeyError(
                        'Expecting "datasetName" and "description" as part of the the ctasParameters dictionary.')
            data = {
                "name": name,
                "description": description,
                "dbName": dbname,
                "sql": sql,
            }
            if templateId is not None:
                data["templateId"] = templateId
            if queryParameters is not None:
                data["queryParameters"] = queryParameters
            if ctasParameters is not None:
                data["ctasParameters"] = ctasParameters
            if insertIntoParameters is not None:
                data["insertIntoParameters"] = insertIntoParameters
        res = self.connector.postData(self.endpoint + path,
                             data=data, headers=self.header)
        return res

    def getQuery(self, queryid: str = None):
        """
        Request the query status by ID.
        Argument : 
            queryid : REQUIRED : the query id to check
        """
        if queryid is None:
            raise AttributeError('Expected "queryid" to be filled')
        path = f'/queries/{queryid}'
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def getSchedules(self, **kwargs):
        """
        Retrieve a list of scheduled queries for the AEP instance.
        possibile kwargs:
            orderby : + for ASC and - for DESC
            limit : number of record to fetch
            start : specific start (use with orderby) 
            property : Comma-separated filters.
                created ; ex : created>2017-04-05T13:30:00Z
                templateId ; ex : templateId==123412354
                userId ; ex : userId==12341235
        """
        if kwargs.get("orderby", None) is not None:
            if kwargs.get("orderby", "-") == "+":
                kwargs.get("orderby", "-") == "%2B"
        path = "/schedules"
        params = {**kwargs}
        res = self.connector.getData(self.endpoint + path, params=params)
        return res

    def getSchedule(self, scheduleId: str = None):
        """
        Get a details about a schedule query.
        Arguments:
            scheduleId : REQUIRED : the schedule id
        """
        if scheduleId is None:
            raise Exception("scheduleId is required")
        path = f"/schedules/{scheduleId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def getScheduleJobs(self, scheduleId: str = None):
        """
        Get the different jobs ran for this schedule
        Arguments:
            scheduleId : REQUIRED : the schedule id
        """
        if scheduleId is None:
            raise Exception("scheduleId is required")
        path = f"/schedules/{scheduleId}/runs"
        res = self.connector.getData(self.endpoint + path)
        return res

    def getScheduleJob(self, scheduleId: str = None, jobId: str = None):
        """
        Get the different jobs ran for this schedule
        Arguments:
            scheduleId : REQUIRED : the schedule id
        """
        if scheduleId is None or jobId is None:
            raise Exception("scheduleId and jobId are required")
        path = f"/schedules/{scheduleId}/runs/{jobId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def createSchedule(self, scheduleQuery: dict = None, name: str = None, dbname: str = "prod:all", sql: str = None, templateId: str = None, queryParameters: dict = None, insertIntoParameters: dict = None, ctasParameters: dict = None, schedule: dict = None, description: str = "", **kwargs):
        """
        Create a scheduled query.
        Arguments:
            scheduleQuery: REQUIRED : a dictionary containing the query and the schedule.
            name : OPTIONAL : Name of the query
            dbname : OPTIONAL : the dataset name (default prod:all)
            sql: OPTIONAL : the SQL query as a string.
            queryParameters : OPTIONAL : in case you are using template, providing the paramter in a dictionary.
            ctasParameters: OPTIONAL : in case you want to create a dataset out of that query, dictionary is required with "datasetName" and "description".
            schedule : OPTIONAL : Dictionary giving the instruction to schedule the query.
        """
        if scheduleQuery is None:
            if name is None or sql is None or schedule is None:
                raise Exception(
                    "Expecting either scheduleQUery dictionary or data in parameters")
            scheduleQuery = {
                "query": {
                    "name": name,
                    "description": description,
                    "dbName": dbname,
                    "sql": sql
                },
                "schedule": schedule
            }
            if templateId is not None:
                scheduleQuery["query"]["templateId"] = templateId
            if queryParameters is not None:
                scheduleQuery["query"]["queryParameters"] = queryParameters
            if ctasParameters is not None:
                scheduleQuery["query"]["ctasParameters"] = ctasParameters
            if insertIntoParameters is not None:
                scheduleQuery["query"]["insertIntoParameters"] = insertIntoParameters
        if type(scheduleQuery) != dict:
            raise Exception(
                "scheduleQuery is required and should be dictionary. ")
        if "query" not in scheduleQuery.keys() or "schedule" not in scheduleQuery.keys():
            raise Exception(
                'scheduleQuery dictonary is expected to contain "schedule" or "query" keys.')
        path = "/schedules"
        res = self.connector.postData(self.endpoint + path, data=scheduleQuery)
        return res

    def deleteSchedule(self, scheduleId: str = None):
        """
        Delete a scheduled query.
        Arguments: 
            scheduleId : REQUIRED : id of the schedule. 
        """
        if scheduleId is None:
            raise Exception("Missing scheduleId")
        path = f"/schedules/{scheduleId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def disableSchedule(self, scheduleId: str = None):
        """
        Disable a scheduled query.
        Arguments: 
            scheduleId : REQUIRED : id of the schedule. 
        """
        if scheduleId is None:
            raise Exception("Missing scheduleId")
        obj = {
            "body": [
                {
                    "op": "replace",
                    "path": "/state",
                    "value": "disable"
                }
            ]
        }
        path = f"/schedules/{scheduleId}"
        res = self.connector.patchData(self.endpoint + path,
                              data=obj, headers=self.header)
        return res

    def enableSchedule(self, scheduleId: str = None):
        """
        Enable a scheduled query.
        Arguments: 
            scheduleId : REQUIRED : id of the schedule. 
        """
        if scheduleId is None:
            raise Exception("Missing scheduleId")
        obj = {
            "body": [
                {
                    "op": "replace",
                    "path": "/state",
                    "value": "enable"
                }
            ]
        }
        path = f"/schedules/{scheduleId}"
        res = self.connector.patchData(self.endpoint + path,
                              data=obj, headers=self.header)
        return res

    def updateSchedule(self, scheduleId: str = None, update_obj: list = None):
        """
        Update the schedule query with the object pass.
        Arguments:
            scheduleId : REQUIRED : id of the schedule. 
            update_obj : REQUIRED : List of patch operations
        """
        if scheduleId is None:
            raise Exception("Missing scheduleId")
        if update_obj is None:
            raise Exception("Missing update_obj to generate the operation.")
        path = f"/schedules/{scheduleId}"
        res = self.connector.patchData(self.endpoint + path,
                              data=update_obj, headers=self.header)
        return res

    def getTemplates(self, **kwargs):
        """
        Retrieve the list of template for this instance.
        possible kwargs:
            limit : Hint on number of records to fetch per page. default (50)
            orderby : Field to order results by. Supported fields: created, updated. Prepend property name with + for ASC,- for DESC order. Default is -created.
            start : Start value of property specified using orderby.
            property : Comma-separated filters.List of properties that allow filtering:
                    name
                    userId
                    lastUpdatedBy
                operations:
                    ‘~’ (contains). This operator can only be used on the name property.
                    ‘==’ (equal to). This operator can be used on both the userId and the lastUpdatedBy properties.
        more details here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Query-Templates/get_query_templates
        """
        path = "/query-templates"
        params = {**kwargs}
        params['limit'] = kwargs.get('limit', 50)
        res = self.connector.getData(self.endpoint + path,
                            headers=self.header, params=params)
        return res

    def createQueryTemplate(self, queryData: dict = None):
        """
        Create a query template based on the dictionary passed.
        Arguments: 
            queryData : REQUIED : An object that contains "sql", "queryParameter" and "name" keys.
        more info : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Query-Templates/create_query_template
        """
        path = "/query-templates"
        if isinstance(queryData, dict):
            if "sql" not in queryData.keys() or "queryParameter" not in queryData.keys() or "name" not in queryData.keys():
                raise KeyError(
                    "Minimum key value are not respected.\nPlease see here for more info :\nhttps://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Query-Templates/create_query_template ")
        else:
            raise Exception("expected a dictionary for queryData")
        res = self.connector.postData(self.endpoint + path,
                             headers=self.header, data=queryData)
        return res


class InteractiveQuery:
    """
    Provide the instance connected to PostgreSQL database and you can return the result directly in your notebook.
    This class requires that you have used connection method in the QueryService.
    The object returned by the connection method should be used when creating this object.  

    """
    config_object = {}

    def __init__(self, conn_object: dict = None):
        if conn_object is None:
            raise AttributeError(
                "You are missing the conn_object. Use the QueryService to retrieve the object.")
        self.dbname = conn_object['dbName']
        self.host = conn_object['host']
        self.port = conn_object['port']
        self.user = conn_object['username']
        self.passwd = conn_object['token']
        self.websocketHost = conn_object['websocketHost']
        self.config_object = {
            "dbname": self.dbname,
            "host": self.host,
            "user": self.user,
            "passwd": self.passwd,
            "port": self.port,
        }
        self.db = DB(**self.config_object)

    def query(self, sql: str = None, output: str = "dataframe"):
        """
        Query the database and return different type of data, depending the format parameters.
        Requests are limited to return 50 K rows
        Arguments:
            sql : REQUIRED : the SQL request you want to realize. 
            output : OPTIONAL : the format you would like to be returned.
            Possible format:
                "raw" : return the instance of the query object.
                "dataframe" : return a dataframe with the data. (default)
        """
        if sql is None:
            raise Exception("Required a SQL query")
        query = self.db.query(sql)
        if output == "raw":
            return query
        elif output == "dataframe":
            data = query.getresult()
            columns = query.listfields()
            df = aepp.modules.pd.DataFrame(data, columns=columns)
            return df
        else:
            raise KeyError("You didn't specify a correct value.")

    def transformToDataFrame(self, query: object = None):
        """
        This will return you a dataFrame 
        """
        data = query.getresult()
        columns = query.listfields()
        df = aepp.modules.pd.DataFrame(data, columns=columns)
        return df
