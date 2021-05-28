
# Internal Library
from aepp import config
from aepp import connector
from .configs import *
from .__version__ import __version__
## other libraries
from copy import deepcopy
from pathlib import Path
import json
connection = None

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
    myHeader = deepcopy(connection.header)
    myHeader["Accept"] = "application/vnd.adobe.platform.xcore.home.hal+json"
    res = connection.getData(endpoint, params=params, headers=myHeader)
    return res


def saveFile(module: str = None, file: object = None, filename: str = None, type_file: str = 'json',encoding:str='utf-8'):
    """
  Save the file in the approriate folder depending on the module sending the information.
   Arguments:
        module: REQUIRED: Module requesting the save file.
        file: REQUIRED: an object containing the file to save.
        filename: REQUIRED: the filename to be used.
        type_file: REQUIRED: the type of file to be saveed(default: json)
        encoding : OPTIONAL : encoding used to write the file.
    """
    if module is None:
        raise ValueError("Require the module to create a folder")
    if file is None or filename is None:
        raise ValueError("Require a object for file and a name for the file")
    here = Path(Path.cwd())
    folder = module.capitalize()
    new_location = Path.joinpath(here, folder)
    if new_location.exists() == False:
        new_location.mkdir()
    if type_file == 'json':
        filename = f"{filename}.json"
        complete_path = Path.joinpath(new_location, filename)
        with open(complete_path, 'w',encoding=encoding) as f:
            f.write(json.dumps(file, indent=4))
    else:
        filename = f"{filename}.txt"
        complete_path = Path.joinpath(new_location, filename)
        with open(complete_path, 'w',encoding=encoding) as f:
            f.write(file)
