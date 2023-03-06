# Internal Library
import aepp
from aepp import connector
from aepp import config
from copy import deepcopy
from typing import Union
import time
import logging
from .configs import ConnectObject

class Instance:
    """
    This class is referring to Destination Instance Service capability for AEP.
    """
    def __init__(self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,):
        """
        Instanciating the class for destination instance service

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
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.endpoint = config.endpoints["global"] + config.endpoints["destinationInstance"]
        
        def createAdhocTask(self, adhocObj: dict = None, accept: str = None)->dict:
            """
            Create an Adhoc Request based on the definition passed in argument.
            Arguments:
                adhocObj : REQUIRED : Object containing the definition of the adhoc request.
            """
            if self.loggingEnabled:
                self.logger.debug(f"Starting creating adhoc task")
            if adhocObj is None or type(adhocObj) != dict:
                raise Exception("Require a dictionary defining the adhoc task configuration")
            self.header.update("Accept", accept)
            path = "/adhocrun"
            res = self.connector.postData(self.endpoint + path, data=adhocObj)
            return res
