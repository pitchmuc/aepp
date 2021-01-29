import aepp
from dataclasses import dataclass
from aepp import connector
import pandas as pd

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
    Arguments:
        config : OPTIONAL : config object in the config module. 
        header : OPTIONAL : header object  in the config module.
    kwargs:
        kwargs value will update the header
    """

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.endpoint = aepp.config.endpoints['global']+aepp.config.endpoints["catalog"]
        self.data = _Data()

    def getBatches(self, n_results:int=None,**kwargs):
        """
        Retrieve a list of batches.
        Arguments:
            n_results : OPTIONAL :  number of result you want to get in total. (will loop)
        Possible kwargs:
            created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
            createdAfter : Exclusively filter records created after this timestamp. 
            createdBefore : Exclusively filter records created before this timestamp.
            start : Returns results from a specific offset of objects. This was previously called offset. (see next line)
                offset : Will offset to the next limit (sort of pagination)
            limit : Limit response to a specified positive number of objects. Ex. limit=10 (max = 100)
            updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
            createdUser : Filter by the ID of the user who created this object.
            dataSet : Used to filter on the related object: &dataSet=dataSetId.
            version : Filter by Semantic version of the account. Updated when the object is modified.
            status : Filter by the current (mutable) status of the batch.
            orderBy : Sort parameter and direction for sorting the response. 
                Ex. orderBy=asc:created,updated. This was previously called sort.
            property : A comma separated whitelist of top-level object properties to be returned in the response. 
                Used to cut down the number of properties and amount of data returned in the response bodies.
            size : The number of bytes processed in the batch.
        # /Batches/get_batch
        more details : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        path = "/batches"
        params = {**kwargs}
        ## looping to retrieve pagination
        if n_results is not None:
            list_results = []
            params['limit'] = 100
            params['start'] = 0
            res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
            list_results += res
            while len(list_results) < n_results and res != 0:
                params['start'] += 100
                res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
                list_results += res
            return list_results
        res = self.connector.getData(self.endpoint+path,
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
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header)
        return res
    
    def createBatch(self, object:dict=None,**kwargs) -> dict:
        """
        Create a new batch.
        Arguments:
            object : REQUIRED : Object that define the data to be onboarded.
                see reference here: https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Batches/postBatch
        """
        if object is None:
            raise Exception('expecting a definition of the data to be uploaded.')
        path = "/batches"
        res = self.connector.postData(self.endpoint+path,data=object,
                            headers=self.header)
        return res

    def getResources(self, **kwargs)->list:
        """
        Retrieve a list of resource links for the Catalog Service.
        Possible kwargs:
            limit : Limit response to a specified positive number of objects. Ex. limit=10
            orderBy : Sort parameter and direction for sorting the response. 
                Ex. orderBy=asc:created,updated. This was previously called sort.
            property : A comma separated whitelist of top-level object properties to be returned in the response. 
                Used to cut down the number of properties and amount of data returned in the response bodies.
        """
        path = "/"
        params = {**kwargs}
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
        return res


    def getDataSets(self,output:str="raw",**kwargs)->dict:
        """
        Return a list of a datasets.
        Arguments:
            output : OPTIONAL : Default is "raw", other option is "df" for dataframe output
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
        res = self.connector.getData(self.endpoint+path,
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
        if output == "df":
            res = pd.DataFrame(res).T
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
        res = self.connector.postData(self.endpoint+path, params=params,
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
        res = self.connector.getData(self.endpoint+path, headers=self.header)
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
        res = self.connector.deleteData(self.endpoint+path, headers=self.header)
        return res

    ## Apparently deprecated.
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
        path = f"/dataSets/{dataset_id}/views"
        params = {**kwargs}
        res = self.connector.getData(self.endpoint+path, headers=self.header)
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
        path = f"/dataSets/{dataset_id}/views/{view_id}"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
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
        path = f"/dataSets/{dataset_id}/views/{view_id}/files"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res
