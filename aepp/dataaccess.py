import aepp
from aepp import connector

class DataAccess:

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        """
        Instantiate the sandbox class.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        Additional kwargs will update the header.
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.endpoint = aepp.config.endpoints["global"] + aepp.config.endpoints["dataaccess"]

    def getBatchesFiles(self,batchId:str=None,**kwargs)->list:
        """
        List all dataset files under a batch.
        Arguments:
            batchId : REQUIRED : The batch ID to look for.
        Possible kwargs:
            limit : A paging parameter to specify number of results per page.
            start : A paging parameter to specify start of new page. For example: page=1
        """
        if batchId is None:
            raise ValueError("Require a batchId to be specified.")
        params={}
        if kwargs.get('limit',None) is not None:
            params['limit'] = str(kwargs.get('limit'))
        if kwargs.get('start',None) is not None:
            params['start'] = str(kwargs.get('start'))
        path = f"/batches/{batchId}/files"
        res = self.connector.getData(self.endpoint+path, headers=self.header,params=params)
        data = res['data']
        return data
    
    def getBatchesFailed(self,batchId:str=None,path:str=None,**kwargs)->list:
        """
        Lists all the dataset files under a failed batch.
        Arguments:  
            batchId : REQUIRED : The batch ID to look for.
            path : OPTIONAL : The full name of the file. The contents of the file would be downloaded if this parameter is provided. 
                For example: path=profiles.csv
        Possible kwargs:
            limit : A paging parameter to specify number of results per page.
            start : A paging parameter to specify start of new page. For example: page=1
        """
        if batchId is None:
            raise ValueError("Require a batchId to be specified.")
        params={}
        if kwargs.get('limit',None) is not None:
            params['limit'] = str(kwargs.get('limit'))
        if kwargs.get('start',None) is not None:
            params['start'] = str(kwargs.get('start'))
        if path is not None:
            params['path'] = path
        pathEndpoint = f"/batches/{batchId}/failed"
        res = self.connector.getData(self.endpoint+pathEndpoint, headers=self.header,params=params)
        data = res['data']
        return data
    
    def getBatchesMeta(self,batchId:str=None,path:str=None,**kwargs)->dict:
        """
        Lists files under a batch’s meta directory or download a specific file under it. The files under a batch’s meta directory may include the following:
            row_errors: A directory containing 0 or more files with parsing, conversion, and/or validation errors found at the row level.
            input_files: A directory containing metadata for 1 or more input files submitted with the batch.
            row_errors_sample.json: A root level file containing the sampled set of row errors for the UX.
        Arguments:  
            batchId : REQUIRED : The batch ID to look for.
            path : OPTIONAL : The full name of the file. The contents of the file would be downloaded if this parameter is provided. 
                Possible values for this query include the following:
                    row_errors
                    input_files
                    row_errors_sample.json
        Possible kwargs:
            limit : A paging parameter to specify number of results per page.
            start : A paging parameter to specify start of new page. For example: page=1
        """
        if batchId is None:
            raise ValueError("Require a batchId to be specified.")
        params={}
        if kwargs.get('limit',None) is not None:
            params['limit'] = str(kwargs.get('limit'))
        if kwargs.get('start',None) is not None:
            params['start'] = str(kwargs.get('start'))
        if path is not None:
            params['path'] = path
        pathEndpoint = f"/batches/{batchId}/meta"
        res = self.connector.getData(self.endpoint+pathEndpoint, headers=self.header,params=params)
        return res
    
    def getHeadFile(self,dataSetFileId:str=None,path:str=None)->dict:
        """
        Get headers regarding a file.
        Arguments:
            dataSetFileId : REQURED : The ID of the dataset file you are retrieving.
            path : REQUIRED : The full name of the file identified. 
                For example: path=profiles.csv
        """
        if dataSetFileId is None or path is None:
            raise ValueError("Require a dataSetFileId and a path for that method")
        params = {"path" : path}
        pathEndpoint = f"/files/{dataSetFileId}"
        res = self.connector.headData(self.endpoint+pathEndpoint,params=params,headers=self.header)
        return res

    def getFiles(self,dataSetFileId:str=None,path:str=None,range:str=None,start:str=None,limit:int=None)->dict:
        """
        Returns either a complete file or a directory of chunked data that makes up the file.
        The response contains a data array that may contain a single entry or a list of files belonging to that directory.
        Arguments:
            dataSetFileId : REQUIRED : The ID of the dataset file you are retrieving.
            path : OPTIONAL : The full name of the file. The contents of the file would be downloaded if this parameter is provided. 
                For example: path=profiles.csv
            range : OPTIONAL : The range of bytes requested. For example: Range: bytes=0-100000
            start : OPTIONAL : A paging parameter to specify start of new page. For example: start=fileName.csv
            limit : OPTIONAL : A paging parameter to specify number of results per page. For example: limit=10
        """
        if dataSetFileId is None:
            raise ValueError("Require a dataSetFileId")
        params = {}
        if path is not None:
            params["path"] = path
        if range is not None:
            params["range"] = range
        if start is not None:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        pathEndpoint = f"/files/{dataSetFileId}"
        res:dict = self.connector.getData(self.endpoint+pathEndpoint, headers=self.header,params=params)
        return res
    
    def getPreview(self,datasetId:str=None)->list:
        """
        Give a preview of a specific dataset
        Arguments:
            datasetId : REQUIRED : the dataset ID to preview
        """
        path = f"/datasets/{datasetId}/preview"
        res:dict = self.connector.getData(self.endpoint+path, headers=self.header)
        data:list = res['data']
        return data
    
     
