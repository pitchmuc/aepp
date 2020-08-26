import aepp
_org_id, _api_key, _tech_id, _pathToKey, _secret, _companyid = "", "", "", "", "", ""
_TokenEndpoint = "https://ims-na1.adobelogin.com/ims/exchange/jwt"
_cwd = aepp.Path.as_posix(aepp.Path.cwd())
_date_limit = 0
_token = ''
header = {"Accept": "application/json",
          "Content-Type": "application/json",
          "Authorization": "",
          "X-Api-Key": _api_key,
          "x-gw-ims-org-id": _org_id,
          "x-sandbox-name": "prod"
          }

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
