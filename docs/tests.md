# Testing aepp

Because of the nature of the aepp package, it is not possible to completely automate all of the testing end to end.\
The aepp package is a wrapper around the Adobe Experience Platform APIs, and as such it relies on the capability to connect to the platform and perform operations on it.\
However, we have implemented a set of unit tests that can be run locally to test the functionality of the package.\

If you wish to add more tests, feel free to do so and also to contribute to the package by opening a pull request.\

## Pytest scripts

The tests are located in the `tests` folder of the repository, and they are organized in different files according to the functionality they test.\
The tests can be run using the `pytest` framework, and they are designed to test the following scenarios:
- Test the creation of a schema manager instance with a schema API instance and with a local folder
- Test the retrieval of a schema from the platform and from a local folder

### Offline CLI and Query Service regression tests

The following suites use mocks and temporary output folders. They do not require Adobe credentials or a live AEP or PostgreSQL connection:

* [`test_cli_commands.py`](../tests/test_cli_commands.py) covers login requirements, grouped and argument-level help, template and schedule retrieval, schedule creation and state changes, UTC dates and input validation, query-history filters, small query-result exports, audience-population argument forwarding, and dataset/descriptor definition exports. Snapshot CLI tests cover the omitted, bare and explicit boolean forms of `--defaultOnly` / `-d`, case-insensitive values, invalid-value rejection, help and CSV export. The suite also checks that API errors are reported without exporting misleading results.
* [`test_queryservice.py`](../tests/test_queryservice.py) covers query, template and schedule pagination, object and string next-page links, exact result limits, empty collections, invalid limits, repeated pagination links, single URL encoding of filters, API errors, schedule creation payloads and the asynchronous enable/disable PATCH contract. Interactive-query tests mock both database drivers to check namespace metadata initialization, history-query delegation, default-policy SQL, profile date sorting, namespace mappings, trend filters and empty results.

The CLI reporting tests cover all five interactive reports: default and custom CSV filenames, full exports versus console samples, namespace/audience filter forwarding, empty data, query/export failures and connection cleanup after report retrieval. Plotting tests use a non-interactive Matplotlib backend to check chronological date axes, separate series, metric selection, finite-value validation and preservation of CSV contents when charting fails. Namespace bar tests check scaling, zero counts, literal labels and legacy Windows encodings.

From the repository root, run both suites together:

```powershell
python -m pytest tests\test_cli_commands.py tests\test_queryservice.py
```

To focus on one area:

```powershell
python -m pytest tests\test_cli_commands.py -k schedule
python -m pytest tests\test_queryservice.py -k pagination
python -m pytest tests\test_cli_commands.py -k "report or trend or namespace"
```

These mocked tests do not validate live Adobe permissions, availability of `qsaccel.profile_agg` reporting tables, asynchronous schedule registration, snapshot dataset discovery, database connection cleanup against a running database, or interactive GUI windows. The CLI audience-population test mocks the Python helper and checks argument forwarding, not its live SQL or count result.

## Environment tests
You can also run tests to see the different implementation of the module in different python environment: 


* from the repo root
`.\tests\run_multiversion_tests.ps1`

* keep the venvs for inspection
`.\tests\run_multiversion_tests.ps1 -KeepEnvs`

* test only specific versions
`.\tests\run_multiversion_tests.ps1 -PythonVersions @("3.12","3.13")`