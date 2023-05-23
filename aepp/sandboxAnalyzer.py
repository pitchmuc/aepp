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
from aepp import connector,schema,catalog,segmentation,flowservice,customerprofile,identity
import logging, time
from typing import Union
from .configs import ConnectObject
import pandas as pd
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import datetime

class SandboxAnalyzer:
    """
    A collection of methods to realize actions on the sandboxes.
    It comes from the sandbox API:
    https://www.adobe.io/apis/experienceplatform/home/api-reference.html#!acpdr/swagger-specs/sandbox-api.yaml
    """

    ## logging capability
    loggingEnabled = False
    logger = None

    def __init__(
        self,
        sandbox:str=None,
        region:str='nld2',
        config: Union[dict,ConnectObject] = aepp.config.config_object,
        header: dict = aepp.config.header,
        loggingObject: dict = None,
        **kwargs,
    ):
        """
        Instantiate the sandbox class.
        Arguments:
            sandbox : REQUIRED : Sandbox to connect to
            region : OPTIONAL : If you are using a different region than the one automatically assigned (default : nld2, possible option: va7)
            config : OPTIONAL : config object in the config module. (DO NOT MODIFY)
            header : OPTIONAL : header object  in the config module. (DO NOT MODIFY)
            loggingObject : OPTIONAL : logging object to log messages.
        Additional kwargs will update the header.
        """
        if sandbox is None:
            raise ValueError("Require a sandbox")
        self.overview = None
        self.overviewSchemas = None
        self.overviewFieldGroups = None
        self.overviewIdentities = None
        self.overviewSegments = None
        self.overviewDatasets = None
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
            config['sandbox'] = sandbox
            config = config
        elif type(config) == ConnectObject:
            config.setSandbox(sandbox)
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
        self.schemaAPI = schema.Schema(config=config)
        self.catalogAPI = catalog.Catalog(config=config)
        self.segmentationAPI = segmentation.Segmentation(config=config)
        self.identityAPI = identity.Identity(config=config,region=region)
        self.profileAPI = customerprofile.Profile(config=config)
        self.flowAPI = flowservice.FlowService(config=config)
        self.overview = self.overviewAnalysis()
        self.list_schemaManagers = []
        self.listFieldGroupManagers = []

    def overviewAnalysis(self,save:bool=False,cache:bool=True)->pd.DataFrame:
        """
        Realize an overview analysis of the sandbox.
        It returns the following information as a dataframe:
         - number of schemas
         - number of datasets
         - number of segments
         - number of data sources
         - number of destinations
         - number of profiles in that sandbox

        NOTE: It will not account for any Adhoce schema based dataset or dataset that contains the word "test" in their name
        """ 
        if cache:
            if self.overview is not None:
                if save:
                    self.overview.to_csv(f'overview_{self.sandbox}.csv',index=False)
                return self.overview
        overview = {'Schemas':[],'Datasets':[],'Segments':[],'DataSources':[],'Destinations':[]}
        self.schemas:list = self.schemaAPI.getSchemas(excludeAdhoc=True)
        overview['Schemas'].append(len(self.schemas))
        self.segments:list = self.segmentationAPI.getSegments()
        overview['Segments'].append(len(self.segments))
        self.datasets:list = self.catalogAPI.getDataSets()
        self.dict_dataset_schema = deepcopy(self.catalogAPI.data.schema_ref)
        self.realDatasetNames = []
        for el in self.dict_dataset_schema:
            tmp_schema = self.schemaAPI.getSchema(self.dict_dataset_schema[el]['id'])
            if 'Adhoc' not in tmp_schema.get('title') and 'test' not in el.lower():
                self.realDatasetNames.append(el)
        self.realDatasetIds:list = [self.catalogAPI.data.ids[dataset] for dataset in self.realDatasetNames]
        self.realDataset_SchemasIds:list = [self.catalogAPI.data.schema_ref[dataset]['id'] for dataset in self.realDatasetNames]
        self.dict_realDatasetIds_Name:dict = {self.catalogAPI.data.ids[dataset]: dataset for dataset in self.realDatasetNames}
        self.datasetId_schemaId:dict = {self.catalogAPI.data.ids[dataset]: self.catalogAPI.data.schema_ref[dataset]['id'] for dataset in self.realDatasetNames}
        overview['Datasets'].append(len(self.realDatasetNames))
        self.connections = self.flowAPI.getConnections()
        self.datasourcesConnections = []
        self.destinationsConnections = []
        for con in self.connections:
            spec = self.flowAPI.getConnectionSpec(con['connectionSpec']['id'])
            if 'attributes' in spec.keys():
                if spec['attributes'].get('isSource'):
                    self.datasourcesConnections.append(con)
                elif spec['attributes'].get('isDestination'):
                    self.destinationsConnections.append(con)
        overview['DataSources'].append(len(self.datasourcesConnections))
        overview['Destinations'].append(len(self.destinationsConnections))
        preview = self.profileAPI.getPreviewStatus()
        overview['Profiles'] = [preview.get('totalRows')]
        df_overview = pd.DataFrame(overview)
        if save:
            df_overview.to_csv(f'overview_{self.sandbox}.csv',index=False)
        return df_overview
    
    def __buildSchemaManagerList__(self,max_workers:int=5)->list:
        """
            Returns the list of schemaManagers built
        """
        listSchemaIds = [s['$id'] for s in self.schemas]
        with ThreadPoolExecutor(max_workers=max_workers,thread_name_prefix = 'Thread') as thread_pool:
            results = thread_pool.map(schema.SchemaManager, listSchemaIds)
        return list(results)

    def schemaAnalyzer(self,save:bool=False,cache:bool=True,max_workers:int=5)->pd.DataFrame:
        """
        This method will run a schema review of your sandbox.
        It returns a dataframe with the following information:
        - schemaId
        - schema Name
        - class associated
        - dataset associated
        - field groups in that schema
        - identities defined in that schema
        - lookups defined in that schema
        - if IdentityMap has been defined
        Arguments:
            save : OPTIONAL : save the data in a csv
            cache : OPTIONAL : if analysis has already been done, re-used the export
            max_workers : OPTIONAL : parallel processing of schemaManager instanciation
        """
        if cache:
            if self.overviewSchemas is not None:
                if save:
                    self.overviewSchemas.to_csv(f'overview_schema_{self.sandbox}.csv',index=False)
                return self.overviewSchemas
        self.list_schemaManagers = self.__buildSchemaManagerList__(max_workers=max_workers)
        schemaDict = {sch.id : {'name':sch.title,'class':'','datasets':0,'fieldGroups':len(sch.fieldGroups),'identities':0,'lookups':0,'identityMap':False} for sch in self.list_schemaManagers}
        for sch in self.list_schemaManagers:
            identityMapField = sch.searchField('identityMap',partialMatch=False)
            if len(identityMapField)>0:
                schemaDict[sch.id]['identityMap'] = True
            if 'experienceevent' in sch.classId:
                schemaDict[sch.id]['class'] = 'experienceevent'
            elif 'context/profile' in sch.classId:
                schemaDict[sch.id]['class'] = 'profile'
            else:
                schemaDict[sch.id]['class'] = 'other'
        identity_descriptors = self.schemaAPI.getDescriptors(type_desc='xdm:descriptorIdentity')
        lookup_descriptors = self.schemaAPI.getDescriptors(type_desc='xdm:descriptorOneToOne')
        for desc in identity_descriptors:
            if desc['xdm:sourceSchema'] in schemaDict.keys():
                schemaDict[desc['xdm:sourceSchema']]['identities'] +=1
        for desc in lookup_descriptors:
            if desc['xdm:sourceSchema'] in schemaDict.keys():
                schemaDict[desc['xdm:sourceSchema']]['lookups'] +=1
        for dataset in self.realDatasetNames:
            if self.catalogAPI.data.schema_ref[dataset]['id'] in schemaDict.keys():
                schemaDict[self.catalogAPI.data.schema_ref[dataset]['id']]['datasets'] +=1
        df_schema = pd.DataFrame(schemaDict).T
        self.overviewSchemas = df_schema
        if save:
            df_schema.to_csv(f'overview_schema_{self.sandbox}.csv',index=False)
        return df_schema

    def fieldGroupAnalyzer(self,save:bool=False,cache:bool=True,max_workers:int=5)->pd.DataFrame:
        """
        This method will run a field group review of your sandbox.
        It only analyses the custom field groups created in your sandbox.
        It returns a dataframe with the following information:
        - Field group ID
        - Field group name
        Arguments:
            save : OPTIONAL : save the data in a csv
            cache : OPTIONAL : if analysis has already been done, re-used the export
            max_workers : OPTIONAL : parallel processing of FieldGroupManager instanciation
        """
        if cache:
            if self.overviewFieldGroups is not None:
                if save:
                    self.overviewFieldGroups.to_csv(f'overview_fieldgroups_{self.sandbox}.csv',index=False)
                return self.overviewFieldGroups
        self.fieldGroups = self.schemaAPI.getFieldGroups()
        listFGids = [fg['$id'] for fg in self.fieldGroups]
        with ThreadPoolExecutor(max_workers=max_workers,thread_name_prefix = 'Thread') as thread_pool:
            results = thread_pool.map(schema.FieldGroupManager, listFGids)
        self.listFieldGroupManagers = list(results)
        fieldGroupDict = {fg.id : {'name':fg.title,'schemas':0,'classExtension':len(fg.fieldGroup.get('meta:intendedToExtend',[]))} for fg in self.listFieldGroupManagers}
        if self.list_schemaManagers == 0:
            self.list_schemaManagers = self.__buildSchemaManagerList__(max_workers=max_workers)
        for sch in self.list_schemaManagers:
            for fgID in sch.fieldGroupIds:
                if fgID in fieldGroupDict.keys():
                    fieldGroupDict[fgID]['schemas'] += 1
        df_fieldGroups = pd.DataFrame(fieldGroupDict).T
        self.overviewFieldGroups = df_fieldGroups
        if save:
            df_fieldGroups.to_csv(f'overview_fieldgroups_{self.sandbox}.csv',index=False)
        return df_fieldGroups
    
    def identitiesAnalyzer(self,save:bool=False,cache:bool=True)->pd.DataFrame:
        """
        Return a dataframe with the identities used in that sandbox.
        """
        if cache:
            if self.overviewIdentities is not None:
                if save:
                    self.overviewIdentities.to_csv(f'overview_identities_{self.sandbox}.csv',index=False)
                return self.overviewIdentities
        identities = self.identityAPI.getIdentities()
        self.overviewIdentities = pd.DataFrame(identities)
        identities_namespaces = self.profileAPI.getPreviewNamespace()
        df_identities_namespace = pd.DataFrame(identities_namespaces['data'])
        df_IDNS_limit = df_identities_namespace[['code','fullIDsCount','fullIDsFragmentCount']]
        self.overviewIdentities = pd.merge(self.overviewIdentities,df_IDNS_limit,left_on='code',right_on='code')
        if save:
            self.overviewIdentities.to_csv(f'overview_identities_{self.sandbox}.csv',index=False)
        return self.overviewIdentities
    
    def segementsAnalyzer(self,save:bool,cache:bool=True)->pd.DataFrame:
        """
        Returns a dataframe with the segment information in that sandbox.
        Update and create also the merge policies overview.
        """
        if cache:
            if self.overviewSegments is not None:
                if save:
                    self.overviewSegments.to_csv('',index=False)
                return self.overviewSegments
        self.mergePolicies = self.profileAPI.getMergePolicies()
        mergePoliciesIdName = {merg['id']:merg['name'] for merg in self.mergePolicies}
        overview_mergePolicies = {merg['id']:{'name' : merg['name'], 'segments':0} for merg in self.mergePolicies}
        def evaluationType(evaluationInfo:dict):
            """Evaluate the type of segment"""
            if evaluationInfo['synchronous']['enabled']:
                return "Edge"
            elif evaluationInfo['continuous']['enabled']:
                return "Streaming"
            elif evaluationInfo['batch']['enabled']:
                return "Batch"
        if cache:
            segments = self.segments
        else:
            segments = self.segmentationAPI.getSegments()
        overview_segments = {seg['name']:{
            'description':seg.get('description'),
            'evaluationType':evaluationType(seg['evaluationInfo']),
            'mergePolicies':mergePoliciesIdName[seg['mergePolicyId']]}
                for seg in segments
                }
        for seg in segments:
            overview_mergePolicies[seg['mergePolicyId']]['segments'] +=1
        self.mergePoliciesOverview = pd.DataFrame(overview_mergePolicies).T
        self.overviewSegments = pd.DataFrame(overview_segments).T
        return self.overviewSegments
    
    def datasetAnalyzer(self,save:bool=False,cache:bool=True)->pd.DataFrame:
        """
        Returns a dataframe with the dataset analysis
        """
        if cache:
            if self.overviewDatasets is not None:
                if save:
                    self.overviewDatasets.to_csv(f"overview_dataset_{self.sandbox}.csv")
                return self.overviewDatasets
        dict_schemaId_SchemaName = {sc['id']:sc['title'] for sc in self.schemas}
        overviewDatasets = {myId:{
            "name":name,
            'flows':0,
            'schemaRef':dict_schemaId_SchemaName[schemaId],
            'enabledProfile':False,
            'identities':0, 
            'errorLast7days':0,
            'lastBatchIngestion':None}
                for myId,name,schemaId in zip(self.realDatasetIds,self.realDatasetNames,self.realDataset_SchemasIds)
            }
        ### Profile storage
        datasetProfileDistribution = self.profileAPI.getPreviewDataSet().get('data',{})
        for dataset in datasetProfileDistribution:
            overviewDatasets[dataset['value']]['identities'] = dataset['fullIDsCount']
        ### Batch errors & Profile enabled
        week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        week_ago_ts = datetime.datetime.timestamp(week_ago)*1000
        for datasetId in tuple(overviewDatasets.keys()):
            tmp_dataset = self.catalogAPI.getDataSet(datasetId)
            tmp_dataset = tmp_dataset[list(tmp_dataset.keys())[0]]
            if 'enabled:true' in tmp_dataset.get('tags',{}).get('unifiedProfile',[]):
                overviewDatasets[datasetId]['enabledProfile'] = True
            tmp_failedBatches = self.catalogAPI.getFailedBatchesDF(dataSet=datasetId,limit=100)
            if len(tmp_failedBatches)>0:
                overviewDatasets[datasetId]['errorLast7days'] = len(tmp_failedBatches[tmp_failedBatches['timestamp']>week_ago_ts])
        ## last batch error
        lastBatches = self.catalogAPI.getLastBatches(limit=100)
        for key in lastBatches.keys():
            if key in overviewDatasets.keys():
                overviewDatasets[key]['lastBatchIngestion'] = time.ctime(lastBatches[key]['updated']/1000)
        self.overviewDatasets = pd.DataFrame(overviewDatasets).T
        if save:
            self.overviewDatasets.to_csv(f"overview_dataset_{self.sandbox}.csv")
        return self.overviewDatasets