#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

import aepp

config_object = {
    "org_id": "",
    "client_id": "",
    "tech_id": "",
    "pathToKey": "",
    "auth_code": "",
    "secret": "",
    "date_limit": 0,
    "sandbox": "",
    "environment": "",
    "token": "",
    "jwtTokenEndpoint": "",
    "oauthTokenEndpoint": "",
    "imsEndpoint": ""
}

header = {"Accept": "application/json",
          "Content-Type": "application/json",
          "Authorization": "",
          "x-api-key": config_object["client_id"],
          "x-gw-ims-org-id": config_object["org_id"],
          "x-sandbox-name": "prod"
          }

# endpoints
endpoints = {
    # global endpoint is https://platform.adobe.io in prod, otherwise https://platform-$ENV.adobe.io
    "global": "",
    "schemas": "/data/foundation/schemaregistry",
    "query": "/data/foundation/query",
    "catalog": "/data/foundation/catalog",
    "policy": "/data/foundation/dulepolicy",
    "segmentation": "/data/core/ups",
    "export": "/data/foundation/export",
    "identity": "/data/core/",
    "sandboxes": "/data/foundation/sandbox-management",
    "sensei": "/data/sensei",
    "access": "/data/foundation/access-control",
    "flow": "/data/foundation/flowservice",
    "privacy": "/data/core/privacy",
    "dataaccess": "/data/foundation/export",
    "mapping": "/data/foundation/conversion",
    "policy": "/data/foundation/dulepolicy",
    "dataset": "/data/foundation/dataset",
    "ingestion": "/data/foundation/import",
    "observability": "/data/infrastructure/observability/insights",
    "destinationAuthoring": "/data/core/activation/authoring",
    "destinationInstance" : "/data/core/activation/disflowprovider",
    "streaming": {
        "inlet": "",
        "collection": "https://dcs.adobedc.net"
    },
    "audit": "/data/foundation"
}