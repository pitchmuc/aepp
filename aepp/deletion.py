#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

import json
from typing import Optional, Union
import json,time
import logging

# Non standard libraries
import aepp
from aepp.configs import ConnectObject
from aepp import connector

class Deletion:
    """
    This class regroups differet methods and combine some to clean and delete artefact from Adobe Experience Platform.
    Supported in this class:
    - Deleting datasets (and associated artefacts)
    - Deleteting dataflows (and associated artefacts)
    - Deleting schemas (and associated artefacts)
    - Deleting audiences
    """
    loggingEnabled = False
    logger = None

    def __init__(self,
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,):
        """
        initialize the Flow Service instance.
        Arguments:
            config : OPTIONAL : config object in the config module.
            header : OPTIONAL : header object  in the config module.
            loggingObject : OPTIONAL : A dictionary presenting the configuration of the logging service.
        """
        if isinstance(config,dict):
            config = ConnectObject(**config)
        self.config = config
        self.header = header
        if loggingObject is not None and sorted(["level", "stream", "format", "filename", "file"]) == sorted(list(loggingObject.keys())):
            self.loggingEnabled = True
            self.logger = logging.getLogger(f"{__name__}")
            self.logger.setLevel(loggingObject["level"])
            formatter = logging.Formatter("%(asctime)s::%(name)s::%(funcName)s::%(levelname)s::%(message)s::%(lineno)d")
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

    def __str__(self):
        return f"Adobe Experience Platform Deletion Service instance with config: {self.config}"
    
    def __repr__self(self):
        return f"Deletion(config={self.config})"
    
    def deleteDataset(self,datasetId: str,associatedArtefacts:bool=False) -> dict:
        """
        Delete a dataset and all associated artefacts (dataflows, schemas, data connections).
        Arguments:
            datasetId : REQUIRED : The identifier of the dataset to delete.
            associatedArtefacts : OPTIONAL : If set to True, all associated artefacts (dataflows, schemas) will also be deleted (default False).
                Note : Deleting associated arterfacts option will be pass down to other methods called within this method. So Field Groups, Data Type could be impacted.
                In case, it is not possible to delete artefacts, it will be silently ignored and returns in the output dictionary.
        """
        result = {}
        from aepp import catalog
        cat = catalog.Catalog(config=self.config)
        dataset = cat.getDataSet(datasetId=datasetId)
        datasetInfo = dataset[list(dataset.keys())[0]]
        schemaRef = datasetInfo.get('schemaRef',{}).get('id',None)
        res = cat.deleteDataSet(datasetId=datasetId)
        result['dataset'] = res
        if associatedArtefacts:
            # Deleting associated dataflows
            result['flows'] = {'connections':{}, 'flows': {}} 
            from aepp import flowservice
            flow = flowservice.FlowService(config=self.config)
            target_dataflows = flow.getTargetConnections()
            source_dataflows = flow.getSourceConnections()
            list_target_dataflowsIds = [fl['id'] for fl in target_dataflows if fl.get('params',{}).get('dataSetId',None) == datasetId] ## target is Datalake
            list_source_dataflows_datalake = [fl for fl in source_dataflows if fl.get('name',None) == 'Datalake Source Connection'] ## source is Datalake
            list_source_dataflowsIds = [fl['id'] for fl in list_source_dataflows_datalake if fl.get('params',{}).get('dataSetId',None) == datasetId]
            flows = flow.getFlows()
            list_flowIds = [f['id'] for f in flows if f.get('sourceConnectionIds',[""])[0] in list_source_dataflowsIds or f.get('targetConnectionIds',[""])[0] in list_target_dataflowsIds]
            for flowId in list_flowIds:
                res_flow = self.deleteDataFlow(flowId=flowId, associatedArtefacts=associatedArtefacts)
                result['flows']['flows'][flowId] = res_flow
            # Deleting associated schema
            if schemaRef is not None:
                result['schema'] = self.deleteSchema(schemaId=schemaRef, associatedArtefacts=associatedArtefacts)
        return result

    def deleteSchema(self,schemaId: str,associatedArtefacts:bool=False) -> dict:
        """
        Delete a schema and possibly all associated artefacts.
        Arguments:
            schemaId : REQUIRED : The identifier of the schema to delete.
            associatedArtefacts : OPTIONAL : If set to True, all associated artefacts (fieldGroup, datatype) will also be deleted (default False).
                Note : Deleting associated arterfacts option will be pass down to other methods called within this method. So Field Groups, Data Type could be impacted.
                In case, it is not possible to delete artefacts, it will be silently ignored and returns in the output dictionary.
        """
        result = {'fieldGroup': {}, 'schema': {} , 'datatypes':{} }
        from aepp import schema, schemamanager
        sch = schema.Schema(config=self.config)
        schemaInfo = schemamanager.SchemaManager(schemaId,config=self.config)
        res = sch.deleteSchema(schemaId=schemaId)
        result['schema'] = res
        if associatedArtefacts:
            for fieldgroupId, fieldgroupName in schemaInfo.fieldGroups.items():
                myFG = schemaInfo.getFieldGroupManager(fieldgroupName)
                datatypes = myFG.dataTypes
                for datatypeId, datatypeName in datatypes.items():
                    res_dt = sch.deleteDataType(datatypeId=datatypeId)
                    result['datatypes'][datatypeId] = res_dt
                res_fg = sch.deleteFieldGroup(fieldGroupId=fieldgroupId)
                result['fieldGroupName'][fieldgroupId] = res_fg
        return result
    
    def deleteDataFlow(self,flowId: str,associatedArtefacts:bool=False) -> dict:
        """
        Delete a dataflow and possibly all associated artefacts.
        Arguments:
            flowId : REQUIRED : The identifier of the dataflow to delete.
            associatedArtefacts : OPTIONAL : If set to True, all associated artefacts (source and target) will also be deleted (default False).
                Note : The base connection will be identified and returned but not deleted. It can contains other dataflows still actives."""
        result = {'flow': {}, 'targetConnection': {},'sourceConnection':{}, 'baseConnection': {} }
        from aepp import flowservice
        flow = flowservice.FlowService(config=self.config)
        flowInfo = flow.getFlow(flowId=flowId)
        sourceConnectionIds = flowInfo.get('sourceConnectionIds',[])
        targetConnectionIds = flowInfo.get('targetConnectionIds',[])
        baseConn = flowInfo.get('inheritedAttributes',{}).get('sourceConnections',[{}])[0].get('baseConnection',{}).get('id',None)
        result['baseConnection'] = baseConn
        res = flow.deleteFlow(flowId=flowId)
        result['response_flow'] = res
        if associatedArtefacts:
            for sourceConnectionId in sourceConnectionIds:
                res_sc = flow.deleteSourceConnection(connectionId=sourceConnectionId)
                result["response_sourceConn"] = res_sc
            for targetConnectionId in targetConnectionIds:
                res_tc = flow.deleteTargetConnection(connectionId=targetConnectionId)
                result['response_targetConn'] = res_tc
        return result

    def deleteAudience(self,audienceId: str,**kwargs) -> dict:
        """
        Delete an audience/segment.
        Arguments:
            audienceId : REQUIRED : The identifier of the audience to delete.
        """
        waittime = kwargs.get('waittime',30)
        from aepp import segmentation, flowservice
        myseg = segmentation.Segmentation(config=self.config)
        myflow = flowservice.FlowService(config=self.config)
        destinationsFlows = myflow.getFlows(onlyDestinations=True)
        # Check if the audience is used as a destination in any flow
        for flow in destinationsFlows:
            segmentSelections = flow['transformations'][0]['params']['segmentSelectors']['selectors']
            if audienceId in [seg['value']['id'] for seg in segmentSelections]:
                indexAudience = [seg['value']['id'] for seg in segmentSelections].index(audienceId)
                payload = [
                            {
                                "op":"remove",
                                "path":f"/transformations/0/params/segmentSelectors/selectors/{indexAudience}",
                                "value":{
                                    "type":"PLATFORM_SEGMENT",
                                    "value":{
                                        "id":audienceId
                                        }
                                }
                            }
                        ]
                myflow.updateFlow(flowId=flow.get('id',None), etag=flow['etag'],updateObj=payload)
        time.sleep(waittime) ## Waiting for the changes to be effective in AEP
        res = myseg.deleteAudience(audienceId=audienceId)
        return res