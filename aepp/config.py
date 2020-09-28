import aepp
org_id, client_id, tech_id, _pathToKey, _secret, _companyid = "", "", "", "", "", ""
_TokenEndpoint = "https://ims-na1.adobelogin.com/ims/exchange/jwt"
_cwd = aepp.modules.Path.as_posix(aepp.modules.Path.cwd())
date_limit = 0
_token = ''
header = {"Accept": "application/json",
          "Content-Type": "application/json",
          "Authorization": "",
          "X-Api-Key": client_id,
          "x-gw-ims-org-id": org_id,
          "x-sandbox-name": "prod"
          }
sandbox = ""

# endpoints
_endpoint = "https://platform.adobe.io"
_endpoint_schema = "/data/foundation/schemaregistry"
_endpoint_query = "/data/foundation/query"
_endpoint_catalog = "/data/foundation/catalog"
_endpoint_dule = "/data/foundation/dulepolicy"
_endpoint_export = "/data/foundation/export"
_endpoint_segmentation = "/data/core/ups"
_endpoint_identity = "/data/core/"
_endpoint_sandboxes = "/data/foundation/sandbox-management"
_endpoint_sensei = "/data/sensei"
