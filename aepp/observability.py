import aepp
from aepp import connector
import time
from concurrent import futures
import pandas as pd

class Observability:

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs)->None:
        """
        Instanciate the observability API methods class.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.sandbox = self.connector.config['sandbox']
        self.endpoint = aepp.config.endpoints["global"]+aepp.config.endpoints["observability"]
        self.POST_METRICS={
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
                                    "groupBy": True
                                    }
                                ],
                                "aggregator": "sum",
                                "downsample": "sum"
                                },
                                {
                                "name": "timeseries.ingestion.dataset.dailysize",
                                "filters": [
                                    {
                                    "name": "dataSetId",
                                    "value": "5eddb21420f516191b7a8dad",
                                    "groupBy": False
                                    }
                                ],
                                "aggregator": "sum",
                                "downsample": "sum"
                                }
                            ]
                            }
        self._loadREFERENCES()
    
    def _loadREFERENCES(self):
        """
        Load document as attributes if possible
        """
        try:
            import importlib.resources as pkg_resources
            pathIdentity = pkg_resources.path("aepp", "observability_identity.pickle")
            pathIngestion = pkg_resources.path("aepp", "observability_ingestion.pickle")
            pathGDPR = pkg_resources.path("aepp", "observability_gdpr.pickle")
            pathQS = pkg_resources.path("aepp", "observability_queryService.pickle")
            pathRLTime = pkg_resources.path("aepp", "observability_realTime.pickle")
        except ImportError:
            # Try backported to PY<37 with pkg_resources.
            try:
                import pkg_resources
                pathIdentity = pkg_resources.resource_filename("aepp", "observability_identity.pickle")
                pathIngestion = pkg_resources.resource_filename("aepp", "observability_ingestion.pickle")
                pathGDPR = pkg_resources.resource_filename("aepp", "observability_gdpr.pickle")
                pathQS = pkg_resources.resource_filename("aepp", "observability_queryService.pickle")
                pathRLTime = pkg_resources.resource_filename("aepp", "observability_realTime.pickle")
            except:
                print('no supported files')
        try:
            with pathIdentity as f:
                self.REFERENCE_IDENTITY = pd.read_pickle(f)
                self.REFERENCE_IDENTITY = self.REFERENCE_IDENTITY.style.set_properties(subset=['Insights metric'], **{'width': '100px'})
            with pathIngestion as f:
                self.REFERENCE_INGESTION = pd.read_pickle(f)
                self.REFERENCE_INGESTION = self.REFERENCE_INGESTION.style.set_properties(subset=['Insights metric'], **{'width': '100px'})
            with pathGDPR as f:
                self.REFERENCE_GDPR = pd.read_pickle(f)
                self.REFERENCE_GDPR = self.REFERENCE_GDPR.style.set_properties(subset=['Insights metric'], **{'width': '100px'})
            with pathRLTime as f:
                self.REFERENCE_REALTIME = pd.read_pickle(f)
                self.REFERENCE_REALTIME = self.REFERENCE_REALTIME.style.set_properties(subset=['Insights metric'], **{'width': '100px'})
            with pathQS as f:
                self.REFERENCE_QUERYSERVICE = pd.read_pickle(f)
                self.REFERENCE_QUERYSERVICE = self.REFERENCE_QUERYSERVICE.style.set_properties(subset=['Insights metric'], **{'width': '100px'})
        except:
            self.REFERENCE_IDENTITY = None
            self.REFERENCE_INGESTION = None
            self.REFERENCE_QUERYSERVICE = None
            self.REFERENCE_GDPR = None
            self.REFERENCE_REALTIME = None

    def createMetricsReport(self,data:dict=None)->dict:
        """
        Using the POST method to retrieve metrics specified in the data dictionary.
        Please use the different REFERENCES attributes to know which metrics are supported.
        You have a template for the data dictionary on the POST_METRICS attribute.
        Arguments:
            data : REQUIRED : The metrics requested in the report creation.
                You can use the POST_METRICS attribute to see a template.
        """
        path = "/metrics"
        res = self.connector.postData(self.endpoint+path,data=data)
        return res