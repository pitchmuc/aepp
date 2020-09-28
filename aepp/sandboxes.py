import aepp

"""
This module doesn't contain a class.
Every method can be used directly from 
"""


def getSandboxes()->list:
    """
    Return the list of all the sandboxes
    """
    path = aepp.config._endpoint + aepp.config._endpoint_sandboxes + "/sandboxes"
    res = aepp._getData(path)
    data = res['sandboxes']
    return data


def createSandbox(name: str = None, title: str = None, type_sandbox: str = "development")->dict:
    """
    Create a new sandbox in your AEP instance.
    Arguments:
        name : REQUIRED : name of your sandbox
        title : REQUIRED : display name of your sandbox
        type_sandbox : OPTIONAL : type of your sandbox. default : development.
    """
    if name is None or title is None:
        raise Exception('name and title cannot be empty')
    path = aepp.config._endpoint + aepp.config._endpoint_sandboxes + "/sandboxes"
    data = {
        "name": name,
        "title": title,
        "type": type_sandbox
    }
    res = aepp._postData(path, data=data)
    return res


def getSandbox(name: str)->dict:
    """
    retrieve a Sandbox information by name
    Argument:
        name : REQUIRED : name of Sandbox
    """
    if name is None:
        raise Exception('Expected a name as parameter')
    path = aepp.config._endpoint + \
        aepp.config._endpoint_sandboxes + f"/sandboxes/{name}"
    res = aepp._getData(path)
    return res


def deleteSandbox(name: str)->dict:
    """
    Delete a sandbox by its name.
    Arguments: 
        name : REQUIRED : sandbox to be deleted.
    """
    if name is None:
        raise Exception('Expected a name as parameter')
    path = aepp.config._endpoint + \
        aepp.config._endpoint_sandboxes + f"/sandboxes/{name}"
    res = aepp._deleteData(path)
    return res


def resetSandbox(name: str)->dict:
    """
    Reset a sandbox by its name. Sandbox will be empty.
    Arguments: 
        name : REQUIRED : sandbox to be deleted.
    """
    if name is None:
        raise Exception('Expected a name as parameter')
    path = aepp.config._endpoint + \
        aepp.config._endpoint_sandboxes + f"/sandboxes/{name}"
    res = aepp._putData(path)
    return res
