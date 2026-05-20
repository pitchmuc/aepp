#  Copyright 2023 Adobe. All rights reserved.
#  This file is licensed to you under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License. You may obtain a copy
#  of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
#  OF ANY KIND, either express or implied. See the License for the specific language
#  governing permissions and limitations under the License.

"""
Tests that verify aepp and each of its modules can be successfully imported
in a clean Python environment.

Run with:
    pytest tests/test_import_modules.py -v
"""

import importlib
import sys
import pytest


# Top-level package
PACKAGE = "aepp"

# All public sub-modules inside aepp/
MODULES = [
    "aepp.accesscontrol",
    "aepp.catalog",
    "aepp.classmanager",
    "aepp.config",
    "aepp.configs",
    "aepp.connector",
    "aepp.customerprofile",
    "aepp.dataaccess",
    "aepp.dataprep",
    "aepp.datasets",
    "aepp.datatypemanager",
    "aepp.deletion",
    "aepp.destination",
    "aepp.destinationinstanceservice",
    "aepp.edge",
    "aepp.exportDatasetToDataLandingZone",
    "aepp.fieldgroupmanager",
    "aepp.flowservice",
    "aepp.hygiene",
    "aepp.identity",
    "aepp.ingestion",
    "aepp.manager_utils",
    "aepp.observability",
    "aepp.policy",
    "aepp.privacyservice",
    "aepp.queryservice",
    "aepp.sandboxes",
    "aepp.schema",
    "aepp.schemamanager",
    "aepp.segmentation",
    "aepp.sensei",
    "aepp.som",
    "aepp.synchronizer",
    "aepp.tags",
    "aepp.utils",
    "aepp.cli",
]


class TestPythonVersion:
    """Ensure we are running on a supported Python version (>=3.10)."""

    def test_python_version_is_supported(self):
        major, minor = sys.version_info.major, sys.version_info.minor
        assert (major, minor) >= (3, 10), (
            f"Python {major}.{minor} is not supported. aepp requires Python >= 3.10."
        )

    def test_python_version_is_reported(self):
        """Informational: print the active Python version."""
        print(f"\nActive Python: {sys.version}")


class TestPackageInstall:
    """Verify aepp is installed and its version is accessible."""

    def test_aepp_is_importable(self):
        mod = importlib.import_module(PACKAGE)
        assert mod is not None

    def test_aepp_has_version(self):
        mod = importlib.import_module(PACKAGE)
        assert hasattr(mod, "__version__"), "aepp.__version__ attribute is missing"
        assert isinstance(mod.__version__, str) and mod.__version__, (
            "aepp.__version__ should be a non-empty string"
        )

    def test_aepp_version_format(self):
        import re
        mod = importlib.import_module(PACKAGE)
        pattern = r"^\d+\.\d+\.\d+"
        assert re.match(pattern, mod.__version__), (
            f"Version '{mod.__version__}' does not match expected semver pattern"
        )


@pytest.mark.parametrize("module_name", MODULES)
class TestModuleImports:
    """Parameterised tests — one test per sub-module."""

    def test_module_is_importable(self, module_name):
        """Each module must be importable without raising any exception."""
        mod = importlib.import_module(module_name)
        assert mod is not None, f"importlib returned None for {module_name}"

    def test_module_has_file_attribute(self, module_name):
        """Each module must have a __file__ attribute (i.e. it is a real file, not a namespace)."""
        mod = importlib.import_module(module_name)
        assert hasattr(mod, "__file__"), f"{module_name} has no __file__ attribute"

    def test_module_has_name_attribute(self, module_name):
        """Each module must expose its own __name__."""
        mod = importlib.import_module(module_name)
        assert mod.__name__ == module_name, (
            f"Expected __name__ == '{module_name}', got '{mod.__name__}'"
        )
