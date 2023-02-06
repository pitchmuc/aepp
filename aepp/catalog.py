import aepp
from dataclasses import dataclass
from aepp import connector
import pandas as pd
from copy import deepcopy
from typing import Union
import time
import codecs
import json
import logging
from itertools import zip_longest
import re
from .configs import ConnectObject

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
        config : OPTIONAL : config object in the config module (DO NOT MODIFY)
        header : OPTIONAL : header object  in the config module (DO NOT MODIFY)
        loggingObject : OPTIONAL : If you want to set logging capability for your actions.
    kwargs:
        kwargs value will update the header
    """
    loggingEnabled = False
    logger = None

    def __init__(self,
                config : Union[dict,ConnectObject]=aepp.config.config_object,
                header : dict=aepp.config.header,
                loggingObject:dict=None,
                **kwargs):
        if loggingObject is not None and sorted(["level","stream","format","filename","file"]) == sorted(list(loggingObject.keys())):
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
            config_object=config, 
            header=header,
            loggingEnabled=self.loggingEnabled,
            logger=self.logger)
        self.header = self.connector.header
        self.header.update(**kwargs)
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.endpoint = aepp.config.endpoints['global']+aepp.config.endpoints["catalog"]
        self.data = _Data()

    def getResource(self,endpoint:str=None,params:dict=None,format:str='json',save:bool=False,**kwargs)->dict:
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
            self.logger.debug(f"Using getResource with following format ({format}) to the following endpoint: {endpoint}")
        res = self.connector.getData(endpoint,params=params,format=format)
        if save:
            if format == 'json':
                aepp.saveFile(module="catalog",file=res,filename=f"resource_{int(time.time())}",type_file="json",encoding=kwargs.get("encoding",'utf-8'))
            elif format == 'txt':
                aepp.saveFile(module="catalog",file=res,filename=f"resource_{int(time.time())}",type_file="txt",encoding=kwargs.get("encoding",'utf-8'))
            else:
                print("element is an object. Output is unclear. No save made.\nPlease save this element manually")
        return res
    
    def decodeStreamBatch(self,message:str)->dict:
        """
        Decode the full txt batch via the codecs module.
        Usually the full batch is returned by the getResource method with format == "txt".
        Arguments:
            message: REQUIRED : the text file return from the failed batch message.
        
        return None when issue is raised
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting decodeStreamBatch")
        try: 
            decodeMessage = codecs.escape_decode(message)[0].decode().replace('"body":"{','"body":{').replace('}","header":"{','},"header":{').replace('}","_errors":"{','},"_errors":{').replace('}"','}')
            return decodeMessage
        except:
            print("Issue decoding the message.")
            return None

    def jsonStreamMessages(self,message:str,verbose:bool = False)->list:
        """
        Try to create a list of dictionary messages from the decoded stream batch extracted from the decodeStreamBatch method.
        Arguments:
            message : REQUIRED : a decoded text file, usually returned from the decodeStreamBatch method
            verbose : OPTIONAL : print errors and information on the decoding.
        
        return None when issue is raised
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting jsonStreamMessages")
        try:
            myList = []
            myYield:iter = (line for line in message.split("\n"))
            countLine,countErrors = 0,0
            for element in myYield:
                countLine +=1
                try:
                    myList.append(json.loads(element))

                except Exception as e:
                    countErrors+=1
                    if verbose:
                        print(e)
            if verbose:
                print(f"error rate is {(countErrors/countLine)*100:.2f}%")
            return myList
        except:
            print("Issue creating a stream of messages.")
            if self.loggingEnabled:
                self.logger.info(f"Issue creating a stream of messages")
            return None

    def getBatches(self,limit:int=10, n_results:int=None,output:str='raw',**kwargs)->Union[pd.DataFrame,dict]:
        """
        Retrieve a list of batches.
        Arguments:
            limit : Limit response to a specified positive number of objects. Ex. limit=10 (max = 100)
            n_results : OPTIONAL :  number of result you want to get in total. (will loop)
            output : OPTIONAL : Can be "raw" response (dict) or "dataframe".
        Possible kwargs:
            created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
            createdAfter : Exclusively filter records created after this timestamp. 
            createdBefore : Exclusively filter records created before this timestamp.
            start : Returns results from a specific offset of objects. This was previously called offset. (see next line)
                offset : Will offset to the next limit (sort of pagination)        
            updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
            createdUser : Filter by the ID of the user who created this object.
            dataSet : Used to filter on the related object: &dataSet=dataSetId.
            version : Filter by Semantic version of the account. Updated when the object is modified.
            status : Filter by the current (mutable) status of the batch.
            orderBy : Sort parameter and direction for sorting the response. 
                Ex. orderBy=asc:created,updated. This was previously called sort.
            properties : A comma separated whitelist of top-level object properties to be returned in the response. 
                Used to cut down the number of properties and amount of data returned in the response bodies.
            size : The number of bytes processed in the batch.
        # /Batches/get_batch
        more details : https://www.adobe.io/apis/experienceplatform/home/api-reference.html
        """
        path = "/batches"
        limit = min([limit,100])
        params = {'limit':limit,**kwargs}
        if self.loggingEnabled:
            self.logger.debug(f"Starting getBatches with output format {output}")
        ## looping to retrieve pagination
        if n_results is not None:
            list_return = {}
            params['start'] = 0
            res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
            list_return.update(**res)
            while len(list_return) < n_results and len(res) != 0:
                params['start'] += limit
                res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
                list_return.update(**res)
            if output=="dataframe":
                return pd.DataFrame(list_return).T
            return list_return
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
        if output=="dataframe":
            return pd.DataFrame(res).T
        return res

    def getFailedBatchesDF(self,limit:int=10,n_results: str=None,orderBy:str="desc:created",**kwargs)->pd.DataFrame:
        """
        Abstraction of getBatches method that focus on failed batches and return a dataframe with the batchId and errors.
        Also adding some meta data information from the batch information provided.
        Arguments:
            limit : Limit response to a specified positive number of objects. Ex. limit=10 (max = 100)
            n_results : OPTIONAL :  number of result you want to get in total. (will loop)
            orderBy : OPTIONAL : The order of the batch. Default "desc:created"
        Possible kwargs: Any additional parameter for filtering the requests
        """
        res = self.getBatches(status="failed",orderBy=orderBy,limit=limit,n_results=n_results,**kwargs)
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFailedBatchesDF")
        dict_failed = {}
        for batch in res:
            if res[batch]['relatedObjects'][0]['type'] == "dataSet":
                datasetId = res[batch]['relatedObjects'][0]['id']
            dict_failed[batch] = {
                "timestamp" : res[batch]['created'],
                "recordsSize" : res[batch].get('metrics',{}).get('recordsSize',0),
                "invalidRecordsProfile" : res[batch].get('metrics',{}).get('invalidRecordsProfile',0),
                "invalidRecordsIdentity" : res[batch].get('metrics',{}).get('invalidRecordsIdentity',0),
                "invalidRecordCount" : res[batch].get('metrics',{}).get('invalidRecordCount',0),
                "invalidRecordsStreamingValidation" : res[batch].get('metrics',{}).get('invalidRecordsStreamingValidation',0),
                "invalidRecordsMapper" : res[batch].get('metrics',{}).get('invalidRecordsMapper',0),
                "invalidRecordsUnknown" : res[batch].get('metrics',{}).get('invalidRecordsUnknown',0),
                "errorCode" : [er['code'] for er in res[batch]['errors']],
                "errorMessage" : [er['description'] for er in res[batch]['errors']],
                "flowId" : res[batch].get('tags',{}).get('flowId',[None])[0],
                "dataSetId" : datasetId,
                "sandbox" : res[batch]['sandboxId'],
            }
        df = pd.DataFrame(dict_failed).T
        return df

    def getBatch(self, batch_id: str = None)->dict:
        """
        Get a specific batch id.
        Arguments:
            batch_id : REQUIRED : batch ID to be retrieved.
        """
        if batch_id is None:
            raise Exception("batch_id parameter is required.")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getBatch for the following batch : {batch_id}")
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
        if self.loggingEnabled:
            self.logger.debug(f"Starting createBatch")
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
        if self.loggingEnabled:
            self.logger.debug(f"Starting getResources")
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
        return res


    def getDataSets(self,limit:int=100,output:str="raw",**kwargs)->dict:
        """
        Return a list of a datasets.
        Arguments:
            limit : REQUIRED : amount of dataset to be retrieved per call. 
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
        params = {"limit":limit,**kwargs}
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDataSets")
        res = self.connector.getData(self.endpoint+path, params=params)
        data = deepcopy(res)
        ## prepare pagination if needed
        start = 1
        while len(res) == limit:
            start +=limit
            params = {"limit":limit,"start":start,**kwargs}
            res = self.connector.getData(self.endpoint+path, params=params)
            data.update(res)
        try:
            if self.loggingEnabled:
                self.logger.debug(f"Starting caching results")
            self.data.table_names = {
                data[key]['name']: data[key]['tags']['adobe/pqs/table'] for key in data}
            self.data.schema_ref = {
                data[key]['name']: data[key]['schemaRef']
                for key in data if 'schemaRef' in data[key].keys()
            }
            self.data.ids = {
                data[key]['name']: key for key in data
            }
        except Exception as e:
            if self.loggingEnabled:
                self.logger.warning(f"Error caching results : {e}")
            print(e)
            print("Couldn't populate the data object from the instance.")
        if output == "df":
            df = pd.DataFrame(data).T
            return df
        return data

    def createDataSets(self, 
                data: dict = None,
                name:str=None, 
                schemaId:str=None, 
                profileEnabled:bool=False,
                identityEnabled:bool=False,
                upsert:bool=False,
                tags:dict=None,
                systemLabels:list[str]=None,
                **kwargs):
        """
        Create a new dataSets based either on preconfigured setup or by passing the full dictionary for creation.
        Arguments:
            data : REQUIRED : If you want to pass the dataset object directly (not require the name and schemaId then)
                more info: https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Datasets/postDataset
            name : REQUIRED : if you wish to create a dataset via autocompletion. Provide a name.
            schemaId : REQUIRED : The schema $id reference for creating your dataSet.
            profileEnabled : OPTIONAL : If the dataset to be created with profile enbaled
            identityEnabled : OPTIONAL : If the dataset should create new identities
            upsert : OPTIONAL : If the dataset to be created with profile enbaled and Upsert capability.
            tags : OPTIONAL : set of attribute to add as tags.
        possible kwargs
            requestDataSource : Set to true if you want Catalog to create a dataSource on your behalf; otherwise, pass a dataSourceId in the body.
        """
        path = "/dataSets"
        params = {"requestDataSource": kwargs.get("requestDataSource", False)}
        if self.loggingEnabled:
            self.logger.debug(f"Starting createDataSets")
        if data is not None or isinstance(data, dict) == True:
            res = self.connector.postData(self.endpoint+path, params=params,
                             data=data)
        elif name is not None and schemaId is not None:
            data = {
                "name":name,
                "schemaRef": {
                    "id": schemaId,
                    "contentType": "application/vnd.adobe.xed+json;version=1"
                },
                "fileDescription": {
                    "persisted": True,
                    "containerFormat": "parquet",
                    "format": "parquet"
                },
                "tags" : {}
            }
            if profileEnabled:
                data['tags']["unifiedProfile"] = ["enabled: true"]
            if identityEnabled:
                data['tags']["unifiedIdentity"] = ["enabled: true"]
            if upsert:
                data['tags']['unifiedProfile'] = ["enabled: true","isUpsert: true"]
            if tags is not None and type(tags) == dict:
                for key in tags:
                    data['tags'][key] = tags[key]
            if systemLabels is not None and type(systemLabels) == list:
                data["systemLabels"] = systemLabels
            res = self.connector.postData(self.endpoint+path, params=params,
                             data=data)
        return res

    def getDataSet(self, datasetId: str = None):
        """
        Return a single dataset.
        Arguments:
            datasetId : REQUIRED : Id of the dataset to be retrieved.
        """
        if datasetId is None:
            raise Exception("Expected a datasetId argument")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDataset for : {datasetId}")
        path = f"/dataSets/{datasetId}"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def deleteDataSet(self, datasetId: str = None):
        """
        Delete a dataset by its id.
        Arguments:
            datasetId : REQUIRED : Id of the dataset to be deleted.
        """
        if datasetId is None:
            raise Exception("Expected a datasetId argument")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteDataset for : {datasetId}")
        path = f"/dataSets/{datasetId}"
        res = self.connector.deleteData(self.endpoint+path, headers=self.header)
        return res

    ## Apparently deprecated.
    def getDataSetViews(self, datasetId: str = None, **kwargs):
        """
        Get views of the datasets.
        Arguments:
            datasetId : REQUIRED : Id of the dataset to be looked down.
        Possible kwargs:
            limit : Limit response to a specified positive number of objects. Ex. limit=10
            orderBy : Sort parameter and direction for sorting the response. Ex. orderBy=asc:created,updated.
            start : Returns results from a specific offset of objects. This was previously called offset. Ex. start=3.
            property : Regex used to filter objects in the response. Ex. property=name~^test.
        """
        if datasetId is None:
            raise Exception("Expected a datasetId argument")
        path = f"/dataSets/{datasetId}/views"
        params = {**kwargs}
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def getDataSetView(self, datasetId: str = None, viewId: str = None):
        """
        Get a specific view on a specific dataset.
        Arguments:
            datasetId : REQUIRED : ID of the dataset to be looked down.
            viewId : REQUIRED : ID of the view to be look upon.
        """
        if datasetId is None or viewId is None:
            raise Exception("Expected a datasetId and an viewId argument")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDataSetView for datasetId: {datasetId} & viewId: {viewId}")
        path = f"/dataSets/{datasetId}/views/{viewId}"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def getDataSetViewFiles(self, datasetId: str = None, viewId: str = None):
        """
        Returns the list of files attached to a view in a Dataset.
        Arguments:
            datasetId : REQUIRED : ID of the dataset to be looked down.
            viewId : REQUIRED : ID of the view to be look upon.
        """
        if datasetId is None or viewId is None:
            raise Exception("Expected a datasetId and an viewId argument")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDataSetViewFiles for datasetId: {datasetId} & viewId: {viewId}")
        path = f"/dataSets/{datasetId}/views/{viewId}/files"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res
    
    def enableDatasetProfile(self,datasetId:str=None,upsert:bool=False)->dict:
        """
        Enable a dataset for profile with upsert.
        Arguments:
            datasetId : REQUIRED : Dataset ID to be enabled for profile
            upsert : OPTIONAL : If you wish to enabled the dataset for upsert.
        """
        if datasetId is None:
            raise ValueError("Require a datasetId")
        if self.loggingEnabled:
            self.logger.debug(f"Starting enableDatasetProfile for datasetId: {datasetId}")
        path = f"/dataSets/{datasetId}"
        privateHeader = deepcopy(self.header)
        privateHeader['Content-Type'] = "application/json-patch+json"
        data = [
            { 
                "op": "add", 
                "path": "/tags/unifiedProfile",
                "value": ["enabled:true"] }
            ]
        if upsert:
            data[0]['value'] = ["enabled:true","isUpsert:true"]
        res = self.connector.patchData(self.endpoint+path, data=data,headers=privateHeader)
        return res
    
    def enableDatasetIdentity(self,datasetId:str=None)->dict:
        """
        Enable a dataset for profile with upsert.
        Arguments:
            datasetId : REQUIRED : Dataset ID to be enabled for Identity
        """
        if datasetId is None:
            raise ValueError("Require a datasetId")
        path = f"/dataSets/{datasetId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting enableDatasetIdentity for datasetId: {datasetId}")
        data = [
            { 
                "op": "add", 
                "path": "/tags/unifiedIdentity",
                "value": ["enabled:true"] }
            ]
        res = self.connector.patchData(self.endpoint+path, data=data)
        return res
    
    def disableDatasetProfile(self,datasetId: str = None)->dict:
        """
        Disable the dataset for Profile ingestion.
        Arguments:
            datasetId : REQUIRED : Dataset ID to be disabled for profile
        """
        path = f"/dataSets/{datasetId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting disableDatasetProfile for datasetId: {datasetId}")
        data = [
            { 
                "op": "replace", 
                "path": "/tags/unifiedProfile",
                "value": ["enabled:false"] }
            ]
        res = self.connector.patchData(self.endpoint+path, data=data)
        return res
    
    def disableDatasetIdentity(self,datasetId:str=None)->dict:
        """
        Enable a dataset for profile with upsert.
        Arguments:
            datasetId : REQUIRED : Dataset ID to be disabled for Identity
        """
        if datasetId is None:
            raise ValueError("Require a datasetId")
        path = f"/dataSets/{datasetId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting disableDatasetIdentity for datasetId: {datasetId}")
        data = [
            { 
                "op": "add", 
                "path": "/tags/unifiedIdentity",
                "value": ["enabled:false"] }
            ]
        res = self.connector.patchData(self.endpoint+path, data=data)
        return res
    
    def createUnionProfileDataset(self)->dict:
        """
        Create a dataset with an union Profile schema.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createUnionProfileDataset")
        path = "/dataSets/"
        data = {
        "name": "Profile Data Export",
        "schemaRef": {
          "id": "https://ns.adobe.com/xdm/context/profile__union",
          "contentType": "application/vnd.adobe.xed+json;version=1"
            }
        }
        res = self.connector.postData(self.endpoint+path, data=data)
        return res
    
    def getMapperErrors(self,limit:int=100,n_results:str=None,**kwargs)->pd.DataFrame:
        """
        Get failed batches for Mapper errors, based on error code containing "MAPPER".
        Arguments:
            limit : OPTIONAL : Number of results per requests
            n_results : OPTIONAL : Total number of results wanted.
        Possible kwargs:
            created : Filter by the Unix timestamp (in milliseconds) when this object was persisted.
            createdAfter : Exclusively filter records created after this timestamp. 
            createdBefore : Exclusively filter records created before this timestamp.
            start : Returns results from a specific offset of objects. This was previously called offset. (see next line)
                offset : Will offset to the next limit (sort of pagination)        
            updated : Filter by the Unix timestamp (in milliseconds) for the time of last modification.
            createdUser : Filter by the ID of the user who created this object.
            dataSet : Used to filter on the related object: &dataSet=dataSetId.
            version : Filter by Semantic version of the account. Updated when the object is modified.
            status : Filter by the current (mutable) status of the batch.
            orderBy : Sort parameter and direction for sorting the response. 
                Ex. orderBy=asc:created,updated. This was previously called sort.
            properties : A comma separated whitelist of top-level object properties to be returned in the response. 
                Used to cut down the number of properties and amount of data returned in the response bodies.
            size : The number of bytes processed in the batch.
        """
        df = self.getFailedBatchesDF(limit=limit,n_results=n_results,**kwargs)
        df['errorCodeStr'] = df['errorCode'].astype(str)
        df_mapper = df[df['errorCodeStr'].str.contains('DPMAP')]
        del df_mapper["errorCodeStr"]
        dict_result = {}
        for index,row in df_mapper.iterrows():
            errorCodes = []
            errorMessages = []
            destinationPaths = []
            expectedTypes = []
            actualTypes = []
            sourceFields = []
            destinationFields = []
            for code,message in zip_longest(row['errorCode'],row['errorMessage']):
                if 'MAPPER' in code:
                    errorMessages.append(message)
                    errorCodes.append(code)
                    matchDestPath = re.search('destination path (.+?)\. ',message)
                    if matchDestPath:
                        destinationPaths.append(matchDestPath.group(1))
                    matchExpectedTypes = re.search('expected data type was: ([A-Z]+?), ',message)
                    if matchExpectedTypes:
                        expectedTypes.append(matchExpectedTypes.group(1))
                    matchActualTypes = re.search('actual data type was: ([A-Z]+?)\. ',message)
                    if matchActualTypes:
                        actualTypes.append(matchActualTypes.group(1))
                    matchSourceField = re.search('sourceField: (.+?) destinationField',message)
                    if matchSourceField:
                        sourceFields.append(matchSourceField.group(1))
                    matchDestinationField = re.search('destinationField: (.+?)$',message)
                    if matchDestinationField:
                        destinationFields.append(matchDestinationField.group(1))
            for message,code,destPath,expType,actType,source,dest in zip_longest(errorMessages,errorCodes,destinationPaths,expectedTypes,actualTypes,sourceFields,destinationFields):
                dict_result[f"{row.name}-{code}"] = {
                    "timestamp" : row['timestamp'],
                    "batchId" : row.name,
                    "datasetId": row['dataSetId'],
                    "flowId":row["flowId"],
                    "invalidRecordCount" : row["invalidRecordCount"],
                    "invalidRecordsMapper": row["invalidRecordsMapper"],
                    "errorCode" : code,
                    "errorMessage":message,
                    "destinationPath" : destPath,
                    "expectedType":expType,
                    "actualType":actType,
                    "sourceField":source,
                    "destinationField":dest
                }
        df_final = pd.DataFrame(dict_result).T
        return df_final