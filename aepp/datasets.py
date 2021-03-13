import aepp
from aepp import connector
from copy import deepcopy

class DataSets:
    """
    module that help for managing labels of the datasets.
    """
    REFERENCE_LABELS_CREATION = {
        "labels": [
            [
            "C1",
            "C2"
            ]
        ],
        "optionalLabels": [
            {
            "option": {
                "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
                "contentType": "application/vnd.adobe.xed-full+json;version=1",
                "schemaPath": "/properties/repositoryCreatedBy"
            },
            "labels": [
                [
                "S1",
                "S2"
                ]
            ]
            }
        ]
    }

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        """
        Instantiate the DataSet class.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        Additional kwargs will update the header.
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.sandbox = self.connector.config['sandbox']
        self.endpoint = aepp.config.endpoints["global"] + aepp.config.endpoints["dataset"]
    
    def getLabels(self,dataSetId:str=None)->dict:
        """
        Return the labels assigned to a dataSet
        Argument:
            dataSetId : REQUIRED : the dataSet ID to retrieve the labels
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        path = f"/datasets/{dataSetId}/labels"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def headLabels(self,dataSetId:str=None)->dict:
        """
        Return the head assigned to a dataSet
        Argument:
            dataSetId : REQUIRED : the dataSet ID to retrieve the head data
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        path = f"/datasets/{dataSetId}/labels"
        res = self.connector.headData(self.endpoint+path)
        return res

    def deleteLabels(self,dataSetId:str=None,ifMatch:str=None)->dict:
        """
        Delete the labels of a dataset.
        Arguments:
            dataSetId : REQUIRED : The dataset ID to delete the labels for.
            ifMatch : REQUIRED : the value is from the header etag of the headLabels. (use the headLabels method)
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        if ifMatch is None:
            raise ValueError("Require the ifMatch parameter")
        path = f"/datasets/{dataSetId}/labels"
        privateHeader = deepcopy(self.header)
        privateHeader["If-Match"] = ifMatch
        res = self.connector.deleteData(self.endpoint + path,headers=privateHeader)
        return res
    
    def createLabels(self,dataSetId:str=None,data:dict=None)->dict:
        """
        Assign labels to a dataset.
        Arguments:
            dataSetId : REQUIRED : The dataset ID to delete the labels for.
            data : REQUIRED : Dictionary setting the labels to be added.
                more info https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Datasets/postDatasetLabels
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        if data is None or type(data)!= dict:
            raise ValueError("Require a dictionary to pass labels")
        path = f"/datasets/{dataSetId}/labels"
        res = self.connector.postData(self.endpoint+path,data=data)
        return res

    def updateLabels(self,dataSetId:str=None,data:dict=None,ifMatch:str=None)->dict:
        """
        Update the labels (PUT method)
            dataSetId : REQUIRED : The dataset ID to delete the labels for.
            data : REQUIRED : Dictionary setting the labels to be added.
                more info https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Datasets/postDatasetLabels
            ifMatch : REQUIRED : the value is from the header etag of the headLabels.(use the headLabels method)
        """
        if dataSetId is None:
            raise ValueError("Require a dataSet ID")
        if data is None or type(data)!= dict:
            raise ValueError("Require a dictionary to pass labels")
        if ifMatch is None:
            raise ValueError("Require the ifMatch parameter")
        path = f"/datasets/{dataSetId}/labels"
        privateHeader = deepcopy(self.header)
        privateHeader["If-Match"] = ifMatch
        res = self.connector.putData(self.endpoint+path,data=data,headers=privateHeader)
        return res
