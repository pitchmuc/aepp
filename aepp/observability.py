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
import pandas as pd
import logging
from typing import Union
from .configs import ConnectObject

class Observability:
    """
    A class that presents the different methods available on the Observability API from AEP.
    A complete documentation of the methods can be found here:
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/observability-insights.yaml
    """

    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ) -> None:
        """
        Instanciate the observability API methods class.
        Arguments:
            loggingObject : OPTIONAL : logging object to log messages.
            config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
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
        self.header.update(**kwargs)
        if kwargs.get('sandbox',None) is not None: ## supporting sandbox setup on class instanciation
            self.sandbox = kwargs.get('sandbox')
            self.connector.config["sandbox"] = kwargs.get('sandbox')
            self.header.update({"x-sandbox-name":kwargs.get('sandbox')})
            self.connector.header.update({"x-sandbox-name":kwargs.get('sandbox')})
        else:
            self.sandbox = self.connector.config["sandbox"]
        self.endpoint = (
            aepp.config.endpoints["global"] + aepp.config.endpoints["observability"]
        )
        self.POST_METRICS = {
            "start": "2020-07-14T00:00:00.000Z",
            "end": "2020-07-22T00:00:00.000Z",
            "granularity": "day",
            "metrics": [
                {
                    "name": "timeseries.ingestion.dataset.recordsuccess.count",
                    "filters": [
                        {
                            "name": "dataSetId",
                            "value": "5edcfb2fbb642119194c7d94|5eddb21420f516191b7a8dad",
                            "groupBy": True,
                        }
                    ],
                    "aggregator": "sum",
                    "downsample": "sum",
                },
                {
                    "name": "timeseries.ingestion.dataset.dailysize",
                    "filters": [
                        {
                            "name": "dataSetId",
                            "value": "5eddb21420f516191b7a8dad",
                            "groupBy": False,
                        }
                    ],
                    "aggregator": "sum",
                    "downsample": "sum",
                },
            ],
        }
        self._loadREFERENCES()

    def _loadREFERENCES(self):
        """
        Load document as attributes if possible
        """
        if self.loggingEnabled:
            self.logger.debug(f"Loading references")
        try:
            import importlib.resources as pkg_resources

            pathIdentity = pkg_resources.path("aepp", "observability_identity.pickle")
            pathIngestion = pkg_resources.path("aepp", "observability_ingestion.pickle")
            pathGDPR = pkg_resources.path("aepp", "observability_gdpr.pickle")
            pathQS = pkg_resources.path("aepp", "observability_queryService.pickle")
            pathRLTime = pkg_resources.path("aepp", "observability_realTime.pickle")
        except ImportError:
            # Try backported to PY<37 with pkg_resources.
            if self.loggingEnabled:
                self.logger.debug(f"Loading references - ImportError - 2nd try")
            try:
                import pkg_resources

                pathIdentity = pkg_resources.resource_filename(
                    "aepp", "observability_identity.pickle"
                )
                pathIngestion = pkg_resources.resource_filename(
                    "aepp", "observability_ingestion.pickle"
                )
                pathGDPR = pkg_resources.resource_filename(
                    "aepp", "observability_gdpr.pickle"
                )
                pathQS = pkg_resources.resource_filename(
                    "aepp", "observability_queryService.pickle"
                )
                pathRLTime = pkg_resources.resource_filename(
                    "aepp", "observability_realTime.pickle"
                )
            except:
                print("no supported files")
                if self.loggingEnabled:
                    self.logger.debug(f"Failed loading references")
        try:
            with pathIdentity as f:
                self.REFERENCE_IDENTITY = pd.read_pickle(f)
                self.REFERENCE_IDENTITY = self.REFERENCE_IDENTITY.style.set_properties(
                    subset=["Insights metric"], **{"width": "100px"}
                )
            with pathIngestion as f:
                self.REFERENCE_INGESTION = pd.read_pickle(f)
                self.REFERENCE_INGESTION = (
                    self.REFERENCE_INGESTION.style.set_properties(
                        subset=["Insights metric"], **{"width": "100px"}
                    )
                )
            with pathGDPR as f:
                self.REFERENCE_GDPR = pd.read_pickle(f)
                self.REFERENCE_GDPR = self.REFERENCE_GDPR.style.set_properties(
                    subset=["Insights metric"], **{"width": "100px"}
                )
            with pathRLTime as f:
                self.REFERENCE_REALTIME = pd.read_pickle(f)
                self.REFERENCE_REALTIME = self.REFERENCE_REALTIME.style.set_properties(
                    subset=["Insights metric"], **{"width": "100px"}
                )
            with pathQS as f:
                self.REFERENCE_QUERYSERVICE = pd.read_pickle(f)
                self.REFERENCE_QUERYSERVICE = (
                    self.REFERENCE_QUERYSERVICE.style.set_properties(
                        subset=["Insights metric"], **{"width": "100px"}
                    )
                )
        except:
            if self.loggingEnabled:
                self.logger.debug(f"Failed loading references - backup to None")
            self.REFERENCE_IDENTITY = None
            self.REFERENCE_INGESTION = None
            self.REFERENCE_QUERYSERVICE = None
            self.REFERENCE_GDPR = None
            self.REFERENCE_REALTIME = None

    def createMetricsReport(self, data: dict = None) -> dict:
        """
        Using the POST method to retrieve metrics specified in the data dictionary.
        Please use the different REFERENCES attributes to know which metrics are supported.
        You have a template for the data dictionary on the POST_METRICS attribute.
        Arguments:
            data : REQUIRED : The metrics requested in the report creation.
                You can use the POST_METRICS attribute to see a template.
        """
        if self.loggingEnabled:
            self.logger.debug(f"Starting createMetricsReport")
        path = "/metrics"
        res = self.connector.postData(self.endpoint + path, data=data)
        return res
