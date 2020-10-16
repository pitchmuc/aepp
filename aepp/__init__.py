
# Internal Library
from aepp import modules
from aepp import config
from aepp import connector

__version__ = "0.0.7"
connection = None

def createConfigFile(sandbox: bool = False, verbose: object = False, **kwargs)->None:
    """
    This function will create a 'config_admin.json' file where you can store your access data.
    Arguments:
        sandbox : OPTIONAL : consider to add a parameter for sandboxes
        verbose : OPTIONAL : set to true, gives you a print stateent where is the location.
    Possible kwargs:
        filename : name of the config file.
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
        config.config_object["org_id"] = f['org_id']
        config.header["x-gw-ims-org-id"] = config.config_object["org_id"]
        if 'api_key' in f.keys():
            config.config_object["client_id"] = f['api_key']
        elif 'client_id' in f.keys():
            config.config_object["client_id"] = f['client_id']
        config.header["x-api-key"] = config.config_object["client_id"] 
        config.header['Authorization'] = ''
        config.config_object["tech_id"] = f['tech_id']
        config.config_object["secret"] = f['secret']
        config.config_object["pathToKey"] = f['pathToKey']
        config.config_object["token"] = ""
        config.date_limit = 0
        if 'sandbox-name' in f.keys():
            config.header["x-sandbox-name"] = f['sandbox-name']
            config.config_object["sandbox"] = f['sandbox-name']
        else:
            config.header["x-sandbox-name"] = "prod"
            config.config_object["sandbox"] = "prod"


def home(product: str = None, limit: int = 50):
    """
    Return the IMS Organization setup and the container existing for the organization
    Arguments:
        product : OPTIONAL : specify one or more product contexts for which to return containers. If absent, containers for all contexts that you have rights to will be returned. The product parameter can be repeated for multiple contexts. An example of this parameter is product=acp
        limit : OPTIONAL : Optional limit on number of results returned (default = 50).
    """
    global connection
    connection = connector.AdobeRequest(config_object=config.config_object,header=config.header)
    endpoint = config.endpoints['global']+"/data/core/xcore/"
    params = {"product": product, "limit": limit}
    myHeader = modules.deepcopy(connection.header)
    myHeader["Accept"] = "application/vnd.adobe.platform.xcore.home.hal+json"
    res = connection.getData(endpoint, params=params, headers=myHeader)
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
