import json
from typing import Union, Any
from copy import deepcopy
import pandas as pd
from collections.abc import Iterable


class Som:
    """
    The Som is a class that will help you to handle to create data in a dictionary format, or JSON.\
    Creating the capability to build XDM payload directly via a simple dot notation path.
    This class is inspired by the SOM project from the JS framework built.
    """

    def __init__(self,data:Union[dict,str]=None,options:dict=None)->None:
        """
        Instantiate the Som Object.
        Arguments:
        data : OPTIONAL : An existing dictionary representation (dict or stringify, or a JSON file) that you want to use as template.
        options : OPTIONAL : A dictionary that contains some keys for additional settings:
            defaultValue : OPTIONAL : The default value to be returned when using the get method and no match is found. Default is None.
            deepcopy : OPTIONAL : Boolean to define if you want to deepcopy the data passed (default True).
            stack : OPTIONAL : If you want to create a stack to track your call.

        Example of options value: 
            {
            "defaultValue" : "my value fallback",
            "deepcopy" : True,
            "stack" : False
            }
        """
        if options is None:
            options = {}
        self.__data__:dict = {}
        if data is not None:
            if type(data) == str:
                if '.json' in data:
                    with open(data,'r') as f:
                        json_data = json.load(f)
                        self.__data__ = self.___build_data__(json_data)
                else:
                    try:
                        json_data = json.loads(f)
                        self.__data__ = self.___build_data__(json_data)
                    except:
                        raise Exception('Cannot read the JSON')
            elif type(data) == dict:
                if options.get("deepcopy",True):
                    self.__data__ = self.___build_data__(deepcopy(data))
                else:
                    self.__data__ = self.___build_data__(data)
        self.__defaultValue__ = options.get('defaultValue',None)
        if options.get('stack',False):
            self.stack = []
        else:
            self.stack = None
    
    def ___build_data__(self,json:dict)->dict:
        """
        Build the data model based on the JSON pass
        """
        subSom = Som()
        for key,value in json.items():
            subSom.assign(key,value)
        return subSom.get()


    def __str__(self)->str:
        return json.dumps(self.to_dict(),indent=2)
    
    def __repr__(self)->str:
        return json.dumps(self.to_dict(),indent=2)

    def setDefaultValue(self,value:Union[str,int,float,bool])->None:
        """
        Set the default value returned as fallback from the get method.
        """
        self.__defaultValue__ = deepcopy(value)

    def __recurseSearch__(self,keys:list,data:dict)->Union[str,int,bool,float,dict]:
        """
        recursive search for the path
        Arguments:
            key : list of keys to search
            data : the dictionary traverse 
        """
        if len(keys) == 1:
            if type(data) == dict:
                if keys[0] in data.keys():
                    return data[keys[0]]
            elif type(data) == set:
                if keys[0] in data:
                    return True
                else:
                    if keys[0].isnumeric():
                        if int(keys[0]) in data:
                            return True
                    else:
                        return False
            elif type(data) == list:
                if keys[0].isnumeric():
                    if abs(int(keys[0])) < len(data):
                        return data[int(keys[0])]
                    elif abs(int(keys[0])) in data:
                        return True
                    else:
                        return None
                elif keys[0] in data:
                    return True
                else:
                    return False
            elif type(data) == tuple:
                if keys[0].isnumeric():
                    if abs(int(keys[0])) < len(data):
                        return data[int(keys[0])]
                    elif abs(int(keys[0])) in data:
                        return True
                    else:
                        return None
                elif keys[0] in data:
                    return True
                else:
                    return False
        else:
            if type(data) == dict:
                if keys[0] in data.keys():
                    return self.__recurseSearch__(keys[1:],data[keys[0]])
            elif type(data) == set:
                if keys[0] in data:
                    return self.__recurseSearch__(keys[1:],data[keys[0]])
            elif type(data) == list:
                if keys[0].isnumeric():
                    if abs(int(keys[0])) < len(data):
                        return self.__recurseSearch__(keys[1:],data[int(keys[0])])
            else:
                return None

    def get(self,path:Union[str,list,set]=None,fallback:Union[str,int,float,bool]=None,params:dict=None,**kwargs)->Union[str,list,set,bool,dict]:
        """
        Retrieve the data based on the dot notation passed. 
        If you want to return everything, use it without any parameter.
        Arguments:
            path : OPTIONAL : The dot notation path that you want to return. You can pass a list of path and the first match is returned.
            fallback : OPTIONAL : Temporary fallback if the dot notation path is not matched and you do not want to get the defaultValue
        """
        if type(self.stack) == list and not kwargs.get('merge',False):
            self.stack.append({'method' : 'get', 'path':path})
        if path is None or path == "":
            if kwargs.get('merge',False):
                return self.__data__
            else:
                return deepcopy(self.__data__)
        if type(path) == str:
            paths = [path]
        elif type(path) == set:
            paths = list(path)
        elif type(path) == list:
            paths = list(set(path))
        results = {}
        if kwargs.get('merge',False):
            data = self.__data__
        else:
            data = deepcopy(self.__data__)
        for p in paths:
            l_path:list = p.split('.')
            results[p] = self.__recurseSearch__(l_path,data)
            if results[p] is not None:
                return results[p]
        if fallback is not None:
            return fallback
        else:
            return self.__defaultValue__
        
    
    def __recursive_assignment__(self,list_paths:list,data:Union[dict,list,set]=None,value:Any=None,override:bool=False,datatype:Union[set,list,tuple]=None)->dict:
        """
        Recursive function to create nested objects.
        """
        node = list_paths[0]
        if len(list_paths)>1:
            next_node = list_paths[1]
        else:
            next_node = None
        if node.startswith('[') and node.endswith(']'):
            node = node[1:-1]
            if node.isnumeric():
                node = int(node)
        if len(list_paths) == 1: ## end of the path
            if type(data) == dict: ## handling assignment to dict
                if datatype is not None and datatype != type(value): ## datatype is specified
                    if node in data.keys():
                        if type(data[node]) == list:
                            if override:
                                if type(value) == datatype:
                                    data[node] = value
                                else:
                                    if type(value) != list and type(value) != set and type(value) != tuple:
                                        data[node] = datatype([value])
                                    else:
                                        data[node] = datatype(value)
                            else:
                                if datatype != list and datatype is not None:
                                    data[node].append(value)
                                    old_value = deepcopy(data[node])
                                    data[node] = datatype(old_value)
                                else:
                                    data[node].append(value)
                        elif type(data[node]) == set:
                            if override:
                                if type(value) == datatype:
                                    data[node] = value
                                else:
                                    if isinstance(value, Iterable) == False or type(value)==str:
                                        data[node] = datatype([value])
                                    else:
                                        data[node] = datatype(value)
                            else:
                                if datatype != set and datatype is not None:
                                    data[node].add(value)
                                    data[node] = datatype(data[node])
                                else:
                                    if isinstance(value, Iterable) and type(value)!=str:
                                        data[node].union(value)
                                    else:
                                        data[node].add(value)
                        elif type(data[node]) == tuple:
                            if isinstance(value, Iterable) == False or type(value)==str:
                                data[node] = datatype([value])
                            else:
                                data[node] = datatype(value)
                        else:
                            if isinstance(value, Iterable) == False or type(value)==str:
                                data[node] = datatype([value])
                            else:
                                data[node] = datatype(value)
                    else:
                        if type(value) != list:
                            data[node] = datatype([value])
                        else:
                            data[node] = datatype(value)
                else:
                    if node not in data.keys():
                        data[node] = value
                    else:
                        if type(data[node]) == list:
                            if override:
                                data[node] = value
                            else:
                                data[node].append(value)
                        elif type(data[node]) == set:
                            if override:
                                data[node] = value
                            else:
                                if isinstance(value,Iterable) and type(value) != str:
                                    for val in value:
                                        data[node].add(val)
                                else:
                                    data[node].add(value)
                        elif type(data[node]) == tuple:
                            if override:
                                data[node] = value
                            elif isinstance(value,Iterable) and type(value)!=str:
                                data[node] = tuple(value)
                            else:
                                data[node] = tuple([value])
                        else:
                            data[node] = value
            elif type(data) == list: ## handling assignment to list
                if datatype is not None and datatype != type(value): ## datatype is specified  
                    if type(node) == int: ## if node is numeric and get to list
                        if node < len(data):
                            if override:
                                if datatype is not None and type(value) != datatype:
                                    data[node] = datatype(value)
                                else:
                                    data[node] = value
                            else:
                                if datatype is not None and type(value) != datatype:
                                    data[node] = datatype(value)
                                else:
                                    data[node].append(value)
                        else:
                            data.append(value)
                    else:## node is not numeric
                        data = {}
                        if datatype is not None and type(value) != datatype:
                            if isinstance(value, Iterable) == False or type(value)==str:
                                data[node] = datatype([value])
                            else:
                                data[node] = datatype(value)
                        else:
                            data[node] = value
                else: ### no datatype assigned
                    if type(node) == int: ## if node is numeric and get to list
                        if node < len(data): ## replacing the value
                            data[node] = value
                        else: ## appending
                            if override:
                                if type(value) == list:
                                    data = value
                                else:
                                    data = [value] 
                            else:
                                data.append(value)
                    else:## node is not numeric
                        data = {}
                        if datatype is not None and type(value) != datatype:
                            if isinstance(value, Iterable) == False or type(value)==str:
                                data[node] = [value]
                            else:
                                data[node] = value
                        else:
                            data[node] = value        
            elif type(data) == set:
                raise Exception(f"Cannot access a specific item of a set: {data}")
            else:
                if datatype is not None and type(value) != list:
                    if isinstance(value, Iterable) == False or type(value)==str:
                        data[node] = datatype([value])
                    else:
                        data[node] = datatype(value)
                else:
                    if type(data[node]) == tuple:
                        if override:
                            data[node] = True
                        elif isinstance(value, Iterable) == False or type(value)==str:
                            data[node] = tuple([value])
                        else:
                            data[node] = tuple(value)
                    elif type(data[node]) == set:
                        if override:
                            data[node] = value
                        elif isinstance(value, Iterable) == False or type(value)==str:
                            data[node] = set([value])
                        else:
                            data[node] = set(value)
                    else:
                        data[node] = value
            return data
        else:
            if type(data) == dict:
                if node not in data.keys():
                    if next_node is not None:
                        if next_node.startswith('[') and next_node.endswith(']'):
                            data[node] = []
                        else:
                            data[node] = {}
                    res = self.__recursive_assignment__(list_paths[1:],data[node],value,override,datatype)
                else:
                    res = self.__recursive_assignment__(list_paths[1:],data[node],value,override,datatype)
            elif type(data) == list:
                if type(node) == int:
                    if node < len(data):
                        res = self.__recursive_assignment__(list_paths[1:],data[node],value,override,datatype)
                    else:
                        data.append({})
                        res = self.__recursive_assignment__(list_paths[1:],data[-1],value,override,datatype)
                else:
                    data = {node:{}}
                    res = self.__recursive_assignment__(list_paths[1:],data[-1],value,override,datatype)
            elif type(data) == tuple:
                if type(node) == int:
                    if node < len(data)-1:
                        res = self.__recursive_assignment__(list_paths[1:],data[node],value,override,datatype)
                    else:
                        data = {node:{}}
                        res = self.__recursive_assignment__(list_paths[1:],data[node],value,override,datatype)
                else:
                    data = {node:{}}
                    res = self.__recursive_assignment__(list_paths[1:],data[node],value,override,datatype)

    def assign(self,path:str=None,value:Any=None,fallback:Any=None,params:dict=None)->None:
        """
        Assign a value to a path via dot notation, creating the path if the path does not already exist.
        Arguments:
            path : REQUIRED : The path where to place the value. In case you want to set at a specific array index of a list, use the "[]" notation, such as "my.path.[1].foo"
            value : REQUIRED : The value to assign, if value is dynamic and return None, you can decide to override it with the fallback value
            fallback : OPTIONAL : Value to be assigned. It would replace the value passed if this one is None (and fallback is not None) if your assignement is dynamic and you want to avoid None.
            params : OPTIONAL : dictionary that can cast the change of an object type or override existing value.
                Example of keys in params:
                type : the type you want to cast your assignement to. Default None.Possible value list, set, tuple
                override : if you want to override the existing value. By default primitive will be overriden, but not list. Default False.
                    An assignement of a value to a list will append that value, the same for Set.
                    An assignment of an dictionary to a list or a Set or a primitive will override that value.
                    By overriding, the value assign to a set or a list will take the place as the unique value of that elements.
        """
        if params is None:
            params = {}
        override = params.get('override',False)
        datatype = params.get('type',None)
        data = self.__data__
        fallback = fallback
        if type(self.stack) == list:
            self.stack.append({'method':'assign','path':path,"value":value})
        list_nodes = path.split('.')
        if value is None and fallback is not None:
            value = fallback
        value = deepcopy(value)
        res = self.__recursive_assignment__(list_nodes,data,value,override,datatype)
        return None
    
    def __mergedata__(self,o_data:dict,data:dict)->dict:
        """
        merge the data provided to the existing data object
        o_data : origin_data
        data : data to be merged
        """
        if type(data) == dict:
            for key,item in data.items():
                if key in o_data.keys():
                    if type(data[key]) == dict:
                        if type(o_data[key]) == dict:
                            self.__mergedata__(o_data[key],data[key])
                        else:
                            o_data[key] = item
                    elif type(data[key]) == list:
                        if isinstance(o_data[key],Iterable) and type(o_data[key])!=str:
                            o_data[key] = list(o_data[key])
                            o_data[key] += data[key]
                        elif type(o_data[key]) == dict:
                            o_data[key] = data[key]
                        else:
                            o_data[key] = [o_data[key]]
                            o_data[key] += data[key]
                    elif type(data[key]) == set:
                        if type(o_data[key]) == set:
                            o_data[key] = o_data[key].union(data[key])
                        elif isinstance(o_data[key],Iterable) and type(o_data[key])!=str:
                            o_data[key] = data[key].union(set(o_data[key]))
                        elif type(o_data[key]) == dict:
                            o_data[key] = data[key]
                        else:
                            o_data[key] = set([o_data[key]])
                            o_data[key] = o_data[key].union(data[key])
                    elif type(data[key]) == tuple:
                        if isinstance(o_data[key],Iterable) and type(o_data[key])!=str:
                            tmp_list = list(deepcopy(o_data[key]))
                            tmp_list += list(data[key])
                            o_data[key] = tuple(tmp_list)
                        elif type(o_data[key])==str:
                            tmp_list = list([o_data[key]])
                            tmp_list += data[key]
                            o_data[key] = tuple(tmp_list)
                        else:
                            tmp_list = list(o_data[key])
                            tmp_list += data[key]
                            o_data[key] = tuple(tmp_list)
                    else:
                        o_data[key] = data[key]
                else:
                    o_data[key] = item
        elif type(data) == list:
            if type(o_data) == list:
                o_data += data
            elif isinstance(o_data,Iterable) and type(o_data) != str:
                o_data = [d for d in o_data]
                o_data += data
            else:
                o_data = data
        elif type(data) == tuple:
            if isinstance(o_data,Iterable) and type(o_data) != str:
                tmp_list = list(deepcopy(o_data))
                tmp_list += list(data)
                o_data = tuple(tmp_list)
            else:
                o_data = data
        elif type(data) == set:
            if isinstance(o_data,Iterable) and type(o_data) != str:
                tmp_list = list(deepcopy(o_data))
                tmp_list += list(data)
                o_data = set(tmp_list)
            else:
                o_data = data

      
    def merge(self,path:str=None,data:Union[dict,list]=None)->None:
        """
        Merge a dictionary object with the existing Som data.
        Arguments:
            path : OPTIONAL : The path as dot notation where the merge should happen
            data : REQUIRED : The data to be merged with the existing Som data
        """
        if data is None:
            raise Exception("Require data to be merged")
        if path is None:
            o_data = self.get(merge=True)
        else:
            o_data = self.get(path,merge=True)
            if type(o_data) == set or type(o_data) == tuple or type(o_data) == list:
                key = path.split('.').pop()
                data = {key : data}
                list_path = list(reversed(path.split('.')))## ensuring the first occurence removed is the last one and reverting
                list_path.remove(key)
                list_path = list(reversed(list_path))
                path = '.'.join(list_path)
                o_data = self.get(path,merge=True)
                print(o_data)
        self.__mergedata__(o_data,deepcopy(data))
        return None
        

    def to_dict(self,jsonCompatible:bool=False,**kwargs)->dict:
        """
        Return the data hosted in the Som instance as a deep copy dictionary
        """
        if type(self.stack) == list:
            self.stack.append({'method' : 'to_dict', 'path':None})
        if kwargs.get('origin',None) == "internal":
            return self.__data__
        if jsonCompatible:
            def serialize_sets(obj):
                if isinstance(obj, set):
                    return list(obj)
                return obj
            json_str = json.dumps(self.__data__, default=serialize_sets)
            data = json.loads(json_str)
        else:
            data = deepcopy(self.__data__)
        return data
    
    def __building_dataframe_flatten__(self,key:str=None,data:dict=None,path:str=None,result_data:dict=None)->dict:
        """
        Build the dataframe columns and value
        data : the data to traverse
        path : the path being built
        result_data : the data to store the result once end of traverse is done
        """
        if result_data is None:
            result_data = {}
        if path is None and key is not None:
            if type(key) == int:
                path = f".[{str(key)}]"
            else:
                path = f"{key}"
        elif path is not None and key is not None:
            if type(key) == int:
                path = f"{path}.[{str(key)}]"
            else:
                path = f"{path}.{key}"
        if type(data) != dict and type(data)!=list and type(data) != tuple:
            if pd.notnull(data):
                result_data[path] = data
        if type(data) == list or type(data) == tuple: ## list or tuple handling
            if len(data)>0: ## only considering not empty list
                if type(data[0]) == dict:
                    for index, el in enumerate(data):
                        self.__building_dataframe_flatten__(index,el,path,result_data)
                else:
                    result_data[path] = data
        else: ## dictionary
            if key == "{}":
                for key1,value1 in data.items():
                    if type(value1) == dict or type(value1) == list or type(value1) == tuple:
                        self.__building_dataframe_flatten__(key1,value1,path,result_data)
                    else:
                        if path is not None:
                            result_data[f"{path}.{key1}"] = value1
                        else:
                            result_data[f"{key1}"] = value1
            else:
                for key1,value1 in data.items():
                    if type(value1) == dict or type(value1) == list or type(value1) == tuple:
                        self.__building_dataframe_flatten__(key1,value1,path,result_data)
                    else:
                        if key is not None:
                            if pd.notnull(value1):
                                result_data[f"{path}.{key1}"] = value1
                        else:
                            if pd.notnull(value1):
                                result_data[f"{key1}"] = value1
        return result_data
    
    def __building_dataframe_explode__(self,key:str=None,data:dict=None,path:str=None,result_data:list=None)->dict:
        """
        build data to be loaded as dataframe
        """
        """
        Build the dataframe columns and value
        data : the data to traverse
        path : the path being built
        result_data : the data to store the result once end of traverse is done
        """
        if result_data is None:
            result_data = [{}]
        if path is None and key is not None:
            path = f"{key}"
        elif path is not None and key is not None:
            path = f"{path}.{key}"
        if type(data) != dict and type(data)!=list and type(data) != tuple:
            for el in result_data:
                if pd.notnull(data):
                    el[path] = data
        elif type(data) == dict:
            for key,item in data.items():
                result_data = self.__building_dataframe_explode__(key,item,path,result_data)
        elif type(data) == list or type(data) == tuple:
            if len(data)>0: ## only capturing not empty list
                if type(data[0]) == dict:
                    new_result_data = []
                    for index,subdict in enumerate(data):
                        for data in result_data:
                            data[path] = index
                        deepCopyData = deepcopy(result_data)
                        new_result = self.__building_dataframe_explode__(None,subdict,path,deepCopyData)
                        new_result_data += deepcopy(new_result)
                    result_data = new_result_data
                else:
                    for result in result_data:
                        result[path] = data
        return result_data


    def to_dataframe(self,expand_arrays:bool=False)->pd.DataFrame:
        """
        Return the data as dataframe
        Arguments:
            expand_arrays : OPTIONAL : By default the data are completely flatten (a single line is returned)
                If you wish to expand arrays as multiple rows, you can set that parameter to True.
                It will create a completely exploded data frame where all list of objects are expanded.
        """
        if type(self.stack) == list:
            self.stack.append({'method' : 'to_dataframe', 'path':None})
        if expand_arrays:
            dict_data = self.__building_dataframe_explode__(None,self.__data__)
            df = pd.DataFrame(dict_data)
            return df
        else:
            dict_data = self.__building_dataframe_flatten__(None,self.__data__)
            ## ensuring the start with a simple value to avoid array decomposition
            simple_start = {'a':'value'}
            simple_start.update(dict_data)
            df = pd.DataFrame.from_dict(simple_start,orient='index').T
            df = df.drop('a',axis=1)
            return df
    
    def from_dataframe(self,dataFrame:pd.DataFrame=None,orient:int=0)->None:
        """
        Build a Som object from a dataframe row. 
        Arguments:
            dataFrame : REQUIRED : The dataframe countaining your data
            orient : OPTIONAL : The orientation of the dataframe. Default 0 by row. 1 by columns.
        """
        if type(self.stack) == list:
            self.stack.append({'method' : 'from_dataframe', 'path':None})
        if orient==0:
            for index, row in dataFrame.iterrows():
                for key,value in row:
                    self.assign(key,value)
        elif orient==1:
            for col in dataFrame:
                for key,value in col:
                    self.assign(key,value)
        return self.to_dict()