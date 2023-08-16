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
from aepp import flowservice
from aepp import destinationinstanceservice
import time
import logging
from typing import Union
from aepp.utils import Utils
from .configs import ConnectObject
from tenacity import Retrying
from tenacity import retry_if_result
from tenacity import wait_fixed
from tenacity import stop_after_attempt
from dataclasses import dataclass,asdict,field

@dataclass
class Flow:
    name: str = None
    flowSpec: dict = field(default_factory=dict)
    sourceConnectionIds: list = field(default_factory=list)
    targetConnectionIds: list= field(default_factory=list)
    scheduleParams: dict = field(default_factory=dict)
    transformations: list = field(default_factory=list)

    def __init__(self,
                 name: str,
                 flow_spec: dict,
                 source_connection_id: str,
                 target_connection_id: str,
                 schedule_params: dict,
                 transformations: dict
                 ):
        self.name = name
        self.sourceConnectionIds = [source_connection_id]
        self.targetConnectionIds = [target_connection_id]
        self.flowSpec = flow_spec
        self.scheduleParams = schedule_params
        self.transformations = transformations
@dataclass
class ScheduleParams:
    interval: int = 0
    timeUnit: str = None
    startTime: int = 0
    def __init__(self,
                 interval: int,
                 timeUnit: str,
                 startTime: int):
        self.interval = interval
        self.timeUnit = timeUnit
        self.startTime = startTime

@dataclass
class FlowOp:
    op: str = None
    path: str = None
    value: dict = field(default_factory=dict)

    def __init__(self,
                 op: str,
                 path: str,
                 value: dict):
        self.op = op
        self.path = path
        self.value = value

class ExportDatasetToDataLandingZone:
    """
    A class for exporting dataset to cloud storage functionality
    Attributes
    ----------
    flow_conn : module
        flow service connection
    dis_conn : module
        destination instance service connection
    """

    ## logging capability
    loggingEnabled = False
    logger = None

    flow_conn = None
    dis_conn = None
    #fixed connection spec id for Data Landing Zone, reference: https://experienceleague.adobe.com/docs/experience-platform/destinations/api/export-datasets.html?lang=en
    DLZ_CONNECTION_SPEC_ID = "10440537-2a7b-4583-ac39-ed38d4b848e8"
    #fixed flow spec id for Data Landing Zone, reference: https://experienceleague.adobe.com/docs/experience-platform/destinations/api/export-datasets.html?lang=en
    DLZ_FLOW_SEPC_ID = "cd2fc47e-e838-4f38-a581-8fff2f99b63a"
    def __init__(
            self,
            config: Union[dict,ConnectObject] = aepp.config.config_object,
            header: dict = aepp.config.header,
            loggingObject: dict = None
    ):
        """
        initialize the Export Dataset to Data Landing Zone.
        Arguments:
            config : OPTIONAL : config object in the config module.
            header : OPTIONAL : header object  in the config module.
        """

        self.flow_conn = flowservice.FlowService(config=config, header=header)
        self.dis_conn = destinationinstanceservice.DestinationInstanceService(config=config, header=header)
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

    def createDataFlowIfNotExists(
            self,
            dataset_id: str,
            compression_type: str,
            data_format: str,
            export_path: str,
            on_schedule: bool,
            config_path: str,
            entity_name: str,
            initial_delay: int = 600):
        """
        Create a data flow if not being saved in config file
        Arguments:
          dataset_id : REQUIRED : The dataset that needs to be exported
          compression_type: REQUIRED : define compression type to use when saving data to file. Possible values:
            gzip
            none
          data_format : REQUIRED : define the data format . Possible values:
            json
            parquet
          export_path : REQUIRED : define the folder path in your dlz container
          on_schedule: REQUIRED: define whether you would like to have the export following a fixed schedule or not
          config_path: REQUIRED: define the path of your aepp config file
        """
        dataflow_id = Utils.check_if_exists("Platform", "dataflow_id", config_path)
        if dataflow_id is not None:
            if self.loggingEnabled:
                self.logger.info(f"Flow {dataflow_id} has already existed in config")
            flow = self.flow_conn.getFlow(dataflow_id)
            source_connection_id = flow["sourceConnectionIds"][0]
            source_connection = self.flow_conn.getSourceConnection(source_connection_id)
            exist_dataset_id = source_connection["params"]["datasets"][0]["dataSetId"]
            if exist_dataset_id != dataset_id:
                dataflow_id = self.createDataFlow(dataset_id, compression_type, data_format, export_path, on_schedule, config_path, entity_name)
            elif flow["state"] == "disabled":
                self.flow_conn.postFlowAction(dataflow_id, "enable")
                if self.loggingEnabled:
                    self.logger.info(f"Flow {dataflow_id} with dataset {dataset_id} is enabled")
        else:
            dataflow_id = self.createDataFlow(dataset_id, compression_type, data_format, export_path, on_schedule, config_path)
        self.createFlowRun(dataflow_id, dataset_id, on_schedule, initial_delay)

    def createDataFlow(
            self,
            dataset_id: str,
            compression_type: str,
            data_format: str,
            export_path: str,
            on_schedule: bool,
            config_path: str,
            entity_name: str):
        """
        Create a data flow as it is not saved in config
        Arguments:
          dataset_id : REQUIRED : The dataset that needs to be exported
          compression_type: REQUIRED : define compression type to use when saving data to file. Possible values:
            gzip
            none
          data_format : REQUIRED : define the data format . Possible values:
            json
            parquet
          export_path : REQUIRED : define the folder path in your dlz container
          on_schedule: REQUIRED: define whether you would like to have the export following a fixed schedule or not
          config_path: REQUIRED: define the config file path
          entity_name: REQUIRED: define the name of flow entities
        """
        base_connection_id = self.createBaseConnection(entity_name)
        source_connection_id = self.createSourceConnection(dataset_id, entity_name)
        target_connection_id = self.createTargetConnection(base_connection_id, compression_type, data_format, export_path, entity_name)
        dataflow_id = self.createFlow(source_connection_id, target_connection_id, on_schedule, entity_name)
        #save dataflow_id to config
        Utils.save_field_in_config("Platform", "dataflow_id", dataflow_id, config_path)
        return dataflow_id

    def createBaseConnection(self, entity_name) -> str:
        """
        Create a base connection for Data Landing Zone Destination
        Returns:
            base_connection_id(str)
        """
        base_connection_res = self.flow_conn.createConnection(data={
            "name": entity_name,
            "auth": None,
            "connectionSpec": {
                "id": self.DLZ_CONNECTION_SPEC_ID,
                "version": "1.0"
            }
        })
        try:
            base_connection_id = base_connection_res["id"]
            if self.loggingEnabled:
                self.logger.info("baseConnectionId " + base_connection_id + " has been created")
            return base_connection_id
        except KeyError:
            raise RuntimeError(f"Error when creating base connection: {base_connection_res}")

    def createSourceConnection(self, dataset_id: str, entity_name: str) -> str:
        """
        Create a source connection for Data Landing Zone Destination
        Arguments:
          dataset_id : REQUIRED : The dataset that needs to be exported
          entity_name: REQUIRED: define the name of source connection
        Returns:
          source_connection_id(str)
        """
        source_res = self.flow_conn.createSourceConnectionDataLake(
            name= entity_name,
            dataset_ids=[dataset_id],
            format="parquet"
        )
        try:
            source_connection_id = source_res["id"]
            if self.loggingEnabled:
                self.logger.info("sourceConnectionId " + source_connection_id + " has been created.")
            return source_connection_id
        except KeyError:
            raise RuntimeError(f"Error when creating source connection: {source_res}")

    def createTargetConnection(self, base_connection_id: str, compression_type: str, data_format: str, export_path: str, entity_name: str) -> str:
        """
        Create a target connection for Data Landing Zone Destination
        Arguments:
            base_connection_id : REQUIRED : The base connection id created in previous step
            compression_type: REQUIRED : define compression type to use when saving data to file. Possible values:
                gzip
                none
            data_format : REQUIRED : define the data format . Possible values:
                json
                parquet
            export_path : REQUIRED : define the folder path in your dlz container
            entity_name: REQUIRED: define the name of target connection
        Returns:
          target_connection_id(str)
        """
        target_res = self.flow_conn.createTargetConnection(
            data={
                "name": entity_name,
                "baseConnectionId": base_connection_id,
                "params": {
                    "mode": "Server-to-server",
                    "compression": compression_type,
                    "datasetFileType": data_format,
                    "path": export_path
                },
                "connectionSpec": {
                    "id": self.DLZ_CONNECTION_SPEC_ID,
                    "version": "1.0"
                }
            }
        )
        try:
            target_connection_id = target_res["id"]
            if self.loggingEnabled:
                self.logger.info("targetconnectionId " + target_connection_id + " has been created")
            return target_connection_id
        except KeyError:
            raise RuntimeError(f"Error when creating target connection: {target_res}")

    def createFlow(self, source_connection_id: str, target_connection_id: str, on_schedule: bool, entity_name: str) -> str:
        """
        Create a data flow for Data Landing Zone Destination
        Arguments:
          source_connection_id : REQUIRED : The source connection id created in previous step
          target_connection_id : REQUIRED : The target connection id created in previous step
          on_schedule: REQUIRED: define whether you would like to have the export following a fixed schedule or not
          entity_name: REQUIRED: define the name of the flow
        Returns:
          dataflow_id(str)
        """
        if on_schedule:
            schedule_params = asdict(ScheduleParams(interval=3, timeUnit="hour", startTime=int(time.time())))
        else:
            schedule_params = asdict(ScheduleParams(interval=1, timeUnit="day", startTime=int(time.time() + 60*60*24*365)))

        flow_data = Flow(
            name = entity_name,
            flow_spec = {
                "id": self.DLZ_FLOW_SEPC_ID,
                "version": "1.0"
            },
            source_connection_id = source_connection_id,
            target_connection_id = target_connection_id,
            schedule_params = schedule_params,
            transformations = []
        )
        flow_obj = asdict(flow_data)
        flow_res = self.flow_conn.createFlow(
            obj = flow_obj,
            flow_spec_id = self.DLZ_FLOW_SEPC_ID
        )
        try:
            dataflow_id = flow_res["id"]
            if self.loggingEnabled:
                self.logger.info("dataflowId " + dataflow_id + " has been created")
            return dataflow_id
        except KeyError:
            raise RuntimeError(f"Error when creating data flow: {flow_res}")

    def createFlowRun(self, dataflow_id: str, dataset_id: str, on_schedule: bool, initial_delay: int = 300):
        """
        Create a data flow run
        Arguments:
          dataflow_id : REQUIRED : The flow that needs to be triggered a flow run
          dataset_id : REQUIRED : The dataset that needs to be exported
          on_schedule: REQUIRED: define whether you would like to have the export following a fixed schedule or not
        """
        if not on_schedule:
            #set up initial delay due to hollow refresh time interval
            if self.loggingEnabled:
                self.logger.info(f"Waiting for flow {dataflow_id} to refreshed after {initial_delay} seconds")
            time.sleep(initial_delay)
            if self.loggingEnabled:
                self.logger.info(f"Start create adhoc dataset export for flow {dataflow_id} with dataset {dataset_id }")
            res = self.retryOnNotReadyException(dataflow_id = dataflow_id, dataset_id= dataset_id)
            flow_run_id = res["destinations"][0]["datasets"][0]["statusURL"].rsplit('/', 1)[-1]
            #check if flowRun has finished
            finished = False
            while not finished:
                try:
                    run = self.flow_conn.getRun(runId = flow_run_id)["items"][0]
                    run_id = run["id"]
                    run_started_at = run["metrics"]["durationSummary"]["startedAtUTC"]
                    run_ended_at = run["metrics"]["durationSummary"]["completedAtUTC"]
                    run_duration_secs = (run_ended_at - run_started_at) / 1000
                    run_size_mb = run["metrics"]["sizeSummary"]["outputBytes"] / 1024. / 1024.
                    run_num_rows = run["metrics"]["recordSummary"]["outputRecordCount"]
                    run_num_files = run["metrics"]["fileSummary"]["outputFileCount"]
                    if self.loggingEnabled:
                        self.logger.info(f"Run ID {run_id} completed with: duration={run_duration_secs} secs; size={run_size_mb} MB; num_rows={run_num_rows}; num_files={run_num_files}")
                    finished = True
                except Exception as e:
                    if self.loggingEnabled:
                        self.logger.warn(f"No runs completed yet for flow {dataflow_id}")
                    time.sleep(30)
            #push the startDate to a year from now
            start_time = int(time.time() + 60*60*24*365)
            op = [asdict(FlowOp(op="Replace", path="/scheduleParams", value={"startTime": start_time}))]
            flow_res = self.flow_conn.getFlow(dataflow_id)
            etag = flow_res["etag"]
            self.flow_conn.updateFlow(dataflow_id,etag,op)
            #disable flow after the adhoc run is completed
            self.flow_conn.postFlowAction(dataflow_id, "disable")

    def checkIfRetry(self, res: dict):
        """
        check whether retry is needed base on the error message
        Arguments:
        res : REQUIRED : response from adhoc dataset export
        Returns:
          if retry is needed or not(boolean)
        """
        error = str(res)
        if self.loggingEnabled:
            self.logger.info(f"Checking if retry is needed for adhoc dataset export response {res}")
        return error.find("Following order ID(s) are not ready for dataset export") != -1


    def retryOnNotReadyException(self, dataflow_id: str, dataset_id: str, wait_time: int = 60, max_attempts: int= 5):
        """
        retry adhoc dataset export based on the error type
        Arguments:
              dataflow_id : REQUIRED : The flow that needs to be triggered a flow run
              dataset_id : REQUIRED : The dataset that needs to be exported
              wait_time: OPTIONAL: the wait time between each retry
              max_attempts: OPTIONAL: the maximum retry attempts
        """
        retryer = Retrying(retry = retry_if_result(self.checkIfRetry),wait= wait_fixed(wait_time), stop=stop_after_attempt(max_attempts))
        return retryer(self.dis_conn.createAdHocDatasetExport, {dataflow_id: [dataset_id]})