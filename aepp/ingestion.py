import aepp
from aepp import connector
from copy import deepcopy
import requests
from typing import IO, Union

class DataIngestion:

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        """
        Instantiate the DataAccess class.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        Additional kwargs will update the header.
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.sandbox = self.connector.config['sandbox']
        self.endpoint = aepp.config.endpoints["global"] + aepp.config.endpoints["ingestion"]
        self.endpoint_streaming = aepp.config.endpoints["streaming"]["collection"]
        self.STREAMING_REFERENCE = {
            "header": {
                "schemaRef": {
                "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
                "contentType": "application/vnd.adobe.xed-full+json;version={SCHEMA_VERSION}"
                },
                "imsOrgId": "{IMS_ORG_ID}",
                "datasetId": "{DATASET_ID}",
                "createdAt": "1526283801869",
                "source": {
                "name": "{SOURCE_NAME}"
                }
            },
            "body": {
                "xdmMeta": {
                "schemaRef": {
                    "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
                    "contentType": "application/vnd.adobe.xed-full+json;version={SCHEMA_VERSION}"
                }
                },
                "xdmEntity": {
                "person": {
                    "name": {
                    "firstName": "Jane",
                    "middleName": "F",
                    "lastName": "Doe"
                    },
                    "birthDate": "1969-03-14",
                    "gender": "female"
                },
                "workEmail": {
                    "primary": True,
                    "address": "janedoe@example.com",
                    "type": "work",
                    "status": "active"
                }
                }
            }
        }
    
    def createBatch(self,datasetId:str=None,format:str='json',multiline:bool=False,enableDiagnostic:bool=False,partialIngestionPercentage:int=0)->dict:
        """
        Create a new batch in Catalog Service.
        Arguments:
            datasetId : REQUIRED : The Dataset ID for the batch to upload data to.
            format : REQUIRED : the format of the data send.(default json)
            multiline : OPTIONAL : If you wish to upload multi-line JSON.
        """
        if datasetId is None:
            raise ValueError("Require a dataSetId ")
        obj = {
            "datasetId": datasetId,
            "inputFormat": {
                "format": format,
                "isMultiLineJson":False
           }
        }
        if multiline is True:
            obj['inputFormat']['isMultiLineJson'] = True
        if enableDiagnostic != False:
            obj["enableErrorDiagnostics"] = True
        if partialIngestionPercentage > 0:
            obj["partialIngestionPercentage"] = partialIngestionPercentage
        path = "/batches"
        res = self.connector.postData(self.endpoint+path,data=obj)
        return res
    
    def uploadSmallFile(self,batchId:str=None,datasetId:str=None,filePath:str=None,data:Union[list,dict]=None,verbose:bool=False)->dict:
        """
        Upload a small file (<256 MB) to the filePath location in the dataset.
        Arguments:
            batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
            datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
            filePath : REQUIRED : the filePath that will store the value.
            data : REQUIRED : The data to be uploaded (following the type provided). List or Dictionary, depending if multiline is enabled.
            verbose: OPTIONAL : if you wish to see comments around the
        """
        if batchId is None:
            raise Exception("require a batchId")
        if datasetId is None:
            raise Exception("require a dataSetId")
        if filePath is None:
            raise Exception("require a filePath value")
        if data is None:
            raise Exception("require data to be passed")
        if verbose:
            print(f"Your data is in {type(data)} format")
        privateHeader = deepcopy(self.header)
        privateHeader['Content-Type'] = "application/octet-stream"
        path = f"/batches/{batchId}/datasets/{datasetId}/files/{filePath}"
        res = self.connector.putData(self.endpoint+path,data=data,headers=privateHeader)
        return res
    
    def uploadSmallFileFinish(self,batchId:str=None,action:str="COMPLETE",verbose:bool=False)->dict:
        """
        Send an action to signify that the import is done.
        Arguments:
            batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
            action : REQUIRED : either one of these actions:
                COMPLETE (default value) 
                ABORT 
                FAIL 
                REVERT
        """
        if batchId is None:
            raise Exception("require a batchId")
        if action is None or action not in ["COMPLETE", "ABORT", "FAIL", "REVERT"]:
            raise Exception("Not a valid action has been passed")
        path = f"/batches/{batchId}"
        params = {"action" : action}
        res = self.connector.postData(self.endpoint+path,params=params,verbose=verbose)
        return res
    
    def uploadLargeFileStartEnd(self,batchId:str=None,datasetId:str=None,filePath:str=None,action:str="INITIALIZE")->dict:
        """
        Start / End the upload of a large file with a POST method defining the action (see parameter)
        Arguments:
            batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
            datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
            filePath : REQUIRED : the filePath that will store the value.
            action : REQUIRED : Action to either INITIALIZE or COMPLETE the upload.
        """
        if batchId is None:
            raise Exception("require a batchId")
        if datasetId is None:
            raise Exception("require a dataSetId")
        if filePath is None:
            raise Exception("require a filePath value")
        params = {"action":action}
        path = f"/batches/{batchId}/datasets/{datasetId}/files/{filePath}"
        res = self.connector.postData(self.endpoint+path,params=params)
        return res


    def uploadLargeFilePart(self,batchId:str=None,datasetId:str=None,filePath:str=None,data:bytes=None,contentRange:str=None)->dict:
        """
        Continue the upload of a large file with a PATCH method. 
        Arguments:
            batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
            datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
            filePath : REQUIRED : the filePath that will store the value.
            data : REQUIRED : The data to be uploaded (in bytes) 
            contentRange : REQUIRED : The range of bytes of the file being uploaded with this request.
        """
        if batchId is None:
            raise Exception("require a batchId")
        if datasetId is None:
            raise Exception("require a dataSetId")
        if filePath is None:
            raise Exception("require a filePath value")
        if data is None:
            raise Exception("require data to be passed")
        if contentRange is None:
            raise Exception("require the content range to be passed")
        privateHeader = deepcopy(self.header)
        privateHeader['Content-Type'] = "application/octet-stream"
        privateHeader['Content-Range'] = contentRange
        path = f"/batches/{batchId}/datasets/{datasetId}/files/{filePath}"
        res = requests.patch(self.endpoint+path,data=data,headers=privateHeader)
        res_json = res.json()
        return res_json

    def headFileStatus(self,batchId:str=None,datasetId:str=None,filePath:str=None)->dict:
        """
        Check the status of a large file upload.
        Arguments:
            batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
            datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
            filePath : REQUIRED : the filePath that reference the file.
        """
        if batchId is None:
            raise Exception("require a batchId")
        if datasetId is None:
            raise Exception("require a dataSetId")
        if filePath is None:
            raise Exception("require a filePath value")
        path = f"/batches/{batchId}/datasets/{datasetId}/files/{filePath}"
        res = self.connector.headData(self.endpoint+path)
        return res
    
    def getPreviewBatchDataset(self,
        batchId:str =None,
        datasetId:str =None,
        format:str = "json",
        delimiter:str =",",
        quote:str = '"',
        escape:str = "\\",
        charset:str = "utf-8",
        header:bool =True,
        nrow:int = 5
        )->dict:
        """
        Generates a data preview for the files uploaded to the batch so far. The preview can be generated for all the batch datasets collectively or for the selected datasets.
        Arguments:
            batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
            datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
            format : REQUIRED : Format of the file ('json' default)
            delimiter : OPTIONAL : The delimiter to use for parsing column values.
            quote : OPTIONAL : The quote value to use while parsing data.
            escape : OPTIONAL : The escape character to use while parsing data.
            charset : OPTIONAL : The encoding to be used (default utf-8)
            header : OPTIONAL : The flag to indicate if the header is supplied in the dataset files.
            nrow : OPTIONAL : The number of rows to parse. (default 5) - cannot be 10 or greater
        """
        if batchId is None:
            raise Exception("require a batchId")
        if datasetId is None:
            raise Exception("require a dataSetId")
        if format is None:
            raise Exception("require a format type")
        params = {"delimiter":delimiter,"quote":quote,"escape":escape,"charset":charset,"header":header,"nrow":nrow}
        path = f"/batches/{batchId}/datasets/{datasetId}/preview"
        res = self.connector.getData(self.endpoint+path,params=params)
        return res

    def StreamMessage(self,connectionId:str=None,data:dict=None,synchronousValidation:str=False)->dict:
        """
        Send a dictionary to the connection for streaming ingestion.
        Arguments:
            connectionId : REQUIRED : the connection ID to be used for ingestion
            data : REQUIRED : The data that you want to ingest to Platform.
            synchronousValidation : OPTIONAL : An optional query parameter, intended for development purposes. 
                If set to true, it can be used for immediate feedback to determine if the request was successfully sent.
        """
        if connectionId is None:
            raise Exception("Require a connectionId to be present")
        if data is None and type(data) != dict:
            raise Exception("Require a dictionary to be send for ingestion")
        params = {"synchronousValidation":synchronousValidation}
        path = f"/collection/{connectionId}"
        res = self.connector.postData(self.endpoint_streaming+path,data=data,params=params)
        return res
    
    def StreamMessages(self,connectionId:str=None,data:list=None,synchronousValidation:str=False)->dict:
        """
        Send a dictionary to the connection for streaming ingestion.
        Arguments:
            connectionId : REQUIRED : the connection ID to be used for ingestion
            data : REQUIRED : The list of data that you want to ingest to Platform.
            synchronousValidation : OPTIONAL : An optional query parameter, intended for development purposes. 
                If set to true, it can be used for immediate feedback to determine if the request was successfully sent.
        """
        if connectionId is None:
            raise Exception("Require a connectionId to be present")
        if data is None and type(data) != list:
            raise Exception("Require a list of dictionary to be send for ingestion")
        params = {"synchronousValidation":synchronousValidation}
        path = f"/collection/batch/{connectionId}"
        res = self.connector.postData(self.endpoint_streaming+path,data=data,params=params)
        return res

