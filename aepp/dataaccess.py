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
import time
import io
from typing import Union
from .configs import ConnectObject

class DataAccess:
    """
    A class providing methods based on the Data Access API
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/data-access-api.yaml
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
    ):
        """
        Instantiate the DataAccess class.
        Arguments:
            config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
            loggingObject : OPTIONAL : logging object to log messages.
        Additional kwargs will update the header.
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
            loggingObject=self.logger,
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
            aepp.config.endpoints["global"] + aepp.config.endpoints["dataaccess"]
        )

    def getBatchFiles(
        self, batchId: str = None, verbose: bool = False, **kwargs
    ) -> list:
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
        if self.loggingEnabled:
            self.logger.debug(f"Starting getBatchFiles")
        params = {}
        if kwargs.get("limit", None) is not None:
            params["limit"] = str(kwargs.get("limit"))
        if kwargs.get("start", None) is not None:
            params["start"] = str(kwargs.get("start"))
        path = f"/batches/{batchId}/files"
        res = self.connector.getData(
            self.endpoint + path, params=params, verbose=verbose
        )
        try:
            return res["data"]
        except:
            return res

    def getBatchFailed(
        self, batchId: str = None, path: str = None, verbose: bool = False, **kwargs
    ) -> list:
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
        if self.loggingEnabled:
            self.logger.debug(f"Starting getBatchFailed")
        params = {}
        if kwargs.get("limit", None) is not None:
            params["limit"] = str(kwargs.get("limit"))
        if kwargs.get("start", None) is not None:
            params["start"] = str(kwargs.get("start"))
        if path is not None:
            params["path"] = path
        pathEndpoint = f"/batches/{batchId}/failed"
        res = self.connector.getData(
            self.endpoint + pathEndpoint, params=params, verbose=verbose
        )
        try:
            return res["data"]
        except:
            return res

    def getBatchMeta(self, batchId: str = None, path: str = None, **kwargs) -> dict:
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
        if self.loggingEnabled:
            self.logger.debug(f"Starting getBatchMeta")
        params = {}
        if kwargs.get("limit", None) is not None:
            params["limit"] = str(kwargs.get("limit"))
        if kwargs.get("start", None) is not None:
            params["start"] = str(kwargs.get("start"))
        if path is not None:
            params["path"] = path
        pathEndpoint = f"/batches/{batchId}/meta"
        res = self.connector.getData(
            self.endpoint + pathEndpoint, headers=self.header, params=params
        )
        return res

    def getHeadFile(
        self,
        dataSetFileId: str = None,
        path: str = None,
        verbose: bool = False,
    ) -> dict:
        """
        Get headers regarding a file.
        Arguments:
            dataSetFileId : REQURED : The ID of the dataset file you are retrieving.
            path : REQUIRED : The full name of the file identified.
                For example: path=profiles.csv
        """
        if dataSetFileId is None or path is None:
            raise ValueError("Require a dataSetFileId and a path for that method")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getHeadFile")
        params = {"path": path}
        pathEndpoint = f"/files/{dataSetFileId}"
        res = self.connector.headData(
            self.endpoint + pathEndpoint, params=params, verbose=verbose
        )
        return res

    def getFiles(
        self,
        dataSetFileId: str = None,
        path: str = None,
        range: str = None,
        start: str = None,
        limit: int = None,
    ) -> Union[dict,bytes]:
        """
        Returns either a complete file or a directory of chunked data that makes up the file.
        The response contains a data array that may contain a single entry or a list of files belonging to that directory.
        Arguments:
            dataSetFileId : REQUIRED : The ID of the dataset file you are retrieving.
            path : OPTIONAL : The full name of the file. The contents of the file would be downloaded if this parameter is provided.
                For example: path=profiles.csv
                if the extension is .parquet, it will try to return the parquet data decoded (io.BytesIO). 
            range : OPTIONAL : The range of bytes requested. For example: Range: bytes=0-100000
            start : OPTIONAL : A paging parameter to specify start of new page. For example: start=fileName.csv
            limit : OPTIONAL : A paging parameter to specify number of results per page. For example: limit=10
        """
        if dataSetFileId is None:
            raise ValueError("Require a dataSetFileId")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getFiles")
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
        if path is None:
            res: dict = self.connector.getData(
                self.endpoint + pathEndpoint, headers=self.header, params=params
            )
        else:
            if path.endswith('.parquet'):
                data = self.getResource(self.endpoint + pathEndpoint,params={"path":path},format='raw')
                res = io.BytesIO(data.content)
            else:
                data = self.getResource(self.endpoint + pathEndpoint,params={"path":path},format='raw')
                res = data.content
        return res

    def getPreview(self, datasetId: str = None) -> list:
        """
        Give a preview of a specific dataset
        Arguments:
            datasetId : REQUIRED : the dataset ID to preview
        """
        if datasetId is None:
            raise ValueError("Require a datasetId")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getPreview")
        path = f"/datasets/{datasetId}/preview"
        res: dict = self.connector.getData(self.endpoint + path, headers=self.header)
        try:
            return res["data"]
        except:
            return res

    def getResource(
        self,
        endpoint: str = None,
        params: dict = None,
        format: str = "json",
        save: bool = False,
        **kwargs,
    ) -> dict:
        """
        Template for requesting data with a GET method.
        Arguments:
            endpoint : REQUIRED : The URL to GET
            params: OPTIONAL : dictionary of the params to fetch
            format : OPTIONAL : Type of response returned. Possible values:
                json : default
                txt : text file
                raw : a response object from the requests module
        """
        if endpoint is None:
            raise ValueError("Require an endpoint")
        if self.loggingEnabled:
            self.logger.debug(
                f"Using getResource with following format ({format}) to the following endpoint: {endpoint}"
            )
        res = self.connector.getData(endpoint, params=params, format=format)
        if save:
            if format == "json":
                aepp.saveFile(
                    module="catalog",
                    file=res,
                    filename=f"resource_{int(time.time())}",
                    type_file="json",
                    encoding=kwargs.get("encoding", "utf-8"),
                )
            elif format == "txt":
                aepp.saveFile(
                    module="catalog",
                    file=res,
                    filename=f"resource_{int(time.time())}",
                    type_file="txt",
                    encoding=kwargs.get("encoding", "utf-8"),
                )
            else:
                print(
                    "element is an object. Output is unclear. No save made.\nPlease save this element manually"
                )
        return res
