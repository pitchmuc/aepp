#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

# Internal Library
from aepp import connector
import pandas as pd
from typing import Union
import re
import aepp
import time
import logging
from .configs import ConnectObject

class QueryService:
    """
    QueryService class is to be used in order to generate queries, scheduled queries or retrieve past queries.
    """

    QUERYSAMPLE = {
        "dbName": "string",
        "sql": "SELECT $key from $key1 where $key > $key2;",
        "queryParameters": {"key": "value", "key1": "value1", "key2": "value2"},
        "templateId": "123",
        "name": "string",
        "description": "powered by aepp",
        "insertIntoParameters": {"datasetName": "string"},
        "ctasParameters": {
            "datasetName": "myDatasetName",
            "description": "powered by aepp",
            "targetSchemaTitle": "mySchemaName",
        },
    }
    SCHEDULESAMPLE = {
        "query": {
            "dbName": "string",
            "sql": "SELECT $key from $key1 where $key > $key2;",
            "queryParameters": {"key": "value", "key1": "value1", "key2": "value2"},
            "templateId": "123",
            "name": "string",
            "description": "string",
            "insertIntoParameters": {"datasetName": "string"},
            "ctasParameters": {
                "datasetName": "string",
                "description": "string",
                "targetSchemaTitle": "mySchemaName",
            },
        },
        "schedule": {
            "schedule": "string",
            "startDate": "string",
            "endDate": "string",
            "maxActiveRuns": 0,
        },
    }
    TEMPLATESAMPLE = {
        "sql": "SELECT $key from $key1 where $key > $key2;",
        "queryParameters": {"key": "value", "key1": "value1", "key2": "value2"},
        "name": "string",
    }

    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header:dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ) -> None:
        """
        Instanciate the class for Query Service call.
        Arguments:
            config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
            loggingObject : OPTIONAL : If you want to set logging capability for your actions.
        kwargs:
            kwargs will update the header
        """
        if loggingObject is not None and sorted(
            ["level", "stream", "format", "filename", "file"]
        ) == sorted(list(loggingObject.keys())):
            self.loggingEnabled = True
            self.logger = logging.getLogger(f"{__name__}")
            self.logger.setLevel(loggingObject["level"])
            if type(loggingObject["format"]) == str:
                formatter = logging.Formatter(loggingObject["format"])
            elif type(loggingObject["format"]) == logging.Formatter:
                formatter = loggingObject["format"]
            if loggingObject["file"]:
                fileHandler = logging.FileHandler(loggingObject["filename"])
                fileHandler.setFormatter(formatter)
                self.logger.addHandler(fileHandler)
            if loggingObject["stream"]:
                streamHandler = logging.StreamHandler()
                streamHandler.setFormatter(formatter)
                self.logger.addHandler(streamHandler)
        if type(config) == dict: ## Supporting either default setup or passing a ConnectObject
            config = config
        elif type(config) == ConnectObject:
            header = config.getConfigHeader()
            config = config.getConfigObject()
        self.connector = connector.AdobeRequest(
            config=config,
            header=header,
            loggingEnabled=self.loggingEnabled,
            logger=self.logger,
        )
        self.header = self.connector.header
        # self.header.update({"Accept": "application/json"})
        self.header.update(**kwargs)
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.endpoint = aepp.config.endpoints["global"] + aepp.config.endpoints["query"]

    def getResource(
        self,
        endpoint: str = None,
        params: dict = None,
        format: str = "json",
        save: bool = False,
        **kwargs,
    ) -> dict:
        """
        Template for requesting data with a GET method.
        Arguments:
            endpoint : REQUIRED : The URL to GET
            params: OPTIONAL : dictionary of the params to fetch
            format : OPTIONAL : Type of response returned. Possible values:
                json : default
                txt : text file
                raw : a response object from the requests module
        """
        if endpoint is None:
            raise ValueError("Require an endpoint")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getResource")
        res = self.connector.getData(endpoint, params=params, format=format)
        if save:
            if format == "json":
                aepp.saveFile(
                    module="catalog",
                    file=res,
                    filename=f"resource_{int(time.time())}",
                    type_file="json",
                    encoding=kwargs.get("encoding", "utf-8"),
                )
            elif format == "txt":
                aepp.saveFile(
                    module="catalog",
                    file=res,
                    filename=f"resource_{int(time.time())}",
                    type_file="txt",
                    encoding=kwargs.get("encoding", "utf-8"),
                )
            else:
                print(
                    "element is an object. Output is unclear. No save made.\nPlease save this element manually"
                )
        return res

    def connection(self) -> dict:
        """
        Create a connection for interactive interface.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Getting a connection")
        path = "/connection_parameters"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def getQueries(
        self,
        orderby: str = None,
        limit: int = 1000,
        start: int = None,
        n_results: int = 1000,
        property: str = None,
        **kwargs,
    ) -> list:
        """
        Retrieve the queries from your organization.
        Arguments:
            orderby : OPTIONAL : possibility to order by "created" or "updated".
            prepend with "+" for ASC and "-" for DESC. To be escaped (default: -)
            limit : OPTIONAL : number of of records to fetch per page. (default 1000)
            start : OPTIONAL : when to start (depending on your orderby)
            property : OPTIONAL : Comma-separated filters. List of properties that allow filtering with all operators:
                        "created"
                        "updated"
                        "state"
                        "id"
                    with following operators >, <, >=, <=, ==, !=, ~
                "referenced_datasets", "scheduleId", "templateId", and "userId" can only be used with ==. Multiple datasets ID with "||"
                "SQL" can only be used with ~ (WITHOUT COMMA)
            n_results : OPTIONAL : total number of results returned (default 1000, set to "inf" to retrieve everything)
        possible kwargs:
            excludeSoftDeleted: Whether to include any queries that have been soft deleted. Defaults to true.
            excludeHidden : Whether to include any queries that have been found to be not interesting, as they were not user driven. Examples include CURSOR definitions, FETCH, and Metadata queries. Defaults to true.
            isPrevLink : Field indicating if the URI is a previous link.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getQueries")
        path = "/queries"
        arguments = {"limit": 1000}
        n_results = float(n_results)
        if orderby is not None:
            if orderby == "+":
                orderby = "%2B"
            arguments["orderby"] = orderby
        if start is not None:
            arguments["start"] = start
        if limit is not None:
            arguments["limit"] = limit
        if property is not None:
            arguments["property"] = property
        if len(kwargs.keys()) > 0:
            arguments["excludeSoftDeleted"] = kwargs.get("excludeSoftDeleted", True)
            arguments["excludeHidden"] = kwargs.get("excludeHidden", True)
            arguments["isPrevLink"] = kwargs.get("isPrevLink", "")
        res = self.connector.getData(self.endpoint + path, params=arguments)
        data = res["queries"]
        nextPage = res["_links"].get("next", {}).get("href", "")
        while nextPage != "":
            hrefParams = nextPage.split("?")[1]
            orderBy = re.search("orderby=(.+?)(&|$)", hrefParams)
            start = re.search("start=(.+?)(&|$)", hrefParams)
            arguments["start"] = start.group(1)
            arguments["orderby"] = orderBy.group(1)
            res = self.connector.getData(self.endpoint + path, params=arguments)
            data += res.get("queries", [])
            nextPage = res.get("_links", {}).get("next", {}).get("href", "")
            if n_results < float(
                len(data)
            ):  ## forcing exit when reaching number of results asked
                nextPage = ""
        return data

    def postQueries(
        self,
        data: dict = None,
        name: str = None,
        dbname: str = "prod:all",
        sql: str = None,
        templateId: str = None,
        queryParameters: dict = None,
        insertIntoParameters: dict = None,
        ctasParameters: dict = None,
        description: str = "",
        **kwargs,
    ) -> dict:
        """
        Create a query.
        Arguments:
            data : OPTIONAL : If you want to pass the full query statement.
            name : REQUIRED : Name of the query
            dbname : REQUIRED : the dataset name (default prod:all)
            sql: REQUIRED : the SQL query as a string.
            queryParameters : OPTIONAL : in case you are using template, providing the paramter in a dictionary.
            insertIntoParameters : OPTIONAL : in case you want to insert the result to an existing dataset
                example : {
                    "datasetName": "string"
                }
            ctasParameters: OPTIONAL : in case you want to create a dataset out of that query, dictionary is required with "datasetName" and "description".
                example : {
                    "datasetName": "string",
                    "description": "string",
                    "targetSchemaTitle":"string"
                    }
                    targetSchemaTitle if you want to use a precreated schema.
        """
        path = "/queries"
        if self.loggingEnabled:
            self.logger.debug(f"Starting postQuery")
        if data is None:
            if (sql is None and templateId is None) or name is None:
                raise AttributeError("You are missing required arguments.")
            if type(ctasParameters) is dict:
                if (
                    "datasetName" not in ctasParameters.keys()
                    or "description" not in ctasParameters.keys()
                ):
                    raise KeyError(
                        'Expecting "datasetName" and "description" as part of the the ctasParameters dictionary.'
                    )
            data = {
                "name": name,
                "description": description,
                "dbName": dbname
            }
            if sql is not None:
                data["sql"] = sql
            if templateId is not None:
                data["templateId"] = templateId
            if queryParameters is not None:
                data["queryParameters"] = queryParameters
            if ctasParameters is not None:
                data["ctasParameters"] = ctasParameters
            if insertIntoParameters is not None:
                data["insertIntoParameters"] = insertIntoParameters
        res = self.connector.postData(
            self.endpoint + path, data=data, headers=self.header
        )
        return res

    def getQuery(self, queryId: str = None) -> dict:
        """
        Request the query status by ID.
        Argument :
            queryid : REQUIRED : the query id to check
        """
        if queryId is None:
            raise AttributeError('Expected "queryId" to be filled')
        if self.loggingEnabled:
            self.logger.debug(f"Starting getQuery")
        path = f"/queries/{queryId}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def cancelQuery(self, queryId: str = None) -> dict:
        """
        Cancel a specific query based on its ID.
        Argument:
            queryId : REQUIRED : the query ID to cancel
        """
        if queryId is None:
            raise AttributeError('Expected "queryId" to be filled')
        if self.loggingEnabled:
            self.logger.debug(f"Starting cancelQuery")
        path = f"/queries/{queryId}"
        data = {"op": "cancel"}
        res = self.connector.patchData(self.endpoint + path, data=data)
        return res

    def deleteQuery(self, queryId: str = None) -> dict:
        """
        Delete a specific query based on its ID.
        Argument:
            queryId : REQUIRED : the query ID to delete
        """
        if queryId is None:
            raise AttributeError('Expected "queryId" to be filled')
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteQuery")
        path = f"/queries/{queryId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def getSchedules(self, n_results: int = 1000, **kwargs) -> list:
        """
        Retrieve a list of scheduled queries for the AEP instance.
        Arguments:
            n_results : OPTIONAL : Total number of scheduled queries retrieved. To get them all, use "inf"
        possibile kwargs:
            orderby : + for ASC and - for DESC
            limit : number of record to fetch
            start : specific start (use with orderby)
            property : Comma-separated filters.
                created ; ex : created>2017-04-05T13:30:00Z
                templateId ; ex : templateId==123412354
                userId ; ex : userId==12341235
        """
        n_results = float(n_results)
        if kwargs.get("orderby", None) is not None:
            if kwargs.get("orderby", "-") == "+":
                kwargs.get("orderby", "-") == "%2B"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchedules")
        path = "/schedules"
        params = {**kwargs}
        res = self.connector.getData(self.endpoint + path, params=params)
        data = res["schedules"]
        nextPage = res["_links"].get("next", {}).get("href", "")
        while nextPage != "":
            hrefParams = nextPage.split("?")[1]
            orderBy = re.search("orderby=(.+?)(&|$)", hrefParams)
            start = re.search("start=(.+?)(&|$)", hrefParams)
            params["start"] = start.group(1)
            params["orderby"] = orderBy.group(1)
            res = self.connector.getData(self.endpoint + path, params=params)
            data += res.get("schedules", [])
            nextPage = res["_links"].get("next", {}).get("href", "")
            if len(data) > float(n_results):
                nextPage = ""
        return data

    def getSchedule(self, scheduleId: str = None) -> dict:
        """
        Get a details about a schedule query.
        Arguments:
            scheduleId : REQUIRED : the schedule id
        """
        if scheduleId is None:
            raise Exception("scheduleId is required")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSchedule")
        path = f"/schedules/{scheduleId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def getScheduleRuns(self, scheduleId: str = None) -> list:
        """
        Get the different jobs ran for this schedule
        Arguments:
            scheduleId : REQUIRED : the schedule id
        """
        if scheduleId is None:
            raise Exception("scheduleId is required")
        path = f"/schedules/{scheduleId}/runs"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getScheduleRuns")
        params = {}
        res = self.connector.getData(self.endpoint + path)
        data = res["runsSchedules"]
        nextPage = res["_links"].get("next", {}).get("href", "")
        while nextPage != "":
            hrefParams = nextPage.split("?")[1]
            orderBy = re.search("orderby=(.+?)(&|$)", hrefParams)
            start = re.search("start=(.+?)(&|$)", hrefParams)
            params["start"] = start.group(1)
            params["orderby"] = orderBy.group(1)
            res = self.connector.getData(self.endpoint + path, params=params)
            data += res.get("runsSchedules", [])
            nextPage = res["_links"].get("next", {}).get("href", "")
        return data

    def getScheduleRun(self, scheduleId: str = None, runId: str = None) -> dict:
        """
        Get the different jobs ran for this schedule
        Arguments:
            scheduleId : REQUIRED : the schedule id
            runId : REQUIRED : the run ID you want to retrieve.
        """
        if scheduleId is None or runId is None:
            raise Exception("scheduleId and jobId are required")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getScheduleRun")
        path = f"/schedules/{scheduleId}/runs/{runId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def createSchedule(
        self,
        scheduleQuery: dict = None,
        name: str = None,
        dbname: str = "prod:all",
        sql: str = None,
        templateId: str = None,
        queryParameters: dict = None,
        insertIntoParameters: dict = None,
        ctasParameters: dict = None,
        schedule: dict = None,
        description: str = "",
        **kwargs,
    ) -> dict:
        """
        Create a scheduled query.
        Arguments:
            scheduleQuery: REQUIRED : a dictionary containing the query and the schedule.
            name : OPTIONAL : Name of the query
            dbname : OPTIONAL : the dataset name (default prod:all)
            sql: OPTIONAL : the SQL query as a string.
            templateId : OPTIONAL : The Template ID to be used
            queryParameters : OPTIONAL : in case you are using template, providing the paramter in a dictionary.
            ctasParameters: OPTIONAL : in case you want to create a dataset out of that query, dictionary is required with "datasetName" and "description".
            schedule : OPTIONAL : Dictionary giving the instruction to schedule the query.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createSchedule")
        if scheduleQuery is None:
            if name is None or (sql is None and templateId is None) or schedule is None:
                raise Exception(
                    "Expecting either scheduleQUery dictionary or data in parameters"
                )
            scheduleQuery = {
                "query": {
                    "name": name,
                    "description": description,
                    "dbName": dbname
                },
                "schedule": schedule,
            }
            if sql is not None:
                scheduleQuery["query"]["sql"] = sql
            if templateId is not None:
                scheduleQuery["query"]["templateId"] = templateId
            if queryParameters is not None:
                scheduleQuery["query"]["queryParameters"] = queryParameters
            if ctasParameters is not None:
                scheduleQuery["query"]["ctasParameters"] = ctasParameters
            if insertIntoParameters is not None:
                scheduleQuery["query"]["insertIntoParameters"] = insertIntoParameters
        if type(scheduleQuery) != dict:
            raise Exception("scheduleQuery is required and should be dictionary. ")
        if (
            "query" not in scheduleQuery.keys()
            or "schedule" not in scheduleQuery.keys()
        ):
            raise Exception(
                'scheduleQuery dictonary is expected to contain "schedule" or "query" keys.'
            )
        path = "/schedules"
        res = self.connector.postData(self.endpoint + path, data=scheduleQuery)
        return res

    def deleteSchedule(self, scheduleId: str = None) -> Union[str, dict]:
        """
        Delete a scheduled query.
        Arguments:
            scheduleId : REQUIRED : id of the schedule.
        """
        if scheduleId is None:
            raise Exception("Missing scheduleId")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteSchedules")
        path = f"/schedules/{scheduleId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def disableSchedule(self, scheduleId: str = None) -> dict:
        """
        Disable a scheduled query.
        Arguments:
            scheduleId : REQUIRED : id of the schedule.
        """
        if scheduleId is None:
            raise Exception("Missing scheduleId")
        if self.loggingEnabled:
            self.logger.debug(f"Starting disableSchedules")
        obj = {"body": [{"op": "replace", "path": "/state", "value": "disable"}]}
        path = f"/schedules/{scheduleId}"
        res = self.connector.patchData(
            self.endpoint + path, data=obj, headers=self.header
        )
        return res

    def enableSchedule(self, scheduleId: str = None) -> dict:
        """
        Enable a scheduled query.
        Arguments:
            scheduleId : REQUIRED : id of the schedule.
        """
        if scheduleId is None:
            raise Exception("Missing scheduleId")
        if self.loggingEnabled:
            self.logger.debug(f"Starting enableSchedule")
        obj = {"body": [{"op": "replace", "path": "/state", "value": "enable"}]}
        path = f"/schedules/{scheduleId}"
        res = self.connector.patchData(
            self.endpoint + path, data=obj, headers=self.header
        )
        return res

    def updateSchedule(self, scheduleId: str = None, update_obj: list = None) -> dict:
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
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateSchedules")
        path = f"/schedules/{scheduleId}"
        res = self.connector.patchData(
            self.endpoint + path, data=update_obj, headers=self.header
        )
        return res

    def getTemplates(self, n_results: int = 1000, **kwargs) -> dict:
        """
        Retrieve the list of template for this instance.
        Arguments:
            n_results : OPTIONAL : number of total results to retrieve. To get them all, use "inf".
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
        if self.loggingEnabled:
            self.logger.debug(f"Starting getTemplates")
        path = "/query-templates"
        n_results = float(n_results)  # changing inf to float inf
        params = {**kwargs}
        params["limit"] = kwargs.get("limit", 50)
        res = self.connector.getData(
            self.endpoint + path, headers=self.header, params=params
        )
        data = res["templates"]
        nextPage = res["_links"].get("next", {}).get("href", "")
        while nextPage != "":
            hrefParams = nextPage.split("?")[1]
            orderBy = re.search("orderby=(.+?)(&|$)", hrefParams)
            start = re.search("start=(.+?)(&|$)", hrefParams)
            params["start"] = start.group(1)
            params["orderby"] = orderBy.group(1)
            res = self.connector.getData(self.endpoint + path, params=params)
            data += res.get("templates", [])
            nextPage = res.get("_links", {}).get("next", {}).get("href", "")
            if len(data) > float(n_results):
                nextPage = ""
        return data

    def getTemplate(self, templateId: str = None) -> dict:
        """
        Retrieve a specific template ID.
        Arguments:
            templateId : REQUIRED : template ID to be retrieved.
        """
        if templateId is None:
            raise ValueError("Require a template ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getTemplate")
        path = f"/query-templates/{templateId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def deleteTemplate(self, templateId: str = None) -> dict:
        """
        Delete a template based on its ID.
        Arguments:
            templateId : REQUIRED : template ID to be deleted.
        """
        if templateId is None:
            raise ValueError("Require a template ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteTemplate")
        path = f"/query-templates/{templateId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def createQueryTemplate(self, queryData: dict = None) -> dict:
        """
        Create a query template based on the dictionary passed.
        Arguments:
            queryData : REQUIED : An object that contains "sql", "queryParameter" and "name" keys.
        more info : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Query-Templates/create_query_template
        """
        path = "/query-templates"
        if self.loggingEnabled:
            self.logger.debug(f"Starting createTemplate")
        if isinstance(queryData, dict):
            if (
                "sql" not in queryData.keys()
                or "queryParameters" not in queryData.keys()
                or "name" not in queryData.keys()
            ):
                raise KeyError(
                    "Minimum key value are not respected.\nPlease see here for more info :\nhttps://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Query-Templates/create_query_template "
                )
        else:
            raise Exception("expected a dictionary for queryData")
        res = self.connector.postData(
            self.endpoint + path, headers=self.header, data=queryData
        )
        return res
    
    def getDatasetStatistics(self,datasetId:str=None,statisticType:str="table HTTP/1.1")->dict:
        """
        Returns statistics on the dataset size.
        Arguments:
            datasetId : REQUIRED : The dataset ID to look for.
            statisticType : OPTIONAL : The type of statistic to retrieve.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDatasetStatistics")
        if datasetId is None:
            raise Exception("A datasetId is required")
        path = "/statistics"
        params = {"dataSet":datasetId,"statisticType":statisticType}
        res = self.connector.getData(self.endpoint + path,params=params)
        return res
    
    def getAlertSubscriptions(self,n_results: int = 1000, **kwargs)->list:
        """
        Get the list of alerts subscriptions.
        Arguments:
            n_results : OPTIONAL : The total number of result you want.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getAlertSubscriptions")
        params = {"page":kwargs.get("page",0)}
        path = f"/alert-subscriptions"
        res = self.connector.getData(self.endpoint + path,params=params)
        data = res.get("alerts")
        count = res.get("_page",{}).get('count',0)
        nextpage = res.get('_links',{}).get('next',{}).get('href','')
        while nextpage != "" and count <n_results:
            params["page"] += 1
            res = self.connector.getData(self.endpoint + path,params=params)
            data += res.get("alerts")
            count += res.get("_page",{}).get('count',0)
            nextpage = res.get('_links',{}).get('next',{}).get('href','')
        return data
    
    def createAlertSubscription(self,assetId:str=None,alertType:str=None,emails:list=None,inAEP:bool=True,inEmail:bool=True)->dict:
        """
        Create a subscription to an asset (queryID or scheduleID) for a list of predefined users.
        Arguments:
            assetId : REQUIRED : The schedule ID or query ID.
            alertType : REQUIRED : The type of alert to listen to. (start, success, failure)
            emails : REQUIRED : A list of email addresses that subscribes to that alert.
            inAEP : OPTIONAL : If the Alert should show up in AEP UI. (default True)
            inEmail : OPTIONAL : If the Alert should be sent via email. (default True)
                NOTE: Consider setting your email address for notification via this tutorial:
                https://experienceleague.adobe.com/docs/experience-platform/observability/alerts/ui.html?lang=en#enable-email-alerts
        """
        if assetId is None:
            raise ValueError("Require an asset ID")
        if alertType is None:
            raise ValueError("Require an alert type")
        if emails is None or type(emails) != list:
            raise ValueError("Require a list of email addresses")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createAlertSubscription for asset: {assetId}")
        path = f"/alert-subscriptions"
        data = {
            "assetId": assetId,
            "alertType": alertType,
            "subscriptions":{
                "emailIds" : emails,
                "inContextNotifications" : inAEP,
                "emailNotifications":inEmail
            }  
        }
        res = self.connector.postData(self.endpoint+path, data=data)
        return res
    
    def deleteAlertSubscription(self,assetId:str=None, alertType:str=None)->dict:
        """
        Delete a subscription for a specific alert on a specifc assetId.
        Arguments
            assetId : REQUIRED : A query ID or a schedule ID that you want to delete the alert for.
            alertType : REQUIRED : The state of query execution that triggers the alert to be deleted. (start, success, failure).
        """
        if assetId is None:
            raise ValueError("Require an asset ID")
        if alertType is None:
            raise ValueError("Require an alert type")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteAlertSubscription for asset: {assetId}")
        path = f"/alert-subscriptions/{assetId}/{alertType}"
        res = self.connector.deleteData(self.endpoint + path)
        return res
    
    def getAlertSubscriptionsTypeId(self,assetId:str=None, alertType:str=None)->dict:
        """
        Retrieve the subscriptions made about a specific asset ID and with or without alertType specification
        Arguments:
            assetId : REQUIRED : A query or schedule ID that you want the subscription information for.
            alertType : OPTIONAL : This property describes the state of query execution that triggers an alert.
                        (start, success, failure).
        """
        if assetId is None:
            raise ValueError("Require an asset ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getAlertSubscriptionsTypeId for asset: {assetId}")
        if alertType is None:
            path = f"/alert-subscriptions/{assetId}"
        elif alertType is not None and type(alertType) == str:
            path = f"/alert-subscriptions/{assetId}/{alertType}"
        res = self.connector.getData(self.endpoint + path)
        return res.get('alerts')
    
    def patchAlert(self,assetId:str=None, alertType:str=None,action:str="disable")->dict:
        """
        Disable or Enable an alert by providing the assetId and the alertType.
        Arguments:
            assetId : REQUIRED : A query or schedule ID that you want the subscription information for.
            alertType : REQUIRED : This property describes the state of query execution that triggers an alert.
                        (start, success, failure)
            action : OPTIONAL : the action to take on that Alert. "disable" (default) or "enable"
        """
        if assetId is None:
            raise ValueError("Require an asset ID")
        if alertType is None:
            raise ValueError("Require an alert Type")
        if self.loggingEnabled:
            self.logger.debug(f"Starting patchAlert for asset: {assetId}, action : {action}")
        path = f"/alert-subscriptions/{assetId}/{alertType}"
        data = {
            "op":"replace",
            "path":"/status",
            "value":action
        }
        res = self.connector.patchData(self.endpoint + path,data=data)
        return res
    
    def getUserAlerts(self,email:str=None)->list:
        """
        Get the alert that a specific user is subscribed to.
        Argument:
            email : REQUIRED : the email address of the user
        """
        if email is None:
            raise ValueError("Require a valid email address")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getUserAlerts for user: {email}")
        params = {'page':0}
        path = f"/alert-subscriptions/user-subscriptions/{email}"
        res = self.connector.getData(self.endpoint + path)
        data = res.get('items')
        nextPage = res.get('_links',{}).get('next',{}).get('href','')
        while nextPage != "":
            params['page'] +=1
            res = self.connector.getData(self.endpoint + path,params=params)
            data += res.get('items')
            nextPage = res.get('_links',{}).get('next',{}).get('href','')
        return data
    
    def createAcceleratedQuery(self,name:str=None,dbName:str=None,sql:str=None,templateId:str=None,description:str="power by aepp")->dict:
        """
        Create an accelerated query statement based on either an SQL statement or a template ID.
        Arguments:
            name : REQUIRED : Name of your query
            dbName : REQUIRED : The name of the database you are making an accelerated query to. 
                        The value for dbName should take the format of {SANDBOX_NAME}:{ACCELERATED_STORE_DATABASE}:{ACCELERATED_STORE_SCHEMA}
            sql : REQUIRED : Either this parameter with a SQL statement or a templateId in the "templateId" parameter.
            templateId : REQUIRED : Either this parameter with a template ID or a SQL statement in the "sql" parameter.
            description : OPTIONAL : An optional comment on the intent of the query to help other users understand its purpose. Max 1000 bytes.
        """
        if name is None:
            raise ValueError("Require a name")
        if dbName is None or len(dbName.split(":")) != 3:
            raise ValueError("Require a dbName such as : {SANDBOX_NAME}:{ACCELERATED_STORE_DATABASE}:{ACCELERATED_STORE_SCHEMA}")
        if templateId is None and sql is None:
            raise SyntaxError("Require either an sql or a templateId parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createAcceleratedQuery with name: {name}")
        path = f"/accelerated-queries"
        data = {
            "name" : name,
            "dbName":dbName,
            "description":description,    
        }
        if sql is not None:
            data['sql'] = sql
        elif templateId is not None:
            data['templateId'] = templateId
        res = self.connector.postData(self.endpoint+path, data=data)
        return res





class InteractiveQuery:
    """
    Provide the instance connected to PostgreSQL database and you can return the result directly in your notebook.
    This class requires that you have used connection method in the QueryService.
    The object returned by the connection method should be used when creating this object.
    USING PyGreSQL

    """
    
    config_object = {}
    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(self, conn_object: dict = None, loggingObject: dict = None):
        """
        Importing the pg (PyGreSQL) library and instantiating the connection via the conn_object pass over the instantiation method.
        Arguments:
            conn_object : REQUIRED : The dictionary returned via the queryservice api "connection"
        """
        from pg import DB
        if conn_object is None:
            raise AttributeError(
                "You are missing the conn_object. Use the QueryService to retrieve the object."
            )
        self.dbname = conn_object["dbName"]
        self.host = conn_object["host"]
        self.port = conn_object["port"]
        self.user = conn_object["username"]
        self.passwd = conn_object["token"]
        self.websocketHost = conn_object["websocketHost"]
        self.config_object = {
            "dbname": self.dbname,
            "host": self.host,
            "user": self.user,
            "passwd": self.passwd,
            "port": self.port,
        }
        self.db = DB(**self.config_object)
        if loggingObject is not None and sorted(
            ["level", "stream", "format", "filename", "file"]
        ) == sorted(list(loggingObject.keys())):
            self.loggingEnabled = True
            self.logger = logging.getLogger(f"{__name__}")
            self.logger.setLevel(loggingObject["level"])
            formatter = logging.Formatter(loggingObject["format"])
            if loggingObject["file"]:
                fileHandler = logging.FileHandler(loggingObject["filename"])
                fileHandler.setFormatter(formatter)
                self.logger.addHandler(fileHandler)
            if loggingObject["stream"]:
                streamHandler = logging.StreamHandler()
                streamHandler.setFormatter(formatter)
                self.logger.addHandler(streamHandler)

    def query(
        self, sql: str = None, output: str = "dataframe"
    ) -> Union[pd.DataFrame, object]:
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
        if self.loggingEnabled:
            self.logger.debug(f"Starting query:\n {sql}")
        query = self.db.query(sql)
        if output == "raw":
            return query
        elif output == "dataframe":
            data = query.getresult()
            columns = query.listfields()
            df = pd.DataFrame(data, columns=columns)
            return df
        else:
            raise KeyError("You didn't specify a correct value.")

    def transformToDataFrame(self, query: object = None) -> pd.DataFrame:
        """
        This will return you a dataFrame
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting transformToDataFrame")
        data = query.getresult()
        columns = query.listfields()
        df = pd.DataFrame(data, columns=columns)
        return df

    def queryIdentity(
        self,
        identityId: str = None,
        fields: list = None,
        tableName: str = None,
        output: str = "dataframe",
        fieldId: str = "ECID",
        limit: str = None,
        save: bool = False,
        verbose: bool = False,
    ) -> Union[pd.DataFrame, object]:
        """
        Return the elements that you have passed in field list and return the output selected.
        Arguments:
            identityId : REQUIRED : The ID you want to retrieve
            fields : REQUIRED : a list of fields you want to return for that ID in your table.
                example : ['person.name']
            tableName : REQUIRED : The dataset table name to use
            output : OPTIONAL : the format you would like to be returned.
            Possible format:
                "raw" : return the instance of the query object.
                "dataframe" : return a dataframe with the data. (default)
            fieldId : OPTIONAL : If you want your selection to be based on another field than ECID in IdentityMap.
            limit : OPTIONAL : If you wish to set a LIMIT on number of row returned.
            save : OPTIONAL : will save a csv file
            verbose : OPTIONAL : will display some comment
        """
        if identityId is None:
            raise ValueError("Require an identity value")
        if type(fields) != list:
            raise ValueError("Require a list of fields to be returned")
        if tableName is None:
            raise ValueError("Require a dataset table name")
        if fieldId == "ECID":
            condition = f"WHERE identityMap['ECID'][0].id = '{identityId}'"
        elif fieldId != "ECID" and fieldId is not None:
            condition = f"WHERE {fieldId} = '{identityId}'"
        else:
            condition = ""
        if limit is None:
            limit = ""
        else:
            limit = f"LIMIT {limit}"
        sql = f"SELECT {','.join(fields)} FROM {tableName} {condition} {limit}"
        if verbose:
            print(sql)
        if self.loggingEnabled:
            self.logger.debug(f"Starting queryIdentity:\n {sql}")
        res = self.query(sql=sql, output=output)
        if verbose:
            print(f"Data is returned in the {output} format")
        if save:
            if isinstance(res, pd.DataFrame):
                res.to_csv(f"{identityId}.csv", index=False)
            else:
                data = res.getresult()
                columns = res.listfields()
                df = pd.DataFrame(data, columns=columns)
                df.to_csv(f"{identityId}.csv", index=False)
        return res

class InteractiveQuery2:
    """
    Provide the instance connected to PostgreSQL database and you can return the result directly in your notebook.
    This class requires that you have used connection method in the QueryService.
    The object returned by the connection method should be used when creating this object.
    USING psycopg2
    """
    
    config_object = {}
    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(self, conn_object: dict = None, loggingObject: dict = None):
        """
        Importing the psycopg2 library and instantiating the connection via the conn_object pass over the instantiation method.
        Arguments:
            conn_object : REQUIRED : The dictionary returned via the queryservice api "connection"
        """
        import psycopg2
        if conn_object is None:
            raise AttributeError(
                "You are missing the conn_object. Use the QueryService to retrieve the object."
            )
        self.dbname = conn_object["dbName"]
        self.host = conn_object["host"]
        self.port = conn_object["port"]
        self.user = conn_object["username"]
        self.passwd = conn_object["token"]
        self.config_object = {
            "dbname": self.dbname,
            "host": self.host,
            "user": self.user,
            "password": self.passwd,
            "port": self.port,
        }
        self.connect = psycopg2.connect(**self.config_object)
        if loggingObject is not None and sorted(
            ["level", "stream", "format", "filename", "file"]
        ) == sorted(list(loggingObject.keys())):
            self.loggingEnabled = True
            self.logger = logging.getLogger(f"{__name__}")
            self.logger.setLevel(loggingObject["level"])
            formatter = logging.Formatter(loggingObject["format"])
            if loggingObject["file"]:
                fileHandler = logging.FileHandler(loggingObject["filename"])
                fileHandler.setFormatter(formatter)
                self.logger.addHandler(fileHandler)
            if loggingObject["stream"]:
                streamHandler = logging.StreamHandler()
                streamHandler.setFormatter(formatter)
                self.logger.addHandler(streamHandler)

    def query(
        self, sql: str = None, output: str = "dataframe"
    ) -> Union[pd.DataFrame, object]:
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
        if self.loggingEnabled:
            self.logger.debug(f"Starting query:\n {sql}")
        cursor = self.connect.cursor()
        cursor.execute(sql)
        if output == "raw":
            return cursor
        elif output == "dataframe":
            df = pd.DataFrame(cursor.fetchall())
            df.columns = [col[0] for col in cursor.description]
            return df
        else:
            raise KeyError("You didn't specify a correct value.")

    def transformToDataFrame(self, query: object = None) -> pd.DataFrame:
        """
        Taking the raw output of the query method use with raw and returning a DataFrame
        Arguments:
            cursor : REQUIRED : The cursor that has been returned 
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting transformToDataFrame")
        df = pd.DataFrame(query.fetchall())
        df.columns = [col[0] for col in query.description]
        return df

    def queryIdentity(
        self,
        identityId: str = None,
        fields: list = None,
        tableName: str = None,
        output: str = "dataframe",
        fieldId: str = "ECID",
        limit: str = None,
        save: bool = False,
    ) -> Union[pd.DataFrame, object]:
        """
        Return the elements that you have passed in field list and return the output selected.
        Arguments:
            identityId : REQUIRED : The ID you want to retrieve
            fields : REQUIRED : a list of fields you want to return for that ID in your table.
                example : ['person.name']
            tableName : REQUIRED : The dataset table name to use
            output : OPTIONAL : the format you would like to be returned.
            Possible format:
                "raw" : return the instance of the query object.
                "dataframe" : return a dataframe with the data. (default)
            fieldId : OPTIONAL : If you want your selection to be based on another field than ECID in IdentityMap.
            limit : OPTIONAL : If you wish to set a LIMIT on number of row returned.
            save : OPTIONAL : will save a csv file
        """
        if identityId is None:
            raise ValueError("Require an identity value")
        if type(fields) != list:
            raise ValueError("Require a list of fields to be returned")
        if tableName is None:
            raise ValueError("Require a dataset table name")
        if fieldId == "ECID":
            condition = f"WHERE identityMap['ECID'][0].id = '{identityId}'"
        elif fieldId != "ECID" and fieldId is not None:
            condition = f"WHERE {fieldId} = '{identityId}'"
        else:
            condition = ""
        if limit is None:
            limit = ""
        else:
            limit = f"LIMIT {limit}"
        sql = f"SELECT {','.join(fields)} FROM {tableName} {condition} {limit}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting queryIdentity:\n {sql}")
        res = self.query(sql)
        if save:
            if isinstance(res, pd.DataFrame):
                res.to_csv(f"{identityId}.csv", index=False)
            else:
                df = pd.DataFrame(res.fetchall())
                df.columns = [col[0] for col in res.description]
                df.to_csv(f"{identityId}.csv", index=False)
        return res
