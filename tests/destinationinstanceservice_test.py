#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

from aepp.destinationinstanceservice import DestinationInstanceService
import unittest
from unittest.mock import patch, MagicMock, ANY


class DestinationInstanceServiceTest(unittest.TestCase):
    ADHOC_INPUT = {"flow1": ["dataset1"], "flow2": ["dataset2", "dataset3"]}
    ADHOC_EXPECTED_PAYLOAD = {'activationInfo': {'destinations': [{'flowId': 'flow1', 'datasets': [{'id': 'dataset1'}]}, {'flowId': 'flow2', 'datasets': [{'id': 'dataset2'}, {'id': 'dataset3'}]}]}}
    
    @patch("aepp.connector.AdobeRequest")
    def test_create_adhoc_dataset_export(self, mock_connector):
        instance_conn = mock_connector.return_value
        instance_conn.postData.return_value = {'foo'}
        destination_instance_service_obj = DestinationInstanceService()
        result = destination_instance_service_obj.createAdHocDatasetExport(self.ADHOC_INPUT)
        assert(result is not None)
        instance_conn.postData.assert_called_once()
        instance_conn.postData.assert_called_with(ANY, data=self.ADHOC_EXPECTED_PAYLOAD)

    @patch("aepp.connector.AdobeRequest")
    def test_create_adhoc_dataset_export_invalid_input(self, mock_connector):
        destination_instance_service_obj = DestinationInstanceService()
        with self.assertRaises(Exception) as cm:
            destination_instance_service_obj.createAdHocDatasetExport(None)
        self.assertEqual('Require a dict for defining the flowId to datasetIds mapping', str(cm.exception))
    