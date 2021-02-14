import aepp
import typing
from aepp import connector

class Policy:
    """
    Class to manage and retrieve DULE policy.
    This is based on the following API reference : https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/
    """

    def __init__(self,config:dict=aepp.config.config_object,header=aepp.config.header, **kwargs):
        """
        Instantiate the class to manage DULE rules and statement directly.
        Arguments:
            config : OPTIONAL : config object in the config module. 
            header : OPTIONAL : header object  in the config module.
        """
        self.connector = connector.AdobeRequest(config_object=config, header=header)
        self.header = self.connector.header
        self.header.update(**kwargs)
        self.endpoint = aepp.config.endpoints["global"]+aepp.config.endpoints["policy"]

    
    def getEnabledCorePolicies(self)->dict:
        """
        Retrieve a list of all enabled core policies.
        """
        path = "/enabledCorePolicies"
        res = self.connector.getData(self.endpoint+path)
        return res

    def createEnabledCorePolicies(self,policyIds:list)->dict:
        """
        Create or update the list of enabled core policies. (PUT)
        Argument:
            policyIds : REQUIRED : list of core policy ID to enable
        """
        path = "/enabledCorePolicies"
        if policyIds is None or type(policyIds) != list:
            raise ValueError("Require a list of policy ID")
        obj = policyIds
        res = self.connector.putData(self.endpoint+path,data=obj)
        return res

    def bulkEval(self,data:dict=None)->dict:
        """
        Enable to pass a list of policies to check against a list of dataSet.
        Argument:
            data : REQUIRED : Dictionary describing the set of label and datasets.
                see https://www.adobe.io/apis/experienceplatform/home/api-reference.html#/Bulk_evaluation/bulkEvalPost
        """
        path = "/bulk-eval"
        if data is None:
            raise Exception("Requires a dictionary to set the labels and dataSets to check")
        res = self.connector.postData(self.endpoint+path,data=data)
        return res



    def getPoliciesCore(self, **kwargs)->dict:
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
        res = self.connector.getData(self.endpoint+path,
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
        res = self.connector.getData(self.endpoint+path, headers=self.header)
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
        res = self.connector.getData(self.endpoint+path,
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
        res = self.connector.getData(self.endpoint+path, headers=self.header)
        return res

    def createPolicy(self, policy: typing.Union(dict, typing.IO) = None):
        """
        Create a custom policy.
        Arguments:
            policy : REQUIRED : A dictionary contaning the policy you would like to implement.
        """
        path = "/policies/custom"
        res = self.connector.postData(self.endpoint+path,data = policy)
        return res


    def getCoreLabels(self,prop:str=None,limit:int=100)->list:
        """
        Retrieve a list of core labels.
        Arguments:
            prop : OPTIONAL : Filters responses based on whether a specific property exists, or whose value passes a conditional expression 
                Example: prop="name==C1".
                Only the “name” property is supported for core resources.
            limit : OPTIONAL : number of results to be returned. Default 100
        """
        params = {"limit":limit}
        if prop is not None:
            params['property'] = prop
        path = "/labels/core"
        res = self.connector.getData(self.endpoint+path,params=params, headers=self.header)
        data = res['children']
        nextPage=res['_links']['page'].get('href','')
        while nextPage != "":
            params['start'] = nextPage
            res = self.connector.getData(self.endpoint+path,params=params, headers=self.header)
            data += res['children']
            nextPage=res['_links']['page'].get('href','')
        return data
    
    def getCoreLabel(self,labelName:str=None)->dict:
        """
        Returns a specific Label by its name.
        Argument:
            labelName : REQUIRED : The name of the core label.
        """
        if labelName is None:
            raise ValueError("Require a label name")
        path = f"/labels/core/{labelName}"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def getCustomLabels(self,prop:str=None,limit:int=100)->list:
        """
        Retrieve a list of custom labels.
        Arguments:
            prop : OPTIONAL : Filters responses based on whether a specific property exists, or whose value passes a conditional expression 
                Example: prop="name==C1".
                Property values include "status", "created", "createdClient", "createdUser", "updated", "updatedClient", and "updatedUser".
            limit : OPTIONAL : number of results to be returned. Default 100
        """
        params = {"limit":limit}
        if prop is not None:
            params['property'] = prop
        path = "/labels/custom"
        res = self.connector.getData(self.endpoint+path,params=params, headers=self.header)
        data = res['children']
        nextPage=res['_links']['page'].get('href','')
        while nextPage != "":
            params['start'] = nextPage
            res = self.connector.getData(self.endpoint+path,params=params, headers=self.header)
            data += res['children']
            nextPage=res['_links']['page'].get('href','')
        return data
    def getCustomLabel(self,labelName:str=None)->dict:
        """
        Returns a specific Label by its name.
        Argument:
            labelName : REQUIRED : The name of the custom label.
        """
        if labelName is None:
            raise ValueError("Require a label name")
        path = f"/labels/custom/{labelName}"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def updateCustomLabel(self,labelName:str=None,data:dict=None)->dict:
        """
        Update a specific Label by its name. (PUT method)
        Argument:
            labelName : REQUIRED : The name of the custom label.
            data : REQUIRED : Data to replace the old definition
                Example:
                {
                    "name": "L2",
                    "category": "Custom",
                    "friendlyName": "Purchase History Data",
                    "description": "Data containing information on past transactions"
                }
        """
        if labelName is None:
            raise ValueError("Require a label name")
        if data is None or type(data)!= dict:
            raise ValueError("Require a dictionary data to be passed")
        path = f"/labels/custom/{labelName}"
        res = self.connector.putData(self.endpoint+path,data=data)
        return res
    
    def getMarketingActionsCore(self,prop:str=None,limit:int=10,**kwargs)->list:
        """
        Retrieve a list of core marketing actions.
        Arguments:
            prop : OPTIONAL : Filters responses based on whether a specific property exists, or whose value passes a conditional expression (e.g. "prop=name==C1"). 
            Only the “name” property is supported for core resources. 
            limit : OPTIONAL : number of results to be returned.
        """
        path = "/marketingActions/core"
        params = {"limit":limit}
        if prop is not None:
            params['property'] = prop
        res = self.connector.getData(self.endpoint+path,params=params)
        data = res['children']
        nextPage = res['_links']['page'].get('href','')
        while nextPage != "":
            params['start'] = nextPage
            res = self.connector.getData(self.endpoint+path,params=params)
            data += res['children']
            nextPage = res['_links']['page'].get('href','')
        return data

