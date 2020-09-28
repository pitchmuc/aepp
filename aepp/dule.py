import aepp
import typing


class Dule:
    """
    Class to manage and retrieve DULE policy.
    This is based on the following API reference : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/
    """

    def __init__(self, **kwargs):
        self.header = aepp.modules.deepcopy(aepp.config.header)
        self.header.update(**kwargs)
        self.endpoint = aepp.config._endpoint+aepp.config._endpoint_dule

    def getPoliciesCore(self, **kwargs):
        """
        Returns the core policies in place in the Organization.
        Possible kwargs:
            limit : A positive integer, providing a hint as to the maximum number of resources to return in one page of results.
            property : Filter responses based on a property and optional existence or relational values. 
            Only the ‘name’ property is supported for core resources. 
            For custom resources, additional supported property values include 'status’, 'created’, 'createdClient’, 'createdUser’, 'updated’, 'updatedClient’, and 'updatedUser’
            orderby : A comma-separated list of properties by which the returned list of resources will be sorted.
            start : Requests items whose ‘orderby’ property value are strictly greater than the supplied ‘start’ value.
            duleLabels : A comma-separated list of DULE labels. Return only those policies whose "deny" expression references any of the labels in this list
            marketingAction : Restrict returned policies to those that reference the given marketing action.
        """
        path = "/policies/core"
        params = {**kwargs}
        res = aepp._getData(self.endpoint+path,
                            params=params, headers=self.header)
        return res

    def getPoliciesCoreId(self, policy_id: str = None):
        """
        Return a specific core policy by its id.
        Arguments:
            policy_id : REQUIRED : policy_id to retrieve.
        """
        if policy_id is None:
            raise Exception("Expected a policy id")
        path = f"/policies/core/{policy_id}"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def getPoliciesCustom(self, **kwargs):
        """
        Returns the custom policies in place in the Organization.
        Possible kwargs:
            limit : A positive integer, providing a hint as to the maximum number of resources to return in one page of results.
            property : Filter responses based on a property and optional existence or relational values. 
            Only the ‘name’ property is supported for core resources. 
            For custom resources, additional supported property values include 'status’, 'created’, 'createdClient’, 'createdUser’, 'updated’, 'updatedClient’, and 'updatedUser’
            orderby : A comma-separated list of properties by which the returned list of resources will be sorted.
            start : Requests items whose ‘orderby’ property value are strictly greater than the supplied ‘start’ value.
            duleLabels : A comma-separated list of DULE labels. Return only those policies whose "deny" expression references any of the labels in this list
            marketingAction : Restrict returned policies to those that reference the given marketing action.
        """
        path = "/policies/custom"
        params = {**kwargs}
        res = aepp._getData(self.endpoint+path,
                            params=params, headers=self.header)
        return res

    def getPoliciesCustom(self, policy_id: str = None):
        """
        Return a specific custom policy by its id.
        Arguments:
            policy_id: REQUIRED: policy_id to retrieve.
        """
        if policy_id is None:
            raise Exception("Expected a policy id")
        path = f"/policies/custom/{policy_id}"
        res = aepp._getData(self.endpoint+path, headers=self.header)
        return res

    def createPolicy(self, policy: typing.Union(dict, typing.IO) = None):
        """
        Create a custom policy.
        Arguments:
            policy : REQURED : A dictionary contaning the policy you would like to implement.
        """
        path = "/policies/custom"
