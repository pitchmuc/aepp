import aepp
from aepp import connector
from copy import deepcopy
import pandas as pd

class Mapping:

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs)->None:
        """
        This will instantiate the Mapping class 
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
    kwargs:
        kwargsvaluewillupdatetheheader
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        # same endpoint than segmentation
        self.endpoint = aepp.config.endpoints['global']+aepp.config.endpoints["mapping"]
    
    def getXDMBatchConversions(self,dataSetId:str=None,prop:str=None,batchId:str=None,status:str=None,limit:int=100)->dict:
        """
        Returns all XDM conversions
        Arguments:
            dataSetId : OPTIONAL : Destination dataSet ID to filter for.
            property : OPTIONAL : Filters for dataSetId, batchId and Status.
            batchId : OPTIONAL : batchId Filter
            status : OPTIONAL : status of the batch.
            limit : OPTIONAL : number of results to return (default 100)
        """
        path = "/xdmBatchConversions"
        params = {"limit":limit}
        if dataSetId is not None:
            params['destinationDatasetId'] = dataSetId
        if prop is not None:
            params["property"] = prop
        if batchId is not None:
            params['sourceBatchId'] = batchId
        if status is not None:
            params['status'] = status
        res = self.connector.getData(self.endpoint+path,params=params)
        return res
    
    def getXDMBatchConversion(self,conversionId:str=None)->dict:
        """
        Returns XDM Conversion info.
        Arguments:
            conversionId : REQUIRED : Conversion ID to be returned
        """
        if conversionId is None:
            raise ValueError("Require a conversion ID")
        path = f"/xdmBatchConversions/{conversionId}"
        res = self.connector.getData(self.endpoint+path)
        return res

    def getXDMBatchConversionActivities(self,conversionId:str=None)->dict:
        """
        Returns activities for a XDM Conversion ID.
        Arguments:
            conversionId : REQUIRED : Conversion ID for activities to be returned
        """
        if conversionId is None:
            raise ValueError("Require a conversion ID")
        path = f"/xdmBatchConversions/{conversionId}/activities"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def getXDMBatchConversionRequestActivities(self,requestId:str=None,activityId:str=None)->dict:
        """
        Returns conversion activities for given request
        Arguments:
            requestId : REQUIRED : the request ID to look for
            activityId : REQUIRED : the activity ID to look for
        """
        if requestId is None:
            raise ValueError("Require a request ID")
        if activityId is None:
            raise ValueError("Require a activity ID")
        path = f"/xdmBatchConversions/{requestId}/activities/{activityId}"
        res = self.connector.getData(self.endpoint+path+path)
        return res
    
    def createXDMConversion(self,dataSetId:str=None,batchId:str=None,mappingId:str=None)->dict:
        """
        Create a XDM conversion request.
        Arguments:
            dataSetId : REQUIRED : destination dataSet ID
            batchId : REQUIRED : Source Batch ID
            mappingSetId : REQUIRED : Mapping ID to be used
        """
        if dataSetId is None:
            raise ValueError("Require a destination dataSet ID")
        if batchId is None:
            raise ValueError("Require a source batch ID")
        if mappingId is None:
            raise ValueError("Require a mapping ID")
        path = "/xdmBatchConversions"
        params = {"destinationDataSetId":dataSetId,"sourceBatchId":batchId,"mappingSetId":mappingId}
        res = self.connector.getData(self.endpoint+path,params=params)
        return res

    def getMappingSets(self,name:str=None,prop:str=None,limit:int=100)->list:
        """
        Returns all mapping sets for given IMS Org Id
        Arguments:
            name : OPTIONAL : Filtering by name
            prop : OPTIONAL : property filter. Supported fields are: xdmSchema, status.
                Example : prop="status==success"
            limit : OPTIONAL : number of result to retun. Default 100.
        """
        params ={"limit":limit}
        if name is not None:
            params['name'] = name
        if prop is not None:
            params['property'] = prop
        path = "/mappingSets"
        res = self.connector.getData(self.endpoint+path,params=params)
        data = res["data"]
        return data
    
    def getMappingSuggestions(self,dataSetId:str=None,batchId:str=None,excludeUnmapped:bool=True)->dict:
        """
        Returns non-persisted mapping set suggestion for review
        Arguments:
            dataSetId : OPTIONAL : Id of destination DataSet. Must be a DataSet with schema.
            batchId : OPTIONAL : Id of source Batch.
            excludeUnmapped : OPTIONAL : Exclude unmapped source attributes (default True)
        """
        path = "/mappingSets/suggestion"
        params = {"excludeUnmapped":excludeUnmapped}
        if dataSetId is not None:
            params['datasetId'] = dataSetId
        if batchId is not None:
            params["batchId"] = batchId
        res = self.connector.getData(self.endpoint+path,params=params)
        return res

    def getMappingSet(self,mappingSetId:str=None)->dict:
        """
        Get a specific mappingSet by its ID.
        Argument:
            mappingSetId : REQUIRED : mappingSet ID to be retrieved.
        """
        if mappingSetId is None:
            raise ValueError("Require a mapping ID")
        path = f"/mappingSets/{mappingSetId}"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def deleteMappingSet(self,mappingSetId:str=None)->dict:
        """
        Delete a specific mappingSet by its ID.
        Argument:
            mappingSetId : REQUIRED : mappingSet ID to be deleted.
        """
        if mappingSetId is None:
            raise ValueError("Require a mapping ID")
        path = f"/mappingSets/{mappingSetId}"
        res = self.connector.deleteData(self.endpoint+path)
        return res

    def createMappingSet(self,mappingSet:dict=None,validate:bool=False)->dict:
        """
        Create a mapping set.
        Arguments:
            mappingSet : REQUIRED : A dictionary that creates the mapping info.
                see info on https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Mappings/createMappingSetUsingPOST
            validate : OPTIONAL : Validate the mapping.
        """
        path = "/mappingSets"
        if mappingSet is None or type(mappingSet) != dict:
            raise ValueError("Require a dictionary as mapping set")
        params = {'validate':validate}
        res = self.connector.postData(self.endpoint + path,params=params)
        return res
    
    def updateMappingSet(self,mappingSetId:str=None,mappingSet:dict=None)->dict:
        """
        Update a specific Mapping set based on its Id.
        Arguments:
            mappingSetId : REQUIRED : mapping Id to be updated
            mappingSet : REQUIRED : the dictionary to update the mappingSet
        """
        if mappingSetId is None:
            raise ValueError("Require a mappingSet ID")
        if mappingSet is None:
            raise ValueError("Require a dictionary as mappingSet")
        path = f"/mappingSets/{mappingSetId}"
        res = self.connector.putData(self.endpoint+path,data=mappingSet)
        return res
    
    def getMappingSetMappings(self,mappingSetId:str=None)->dict:
        """
        Returns all mappings for a mapping set
        Arguments:
            mappingSetId : REQUIRED : the mappingSet ID to retrieved
        """
        if mappingSetId is None:
            raise ValueError("Require a mapping ID")
        path = f"/mappingSets/{mappingSetId}/mappings"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def createMappingSetMapping(self,mappingSetId:str=None,mapping:dict=None)->dict:
        """
        Create mappings for a mapping set
        Arguments:
            mappingSetId : REQUIRED : the mappingSet ID to attached the mapping
            mapping : REQUIRED : a dictionary to define the new mapping.
        """
        if mappingSetId is None:
            raise ValueError("Require a mapping ID")
        if mapping is None or type(mapping)!=dict:
            raise Exception("Require a dictionary as mapping")
        path = f"/mappingSets/{mappingSetId}/mappings"
        res = self.connector.postData(self.endpoint+path,data=mapping)
        return res

    def getMappingSetMapping(self,mappingSetId:str=None,mappingId:str=None)->dict:
        """
        Get a mapping from a mapping set.
        Arguments:
            mappingSetId : REQUIRED : The mappingSet ID
            mappingId : REQUIRED : The specific Mapping
        """
        if mappingSetId is None:
            raise ValueError("Require a mappingSet ID")
        if mappingId is None:
            raise ValueError("Require a mapping ID")
        path = f"/mappingSets/{mappingSetId}/mappings/{mappingId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def deleteMappingSetMapping(self,mappingSetId:str=None,mappingId:str=None)->dict:
        """
        Delete a mapping in a mappingSet
        Arguments:
            mappingSetId : REQUIRED : The mappingSet ID
            mappingId : REQUIRED : The specific Mapping
        """
        if mappingSetId is None:
            raise ValueError("Require a mappingSet ID")
        if mappingId is None:
            raise ValueError("Require a mapping ID")
        path = f"/mappingSets/{mappingSetId}/mappings/{mappingId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res
    
    def updateMappingSetMapping(self,mappingSetId:str=None,mappingId:str=None,mapping:dict=None)->dict:
        """
        Update a mapping for a mappingSet (PUT method)
        Arguments:
            mappingSetId : REQUIRED : The mappingSet ID
            mappingId : REQUIRED : The specific Mapping
            mapping : REQUIRED : dictionary to update
        """
        if mappingSetId is None:
            raise ValueError("Require a mappingSet ID")
        if mappingId is None:
            raise ValueError("Require a mapping ID")
        if mapping is None or type(mapping) != dict:
            raise Exception("Require a dictionary as mapping")
        path = f"/mappingSets/{mappingSetId}/mappings/{mappingId}"
        res = self.connector.putData(self.endpoint + path,data=mapping)
        return res


        

    
