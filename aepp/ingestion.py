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
from copy import deepcopy
import requests
from typing import Union
import logging
import json
from pathlib import Path
from .configs import ConnectObject

class DataIngestion:
    """
    Class that manages sending data via authenticated methods.
    For Batch and Streaming messages.
    """

    loggingEnabled = False
    logger = None

    def __init__(
        self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ):
        """
        Instantiate the DataAccess class.
        Arguments:
            config : OPTIONAL : config object in the config module.
            header : OPTIONAL : header object  in the config module.
        Additional kwargs will update the header.
        """
        requests.packages.urllib3.disable_warnings()
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
            logger=self.logger,
            loggingEnabled=self.loggingEnabled)
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
            aepp.config.endpoints["global"] + aepp.config.endpoints["ingestion"]
        )
        self.endpoint_streaming = aepp.config.endpoints["streaming"]["collection"]
        self.STREAMING_REFERENCE = {
            "header": {
                "schemaRef": {
                    "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
                    "contentType": "application/vnd.adobe.xed-full+json;version={SCHEMA_VERSION}",
                },
                "imsOrgId": "{IMS_ORG_ID}",
                "datasetId": "{DATASET_ID}",
                "createdAt": "1526283801869",
                "source": {"name": "{SOURCE_NAME}"},
            },
            "body": {
                "xdmMeta": {
                    "schemaRef": {
                        "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
                        "contentType": "application/vnd.adobe.xed-full+json;version={SCHEMA_VERSION}",
                    }
                },
                "xdmEntity": {
                    "person": {
                        "name": {
                            "firstName": "Jane",
                            "middleName": "F",
                            "lastName": "Doe",
                        },
                        "birthDate": "1969-03-14",
                        "gender": "female",
                    },
                    "workEmail": {
                        "primary": True,
                        "address": "janedoe@example.com",
                        "type": "work",
                        "status": "active",
                    },
                },
            },
        }

    def createBatch(
        self,
        datasetId: str = None,
        format: str = "json",
        multiline: bool = False,
        enableDiagnostic: bool = False,
        partialIngestionPercentage: int = 0,
        **kwargs
    ) -> dict:
        """
        Create a new batch in Catalog Service.
        Arguments:
            datasetId : REQUIRED : The Dataset ID for the batch to upload data to.
            format : REQUIRED : the format of the data send.(default json)
            multiline : OPTIONAL : If you wish to upload multi-line JSON.
        Possible kwargs:
            replay : the replay object to replay a batch.
            https://experienceleague.adobe.com/docs/experience-platform/ingestion/batch/api-overview.html?lang=en#replay-a-batch
        """
        if datasetId is None:
            raise ValueError("Require a dataSetId")
        if self.loggingEnabled:
            self.logger.debug(f"Using createBatch with following format ({format})")
        obj = {
            "datasetId": datasetId,
            "inputFormat": {"format": format, "isMultiLineJson": False},
        }
        if len(kwargs.get('replay',{}))>0:
            obj['replay'] = kwargs.get('replay')
        if multiline is True:
            obj["inputFormat"]["isMultiLineJson"] = True
        if enableDiagnostic != False:
            obj["enableErrorDiagnostics"] = True
        if partialIngestionPercentage > 0:
            obj["partialIngestionPercentage"] = partialIngestionPercentage
        path = "/batches"
        res = self.connector.postData(self.endpoint + path, data=obj)
        return res

    def deleteBatch(self, batchId: str = None) -> str:
        """
        Delete a batch by applying the revert action on it.
        Argument:
            batchId : REQUIRED : Batch ID to be deleted
        """
        if batchId is None:
            raise ValueError("Require a batchId argument")
        if self.loggingEnabled:
            self.logger.debug(f"Starting deleteBatch for ID: ({batchId})")
        path = f"/batches/{batchId}"
        params = {"action": "REVERT"}
        res = self.connector.postData(self.endpoint + path, params=params)
        return res

    def replayBatch(self, datasetId: str = None, batchIds: list = None) -> dict:
        """
        You can replay a batch that has already been ingested. You need to provide the datasetId and the list of batch to be replay.
        Once specify through that action, you will need to re-upload batch information via uploadSmallFile method with JSON format and then specify the completion.
        You will need to re-use the batchId provided for the re-upload.
        Arguments:
            dataSetId : REQUIRED : The dataset ID attached to the batch
            batchIds : REQUIRED : The list of batchID to replay.
        """
        if datasetId is None:
            raise ValueError("Require a dataset ID")
        if batchIds is None or type(batchIds) != list:
            raise ValueError("Require a list of batch ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting replayBatch for dataset ID: ({datasetId})")
        path = "/batches"
        predecessors = [f"${batchId}" for batchId in batchIds]
        data = {
            "datasetId": datasetId,
            "inputFormat": {"format": "json"},
            "replay": {"predecessors": predecessors, "reason": "replace"},
        }
        res = self.connector.patchData(self.endpoint + path, data=data)
        return res

    def uploadSmallFile(
        self,
        batchId: str = None,
        datasetId: str = None,
        filePath: str = None,
        data: Union[list, dict,str] = None,
        verbose: bool = False,
    ) -> dict:
        """
        Upload a small file (<256 MB) to the filePath location in the dataset.
        Arguments:
            batchId : REQUIRED : The batchId referencing the batch processed created beforehand.
            datasetId : REQUIRED : The dataSetId related to where the data are ingested to.
            filePath : REQUIRED : the filePath that will store the value.
            data : REQUIRED : The data to be uploaded (following the type provided). List or Dictionary, depending if multiline is enabled.
                You can also pass a JSON file path. If the element is a string and ends with ".json", the file will be loaded and transform automatically to a dictionary. 
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
        if self.loggingEnabled:
            self.logger.debug(f"uploadSmallFile as format: ({type(data)})")
        privateHeader = deepcopy(self.header)
        privateHeader["Content-Type"] = "application/octet-stream"
        path = f"/batches/{batchId}/datasets/{datasetId}/files/{filePath}"
        if type(data) == str:
            if '.json' in data:
                with open(Path(path),'r') as f:
                    data = json.load(f)
        res = self.connector.putData(
            self.endpoint + path, data=data, headers=privateHeader
        )
        return res

    def uploadSmallFileFinish(
        self, batchId: str = None, action: str = "COMPLETE", verbose: bool = False
    ) -> dict:
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
        if self.loggingEnabled:
            self.logger.debug(f"Finishing upload for batch ID: ({batchId})")
        params = {"action": action}
        res = self.connector.postData(
            self.endpoint + path, params=params, verbose=verbose
        )
        return res

    def uploadLargeFileStartEnd(
        self,
        batchId: str = None,
        datasetId: str = None,
        filePath: str = None,
        action: str = "INITIALIZE",
    ) -> dict:
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
        params = {"action": action}
        if self.loggingEnabled:
            self.logger.debug(
                f"Starting or Ending large upload for batch ID: ({batchId})"
            )
        path = f"/batches/{batchId}/datasets/{datasetId}/files/{filePath}"
        res = self.connector.postData(self.endpoint + path, params=params)
        return res

    def uploadLargeFilePart(
        self,
        batchId: str = None,
        datasetId: str = None,
        filePath: str = None,
        data: bytes = None,
        contentRange: str = None,
    ) -> dict:
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
        privateHeader["Content-Type"] = "application/octet-stream"
        privateHeader["Content-Range"] = contentRange
        if self.loggingEnabled:
            self.logger.debug(f"Uploading large part for batch ID: ({batchId})")
        path = f"/batches/{batchId}/datasets/{datasetId}/files/{filePath}"
        res = requests.patch(self.endpoint + path, data=data, headers=privateHeader, verify=False)
        res_json = res.json()
        return res_json

    def headFileStatus(
        self, batchId: str = None, datasetId: str = None, filePath: str = None
    ) -> dict:
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
        if self.loggingEnabled:
            self.logger.debug(f"Head File Status batch ID: ({batchId})")
        path = f"/batches/{batchId}/datasets/{datasetId}/files/{filePath}"
        res = self.connector.headData(self.endpoint + path)
        return res

    def getPreviewBatchDataset(
        self,
        batchId: str = None,
        datasetId: str = None,
        format: str = "json",
        delimiter: str = ",",
        quote: str = '"',
        escape: str = "\\",
        charset: str = "utf-8",
        header: bool = True,
        nrow: int = 5,
    ) -> dict:
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
        params = {
            "delimiter": delimiter,
            "quote": quote,
            "escape": escape,
            "charset": charset,
            "header": header,
            "nrow": nrow,
        }
        if self.loggingEnabled:
            self.logger.debug(f"getPreviewBatchDataset for dataset ID: ({datasetId})")
        path = f"/batches/{batchId}/datasets/{datasetId}/preview"
        res = self.connector.getData(self.endpoint + path, params=params)
        return res

    def streamMessage(
        self,
        inletId: str = None,
        data: dict = None,
        flowId: str = None,
        syncValidation: bool = False,
    ) -> dict:
        """
        Send a dictionary to the connection for streaming ingestion.
        Arguments:
            inletId : REQUIRED : the connection ID to be used for ingestion
            data : REQUIRED : The data that you want to ingest to Platform.
            flowId : OPTIONAL : The flow ID for the stream inlet.
            syncValidation : OPTIONAL : An optional query parameter, intended for development purposes.
                If set to true, it can be used for immediate feedback to determine if the request was successfully sent.
        """
        privateHeader = deepcopy(self.header)
        if inletId is None:
            raise Exception("Require a connectionId to be present")
        if data is None and type(data) != dict:
            raise Exception("Require a dictionary to be send for ingestion")
        if flowId is not None:
            privateHeader['x-adobe-flow-id'] = flowId
        if self.loggingEnabled:
            self.logger.debug(f"Starting Streaming single message")
        params = {"syncValidation": syncValidation}
        path = f"/collection/{inletId}"
        res = self.connector.postData(
            self.endpoint_streaming + path, data=data, params=params, headers=privateHeader
        )
        return res

    def streamMessages(
        self,
        inletId: str = None,
        data: list = None,
        flowId: str = None,
        syncValidation: bool = False,
    ) -> dict:
        """
        Send a dictionary to the connection for streaming ingestion.
        Arguments:
            inletId : REQUIRED : the connection ID to be used for ingestion
            data : REQUIRED : The list of data that you want to ingest to Platform.
            flowId : OPTIONAL : The flow ID for the stream inlet.
            syncValidation : OPTIONAL : An optional query parameter, intended for development purposes.
                If set to true, it can be used for immediate feedback to determine if the request was successfully sent.
        """
        privateHeader = deepcopy(self.header)
        if inletId is None:
            raise Exception("Require a connectionId to be present")
        if data is None and type(data) != list:
            raise Exception("Require a list of dictionary to be send for ingestion")
        if flowId is not None:
            privateHeader['x-adobe-flow-id'] = flowId
        if self.loggingEnabled:
            self.logger.debug(f"Starting Streaming multiple messages")
        params = {"syncValidation": syncValidation}
        data = {"messages": data}
        path = f"/collection/batch/{inletId}"
        res = self.connector.postData(
            self.endpoint_streaming + path, data=data, params=params, headers=privateHeader
        )
        return res
