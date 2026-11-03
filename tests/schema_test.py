#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

from aepp.schema import Schema
from copy import deepcopy
import unittest
from unittest.mock import patch, MagicMock
from urllib.parse import quote_plus

import pytest


PROFILE_CLASS = "https://ns.adobe.com/xdm/context/profile"
EVENT_CLASS = "https://ns.adobe.com/xdm/context/experienceevent"
CUSTOM_CLASS = "https://ns.adobe.com/test/classes/custom"
FIELDGROUP_ID = "https://ns.adobe.com/test/mixins/example"


@pytest.fixture
def schema_api():
    with patch("aepp.connector.AdobeRequest"):
        api = Schema()
        api.connector.getData.return_value = {
            "$id": FIELDGROUP_ID,
            "meta:intendedToExtend": [CUSTOM_CLASS],
        }
        yield api


@pytest.mark.parametrize("values,current,expected", [
    (None, [CUSTOM_CLASS], [CUSTOM_CLASS, PROFILE_CLASS, EVENT_CLASS]),
    (PROFILE_CLASS, [CUSTOM_CLASS], [CUSTOM_CLASS, PROFILE_CLASS]),
    ([PROFILE_CLASS], [CUSTOM_CLASS], [CUSTOM_CLASS, PROFILE_CLASS]),
    ([CUSTOM_CLASS, PROFILE_CLASS, PROFILE_CLASS], [CUSTOM_CLASS, CUSTOM_CLASS],
     [CUSTOM_CLASS, PROFILE_CLASS]),
    (None, [CUSTOM_CLASS, PROFILE_CLASS, EVENT_CLASS], [CUSTOM_CLASS, PROFILE_CLASS, EVENT_CLASS]),
    ([], [CUSTOM_CLASS], [CUSTOM_CLASS]),
    (None, [], [PROFILE_CLASS, EVENT_CLASS]),
])
def test_extend_fieldgroup_preserves_and_deduplicates_classes(schema_api, values, current, expected):
    definition = {"$id": FIELDGROUP_ID, "meta:intendedToExtend": current}
    original = deepcopy(definition)
    original_values = deepcopy(values)
    schema_api.connector.getData.return_value = definition

    result = schema_api.extendFieldGroup(FIELDGROUP_ID, values=values)

    schema_api.connector.patchData.assert_called_once_with(
        f"{schema_api.endpoint}/tenant/fieldgroups/{quote_plus(FIELDGROUP_ID)}",
        data=[{"op": "replace", "path": "/meta:intendedToExtend", "value": expected}],
    )
    assert definition == original
    assert values == original_values
    assert result is schema_api.connector.patchData.return_value


@pytest.mark.parametrize("container", ["tenant", "global"])
@pytest.mark.parametrize("initial_container", ["tenant", "global"])
@pytest.mark.parametrize("identifier", [FIELDGROUP_ID, "_test.mixins.example"])
def test_extend_fieldgroup_reads_and_patches_same_container(schema_api, container, initial_container, identifier):
    schema_api.container = initial_container

    schema_api.extendFieldGroup(identifier, tenant=container)

    expected_url = f"{schema_api.endpoint}/{container}/fieldgroups/{quote_plus(identifier)}"
    assert schema_api.connector.getData.call_args.args[0] == expected_url
    assert schema_api.connector.patchData.call_args.args[0] == expected_url
    assert schema_api.container == initial_container


@pytest.mark.parametrize("response", [
    {"errorMessage": "Permission denied"},
    {"status": 404, "title": "Not found"},
    {"$id": FIELDGROUP_ID},
    {"meta:intendedToExtend": None},
    {"meta:intendedToExtend": CUSTOM_CLASS},
    {"meta:intendedToExtend": [None]},
    {"meta:intendedToExtend": [""]},
    None,
    [],
])
def test_extend_fieldgroup_rejects_unreadable_existing_classes(schema_api, response):
    schema_api.connector.getData.return_value = response

    with pytest.raises(ValueError, match="Field group retrieval failed"):
        schema_api.extendFieldGroup(FIELDGROUP_ID)

    schema_api.connector.patchData.assert_not_called()


@pytest.mark.parametrize("values", [1, ("class-id",), "", [None], [""], [1]])
def test_extend_fieldgroup_rejects_invalid_class_values(schema_api, values):
    with pytest.raises(ValueError, match="values"):
        schema_api.extendFieldGroup(FIELDGROUP_ID, values=values)

    schema_api.connector.getData.assert_not_called()
    schema_api.connector.patchData.assert_not_called()


def test_extend_fieldgroup_does_not_patch_when_read_fails(schema_api):
    schema_api.connector.getData.side_effect = RuntimeError("Read failed")

    with pytest.raises(RuntimeError, match="Read failed"):
        schema_api.extendFieldGroup(FIELDGROUP_ID)

    schema_api.connector.patchData.assert_not_called()


class SchemaTest(unittest.TestCase):

    @patch("aepp.connector.AdobeRequest")
    def test_schema_get_resource(self, mock_connector):
        instance_conn = mock_connector.return_value
        instance_conn.getData.return_value = "foo"
        schema_obj = Schema()
        result = schema_obj.getResource(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        assert(result is not None)
        instance_conn.getData.assert_called_once()

    @patch("aepp.connector.AdobeRequest")
    def test_schema_update_sandbox(self, mock_connector):
        schema_obj = Schema()
        test_sandbox = "prod"
        schema_obj.updateSandbox(test_sandbox)
        assert(schema_obj.sandbox == test_sandbox)

    @patch("aepp.connector.AdobeRequest")
    def test_schema_get_stats(self, mock_connector):
        instance_conn = mock_connector.return_value
        instance_conn.getData.return_value = MagicMock()
        schema_obj = Schema()
        stats_result = schema_obj.getStats()
        assert (stats_result is not None)
        assert(stats_result == instance_conn.getData.return_value)
        instance_conn.getData.assert_called_once()

    @patch("aepp.connector.AdobeRequest")
    def test_schema_get_tenant_id(self, mock_connector):
        instance_conn = mock_connector.return_value
        instance_conn.getStats.return_value = MagicMock()
        schema_obj = Schema()
        tenant_id_result = schema_obj.getTenantId()
        assert (tenant_id_result is not None)
        instance_conn.getData.assert_called_once()

    @patch("aepp.connector.AdobeRequest")
    def test_schema_get_behavior(self, mock_connector):
        instance_conn = mock_connector.return_value
        instance_conn.getData.return_value = {"results":[1234,5678]}
        schema_obj = Schema()
        stats_result = schema_obj.getBehaviors()
        assert (stats_result is not None)
        assert (stats_result == instance_conn.getData.return_value.get("results"))
        instance_conn.getData.assert_called_once()