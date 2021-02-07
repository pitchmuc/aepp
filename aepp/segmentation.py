# Internal Library
import aepp
from aepp import connector

class Segmentation:

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs)->None:
        """
        Instanciate the segmentation API methods class-
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header['Accept'] = "application/vnd.adobe.xdm+json"
        self.header.update(**kwargs)
        self.endpoint = aepp.config.endpoints["global"]+aepp.config.endpoints["segmentation"]

    def getSegments(self, onlyRealTime:bool=False,**kwargs)->list:
        """
        Return segment definitions in your experience platfom instance.
        Arguments:
            onlyRealTime : OPTIONAL : If you wish to retrieve only real time compatible segment. (default False)
        Possible arguments:
            - limit : number of segment returned per page
        """
        params = {'limit': kwargs.get('limit', 100)}
        if onlyRealTime:
            params['evaluationInfo.continuous.enabled'] = True
        path = "/segment/definitions"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        if 'segments' in res.keys():
            data = res['segments']
        else:
            data = []
        total_pages = res['page']['totalPages']
        if total_pages > 1:
            nb_request = total_pages
            max_workers = min((len(total_pages), 5))
            list_parameters = [{'page': str(
                x), **params} for x in range(2, total_pages+1)]
            urls = [self.endpoint+path for x in range(2, total_pages+1)]
            with aepp.modules.futures.ThreadPoolExecutor(max_workers) as executor:
                res = executor.map(lambda x, y: self.connector.getData(
                    x, params=y), urls, list_parameters)
            res = list(res)
            append_data = [val for sublist in [data['data'] for data in res]
                           for val in sublist]  # flatten list of list
            data = data + append_data
        return data

    def getSegment(self, segment_id: str = None):
        """
        Return a specific segment definition.
        Argument:
            segment_id : REQUIRED : Segment ID of the segment to be retrieved.
        """
        if segment_id is None:
            raise Exception(
                "Expecting a segment ID to fetch the segment definition.")
        path = f"/segment/definitions/{segment_id}"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def createSegment(self, segment_data: dict = None):
        """
        Create a segment based on the information provided by the dictionary passed.
        Argument :
            segment_data : REQUIRED : Dictionary of the segment definition.
                require in the segment_data: name, description, expression, schema, ttlInDays
        """
        path = "/segment/definitions"
        if segment_data is None or type(segment_data) != dict:
            raise Exception(
                "Expecting data as dictionary format to update the segment.")
        checks = "name,description,expression,schema,ttlInDays".split(
            ',')  # mandatory elements in segment definition
        if len(set(checks) & set(segment_data.keys())) != len(checks):
            raise Exception(
                "Segment data doesn't hold one or several mandatory fields:\n\
                name, description, expression, schema, ttlInDays")
        res = self.connector.postData(self.endpoint+path,
                             data=segment_data, headers=self.header)
        return res

    def deleteSegment(self, segment_id: str = None):
        """
        Delete a specific segment definition.
        Argument:
            segment_id : REQUIRED : Segment ID of the segment to be deleted.
        """
        if segment_id is None:
            raise Exception(
                "Expecting a segment ID to delete the segment.")
        path = f"/segment/definitions/{segment_id}"
        res = self.connector.deleteData(self.endpoint+path, headers=self.header)
        return res

    def updateSegment(self, segment_id: str = None, segment_data: dict = None):
        """
        Update the segment characteristics from the definition pass to that method.
        Arguments:
            segment_id : REQUIRED : id of the segment to be udpated.
            segment_data : REQUIRED : Dictionary of the segment definition.
                require in the segment_data: name, description, expression, schema, ttlInDays
        """
        if segment_id is None:
            raise Exception(
                "Expecting a segment ID to update the segment.")
        elif segment_data is None or type(segment_data) != dict:
            raise Exception(
                "Expecting data as dictionary format to update the segment.")
        path = f"/segment/definitions/{segment_id}"
        checks = "name,description,expression,schema,ttlInDays".split(
            ',')  # mandatory elements in segment definition
        if len(set(checks) & set(segment_data.keys())) != len(checks):
            raise Exception(
                "Segment data doesn't hold one or several mandatory fields:\n\
                name, description, expression, schema, ttlInDays")
        update = self.connector.postData(
            self.endpoint+path, headers=self.header, data=segment_data)
        return update

    def exportJobs(self, limit: int = 100, status: str = None):
        """
        Retrieve a list of all export jobs.
        Arguments:
            limit : OPTIONAL : number of jobs to be returned (default 100)
            status : OPTIONAL : status of the job (NEW, SUCCEEDED, FAILED)
        """
        path = "/export/jobs"
        params = {"limit": limit}
        if status is not None and status in ['NEW', 'SUCEEDED', 'FAILED']:
            params['status'] = status
        res = self.connector.getData(self.endpoint+path,
                            params=params, headers=self.header)
        return res

    def createExport(self, export_data: dict = None):
        """
        Retrieve a list of all export jobs.
        Arguments:
            export_data : REQUIRED : number of jobs to be returned (default 100)
        """
        path = "/export/jobs"
        if export_data is None:
            raise Exception(
                "Expected export data to specify segment to export.")
        res = self.connector.postData(self.endpoint+path,
                             data=export_data, headers=self.header)
        return res

    def getExport(self, export_id: str = None):
        """
        Retrieve a specific export Job.
        Arguments:
            export_id : REQUIRED : Export Job to be retrieved.
        """
        if export_id is None:
            raise Exception("Expected a export_id")
        path = f"/export/jobs/{export_id}"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def deleteExport(self, export_id: str = None):
        """
        Cancel or delete an export Job.
        Arguments:
            export_id : REQUIRED : Export Job to be deleted.
        """
        if export_id is None:
            raise Exception("Expected a export_id")
        path = f"/export/jobs/{export_id}"
        res = self.connector.deleteData(self.endpoint+path, headers=self.header)
        return res

    def searchNamespaces(self, query: str = None, schema: str = "_xdm.context.segmentdefinition", **kwargs):
        """
        Return a list of search count results, queried across all namespaces.
        Arguments:
            query : REQUIRED : the search query.
            schema : OPTIONAL : The schema class value associated with the search objects. (default _xdm.context.segmentdefinition)
        """
        path = "/search/namespaces"
        if query is None:
            raise Exception("Expected a query to search for.")
        params = {"schema.name": schema, "s": query}
        self.header['x-ups-search-version'] = "1.0"
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
        del self.header["x-ups-search-version"]
        return res

    def searchEntity(self, query: str = None, namespace: str = "ECID", entityId: str = None, schema: str = "_xdm.context.segmentdefinition", **kwargs):
        """
        Return the list of objects that are contained  within a namespace.
        Arguments:
            query : REQUIRED : the search query.
            schema : OPTIONAL : The schema class value associated with the search objects.(defaul _xdm.context.segmentdefinition)
            namespace : OPTIONAL : The namespace you want to search within (default ECID)
            entityId : OPTIONAL : The ID of the folder you want to search for external segments in
        possible kwargs:
            limit : maximum number of result per page. Max 50.
            page : page to be retrieved (start at 0)
            page_limit : maximum number of pages retrieved.
        """
        path = "/search/entities"
        if query is None:
            raise Exception("Expected a query to search for.")
        limit = kwargs.get('limit', 50)
        page = kwargs.get("page", 0)
        page_limit = kwargs.get("page_limit", 0)
        self.header['x-ups-search-version'] = "1.0"
        params = {"schemaClass": schema,
                  "namespace": namespace, "s": query, "entityId": entityId, "limit": limit, "page": page}
        res = self.connector.getData(self.endpoint+path,
                            headers=self.header, params=params)
        data = res['entities']
        curr_page = res['page']["pageOffset"]
        total_pages = res['page']["totalPages"]
        while curr_page <= page_limit - 1 or curr_page == total_pages:
            res = self.connector.getData(self.endpoint+path,
                                headers=self.header, params=params)
            data += res['entities']
            curr_page = res['page']["pageOffset"]
            total_pages = res['page']["totalPages"]
        del self.header["x-ups-search-version"]
        return data

    def getSchedules(self):
        """
        Return the list of scheduled segments.
        """
        path = "/config/schedules"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def createSchedule(self, schedule_data: dict = None):
        """
        Schedule a segment to run.
        Arguments:
            schedule_data : REQUIRED : Definition of the schedule.
            Should contains name, type, properties, schedule.
        """
        path = "/config/schedules"
        if schedule_data is None or type(schedule_data) != dict:
            raise Exception(
                "Expected a dictionary data for setting the segment schedule.")
        min_requirements = "name,type,properties,schedule".split(',')
        if len(set(min_requirements) & set(schedule_data.keys())) != len(min_requirements):
            raise Exception(
                "Missing one minimal requirements : name, type, properties, schedule")
        res = self.connector.postData(self.endpoint+path,
                             data=schedule_data, headers=self.header)
        return res

    def getSchedule(self, schedule_id: str = None):
        """
        Get a specific schedule definition.
        Argument:
            schedule_id : REQUIRED : Segment ID to be retrieved.
        """
        if schedule_id is None:
            raise Exception("Expected a schedule_id")
        path = f"/config/schedules/{schedule_id}"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def deleteSchedule(self, schedule_id: str = None):
        """
        Delete a specific schedule definition.
        Argument:
            schedule_id : REQUIRED : Segment ID to be deleted.
        """
        if schedule_id is None:
            raise Exception("Expected a schedule_id")
        path = f"/config/schedules/{schedule_id}"
        res = self.connector.deleteData(self.endpoint+path, headers=self.header)
        return res

    def getJobs(self, name: str = None, status: str = None, limit: int = 100, **kwargs):
        """
        Returns the list of segment jobs.
        Arguments: 
            name : OPTIONAL : Name of the snapshot
            status : OPTIONAL : Status of the job (PROCESSING,)
            limit : OPTIONAL : Amount of jobs to be retrieved
        """
        path = "/segment/jobs"
        params = {"snapshot.name": name, "status": status, "limit": limit}
        res = self.connector.getData(self.endpoint+path,
                            params=params, headers=self.header)
        return res

    def createJob(self, job_data: list = None):
        """
        Create a new job for a segment.
        Argument: 
            job_data : REQUIRED : a list describing the job to be created.
        """
        path = "/segment/jobs"
        if job_data is None or type(job_data) != list:
            raise Exception("Expecting a list of segment ID to run.")
        res = self.connector.postData(self.endpoint+path,
                             data=job_data, headers=self.header)
        return res

    def getJob(self, job_id: str = None):
        """
        Retrieve a Segment job by ID.
        Argument:
            job_id: REQUIRED : The job ID to retrieve.
        """
        path = f"/segment/jobs/{job_id}"
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def deleteJob(self, job_id: str = None):
        """
        deleteJob a Segment job by ID.
        Argument:
            job_id: REQUIRED : The job ID to delete.
        """
        path = f"/segment/jobs/{job_id}"
        res = self.connector.deleteData(self.endpoint+path, headers=self.header)
        return res
