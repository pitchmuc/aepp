import flowservice
import destinationinstanceservice
import os
import time
from utils import Utils

class ExportDatasetToCloudStorage:
    global flow_conn
    global dis_conn
    global utils
    global username
    def __init__(self):
        self.username = os.getlogin()
        self.flow_conn = flowservice.FlowService()
        self.dis_conn = destinationinstanceservice.DestinationInstanceService()
        self.utils = Utils()

    def createDataFlowIfNotExists(self, dataset_id, compression_type, data_format, export_path, on_schedule):
        dataflow_id = self.utils.check_if_exist("Platform", "dataflow_id")
        if dataflow_id is not None:
            flow = self.flow_conn.getFlow(dataflow_id)
            source_connection_id = flow["sourceConnectionIds"][0]
            source_connection = self.flow_conn.getSourceConnection(source_connection_id)
            exist_dataset_id = source_connection["params"]["datasets"][0]["dataSetId"]
            if exist_dataset_id == dataset_id and flow["state"] == "disabled":
                self.flow_conn.postFlowAction(dataflow_id, "enable")
            else:
                dataflow_id = self.createDataFlow(dataset_id, compression_type, data_format, export_path, on_schedule)
        self.createFlowRun(dataflow_id, dataset_id, on_schedule)

    def createDataFlow(self, dataset_id, compression_type, data_format, export_path, on_schedule):
        source_res = self.flow_conn.createSourceConnectionDataLake(
            name=f"[CMLE][Week2] Featurized Dataset source connection created by {self.username}",
            dataset_ids=[dataset_id],
            format="parque"
        )
        try:
            source_connection_id = source_res["id"]
            print("sourceConnectionId " + source_connection_id + "has been created.")
        except KeyError:
            raise RuntimeError(f"Error when creating source connection: {source_res}")

        connection_spec_id = "10440537-2a7b-4583-ac39-ed38d4b848e8"
        base_connection_res = self.flow_conn.createConnection(data={
            "name": f"[CMLE][Week2] Base Connection to DLZ created by {self.username}",
            "auth": None,
            "connectionSpec": {
                "id": connection_spec_id,
                "version": "1.0"
            }
        })
        try:
            base_connection_id = base_connection_res["id"]
            print("baseConnectionId " + base_connection_id + "has been created")
        except KeyError:
            raise RuntimeError(f"Error when creating base connection: {base_connection_res}")

        target_res = self.flow_conn.createTargetConnection(
            data={
                "name": f"[CMLE][Week2] Data Landing Zone target connection created by {self.username}",
                "baseConnectionId": base_connection_id,
                "params": {
                    "mode": "Server-to-server",
                    "compression": compression_type,
                    "datasetFileType": data_format,
                    "path": export_path
                },
                "connectionSpec": {
                    "id": connection_spec_id,
                    "version": "1.0"
                }
            }
        )
        try:
            target_connection_id = target_res["id"]
            print("targetconnectionId " + target_connection_id + " has been created")
        except KeyError:
            raise RuntimeError(f"Error when creating target connection: {target_res}")

        if on_schedule:
            schedule_params = {
                "interval": 3,
                "timeUnit": "hour",
                "startTime": int(time.time())
            }
        else:
            schedule_params = {
                "interval": 1,
                "timeUnit": "day",
                "startTime": int(time.time() + 60*60*24*365)
            }
        flow_spec_id = "cd2fc47e-e838-4f38-a581-8fff2f99b63a"
        flow_obj = {
            "name": f"[CMLE][Week2] Flow for Featurized Dataset to DLZ created by {self.username}",
            "flowSpec": {
                "id": flow_spec_id,
                "version": "1.0"
            },
            "sourceConnectionIds": [
                source_connection_id
            ],
            "targetConnectionIds": [
                target_connection_id
            ],
            "transformations": [],
            "scheduleParams": schedule_params
        }
        flow_res = self.flow_conn.createFlow(
            obj = flow_obj,
            flow_spec_id = flow_spec_id
        )
        try:
            dataflow_id = flow_res["id"]
            print("dataflowId " + dataflow_id + " has been created")
        except KeyError:
            raise RuntimeError(f"Error when creating data flow: {flow_res}")

        #save dataflow_id to config
        self.utils.save_field_in_config("Platform", "dataflow_id", dataflow_id)
        return dataflow_id

    def createFlowRun(self, dataflow_id, dataset_id, on_schedule):
        if not on_schedule:
            res = self.retryOnNotReadyException(dataflow_id = dataflow_id, dataset_id= dataset_id)
            flowRunId = res["destinations"][0]["datasets"][0]["statusURL"].rsplit('/', 1)[-1]
            #check if flowRun has finished
            finished = False
            while not finished:
                try:
                    run = self.flow_conn.getRun(runId = flowRunId)["items"][0]
                    run_id = run["id"]
                    run_started_at = run["metrics"]["durationSummary"]["startedAtUTC"]
                    run_ended_at = run["metrics"]["durationSummary"]["completedAtUTC"]
                    run_duration_secs = (run_ended_at - run_started_at) / 1000
                    run_size_mb = run["metrics"]["sizeSummary"]["outputBytes"] / 1024. / 1024.
                    run_num_rows = run["metrics"]["recordSummary"]["outputRecordCount"]
                    run_num_files = run["metrics"]["fileSummary"]["outputFileCount"]
                    print(f"Run ID {run_id} completed with: duration={run_duration_secs} secs; size={run_size_mb} MB; num_rows={run_num_rows}; num_files={run_num_files}")
                    finished = True
                except Exception as e:
                    print(f"No runs completed yet for flow {self.dataflow_Id}")
                    time.sleep(30)
            #push the startDate to a year from now
            startTime = int(time.time() + 60*60*24*365)
            op = [
                {
                    "op" : "Replace",
                    "path":"/scheduleParams",
                    "value":{
                        "startTime": startTime
                    }

                }
            ]
            flowRes = self.flow_conn.getFlow(dataflow_id)
            eTag = flowRes["etag"]
            self.flow_conn.updateFlow(dataflow_id,eTag,op)
            #disable flow after the adhoc run is completed
            self.flow_conn.postFlowAction(dataflow_id, "disable")

    def retryOnNotReadyException(self, dataflow_id, dataset_id, max_attempts=3, delay=60):
        #set up initial delay due to hollow refresh time interval
        time.sleep(300)
        attempts = 1
        while attempts <= max_attempts:
            print("attempt adhoc dataset export " + str(attempts) + " time(s)")
            res = self.dis_conn.createAdHocDatasetExport({dataflow_id: [dataset_id]})
            try:
                statusURL = res["destinations"][0]["datasets"][0]["statusURL"]
                return res
            except KeyError:
                error = str(res)
                if error.find("Following order ID(s) are not ready for dataset export") != -1:
                    attempts += 1
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    raise RuntimeError(f"Error happens during adhoc dataset export {error}")
        raise RuntimeError(f"Maximum retry attempts ({max_attempts}) reached. Aborting.")