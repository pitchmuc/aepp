# Internal Library
import aepp
from aepp import connector
from typing import Union
import logging
from .configs import ConnectObject

class DestinationInstanceService:
    """
    This class is referring to Destination Instance Service capability for AEP.
    """
    def __init__(self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,):
        """
        Instantiating the class for destination instance service

        Arguments:
            loggingObject : OPTIONAL : logging object to log messages.
            config : OPTIONAL : config object in the config module.
            header : OPTIONAL : header object  in the config module.
        possible kwargs:
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
            config_object=config,
            header=header,
            loggingEnabled=self.loggingEnabled,
            logger=self.logger,
        )
        self.header = self.connector.header
        # self.header.update({"Accept": "application/json"})
        self.header.update(**kwargs)
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instantiation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.endpoint = config.endpoints["global"] + config.endpoints["destinationInstance"]
        
        
    def createAdHocDatasetExport(self, flowIdToDatasetIds: dict = None)->dict:
        """
        Create an Adhoc Request based on the flowId and the datasetId passed in argument.
        Arguments:
            flowIdToDatasetIds : REQUIRED :  dict containing the definition of flowId to datasetIds
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting creating adhoc dataset export")
        if flowIdToDatasetIds is None or type(flowIdToDatasetIds) != dict:
            raise Exception("Require a dict for defining the flowId to datasetIds mapping")
        activationInfo = {'activationInfo': {'destinations': []}};
        for flowId, datasetIds in flowIdToDatasetIds.items():
            destination = {'flowId': flowId, 'datasets': []}
            for datasetId in datasetIds:
                dataset = {'id': datasetId}
                destination['datasets'].append(dataset)
            activationInfo['activationInfo']['destinations'].append(destination)
        self.header.update({"Accept":"application/vnd.adobe.adhoc.activation+json; version=3"})
        path = "/adhocrun"
        res = self.connector.postData(self.endpoint + path, data=activationInfo)
        return res
