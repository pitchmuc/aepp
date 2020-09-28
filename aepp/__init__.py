
# Internal Library
from aepp import modules
from aepp import config
from aepp import adobeio_auth

__version__ = "0.0.6"


def createConfigFile(sandbox: bool = False, verbose: object = False, **kwargs)->None:
    """
    This function will create a 'config_admin.json' file where you can store your access data.
    Arguments:
        sandbox : OPTIONAL : consider to add a parameter for sandboxes
        verbose : OPTIONAL : set to true, gives you a print stateent where is the location.
    """
    json_data = {
        'org_id': '<orgID>',
        'client_id': "<client_id>",
        'tech_id': "<something>@techacct.adobe.com",
        'secret': "<YourSecret>",
        'pathToKey': '<path/to/your/privatekey.key>',
    }
    if sandbox:
        json_data['sandbox-name'] = "<your_sandbox_name>"
    filename = f"{kwargs.get('filename', 'config_aep')}.json"
    with open(filename, 'w') as cf:
        cf.write(modules.json.dumps(json_data, indent=4))
    if verbose:
        print(f'File created at this location :{config._cwd}/{filename}')


def importConfigFile(file: str)-> None:
    """
    This function will read the 'config_admin.json' to retrieve the information to be used by this module.
    """
    with open(modules.Path(file), 'r') as file:
        f = modules.json.load(file)
        config.org_id = f['org_id']
        config.header["x-gw-ims-org-id"] = config.org_id
        if 'api_key' in f.keys():
            config.client_id = f['api_key']
        elif 'client_id' in f.keys():
            config.client_id = f['client_id']
        config.header["X-Api-Key"] = config.client_id
        config.header['Authorization'] = ''
        config.tech_id = f['tech_id']
        config._secret = f['secret']
        config._pathToKey = f['pathToKey']
        config.date_limit = 0
        if 'sandbox-name' in f.keys():
            config.header["x-sandbox-name"] = f['sandbox-name']
            config.sandbox = f['sandbox-name']
        else:
            config.header["x-sandbox-name"] = "prod"
            config.sandbox = "prod"


@adobeio_auth._checkToken
def _getData(endpoint: str, params: dict = None, data: dict = None, headers: dict = None, *args, **kwargs):
    """
    Abstraction for getting data
    """
    if headers is None:
        headers = config.header
    if params == None and data == None:
        res = modules.requests.get(endpoint, headers=headers)
    elif params != None and data == None:
        res = modules.requests.get(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = modules.requests.get(endpoint, headers=headers, data=data)
    elif params != None and data != None:
        res = modules.requests.get(endpoint, headers=headers,
                                   params=params, data=data)
    try:
        res_json = res.json()
    except:
        res_json = {'error': 'Request Error'}
    return res_json


@adobeio_auth._checkToken
def _postData(endpoint: str, params: dict = None, data: dict = None, headers: dict = None, * args, **kwargs):
    """
    Abstraction for posting data
    """
    if headers is None:
        headers = config.header
    if params == None and data == None:
        res = modules.requests.post(endpoint, headers=headers)
    elif params != None and data == None:
        res = modules.requests.post(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = modules.requests.post(endpoint, headers=headers,
                                    data=modules.json.dumps(data))
    elif params != None and data != None:
        res = modules.requests.post(endpoint, headers=headers,
                                    params=params, data=modules.json.dumps(data))
    try:
        res_json = res.json()
    except:
        res_json = {'error': 'Request Error'}
    return res_json


@adobeio_auth._checkToken
def _patchData(endpoint: str, params: dict = None, data: dict = None, headers: dict = None, *args, **kwargs):
    """
    Abstraction for patching data
    """
    if headers is None:
        headers = config.header
    if params == None and data == None:
        res = modules.requests.patch(endpoint, headers=headers)
    elif params != None and data == None:
        res = modules.requests.patch(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = modules.requests.patch(endpoint, headers=headers,
                                     data=modules.json.dumps(data))
    elif params != None and data != None:
        res = modules.requests.patch(endpoint, headers=headers,
                                     params=params, data=modules.json.dumps(data))
    try:
        res_json = res.json()
    except:
        res_json = {'error': 'Request Error'}
    return res_json


@adobeio_auth._checkToken
def _deleteData(endpoint: str, params: dict = None, data=None, headers: dict = None, *args, **kwargs):
    """
    Abstraction for deleting data
    """
    if headers is None:
        headers = config.header
    if params == None and data == None:
        res = modules.requests.delete(endpoint, headers=headers)
    elif params != None and data == None:
        res = modules.requests.delete(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = modules.requests.delete(endpoint, headers=headers,
                                      data=modules.json.dumps(data))
    elif params != None and data != None:
        res = modules.requests.delete(endpoint, headers=headers,
                                      params=params, data=modules.json.dumps(data=data))
    try:
        status_code = res.status_code
    except:
        status_code = {'error': 'Request Error'}
    return status_code


@adobeio_auth._checkToken
def _putData(endpoint: str, params: dict = None, data=None, headers: dict = None, *args, **kwargs):
    """
    Abstraction for deleting data
    """
    if headers is None:
        headers = config.header
    if params != None and data == None:
        res = modules.requests.put(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = modules.requests.put(endpoint, headers=headers,
                                   data=modules.json.dumps(data))
    elif params != None and data != None:
        res = modules.requests.put(endpoint, headers=headers,
                                   params=params, data=modules.json.dumps(data=data))
    try:
        status_code = res.json()
    except:
        status_code = {'error': 'Request Error'}
    return status_code


@adobeio_auth._checkToken
def _patchData(endpoint: str, params: dict = None, data=None, headers: dict = None, *args, **kwargs):
    """
    Abstraction for deleting data
    """
    if headers is None:
        headers = config.header
    if params != None and data == None:
        res = modules.requests.patch(endpoint, headers=headers, params=params)
    elif params == None and data != None:
        res = modules.requests.patch(endpoint, headers=headers,
                                     data=modules.json.dumps(data))
    elif params != None and data != None:
        res = modules.requests.patch(endpoint, headers=headers,
                                     params=params, data=modules.json.dumps(data=data))
    try:
        status_code = res.json()
    except:
        status_code = {'error': 'Request Error'}
    return status_code


def home(product: str = None, limit: int = 50):
    """
    Return the IMS Organization setup and the container existing for the organization
    Arguments:
        product : OPTIONAL : specify one or more product contexts for which to return containers. If absent, containers for all contexts that you have rights to will be returned. The product parameter can be repeated for multiple contexts. An example of this parameter is product=acp
        limit : OPTIONAL : Optional limit on number of results returned (default = 50).
    """
    endpoint = config._endpoint+"/data/core/xcore/"
    params = {"product": product, "limit": limit}
    myHeader = modules.deepcopy(config.header)
    myHeader["Accept"] = "application/vnd.adobe.platform.xcore.home.hal+json"
    res = _getData(endpoint, params=params, headers=myHeader)
    return res


def saveFile(module: str = None, file: object = None, filename: str = None, type_file: str = 'json'):
    """
  Save the file in the approriate folder depending on the module sending the information.
   Arguments:
        module: REQUIRED: Module requesting the save file.
        file: REQUIRED: an object containing the file to save.
        filename: REQUIRED: the filename to be used.
        type_file: REQUIRED: the type of file to be saveed(default: json)
    """
    if module is None:
        raise ValueError("Require the module to create a folder")
    if file is None or filename is None:
        raise ValueError("Require a object for file and a name for the file")
    here = modules.Path(modules.Path.cwd())
    folder = module.capitalize()
    new_location = modules.Path.joinpath(here, folder)
    if new_location.exists() == False:
        new_location.mkdir()
    if type_file == 'json':
        filename = f"{filename}.json"
        complete_path = modules.Path.joinpath(new_location, filename)
        with open(complete_path, 'w') as f:
            f.write(modules.json.dumps(file, indent=4))
    else:
        filename = f"{filename}.txt"
        complete_path = modules.Path.joinpath(new_location, filename)
        with open(complete_path, 'w') as f:
            f.write(file)
