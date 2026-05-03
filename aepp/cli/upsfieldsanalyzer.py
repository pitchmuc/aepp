import aepp
from aepp import schema,catalog,segmentation,flowservice, ConnectObject,schemamanager
from typing import Union
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import re

class UpsFieldsAnalyzer:
    """
    Class that extract the relationships of the fields for union schemas
    """
    loggingEnabled = False
    logger = None

    def __init__(
            self,
        union:str="https://ns.adobe.com/xdm/context/profile__union",
        config: Union[dict,'ConnectObject'] = aepp.config.config_object,
        region:str='nld2',
        **kwargs,
    ):
        """
        Instantiate the data Lineage class.
        Arguments:
            config : REQUIRED : Either ConnectObject instance or a config file to connect to the sandbox.
            union : REQUIRED : The union schema you want to analyze. Default: https://ns.adobe.com/xdm/context/profile__union
                Possible values:
                    'https://ns.adobe.com/xdm/context/experienceevent__union'
                    'https://ns.adobe.com/experience/journeyOrchestration/stepEvents/journeyStepEvent__union'
                    'https://ns.adobe.com/experience/journeyOrchestration/stepEvents/journeyStepEvent__union'
                    'https://ns.adobe.com/xdm/context/segmentdefinition__union'
                    'https://ns.adobe.com/experience/customerJourneyManagement/ajoEntity__union'
            region : OPTIONAL : If you are using a different region than the one automatically assigned (default : nld2, possible option: va7,aus5)
        Additional kwargs will update the header.
        """
        if union is None:
            raise ValueError("Requires the usage of an union schema definition")
        self.union = union
        self.classId = self.union.split('__')[0]
        self.config = config
        self.region = region
        self.sandbox = config.sandbox
        self.schemaAPI = schema.Schema(config=config)
        self.catalogAPI = catalog.Catalog(config=config)
        self.segmentationAPI = segmentation.Segmentation(config=config)
        self.flowAPI = flowservice.FlowService(config=config)
        self.unionSchema = schemamanager.SchemaManager(union,config=config)
        df_union = self.unionSchema.to_dataframe(queryPath=True)
        self.df_union = df_union.set_index('querypath',drop=True)
        self.__schemaInfo__(config=config)
        self.__datasetInfo__()
        self.__audienceInfo__()
        self.__flowserviceInfoDestinations__()
        self.__flowserviceInfoSource__()
        self.__audienceInfo__()


    def __schemaInfo__(self,config)->None:
        """
        Extract the information of schema.
        Provide the following attributes:
        * schemaManagers : dict {$id:schemaManager}

        """
        schemas = self.schemaAPI.getSchemas(classFilter=self.classId)
        list_schemaIds = [sch.get('$id') for sch in schemas]
        none_params = [None for _ in range(len(list_schemaIds))]
        config_params = [deepcopy(config) for _ in range(len(list_schemaIds))]
        self.schemaManagers = {}
        with ThreadPoolExecutor(max_workers=10) as executor: 
            schemaDetails = list(executor.map(schemamanager.SchemaManager, list_schemaIds,none_params,none_params,none_params,none_params,config_params))
        for sch in schemaDetails:
            self.schemaManagers[sch.id] = sch

    def __audienceInfo__(self)->None:
        """
        Extract the segmentation information
        Provide the following attributes:
        * audiences : list of audiences
        * audiences_definitions : dict { id : {definition, class}}
        """
        audiences = self.segmentationAPI.getAudiences()
        self.audiences_definitions = {
            seg['id']:{
                'name':seg.get('name'),
                'definition':seg,
                'format' : seg.get('expression',{}).get('format'),
                'class':[el.get("$ref") for el in seg.get('definedOn',[{}])]
                }
                for seg
                in audiences
                if self.union in [el.get("$ref") for el in seg.get('definedOn',[{}])]
            }
        self.paths_audiences = {path:{} for path in self.df_union['path'].to_list()}
        for segId in self.audiences_definitions:
            paths = self.segmentationAPI.extractPaths(self.audiences_definitions[segId].get('definition'))
            for path in paths:
                if path in self.paths_audiences.keys():
                    self.paths_audiences[path][segId] = {
                            "name": self.audiences_definitions[segId]["name"]
                        }
    
    def __datasetInfo__(self):
        """
        Extract the dataset information
        Provide the following attributes:
        * dict_datasetId_name : dict { id : name }
        * observableSchemas : dict { id : ObsSchema}
        * observable_df : dict { id : df }
        * dataset_schema : dict { id : schema $id }
        * datasets : list (of dataset ID)
        """
        datasets = self.catalogAPI.getDataSets(output='list')
        enabledDatasets = []
        self.dict_datasetId_name = {}
        list_enabled_datasetIds = []
        for ds in datasets:
            if 'enabled:true' in ds.get('tags',{}).get('unifiedProfile',[]):
                enabledDatasets.append(ds)
                self.dict_datasetId_name[ds['id']] = ds['name']
                list_enabled_datasetIds.append(ds['id'])
        with ThreadPoolExecutor(max_workers=10) as executor: 
            observableSchemasList = list(executor.map(self.catalogAPI.getDataSetObservableSchema, list_enabled_datasetIds,[True]*len(list_enabled_datasetIds)))
        self.observableSchemas = {}
        self.observable_df = {}
        self.dataset_schema = {}
        self.datasets = []
        for element in observableSchemasList:
            obs = catalog.ObservableSchemaManager(element)
            if obs.schemaId is not None:
                datasetSchema = self.schemaAPI.getSchema(obs.schemaId)
                if datasetSchema.get('meta:class') == self.classId:
                    self.datasets.append(obs.datasetId)
                    self.observableSchemas[element.get('datasetId')] = obs
                    self.dataset_schema[element.get('datasetId')] = datasetSchema
                    self.observable_df[element.get('datasetId')] = self.observableSchemas[element.get('datasetId')].to_dataframe()
    
    def __flowserviceInfoDestinations__(self)->dict:
        """
        Build the flow service data for destination
        Provide the following attributes:
        * destinationsPath : dict { id : {name:str, paths:list }
        """
        selectors = set()
        destinationFlows = self.flowAPI.getFlows(onlyDestinations=True)
        self.destinationsPath = {}
        for destination in destinationFlows:
            transformations = destination.get('transformations',[{}])
            if len(transformations) > 0:
                if transformations[0].get('name') == 'GeneralTransform':
                    name = destination['name']
                    transformationParams = destination.get('transformations',[{}])[0].get('params',{})
                    if 'profileSelectors' in transformationParams.keys():
                        for selector in transformationParams['profileSelectors'].get('selectors',[]):
                            selectors.add(selector.get('value',{}).get('path'))
                    if 'attributeMapping' in transformationParams.keys() and len(transformationParams.get('attributeMapping',[])) > 0:
                        from aepp import dataprep
                        dp = dataprep.DataPrep(config=self.config)
                        for mapping in transformationParams['attributeMapping']:
                            mapping = dp.getMappingSet(mapping.get('mappingId'))
                            for map in mapping.get('mappings',[]):
                                selectors.add(map.get('source','unknown'))
                    if 'identityMapping' in transformationParams.keys() and len(transformationParams.get('identityMapping',[])) > 0:
                        for mapping in transformationParams['identityMapping'].get('mappings',[{}]):
                            identitySource = mapping.get('source','unknown')
                            if identitySource != 'unknown':
                                identitySource = identitySource.split('(').pop().split(')')[0]
                                selectors.add(identitySource)
                self.destinationsPath[destination['id']]={
                            'name':name,
                            "paths":list(selectors)
                        }

    
    def __flowserviceInfoSource__(self)->dict:
        """
        Build the flow service data for source
        Provide the following attributes:
        * destinationsPath : dict { id : {name:str, datasetId:str,schemaRef:str }
        """
        sourceFlows = self.flowAPI.getFlows(onlySources=True)
        self.sourceFlows = {}
        def getTargetDetails(sourceConnId)->dict:
            tmp_sourceConnection = self.flowAPI.getTargetConnection(sourceConnId)
            return tmp_sourceConnection
        def getFlowSpec(specId)->dict:
            tmp_sourceSpec = self.flowAPI.getFlowSpec(specId)
            return tmp_sourceSpec
        list_targetIds = [source.get('targetConnectionIds')[0] for source in sourceFlows]
        list_flowSpecIds = [source.get('flowSpec',{}).get('id') for source in sourceFlows if source.get('flowSpec',{}).get('id') is not None]
        with ThreadPoolExecutor(max_workers=10) as executor:
            targetconnections = list(executor.map(getTargetDetails, list_targetIds))
            flowSpecs = list(executor.map(getFlowSpec, list_flowSpecIds))
        for source in sourceFlows:
            sourceName = source['name']
            sourceId = source['id']
            tmp_sourceTargetId = source.get('targetConnectionIds')[0]
            tmp_sourceTarget = [item for item in targetconnections if item['id'] == tmp_sourceTargetId][0]
            params = tmp_sourceTarget.get('params',{})
            specId = source.get('flowSpec',{}).get('id')
            frequency = None
            if specId is not None:
                tmp_sourceSpec = [item for item in flowSpecs if item['id'] == specId][0]
                frequency = tmp_sourceSpec.get('attributes',{}).get('frequency')
            datasetId = params.get('dataSetId',params.get('datasetId'))
            if datasetId in self.datasets:
                self.sourceFlows[sourceId] = {
                    'name' : sourceName,
                    'datasetId' : datasetId,
                    'schemaRef' : self.dataset_schema[datasetId],
                    'frequency':frequency
                }
        

    def __buildRelationships__(self,path:str)->dict:
        """
        Build relationship between a path and the different elements
        Arguments:
            path : REQUIRED : the path to analyze
        """
        result_dict = {'path':path}
        if path in self.df_union.index:
            result_dict['description'] = self.df_union.at[path,'type'] if type(self.df_union.at[path,'type']) == str else self.df_union.at[path,'type'].iloc[0]
            result_dict['fieldGroup'] = self.df_union.at[path,'fieldGroup']
            result_dict['type'] = self.df_union.at[path,'type'] if type(self.df_union.at[path,'type']) == str else self.df_union.at[path,'type'].iloc[0]
        result_dict['schemas'] = {}
        for schemaId in self.schemaManagers:
            if path in self.schemaManagers[schemaId].to_dataframe()['path'].to_list():
                result_dict['schemas'][schemaId] = self.schemaManagers[schemaId].title
        result_dict['datasets'] = {}
        for dsId in self.datasets:
            if path in self.observable_df[dsId]['path'].to_list():
                result_dict['datasets'][dsId] = self.dict_datasetId_name[dsId]
        result_dict['destinationFlows'] = {}
        for flowId in self.destinationsPath:
            if path in self.destinationsPath[flowId]['paths']:
                result_dict['destinationFlows'][flowId] = self.destinationsPath[flowId]['name']
        result_dict['sourceFlows'] = {}
        for sourceId in self.sourceFlows:
            datasetId = self.sourceFlows[sourceId]['datasetId']
            if path in self.observable_df[datasetId]['path'].to_list():
                result_dict['sourceFlows'][sourceId] = {'name':self.sourceFlows[sourceId]['name'],'frequency':self.sourceFlows[sourceId]['frequency']}
        result_dict['audiences'] = self.paths_audiences[path]
        return result_dict
    
    def analyzePaths(self,output:str='df')->Union[list,pd.DataFrame]:
        """
        Analyze the paths of your union schema
        Arguments:
            output : OPTIONAL : The type of output provided. Default "df", possible: "raw" (list)
        """
        list_dictionary = []
        for path in self.df_union.path.to_list():
            list_dictionary.append(self.analyzePath(path))
        if output=='df':
            df = pd.DataFrame(list_dictionary)
            return df
        return list_dictionary

    def analyzePath(self,path:str=None,output:str='dict')->Union[dict,pd.DataFrame]:
        """
        Analyze a specific path
        Arguments:
            path : REQUIRED : The path to analyze
            output : OPTIONAL : The type of output provided ('dict' (default) or 'dataframe' )
        """
        if path is None:
            raise ValueError('path must be specified')
        res = self.__buildRelationships__(path)
        return res

    def to_dataframe(self,save:bool=False)->pd.DataFrame:
        """
        Returns the union schema as dataframe.
        Arguments:
            save : OPTIONAL : If the dataframe is to be saved in a file
        """
        return self.unionSchema.to_dataframe(save=save)
    
    def to_dict(self)->dict:
        """
        Returns the union schema as dictionary.
        """
        return self.unionSchema.to_dict()
