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
import aepp
from aepp import connector
from aepp import config
from copy import deepcopy
from typing import Union
import time
import logging
from .configs import ConnectObject

class Authoring:
    """
    This class is referring to Destination Authoring capability for AEP. 
    It is a suite of configuration APIs that allow you to configure destination integration patterns for Experience Platform to deliver audience and profile data to your endpoint, based on data and authentication formats of your choice.
    More information on the API, available at: https://developer.adobe.com/experience-platform-apis/references/destination-authoring/
    """

    def __init__(self, 
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,):
        """
        Instanciating the class for Authoring.

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
        self.endpoint = config.endpoints["global"] + config.endpoints["destinationAuthoring"]
    
    def getDestinations(self)->list:
        """
        Return a list of all destination SDK authored by the organization.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDestinations")
        path = "/destinations"
        res = self.connector.getData(self.endpoint + path)
        return res
    
    def getDestination(self, destinationId:str = None)->dict:
        """
        Return a destination specific configuration.
        Arguments:
            destinationId : REQUIRED : The destination ID to be retrieved
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDestination with ID : {destinationId}")
        if destinationId is None:
            raise ValueError("Require a destination ID")
        path = f"/destinations/{destinationId}"
        res = self.connector.getData(self.endpoint + path)
        return res
    
    def deleteDestination(self, destinationId: str = None)->dict:
        """
        Delete a specific destination based on its ID.
        Arguments:
            destinationId : REQUIRED : The destination ID to be deleted
        """
        if destinationId is None:
            raise ValueError("Require a destination ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteDestination with ID: {destinationId}")
        path = f"/destinations/{destinationId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res
    
    def createDestination(self, destinationObj: dict = None)->dict:
        """
        Create a destination based on the definition passed in argument.
        Arguments:
            destinationObj : REQUIRED : Object containing the definition of the destination.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createDestination")
        if destinationObj is None or type(destinationObj) != dict:
            raise Exception("Require a dictionary defining the destination configuration")
        path = "/destinations"
        res = self.connector.postData(self.endpoint + path, data=destinationObj)
        return res

    def updateDestination(self, destinationId:str=None,destinationObj: dict = None)->dict:
        """
        Create a destination based on the definition passed in argument.
        Arguments:
            destinationId : REQUIRED : The destination ID to be updated
            destinationObj : REQUIRED : Object containing the definition of the destination.
        """
        if destinationId is None:
            raise ValueError("Require a destination ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateDestination with ID: {destinationId}")
        if destinationObj is None or type(destinationObj) != dict:
            raise Exception("Require a dictionary defining the destination configuration")
        path = "/destinations"
        res = self.connector.putData(self.endpoint + path, data=destinationObj)
        return res
    
    def getDestinationServers(self)->list:
        """
        Retrieve a list of all destination server configurations for your IMS Organization
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDestinationServers")
        path = "/destination-servers"
        res = self.connector.getData(self.endpoint + path)
        return res
    
    def getDestinationServer(self,serverId:str=None)->dict:
        """
        Retrieve a specific destination server configuration by its ID.
        Arguments:
            serverId : REQUIRED : destination server ID of the server
        """
        if serverId is None:
            raise ValueError("Require a server ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getDestinationServer with ID: {serverId}")
        path = f"/destination-servers/{serverId}"
        res = self.connector.getData(self.endpoint + path)
        return res
    
    def deleteDestinationServer(self,serverId:str = None)->dict:
        """
        Delete a destination server by its ID.
        Arguments:
            serverId : REQUIRED : destination server ID to be deleted
        """
        if serverId is None:
            raise ValueError("Require a server ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteDestinationServer with ID: {serverId}")
        path = f"/destination-servers/{serverId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def createDestinationServer(self,serverObj:dict=None)->dict:
        """
        Create a new destination server configuration.
        Arguments:
            serverObj : REQUIRED : dictionary containing the server destination configuration
        """
        path = "/destination-servers"
        if serverObj is None:
            raise ValueError("Require a dictionary containing the server configuration")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createDestinationServer")
        res = self.connector.postData(self.endpoint + path, data=serverObj)
        return res

    def updateDestinationServer(self,serverId:str=None, serverObj: dict = None)->dict:
        """
        Update the destination with a new definition (PUT request)
        Arguments:
            serverId : REQUIRED : destination server ID to be updated
            serverObj : REQUIRED : dictionary containing the server configuration
        """
        if serverId is None:
            raise ValueError("Require a destination server ID")
        if serverObj is None or type(serverObj) != dict:
            raise Exception("Require a dictionary defining the server destination configuration")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateDestinationServer with ID: {serverId}")
        path = f"/destination-servers/{serverId}"
        res = self.connector.putData(self.endpoint+path, data=serverObj)
        return res
    
    def getAudienceTemplates(self)->list:
        """
        Return a list of all audience templates for your IMS Organization
        """
        path = "/audience-templates"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def getAudienceTemplate(self,audienceId:str=None)->dict:
        """
        Return a specific Audience Template.
        Arguments:
            audienceId : REQUIRED : The ID of the audience template configuration that you want to retrieve.
        """
        if audienceId is None:
            raise ValueError("Require an audience ID")
        path = f"/audience-templates/{audienceId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getAudienceTemplate with ID: {audienceId}")
        res = self.connector.getData(self.endpoint + path)
        return res
    
    def deleteAudienceTemplate(self,audienceId:str=None)->dict:
        """
        Delete a specific Audience Template.
        Arguments:
            audienceId : REQUIRED : The ID of the audience template configuration that you want to delete
        """
        if audienceId is None:
            raise ValueError("Require an audience ID")
        path = f"/audience-templates/{audienceId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteAudienceTemplate with ID: {audienceId}")
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def createAudienceTemplate(self,templateObj:dict=None)->dict:
        """
        Create a specific Audience Template based on a dictionary definition passed as parameter.
        Arguments:
            templateObj : REQUIRED : The ID of the audience template configuration that you want to retrieve.
        """
        path = f"/audience-templates/"
        if templateObj is None and type(templateObj) != dict:
            raise ValueError("Require a dictionary for Audience template definition")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createAudienceTemplate")
        res = self.connector.postData(self.endpoint + path,data=templateObj)
        return res
    
    def updateAudienceTemplate(self,audienceId:str=None,templateObj:dict=None)->dict:
        """
        Update a specific Audience Template based on a dictionary definition passed as parameter.
        Arguments:
            audienceId : REQUIRED : The ID of the audience template configuration that you want to delete
            templateObj : REQUIRED : The ID of the audience template configuration that you want to retrieve.
        """
        path = f"/audience-templates/{audienceId}"
        if audienceId is None:
            raise ValueError("Require an audience template ID")
        if templateObj is  None and type(templateObj) != dict:
            raise ValueError("Require a dictionary for Audience template definition")
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateAudienceTemplate with ID: {audienceId}")
        res = self.connector.postData(self.endpoint + path,data=templateObj)
        return res

    def getCredentials(self)->list:
        """
        Retrieve a list of all credentials configurations for your IMS Organization 
        """
        path = "/credentials"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getCredentials")
        res = self.connector.getData(self.endpoint + path)
        return res
    
    def getCredential(self,credentialId:str=None)->dict:
        """
        Return a specific credential based on its ID.
        Arguments:
            credentialId : REQUIRED : The ID of the credential to retrieve
        """
        if credentialId is None:
            raise ValueError("Require a credential ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getCredential with ID: {credentialId}")
        path = f"/credentials/{credentialId}"
        res = self.connector.getData(self.endpoint + path)
        return res
    
    def deleteCredential(self,credentialId:str=None)->dict:
        """
        Delete a specific credential based on its ID
        Arguments:
            credentialId : REQUIRED : Credential ID to be deleted
        """
        if credentialId is None:
            raise ValueError("Require a credential ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteCredential with ID: {credentialId}")
        path = f"/credentials/{credentialId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res
    
    def createCredential(self,credentialObj:dict=None)->dict:
        """
        Create a credential configuration based on the dictionary passed.
        Arguments:
            credentialObj : REQUIRED : The credential object definition
        """
        if credentialObj is None or type(credentialObj) != dict:
            raise ValueError("Require a dictionary for definition")
        if self.loggingEnabled:
            self.logger.debug(f"Starting createCredential")
        path = "/credentials"
        res = self.connector.postData(self.endpoint + path,data=credentialObj)
        return res
    
    def updateCredential(self,credentialId:str=None,credentialObj:dict=None)->dict:
        """
        Update the credential configuration based on the dictionary and the credential ID passed.
        Arguments:
            credentialId : REQUIRED : The credentialId to be updated
            credentialObj : REQUIRED : The credential object definition
        """
        if credentialObj is None or type(credentialObj) != dict:
            raise ValueError("Require a dictionary for definition")
        path = f"/credentials/{credentialId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting updateCredential with ID: {credentialId}")
        res = self.connector.putData(self.endpoint + path,data=credentialObj)
        return res
    
    def getSampleProfile(self,destinationInstanceId:str=None,destinationId:str=None,count:int=100)->dict:
        """
        Generate a sample profile of a destination given the correct arguments.
        Arguments:
            destinationInstanceId : REQUIRED : Also known as order ID. The ID of the destination instance based on which you are generating sample profiles. (example: "49966037-32cd-4457-a105-2cbf9c01826a")
                                    Documentation on how to retrieve it: https://experienceleague.adobe.com/docs/experience-platform/destinations/destination-sdk/api/developer-tools-reference/destination-testing-api.html?lang=en#get-destination-instance-id
            destinationId : REQUIRED : he ID of the destination configuration based on which you are generating sample profiles. The destination ID that you should use here is the ID that corresponds to a destination configuration, created using the createDestination method.
            count : OPTIONAL : The number of sample profiles that you are generating. The parameter can take values between 1 - 1000.
        """
        if destinationId is None:
            raise ValueError("Require a destination ID")
        if destinationInstanceId is None:
            raise ValueError("Require a destination instance ID")
        path = "/sample-profiles"
        params = {
            "destinationInstanceId" : destinationInstanceId,
            "destinationId" : destinationId,
            "count" : count
        }
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSampleProfile")
        res = self.connector.getData(self.endpoint + path,params=params)
        return res
    
    def getSampleDestination(self,destinationConfigId:str=None)->dict:
        """
        Returns a sample template corresponding to the destinationID passed.
        Argument:
            destinationConfigId : REQUIRED : The ID of the destination configuration for which you are generating a message transformation template.
                                            The destination ID that you should use here is the ID that corresponds to a destination configuration, created using the createDestination method
        """
        if destinationConfigId is None:
            raise ValueError("A Destination configuration ID must be specified")
        path = f"/testing/template/sample/{destinationConfigId}"
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSampleDestination with ID: {destinationConfigId}")
        res = self.connector.getData(self.endpoint + path)
        return res

    def generateTestProfile(self,destinationId:str=None,template:str=None,profiles:list=None)->str:
        """
        Generate exported data by making a POST request to the testing/template/render endpoint and providing the destination ID of the destination configuration and the template you created using the sample template API endpoint
        Arguments:
            destinationId : REQUIRED : The ID of the destination configuration for which you are rendering exported data.
            template : REQUIRED : The character-escaped version of the template based on which you are rendering exported data.
            profiles : OPTIONAL : list of dictionary returned by the getSampleProfile method
        """
        if destinationId is None:
            raise ValueError("Require a destination ID")
        if template is None and type(template) != str:
            raise ValueError("Must provide a string that is an escape version of the template")
        path = f"/testing/template/render"
        data = {
            "destinationId": destinationId,
            "template": template,
        }
        if self.loggingEnabled:
            self.logger.debug(f"Starting getSampleDestination with ID: {destinationId}")
        if profiles is not None and type(profiles) == list:
            data['profiles'] = profiles
        res = self.connector.postData(self.endpoint+path, data=data)
        return res
    
    def sendMessageToPartner(self,destinationInstanceId:str=None,profiles:list=None)->dict:
        """
        Test the connection to your destination by sending messages to the partner endpoint.
        Optionally, you can send a list of profiles in the request. If you do not send any profiles, Experience Platform generates those internally. 
        In this case, you can view the profiles that were used for validation in the response you receive from your getSampleProfile endpoint.
        Arguments:
            destinationInstanceId : REQUIRED : Also known as order ID. The ID of the destination instance based on which you are generating sample profiles.
                                            See documentation for info on how to retrieve it: https://experienceleague.adobe.com/docs/experience-platform/destinations/destination-sdk/api/developer-tools-reference/destination-testing-api.html?lang=en#get-destination-instance-id
            profiles : OPTIONAL : list of dictionary returned by the getSampleProfile method
        """
        if destinationInstanceId is None:
            raise ValueError("Require a destination instance ID")
        path = f"/testing/destinationInstance/{destinationInstanceId}"
        data = []
        if profiles is not None:
            data = profiles
        res = self.connector.postData(self.endpoint+path,data=data)
        return res

    def getSubmissions(self)->list:
        """
        List of all destinations submitted for publishing for your IMS Organization
        """
        path = "/destinations/publish"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def getSubmission(self,destinationConfigId:str=None)->dict:
        """
        Get a specific destination submission status based on the ID passed.
        Argument:
            destinationConfigId : REQUIRED : The ID of the destination configuration you have submitted for publishing.
        """
        if destinationConfigId is None:
            raise ValueError("Destination configuration ID is required")
        path = f"/destinations/publish/{destinationConfigId}"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def SubmitDestination(self,destinationObj:dict=None)->dict:
        """
        Submit a destination configuration for publishing
        Arguments:
            destinationObj : REQUIRED : The object defining the destination config. (DestinationId, Access, AllowedOrgs)
        """
        path = "/destinations/publish/"
        if destinationObj is None:
            raise ValueError("A destination object must be specified")
        res = self.connector.postData(self.endpoint+path,data=destinationObj)
        return res

    def updateSubmissionRequest(self,destinationConfigId:str,destinationObj:dict=None)->dict:
        """
        Update the allowed organizations in a destination publish request. 
        Arguments:
           destinationConfigId : REQUIRED : The ID of the destination configuration you have submitted for publishing.
           destinationObj : REQUIRED : The object defining the destination config. (DestinationId, Access, AllowedOrgs)
        """
        if destinationConfigId is None:
            raise ValueError("Require of destinationConfigId value")
        if destinationObj is None:
            raise ValueError("Require a dictionary for defining")
        path = f"/destinations/publish/{destinationConfigId}"
        res = self.connector.putData(self.endpoint+path,data=destinationObj)
        return res

