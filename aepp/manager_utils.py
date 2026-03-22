from copy import deepcopy
import json,re

def __transformationDict__(mydict:dict=None,typed:bool=False,dictionary:dict=None)->dict:
    """
    Transform the current XDM schema to a dictionary.
    """
    if dictionary is None:
        dictionary = {}
    else:
        dictionary = dictionary
    for key in mydict:
        if type(mydict[key]) == dict:
            if mydict[key].get('type') == 'object' or 'properties' in mydict[key].keys():
                properties = mydict[key].get('properties',None)
                additionalProperties = mydict[key].get('additionalProperties',None)
                if properties is not None:
                    if key != "property" and key != "customFields":
                        if key not in dictionary.keys():
                            dictionary[key] = {}
                        __transformationDict__(mydict[key]['properties'],typed,dictionary=dictionary[key])
                    else:
                        __transformationDict__(mydict[key]['properties'],typed,dictionary=dictionary)
                elif additionalProperties is not None:
                    if additionalProperties.get('type') == 'array':
                        items = additionalProperties.get('items',{}).get('properties',None)
                        if items is not None:
                            dictionary[key] = {'key':[{}]}
                            __transformationDict__(items,typed,dictionary=dictionary[key]["key"][0])
            elif mydict[key].get('type') == 'array':
                levelProperties = mydict[key]['items'].get('properties',None)
                if levelProperties is not None:
                    dictionary[key] = [{}]
                    __transformationDict__(levelProperties,typed,dictionary=dictionary[key][0])
                else:
                    if typed:
                        type_array = mydict[key]['items'].get('type','object')
                        if mydict[key]['items'].get('type','object') == 'string':
                            if mydict[key]['items'].get('format',None) == 'date-time':
                                type_array = 'string:date-time'
                            elif mydict[key]['items'].get('format',None) == 'date':
                                type_array = 'string:date'
                            elif mydict[key]['items'].get('format',None) == 'uri-reference':
                                type_array = 'string:uri-reference'
                            elif mydict[key]['items'].get('format',None) == 'ipv4' or mydict[key]['items'].get('format',None) == 'ipv6':
                                type_array = mydict[key]['items'].get('format',None)
                        if mydict[key]['items'].get('type','object') == 'integer':
                            if mydict[key]['items'].get('minimum',None) is not None and mydict[key]['items'].get('maximum',None) is not None:
                                if mydict[key]['items'].get('minimum',None) == -9007199254740991:
                                    type_array = f"integer:long"
                                elif mydict[key]['items'].get('minimum',None) == -2147483648 and mydict[key]['items'].get('maximum',None) == 2147483647:
                                    type_array = f"integer:int"
                                elif mydict[key]['items'].get('minimum',None) == -32768 and mydict[key]['items'].get('maximum',None) == 32767:
                                    type_array = f"integer:short"
                                elif mydict[key]['items'].get('minimum',None) == -128 and mydict[key]['items'].get('maximum',None) == 128:
                                    type_array = f"integer:byte"
                        dictionary[key] = [type_array]
                    else:
                        dictionary[key] = []
            else:
                if typed:
                    dictionary[key] = mydict[key].get('type','object')
                    if mydict[key].get('enum',None) is not None:
                        dictionary[key] = f"{mydict[key].get('type')} enum: {','.join(mydict[key].get('enum',[]))}"
                    if mydict[key].get('type','object') == 'string':
                        if mydict[key].get('format',None) == 'date-time':
                            dictionary[key] = 'string:date-time'
                        elif mydict[key].get('format',None) == 'date':
                            dictionary[key] = 'string:date'
                        elif mydict[key].get('format',None) == 'uri-reference':
                            dictionary[key] = 'string:uri-reference'
                        elif mydict[key].get('format',None) == 'ipv4' or mydict[key].get('format',None) == 'ipv6':
                            dictionary[key] = mydict[key].get('format',None)
                    if mydict[key].get('type','object') == 'integer':
                        if mydict[key].get('minimum',None) is not None and mydict[key].get('maximum',None) is not None:
                            if mydict[key].get('minimum',None) == -9007199254740991:
                                dictionary[key] = f"integer:long"
                            elif mydict[key].get('minimum',None) == -2147483648 and mydict[key].get('maximum',None) == 2147483647:
                                dictionary[key] = f"integer"
                            elif mydict[key].get('minimum',None) == -32768 and mydict[key].get('maximum',None) == 32767:
                                dictionary[key] = f"integer:short"
                            elif mydict[key].get('minimum',None) == -128 and mydict[key].get('maximum',None) == 128:
                                dictionary[key] = f"integer:byte"
                else:
                    dictionary[key] = ""
    return dictionary

def __simpleDeepMerge__(base:dict,append:dict)->dict:
    """
    Loop through the keys of 2 dictionary and append the new found key of append to the base.
    Arguments:
        base : The base you want to extend
        append : the new dictionary to append
    """
    if type(append) == list:
        append = append[0]
    for key in append:
        if type(base)==dict:
            if key in base.keys():
                __simpleDeepMerge__(base[key],append[key])
            else:
                base[key] = append[key]
        elif type(base)==list:
            base = base[0]
            if type(base) == dict:
                if key in base.keys():
                    __simpleDeepMerge__(base[key],append[key])
                else:
                    base[key] = append[key]
    return base

def __cleanPath__(string:str=None)->str:
    """
    An abstraction to clean the path string and remove the following characters : [,],{,}
    Arguments:
        string : REQUIRED : a string 
    """
    return string.replace('[','').replace(']','').replace("{",'').replace('}','')

def __accessorAlgo__(mydict:dict,path:str=None,allOf:list=None)->dict:
    """
    recursive method to retrieve all the elements.
    Arguments:
        mydict : REQUIRED : The dictionary containing the elements to fetch (in "properties" key)
        path : REQUIRED : the path with dot notation.
        allOf : OPTIONAL : The list of allOf references from the field group, used to transparently traverse wrapper keys.
    """
    path = __cleanPath__(path)
    pathSplit = path.split('.')
    key = pathSplit[0]
    list_allOf_keys = [el['$ref'].split('/').pop() for el in (allOf or []) if '$ref' in el]
    if 'customFields' in mydict.keys():
        level = __accessorAlgo__(mydict.get('customFields',{}).get('properties',{}),'.'.join(pathSplit),allOf)
        if 'error' not in level.keys():
            return level
    if 'property' in mydict.keys():
        level = __accessorAlgo__(mydict.get('property',{}).get('properties',{}),'.'.join(pathSplit),allOf)
        if 'error' not in level.keys():
            return level
    level = mydict.get(key,None)
    if level is not None:
        fieldType = level.get("type") if type(level) == dict else None
        if fieldType == "object" or (type(level) == dict and 'properties' in level):
            levelProperties = mydict[key].get('properties',None)
            if levelProperties is not None and len(pathSplit) > 1:
                level = __accessorAlgo__(levelProperties,'.'.join(pathSplit[1:]),allOf)
            return level
        elif fieldType == "array":
            levelProperties = mydict[key]['items'].get('properties',None)
            if levelProperties is not None and len(pathSplit) > 1:
                level = __accessorAlgo__(levelProperties,'.'.join(pathSplit[1:]),allOf)
            return level
        else:
            if len(pathSplit) > 1: 
                return {'error':f'cannot find the key "{pathSplit[1]}"'}
            return level
    else:
        if key == "":
            return mydict
        ## Key not found — transparently traverse allOf wrapper dicts (e.g. 'experienceevent')
        for wrapperKey in list_allOf_keys:
            wrapper = mydict.get(wrapperKey)
            if wrapper is not None and type(wrapper) == dict and 'properties' in wrapper:
                level = __accessorAlgo__(wrapper['properties'],'.'.join(pathSplit),allOf)
                if 'error' not in level:
                    return level
        return {'error':f'cannot find the key "{key}"'}

def __searchAlgo__(allOf:list,mydict:dict,string:str=None,partialMatch:bool=False,caseSensitive:bool=False,results:list=None,path:str=None,completePath:str=None)->list:
    """
    recursive method to retrieve all the elements.
    Arguments:
        allOf : REQUIRED : The list of allOf references.
        mydict : REQUIRED : The dictionary containing the elements to fetch (start with fieldGroup definition)
        string : the string to look for with dot notation.
        partialMatch : if you want to use partial match
        caseSensitive : to see if we should lower case everything
        results : the list of results to return
        path : the path currently set
        completePath : the complete path from the start.
    """
    list_allOf_keys = [el['$ref'].split('/').pop() for el in allOf if '$ref' in el.keys()]
    finalPath = None
    if results is None:
        results=[]
    for key in mydict:
        if path is not None:
            finalPath = f"{path}.{key}"
        else:
            finalPath = f"{key}"
            
        title = mydict[key].get('title', '') if type(mydict[key]) == dict else ''
        
        if caseSensitive == False:
            keyComp = key.lower()
            string = string.lower()
            pathComp = finalPath.lower()
            titleComp = title.lower()
        else:
            keyComp = key
            string = string
            pathComp = finalPath
            titleComp = title
            
        if partialMatch:
            if string in keyComp or string in pathComp or string in titleComp:
                ### checking if element is an array without deeper object level
                if type(mydict[key]) == dict and mydict[key].get('type') == 'array' and mydict[key].get('items', {}).get('properties',None) is None:
                    finalPathArr = finalPath + "[]"
                else:
                    finalPathArr = finalPath
                value = deepcopy(mydict[key]) if type(mydict[key]) == dict else {}
                value['path'] = finalPathArr
                value['queryPath'] = __cleanPath__(finalPathArr)
                if completePath is None:
                    value['completePath'] = f"/definitions/{key}"
                else:
                    value['completePath'] = completePath + "/" + key
                results.append({key:value})
        else:
            if keyComp == string or pathComp == string or titleComp == string:
                value = deepcopy(mydict[key]) if type(mydict[key]) == dict else {}
                value['path'] = finalPath
                value['queryPath'] = __cleanPath__(finalPath)
                if completePath is None:
                    value['completePath'] = f"/definitions/{key}"
                else:
                    value['completePath'] = completePath + "/" + key
                results.append({key:value})
        ## loop through keys
        if type(mydict[key]) == dict and ('properties' in mydict[key] or (mydict[key].get("type") == "object" and 'additionalProperties' in mydict[key])):
            levelProperties = mydict[key].get('properties',{})
            if levelProperties != dict():
                if completePath is None:
                    tmp_completePath = f"/definitions/{key}"
                else:
                    tmp_completePath = f"{completePath}/{key}"
                tmp_completePath += f"/properties"
                if path is None:
                    if len(list_allOf_keys)>0:
                        if key not in list_allOf_keys:
                            tmp_path = key
                        else:
                            tmp_path = None
                    else:
                        tmp_path = key
                else:
                    tmp_path = f"{path}.{key}"
                results = __searchAlgo__(allOf,levelProperties,string,partialMatch,caseSensitive,results,tmp_path,tmp_completePath)
            additionalProperties = mydict[key].get('additionalProperties',None)
            if additionalProperties is not None:
                if additionalProperties.get('type') == 'array':
                    levelProperties = additionalProperties.get('items',{}).get('properties',{})
                    if levelProperties != dict():
                        if completePath is None:
                            tmp_completePath = f"/definitions/{key}"
                        else:
                            tmp_completePath = f"{completePath}/{key}"
                        tmp_completePath += f"/additionalProperties/items/properties"
                        if path is None:
                            if len(list_allOf_keys)>0:
                                if key not in list_allOf_keys:
                                    tmp_path = f"{key}.key[]{{}}"
                                else:
                                    tmp_path = None
                            else:
                                tmp_path = f"{key}.key[]{{}}"
                        else:
                            tmp_path = f"{path}.{key}.key[]{{}}"
                        results = __searchAlgo__(allOf,levelProperties,string,partialMatch,caseSensitive,results,tmp_path,tmp_completePath)
        elif mydict[key].get("type") == "array":
            levelProperties = mydict[key]['items'].get('properties',{})
            if levelProperties != dict():
                if completePath is None:
                    tmp_completePath = f"/definitions/{key}"
                else:
                    tmp_completePath = f"{completePath}/{key}"
                tmp_completePath += f"/items/properties"
                if levelProperties is not None:
                    if path is None:
                        if len(list_allOf_keys)>0:
                            if key not in list_allOf_keys:
                                tmp_path = key
                            else:
                                tmp_path = None
                        else:
                            tmp_path = key
                    else:
                        tmp_path = f"{path}.{key}[]{{}}"
                    results = __searchAlgo__(allOf,levelProperties,string,partialMatch,caseSensitive,results,tmp_path,tmp_completePath)
    return results

def __searchAttrAlgo__(mydict:dict,key:str=None,value:str=None,regex:bool=False, originalField:str=None, results:list=None)->list:
    """
    recursive method to retrieve all the elements.
    Arguments:
        mydict : REQUIRED : The dictionary containing the elements to fetch (start with fieldGroup definition)
        key : key of the attribute
        value : the value of that key to look for.
        regex : if the regex match should be used.
        originalField : the key used to dig deeper.
        results : the list of results to return
    """
    if results is None:
        results=[]
    for k in mydict:
        if key == k:
            if regex:
                checkValue = deepcopy(mydict[k])
                if type(checkValue) == list or type(checkValue) == dict:
                    checkValue = json.dumps(checkValue)
                if re.match(value,checkValue):
                    if originalField is not None and originalField != 'property' and originalField != 'properties' and originalField != 'items':
                        results.append(originalField)
            else:
                if mydict[k] == value:
                    if originalField is not None and originalField != 'property' and originalField != 'properties' and originalField != 'items':
                        results.append(originalField)
        ## recursive action for objects and array
        if type(mydict[k]) == dict:
            if k == "properties" or k == 'items':
                __searchAttrAlgo__(mydict[k],key,value,regex,originalField,results)
            else:
                __searchAttrAlgo__(mydict[k],key,value,regex,k,results)
    return results