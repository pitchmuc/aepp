# Internal Library
import aepp
from aepp import modules


class Profile:

    def __init__(self, **kwargs):
        self.header = aepp.modules.deepcopy(aepp.config.header)
        self.header['Accept'] = "application/vnd.adobe.xdm+json"
        self.header.update(**kwargs)
        # same endpoint than segmentation
        self.endpoint = aepp.config._endpoint+aepp.config._endpoint_segmentation

    def getEntity(self, schema_name: str = "_xdm.context.profile", entityId: str = None, entityIdNS: str = None, mergePoliciyId: str = None, **kwargs):
        """
        Returns an entity by ID or Namespace.
        Arguments:
            schema_name : REQUIRED : class name of the schema to be retrieved. default : _xdm.context.profile
            entityId : OPTIONAL : idenitity ID
            entityIdNS : OPTIONAL : Identity Namespace code. Required if entityId is used.
            mergePoliciyId : OPTIONAL : Id of the merge policy.
        Possible kwargs:
            fields : path of the elements to be retrieved, separated by comma. Ex : "person.name.firstName,person.name.lastName"
            relatedSchema_name : If schema.name is "_xdm.context.experienceevent", this value must specify the schema for the profile entity that the time series events are related to. 
            relatedEntityId : ID of the entity that the ExperienceEvents are associated with. Used when looking up ExperienceEvents. For Native XID lookup, use relatedEntityId=<XID> and leave relatedEntityIdNS absent; 
            For ID:NS lookup, use both relatedEntityId and relatedEntityIdNS fields.
            relatedEntityIdNS : Identity Namespace code of the related entity ID of ExperienceEvent. Used when looking up ExperienceEvents. If this field is used, entityId cannot be empty.
            startTime : Start time of Time range filter for ExperienceEvents. Should be at millisecond granularity. Included. Default: From beginning.
            endTime : End time of Time range filter for ExperienceEvents. Should be at millisecond granularity. Excluded. Default: To the end.
            limit : Number of records to return from the result. Only for time-series objects. Default: 1000
        """
        path = "/access/entities"
        params = {"schema.name":  schema_name, "entityId": entityId,
                  "entityIdNS": entityIdNS, "mergePoliciyId": mergePoliciyId}
        if schema_name == "_xdm.context.experienceevent":
            params["relatedSchema.name"] = kwargs.get(
                "relatedSchema_name", "_xdm.context.profile")
            params["relatedEntityId"] = kwargs.get(
                "relatedEntityId", entityId)
            params["relatedEntityIdNS"] = kwargs.get(
                "relatedEntityIdNS", None)
            params["limit"] = kwargs.get("limit", 1000)
            params["startTime"] = kwargs.get("startTime", None)
            params["endTime"] = kwargs.get("endTime", None)
        params["fields"] = kwargs.get("fields", None)
        res = aepp._getData(self.endpoint+path,
                            params=params, headers=self.header)
        return res

    def getEntities(self, request_data: dict = None):
        """
        Get a number of different identities from ID or namespaces.
        Argument:
            request_data : Required : A dictionary that contains fields for the search.
            Example
            {
                "schema": {
                    "name": "_xdm.context.profile"
                },
                "relatedSchema": {
                    "name": "_xdm.context.profile"
                },
                "fields": [
                    "person.name.firstName"
                ],
                "identities": [
                    {
                    "entityId": "69935279872410346619186588147492736556",
                    "entityIdNS": {
                        "code": "CRMID"
                    }
                    }
                ],
                "timeFilter": {
                    "startTime": 1539838505,
                    "endTime": 1539838510
                },
                "limit": 10
                }
        """
        path = "/access/entities"
        if request_data is None or type(request_data) != dict:
            raise Exception("Expected a dictionary to fetch entities")
        res = aepp._postData(self.endpoint + path,
                             data=request_data, headers=self.header)
        return res

    def deleteEntity(self, schema_name: str = None, entityId: str = None, entityIdNS: str = None):
        """
        Delete a specific entity
        Arguments:
            schema_name : REQUIRED : Name of the associated XDM schema.
            entityId : REQUIRED : entity ID
            entityIdNS : OPTIONAL : entity ID Namespace
        """
        path = "/access/entities"
        params = {}
        if schema_name is None:
            raise Exception("Expected a schema name")
        else:
            params["schema.name"] = schema_name
        if entityId is not None:
            params["entityId"] = entityId
        if entityIdNS is not None:
            params["entityIdNS"] = entityIdNS
        res = aepp._getData(self.endpoint+path,
                            params=params, headers=self.header)

    def getMergePolicies(self, limit: int = 100):
        """
        Returns the list of merge policies hosted in this instance.
        Arguments:
            limit : OPTIONAL : amount of merge policies returned by pages.
        """
        path = "/config/mergePolicies"
        params = {"limit": limit}
        res = aepp._getData(self.endpoint+path,
                            params=params, headers=self.header)
        return res

    def getMergePolicy(self, policy_id: str = None):
        """
        Return a specific merge policy.
        Arguments:
            policy_id : REQUIRED : id of the the policy id to be returned.
        """
        if policy_id is None:
            raise Exception("Missing the policy id")
        path = f"/config/mergePolicies/{policy_id}"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res
