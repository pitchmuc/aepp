#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

import aepp
from aepp import connector
import logging
from typing import Union
from .configs import ConnectObject

class Privacy:
    """
    Class to instanciate a Privacy API connection. Ensure you have the correct access within you Adobe IO connection.
    Information about that class can be found here : https://docs.adobe.com/content/help/en/experience-platform/privacy/api/privacy-jobs.html
    """

    SAMPLE_PAYLOAD = {
        "companyContexts": [{"namespace": "imsOrgID", "value": "{IMS_ORG}"}],
        "users": [
            {
                "key": "DavidSmith",
                "action": ["access"],
                "userIDs": [
                    {
                        "namespace": "email",
                        "value": "dsmith@acme.com",
                        "type": "standard",
                    },
                    {
                        "namespace": "ECID",
                        "type": "standard",
                        "value": "443636576799758681021090721276",
                        "isDeletedClientSide": False,
                    },
                ],
            },
            {
                "key": "user12345",
                "action": ["access", "delete"],
                "userIDs": [
                    {
                        "namespace": "email",
                        "value": "ajones@acme.com",
                        "type": "standard",
                    },
                    {
                        "namespace": "loyaltyAccount",
                        "value": "12AD45FE30R29",
                        "type": "integrationCode",
                    },
                ],
            },
        ],
        "include": ["Analytics", "AudienceManager"],
        "expandIds": False,
        "priority": "normal",
        "analyticsDeleteMethod": "anonymize",
        "regulation": "ccpa",
    }
    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(
        self,
        privacyScope: bool = True,
        aepScope: bool = False,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ) -> None:
        """
        Instanciate the class for Privacy Service call.
        Arguments:
            privacyScope : REQUIRED : set the connection retrieved process with the Privacy JWT scope (default True).
            aepScope : OPTIONAL : set the connection retrieved process with the AEP JWT scope if set to True (default False).
            config : OPTIONAL : config object in the config module.
            header : OPTIONAL : header object  in the config module.
        kwargs:
            kwargs will update the header
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
            aepScope=aepScope,
            privacyScope=privacyScope,
            loggingEnabled=self.loggingEnabled,
            logger=self.logger,
        )
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.endpoint = (
            aepp.config.endpoints["global"] + aepp.config.endpoints["privacy"]
        )

    def getJobs(
        self, regulation: str = None, limit: int = 50, status: str = None, **kwargs
    ) -> dict:
        """
        Returns the job that are being processed on Adobe.
        Arguments:
            regulation : REQUIRED : The privacy regulation to return jobs from. (gdpr, ccpa, pdpa_tha)
            limit : OPTIONAL : The number of jobs to return in the response body.(default 50)
            status : OPTIONAL : Filters jobs by processing status. (complete, processing, submitted, error)
        Possible kwargs: see documentation : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Privacy_Jobs/fetchAllJobs
        """
        if regulation is None:
            raise Exception("Required regulation parameter")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getJobs")
        path = "/jobs"
        params = {"size": limit, "regulation": regulation}
        if status is not None:
            params["status"] = status
        if len(kwargs) > 0:
            for key in kwargs:
                params[key] = str(kwargs[key])
        res = self.connector.getData(
            self.endpoint + path, params=params, headers=self.header
        )
        return res

    def getJob(self, jobId: str = None) -> dict:
        """
        Return a specific job by its job ID.
        Arguments:
            jobId : REQUIRED : the Job ID to fetch
        """
        if jobId is None:
            raise Exception("Require a job ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getJob")
        path = f"/jobs/{jobId}"
        res = self.connector.getData(self.endpoint + path, headers=self.header)
        return res

    def postJob(self, data: dict = None) -> dict:
        """
        Return a specific job by its job ID.
        Arguments:
            data : REQUIRED : data to be send in order to start a job.
            You can use the SAMPLE_PAYLOAD to help you create the data.
        """
        if data is None or type(data) != dict:
            raise Exception("Require a dictionary to be passed")
        if self.loggingEnabled:
            self.logger.debug(f"Starting postJob")
        path = "/jobs/"
        res = self.connector.postData(
            self.endpoint + path, data=data, headers=self.header
        )
        return res

    def postChildJob(self, jobId: str = None, data: dict = None) -> dict:
        """
        This is to add a job on a parent Job.
        Argument:
            jobId : REQUIRED : the Job ID to append the job to
            data : REQUIRED : dictionary of data to be added.
        """
        if jobId is None:
            raise Exception("Require a job ID")
        if data is None or type(data) != dict:
            raise Exception("Require a dictionary to be passed")
        if self.loggingEnabled:
            self.logger.debug(f"Starting gpostChildJob")
        path = f"/jobs/{jobId}/child-job"
        res = self.connector.postData(
            self.endpoint + path, data=data, headers=self.header
        )
        return res
