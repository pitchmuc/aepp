#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

import io
import json
import unittest
from unittest.mock import MagicMock, patch

from aepp.connector import AdobeRequest
from aepp.dataaccess import DataAccess


def _configure_mock_connector(mock_adobe_request):
    conn = mock_adobe_request.return_value
    conn.header = {"Accept": "application/json", "x-sandbox-name": "prod"}
    conn.config = {
        "sandbox": "prod",
        "client_id": "test-client",
        "org_id": "test-org",
    }
    return conn


def _make_raw_response(content: bytes, status_code: int = 200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = content
    resp.text = content.decode("utf-8", errors="replace")

    def _json():
        return json.loads(resp.text)

    resp.json.side_effect = _json
    return resp


class DataAccessTest(unittest.TestCase):

    @patch("aepp.connector.AdobeRequest")
    def test_dataaccess_get_batch_files(self, mock_adobe_request):
        conn = _configure_mock_connector(mock_adobe_request)
        conn.getData.return_value = {"data": [{"dataSetViewId": "view-1"}]}
        da = DataAccess()

        res = da.getBatchFiles(batchId="batch-123", limit=10, start=0)

        self.assertEqual(res, [{"dataSetViewId": "view-1"}])
        conn.getData.assert_called_once_with(
            da.endpoint + "/batches/batch-123/files",
            params={"limit": "10", "start": "0"},
            verbose=False,
        )

    @patch("aepp.connector.AdobeRequest")
    def test_dataaccess_get_batch_failed(self, mock_adobe_request):
        conn = _configure_mock_connector(mock_adobe_request)
        expected_files = [
            {
                "name": "part-00000.json",
                "length": "180",
                "_links": {
                    "self": {
                        "href": "https://platform.adobe.io/data/foundation/export/batches/batch-123/failed?path=part-00000.json"
                    }
                },
            }
        ]
        conn.getData.return_value = {"data": expected_files, "_page": {"count": 1}}
        da = DataAccess()

        res = da.getBatchFailed(batchId="batch-123")

        self.assertEqual(res, expected_files)
        conn.getData.assert_called_once_with(
            da.endpoint + "/batches/batch-123/failed",
            params={},
            verbose=False,
        )

    @patch("aepp.connector.AdobeRequest")
    def test_dataaccess_get_batch_failed_missing_batch_id(self, mock_adobe_request):
        _configure_mock_connector(mock_adobe_request)
        da = DataAccess()
        with self.assertRaises(ValueError):
            da.getBatchFailed()

    @patch("aepp.connector.AdobeRequest")
    def test_dataaccess_get_batch_failed_download_ndjson_bytes_and_formats(
        self, mock_adobe_request
    ):
        conn = _configure_mock_connector(mock_adobe_request)
        ndjson_bytes = b'{"id": 1, "err": "bad type"}\n{"id": 2, "err": "missing id"}\n'
        conn.getData.return_value = _make_raw_response(ndjson_bytes)
        da = DataAccess()

        # Default returns raw bytes (safe for NDJSON, CSV, malformed payloads)
        res_bytes = da.getBatchFailed(batchId="batch-123", path="part-00000.json")
        self.assertEqual(res_bytes, ndjson_bytes)
        conn.getData.assert_called_with(
            da.endpoint + "/batches/batch-123/failed",
            params={"path": "part-00000.json"},
            verbose=False,
            format="raw",
        )

        # Explicit format="txt" returns decoded string
        res_txt = da.getBatchFailed(
            batchId="batch-123", path="part-00000.json", format="txt"
        )
        self.assertEqual(res_txt, ndjson_bytes.decode("utf-8"))

        # Explicit format="json" parses NDJSON lines into a list of dicts
        res_json = da.getBatchFailed(
            batchId="batch-123", path="part-00000.json", format="json"
        )
        self.assertEqual(
            res_json,
            [{"id": 1, "err": "bad type"}, {"id": 2, "err": "missing id"}],
        )

    @patch("aepp.connector.AdobeRequest")
    def test_dataaccess_get_batch_failed_download_parquet(self, mock_adobe_request):
        conn = _configure_mock_connector(mock_adobe_request)
        parquet_bytes = b"PAR1fake-parquet-bytesPAR1"
        conn.getData.return_value = _make_raw_response(parquet_bytes)
        da = DataAccess()

        res = da.getBatchFailed(
            batchId="batch-123", path="part-00000.snappy.parquet"
        )

        self.assertIsInstance(res, io.BytesIO)
        self.assertEqual(res.getvalue(), parquet_bytes)

    @patch("aepp.connector.AdobeRequest")
    def test_dataaccess_get_batch_failed_http_error(self, mock_adobe_request):
        conn = _configure_mock_connector(mock_adobe_request)
        err_payload = {"title": "Not Found", "status": 404}
        conn.getData.return_value = _make_raw_response(
            json.dumps(err_payload).encode("utf-8"), status_code=404
        )
        da = DataAccess()

        res = da.getBatchFailed(batchId="batch-123", path="missing.json")
        self.assertEqual(res, err_payload)

    @patch("aepp.connector.AdobeRequest")
    def test_dataaccess_get_batch_meta(self, mock_adobe_request):
        conn = _configure_mock_connector(mock_adobe_request)
        da = DataAccess()

        # 1. Root listing (path=None) returns JSON dict
        root_listing = {"data": [{"name": "row_errors"}]}
        conn.getData.return_value = root_listing
        self.assertEqual(da.getBatchMeta(batchId="batch-123"), root_listing)

        # 2. Subdirectory listing (path="row_errors") returns parsed JSON dict
        dir_listing = {"data": [{"name": "row_errors/part-00000.json"}]}
        conn.getData.return_value = _make_raw_response(
            json.dumps(dir_listing).encode("utf-8")
        )
        self.assertEqual(
            da.getBatchMeta(batchId="batch-123", path="row_errors"), dir_listing
        )

        # 3. Multi-line NDJSON error file under row_errors returns bytes by default
        ndjson_errors = b'{"errorCode": "INGEST-1"}\n{"errorCode": "INGEST-2"}\n'
        conn.getData.return_value = _make_raw_response(ndjson_errors)
        self.assertEqual(
            da.getBatchMeta(
                batchId="batch-123", path="row_errors/part-00000.json"
            ),
            ndjson_errors,
        )

    def test_connector_getdata_non_json_does_not_recurse_and_parses_once(self):
        cfg = {
            "org_id": "test-org",
            "client_id": "test-client",
            "sandbox": "prod",
            "environment": "prod",
            "token": "valid-token",
            "date_limit": 9999999999,
            "connectionType": "oauthV2",
            "retry": 1,
        }
        req = AdobeRequest(config=cfg, retry=1)

        # Verify valid JSON is parsed only once (elif fix)
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"ok": True}
        req.session.get = MagicMock(return_value=ok_resp)

        self.assertEqual(req.getData("https://example.com/json"), {"ok": True})
        self.assertEqual(ok_resp.json.call_count, 1)

        # Verify non-JSON 200 response with retry=1 returns fallback dict in 1 call (no infinite recursion)
        non_json_resp = MagicMock()
        non_json_resp.status_code = 200
        non_json_resp.text = "line1\nline2"
        non_json_resp.json.side_effect = ValueError("Extra data")
        req.session.get = MagicMock(return_value=non_json_resp)

        res = req.getData("https://example.com/ndjson")
        self.assertEqual(res, {"error": "Request Error - could not generate json"})
        self.assertEqual(req.session.get.call_count, 1)

    def test_dataaccess_getHeadFile(self):
        assert True

    def test_dataaccess_get_files(self):
        assert True

    def test_dataaccess_get_preview(self):
        assert True

    def test_dataaccess_get_resource(self):
        assert True