import aepp
from aepp import config
from copy import deepcopy
import re
import typing
from dataclasses import dataclass


@dataclass
class _Data:

    def __init__(self):
        self.table_names = {}
        self.schema_ref = {}
        self.ids = {}


class Catalog:
    """
    Catalog class from the AEP API. This class helps you to find where the data are coming from in AEP.
    More details here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#
    It possess a data attribute that is containing information about your datasets. 
    """

    def __init__(self, **kwargs):
        self.header = deepcopy(aepp.config._header)
        self.header['Accept'] = "application/vnd.adobe.xdm+json"
        self.header.update(**kwargs)
        self.endpoint = config._endpoint+config._endpoint_catalog
        self.data = _Data()

    def getAccounts(self, **kwargs):
        """
        Returns the list of all account.
        Possible kwargs:
            connector : The ID for the Connector this Account params was created from
            description : Filter by user-provided description of the account.
            version : Filter by Semantic version of the account. Updated when the object is modified.
            created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
            updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
            createdUser : Filter by the ID of the user who created this object.
            property : Regex used to filter objects in the response. Ex. property=name~^test.
        # /Accounts/get_accounts
        more details : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        path = "/accounts/"
        params = {**kwargs}
        res = aepp._getData(self.endpoint+path,
                            headers=self.header, params=params)
        return res

    def getAccount(self, account_id: str = None):
        """
        Get a specific Account based on the id.
        Arguments:
            account_id : REQUIRED : object ID
        """
        if account_id is None:
            raise Exception("Require an account_id")
        path = f"/accounts/{account_id}"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def createAccount(self, data: dict = None):
        """
        Create a new account.
        Arguments:
            data : REQUIRED : Object that should describe the new connector.
        More information on data requirement can be found here :
        https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Accounts/post_account
        """
        if type(data) != dict:
            raise TypeError("data should a dictionary")
        elif "params" not in data.keys():
            raise AttributeError("params should be part of the dictionnary")
        path = "/accounts/"
        res = aepp._postData(self.endpoint+path,
                             headers=self.header, data=data)
        return res

    def updateAccount(self, account_id: str = None, data: dict = None):
        """
        Update an account.
        Arguments:
            account_id : REQUIRED : account id to be udpated.
            data : REQUIRED : Object that should describe the new connector.
        """
        if account_id is None:
            raise Exception("Require an account_id")
        elif type(data) != dict:
            raise TypeError("data should a dictionary")
        elif "params" not in data.keys():
            raise AttributeError("params should be part of the dictionnary")
        path = f"/accounts/{account_id}"
        res = aepp._putData(self.endpoint+path,
                            headers=self.header, data=data)
        return res

    def deleteAccount(self, account_id: str = None):
        """
        Delete an account.
        Arguments:
            account_id : REQUIRED : account id to be deleted.
        """
        if account_id is None:
            raise Exception("Require an account_id")
        path = f"/accounts/{account_id}"
        res = aepp._deleteData(self.endpoint+path,
                               headers=self.header)
        return res

    def getBatches(self, **kwargs):
        """
        Retrieve a list of batches.
        Possible kwargs:
            created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
            createdAfter : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
            limit : Limit response to a specified positive number of objects. Ex. limit=10
            updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
            createdUser : Filter by the ID of the user who created this object.
            dataSet : Used to filter on the related object: &dataSet=dataSetId.
            version : Filter by Semantic version of the account. Updated when the object is modified.
            property : Regex used to filter objects in the response. Ex. property=name~^test.
        # /Batches/get_batch
        more details : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        path = "/batches"
        params = {**kwargs}
        res = aepp._getData(self.endpoint+path,
                            headers=self.header, params=params)
        return res

    def getBatch(self, batch_id: str = None):
        """
        Get a specific batch id.
        Arguments:
            batch_id : REQUIRED : batch ID to be retrieved.
        """
        if batch_id is None:
            raise Exception("batch_id parameter is required.")
        path = f"/batches/{batch_id}"
        res = aepp._getData(self.endpoint+path,
                            headers=self.header)
        return res

    def getConnectors(self, **kwargs):
        """
        Returns the list of connectors
        Possible kwargs:
            name : Filter by the name of this Connector.
            type : Filter by the ingest type for this Connector.
            category : Connectors currently have 2 categories: 1) standard: we are connecting to a known source with known data (ie. other companies data stores) or 2) custom: a generic connector to FTP or S3 etc.
            limit : Limit response to a specified positive number of objects. Ex. limit=10
            version : Filter by Semantic version of the account. Updated when the object is modified.
            property : Regex used to filter objects in the response. Ex. property=name~^test.
        """
        path = "/connectors"
        params = {**kwargs}
        res = aepp._getData(self.endpoint+path,
                            headers=self.header, params=params)
        return res

    def getConnector(self, connector_id: str = None, stats: bool = False):
        """
        Returns a scpecific connector details and its stats if required in the parameter.
        Arguments:
            connector_id : REQUIRED : connector id for the connector to be retrieved.
            stats : OPTIONAL : If set to True, return a 2nd object with the stat of the connector.
        """
        if connector_id is None:
            raise Exception("Expected a connector_id parameter.")
        path = f"/connectors/{connector_id}"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        if stats == False:
            return res
        elif stats:
            stats = self.getConnectorStats(connector_id)
            return res, stats

    def getConnectorStats(self, connector_id: str = None):
        """
        Retrieve the stats for a specific connector.
        Arguments:
            connector_id : REQUIRED : connector id for the connector stats to be retrieved.
        """
        if connector_id is None:
            raise Exception("Expected a connector_id parameter.")
        path = f"/connectors/{connector_id}/stats"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def getConnections(self, **kwargs):
        """
        Returns list of connections.
        Possible kwargs:
            connector : Filter by the ID for the Connector this Connection was created from.
            parentConnectionId : Used in cases where global/shared data is managed by this connection. The parent connection performs the ETL/Mapping jobs, and this child connection represents a customer’s membership and visibility into the parent.
            name : Filter by the user-facing name of this Connection.
            accountId : Filter by the foreign key to the account where the credentials and related fields of the connector and connection combination is stored.
            description : Filter by the user-provided description of the Connection.
            enabled : Indicates the status of the Connection. Should be interpreted as disabled or suspended when set to false.
            created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
            limit : Limit response to a specified positive number of objects. Ex. limit=10
        # /Connections/get_connections
        More info can be found here : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        path = "/connections"
        params = {**kwargs}
        res = aepp._getData(self.endpoint+path,
                            headers=self.header, params=params)
        return res

    def getConnection(self, connection_id: str = None):
        """
        Retrieve a specific connection
        Arguments:
            connection_id : REQUIRED : ID of the connection to retrieve.
        """
        if connection_id is None:
            raise Exception("Expected a connection_id parameter")
        path = f"/connections/{connection_id}"
        res = aepp._getData(self.endpoint+path,
                            headers=self.header)
        return res

    def createConnection(self, data: dict = None):
        """
        create a new connection for data ingestion.
        """
        if type(data) != dict:
            raise TypeError("data should a dictionary")
        path = "/connections"
        res = aepp._postData(self.endpoint+path,
                             headers=self.header)
        return res

    def updateConnection(self, connection_id: str = None, data: dict = None):
        """
        Update the connection based on the data passed.
        Arguments:
            connection_id : REQUIRED : id of the connection to be updated
            data : REQUIRED : Object to update the data.
        Note : This is using the put statement.
        """
        if connection_id is None:
            raise Exception("Expected connection connection_id as argument")
        elif data is None or type(data) != dict:
            raise TypeError("Expected dictionary on the data argument")
        path = f"/connections/{connection_id}"
        res = aepp._putData(self.endpoint+path, data=data, headers=self.header)
        return res

    def deleteConnection(self, connection_id: str = None):
        """
        Delete a connection.
        Argument:
            connection_id : REQUIRED : ID of the connection to be deleted.
        """
        if connection_id is None:
            raise Exception("Expected connection connection_id as argument")
        path = f"/connections/{connection_id}"
        res = aepp._deleteData(self.endpoint+path, headers=self.header)
        return res

    def getConnectionDataSets(self, connection_id: str = None):
        """
        Return the dataSet attached to the conenction
        Arguments:
            connection_id : REQUIRED : ID of the connection.
        """
        if connection_id is None:
            raise Exception("Expected connection connection_id as argument")
        path = f"/connections/{connection_id}/dataSets"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def getDataSets(self, **kwargs):
        """
        Return a list of a datasets.
        Possible kwargs:
            state : The state related to a dataset.
            created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
            updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
            name : Filter by the a descriptive, human-readable name for this DataSet.
            namespace : One of the registered platform acronyms that identify the platform.
            version : Filter by Semantic version of the account. Updated when the object is modified.
            property : Regex used to filter objects in the response. Ex. property=name~^test.
            # /Datasets/get_data_sets
            more possibilities : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        path = "/dataSets"
        params = {**kwargs}
        res = aepp._getData(self.endpoint+path,
                            headers=self.header, params=params)
        try:
            self.data.table_names = {
                res[key]['name']: res[key]['tags']['adobe/pqs/table'] for key in res}
            self.data.schema_ref = {
                res[key]['name']: res[key]['schemaRef']
                for key in res if 'schemaRef' in res[key].keys()
            }
            self.data.ids = {
                res[key]['name']: key for key in res
            }
        except Exception as e:
            print(e)
            print("Couldn't populate the data object from the instance.")
        return res

    def createDataSets(self, data: dict = None, **kwargs):
        """
        Create a new dataSets.
        Arguments:
            data : REQUIRED : Data set to be posted
        possible kwargs
            requestDataSource : Set to true if you want Catalog to create a dataSource on your behalf; otherwise, pass a dataSourceId in the body.
        """
        path = "/dataSets"
        if data is None or isinstance(data, dict) == False:
            raise Exception("Excepting data of type dictionary")
        params = {"requestDataSource": kwargs.get("requestDataSource", False)}
        res = aepp._postData(self.endpoint+path, params=params,
                             data=data, headers=self.header)
        return res

    def getDataSet(self, dataset_id: str = None):
        """
        Return a single dataset.
        Arguments:
            dataset_id : REQUIRED : Id of the dataset to be retrieved.
        """
        if dataset_id is None:
            raise Exception("Expected a dataset_id argument")
        path = f"/dataSets/{dataset_id}"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def deleteDataSet(self, dataset_id: str = None):
        """
        Delete a dataset by its id.
        Arguments:
            dataset_id : REQUIRED : Id of the dataset to be deleted.
        """
        if dataset_id is None:
            raise Exception("Expected a dataset_id argument")
        path = f"/dataSets/{dataset_id}"
        res = aepp._deleteData(self.endpoint+path, headers=self.header)
        return res

    def getDataSetViews(self, dataset_id: str = None, **kwargs):
        """
        Get views of the datasets.
        Arguments:
            dataset_id : REQUIRED : Id of the dataset to be looked down.
        Possible kwargs:
            limit : Limit response to a specified positive number of objects. Ex. limit=10
            orderBy : Sort parameter and direction for sorting the response. Ex. orderBy=asc:created,updated.
            start : Returns results from a specific offset of objects. This was previously called offset. Ex. start=3.
            property : Regex used to filter objects in the response. Ex. property=name~^test.
        """
        if dataset_id is None:
            raise Exception("Expected a dataset_id argument")
        path = f"dataSets/{dataset_id}/views"
        params = {**kwargs}
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def getDataSetView(self, dataset_id: str = None, view_id: str = None):
        """
        Get a specific view on a specific dataset.
        Arguments:
            dataset_id : REQUIRED : ID of the dataset to be looked down.
            view_id : REQUIRED : ID of the view to be look upon.
        """
        if dataset_id is None or view_id is None:
            raise Exception("Expected a dataset_id and an view_id argument")
        path = f"dataSets/{dataset_id}/views/{view_id}"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def getDataSetViewFiles(self, dataset_id: str = None, view_id: str = None):
        """
        Returns the list of files attached to a view in a Dataset.
        Arguments:
            dataset_id : REQUIRED : ID of the dataset to be looked down.
            view_id : REQUIRED : ID of the view to be look upon.
        """
        if dataset_id is None or view_id is None:
            raise Exception("Expected a dataset_id and an view_id argument")
        path = f"dataSets/{dataset_id}/views/{view_id}/files"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res
