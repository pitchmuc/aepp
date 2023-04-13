#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

# Internal Library
from aepp import config
from aepp import connector
from .configs import *
from .__version__ import __version__
from typing import Union

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
    if connection is None:
        connection = connector.AdobeRequest(
            config_object=config.config_object, header=config.header
        )
    endpoint = config.endpoints["global"] + "/data/core/xcore/"
    params = {"product": product, "limit": limit}
    myHeader = deepcopy(connection.header)
    myHeader["Accept"] = "application/vnd.adobe.platform.xcore.home.hal+json"
    res = connection.getData(endpoint, params=params, headers=myHeader)
    return res


def getPlatformEvents(
    limit: int = 50, n_results: Union[int, str] = "inf", prop: str = None, **kwargs
) -> dict:
    """
    Timestamped records of observed activities in Platform. The API allows you to query events over the last 90 days and create export requests.
    Arguments:
        limit : OPTIONAL : Number of events to retrieve per request (50 by default)
        n_results : OPTIONAL : Number of total event to retrieve per request.
        prop : OPTIONAL : An array that contains one or more of a comma-separated list of properties (prop="action==create,assetType==Sandbox")
            If you want to filter results using multiple values for a single filter, pass in a comma-separated list of values. (prop="action==create,update")
    """
    global connection
    if connection is None:
        connection = connector.AdobeRequest(
            config_object=config.config_object, header=config.header
        )
    endpoint = "https://platform.adobe.io/data/foundation/audit/events"
    params = {"limit": limit}
    if prop is not None:
        params["property"] = prop
    # myHeader = deepcopy(connection.header)
    lastPage = False
    data = list()
    while lastPage != True:
        res = connection.getData(endpoint, params=params)
        data += res.get("_embedded", {}).get("events", [])
        nextPage = res.get("_links", {}).get("next", {}).get('href','')
        if float(len(data)) >= float(n_results):
            lastPage = True
        if nextPage == "" and lastPage != True:
            lastPage = True
        else:
            start = nextPage.split("start=")[1].split("&")[0]
            queryId = nextPage.split("queryId=")[1].split("&")[0]
            params["queryId"] = queryId
            params["start"] = start
    return data


def saveFile(
    module: str = None,
    file: object = None,
    filename: str = None,
    type_file: str = "json",
    encoding: str = "utf-8",
):
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
    if type_file == "json":
        filename = f"{filename}.json"
        complete_path = Path.joinpath(new_location, filename)
        with open(complete_path, "w", encoding=encoding) as f:
            f.write(json.dumps(file, indent=4))
    else:
        filename = f"{filename}.txt"
        complete_path = Path.joinpath(new_location, filename)
        with open(complete_path, "w", encoding=encoding) as f:
            f.write(file)
