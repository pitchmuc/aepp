import json
from decimal import Decimal
from datetime import datetime, timezone
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest
from rich.console import Console

from aepp.cli import __main__ as cli


QUERY_COMMANDS = [
    "get_queries",
    "get_query",
    "get_query_templates",
    "get_query_template",
    "get_queries_scheduled",
    "create_query_scheduled",
    "enable_query_scheduled",
    "disable_query_scheduled",
    "query",
    "query_audience_population",
    "query_history_meta",
    "query_profiles_trend",
    "query_namespaces_distribution",
    "query_namespaces_trend",
    "query_audience_population_trend",
]

INTERACTIVE_REPORTS = [
    ("query_history_meta accounts", "queryHistoryMeta", {"table": "accounts"}, "dev_history_meta.csv"),
    ("query_profiles_trend", "queryProfilesTrend", {}, "dev_profiles_trend.csv"),
    ("query_namespaces_distribution", "queryNamespacesDistribution", {}, "dev_namespaces_distribution.csv"),
    ("query_namespaces_trend", "queryNamespacesTrend", {"namespace": None}, "dev_namespaces_trend.csv"),
    ("query_audience_population_trend", "queryAudiencePopulationTrend", {"segment": None}, "dev_audience_population_trend.csv"),
]

TREND_REPORTS = [INTERACTIVE_REPORTS[index] for index in (1, 3, 4)]


@pytest.fixture
def shell(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    output = StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, width=200, color_system=None))
    service = Mock()
    monkeypatch.setattr(cli.queryservice, "QueryService", Mock(return_value=service))
    instance = cli.ServiceShell()
    instance.config = SimpleNamespace(sandbox="dev")
    return instance, service, output


@pytest.fixture
def trend_figures(monkeypatch):
    import matplotlib
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    original = set(plt.get_fignums())
    figures = []

    def show(*, block):
        assert block is True
        figure = plt.gcf()
        figure.canvas.draw()
        figures.append(figure)

    monkeypatch.setattr(plt, "show", Mock(side_effect=show))
    yield figures
    for number in set(plt.get_fignums()) - original:
        plt.close(number)


@pytest.mark.parametrize("command", QUERY_COMMANDS + ["get_descriptor", "get_dataset", "get_snapshot_datasets"])
def test_commands_require_login(shell, command, capsys):
    instance, service, output = shell
    instance.config = None
    instance.onecmd(command)
    assert "Access Denied" in capsys.readouterr().out
    cli.queryservice.QueryService.assert_not_called()


@pytest.mark.parametrize("command,function", [
    ("extract_artifacts", "extractSandboxArtifacts"),
    ('extract_artifact "Customer Events" -at schema', "extractSandboxArtifact"),
])
@pytest.mark.parametrize("option,expected_verbose", [
    ("", False),
    ("-v", True),
    ("--verbose", True),
    ("-v True", True),
    ("--verbose True", True),
    ("-v False", False),
    ("--verbose False", False),
    ("-v true", True),
    ("--verbose false", False),
    ("--verbose=True", True),
    ("--verbose=False", False),
])
def test_extraction_verbose_accepts_flag_or_boolean(shell, monkeypatch, command, function, option, expected_verbose):
    instance, service, output = shell
    extraction = Mock()
    monkeypatch.setattr(cli.aepp, function, extraction)

    instance.onecmd(f'{command} {option} -lf "folder with spaces"')

    expected = {
        "sandbox": instance.config,
        "localFolder": "folder with spaces",
        "verbose": expected_verbose,
    }
    if function == "extractSandboxArtifacts":
        expected.update(filters=None, artifactTypes=None)
    else:
        expected.update(artifact="Customer Events", artifactType="schema")
    extraction.assert_called_once_with(**expected)
    assert extraction.call_args.kwargs["verbose"] is expected_verbose
    assert "Extraction completed!" in output.getvalue()
    assert "(!) Error" not in output.getvalue()


@pytest.mark.parametrize("command,function", [
    ("extract_artifacts", "extractSandboxArtifacts"),
    ('extract_artifact "Customer Events" -at schema', "extractSandboxArtifact"),
])
@pytest.mark.parametrize("option", ["-v invalid", "--verbose invalid"])
def test_extraction_verbose_rejects_invalid_boolean(shell, monkeypatch, capsys, command, function, option):
    instance, service, output = shell
    extraction = Mock()
    monkeypatch.setattr(cli.aepp, function, extraction)

    instance.onecmd(f"{command} {option}")

    extraction.assert_not_called()
    assert "Boolean value expected" in capsys.readouterr().err
    assert "Extraction completed!" not in output.getvalue()


def test_query_template_list_uses_library_list(shell):
    instance, service, output = shell
    service.getTemplates.return_value = [
        {"id": "template-1", "name": "Daily accounts", "created": "2026-10-01T12:00:00.000Z"}
    ]
    instance.onecmd("get_query_templates")
    service.getTemplates.assert_called_once_with(n_results="inf")
    assert "template-1" in output.getvalue()
    assert "Daily accounts" in output.getvalue()
    assert "(!) Error" not in output.getvalue()


def test_query_template_is_displayed_and_exported(shell, tmp_path):
    instance, service, output = shell
    template = {"id": "template-1", "name": "Daily accounts", "sql": "SELECT 1"}
    service.getTemplate.return_value = template
    instance.onecmd("get_query_template template-1")
    service.getTemplate.assert_called_once_with(templateId="template-1")
    assert json.loads((tmp_path / "query_template_template-1.json").read_text()) == template


def test_schedules_display_api_states_and_export(shell, tmp_path):
    instance, service, output = shell
    schedules = [
        {
            "id": f"schedule-{state}",
            "state": state,
            "query": {"name": state},
            "schedule": {"startDate": "2026-10-01T12:00:00.000Z", "schedule": "@daily"},
        }
        for state in ("ENABLED", "DISABLED", "REGISTERING")
    ]
    service.getSchedules.return_value = schedules
    instance.onecmd("get_queries_scheduled")
    service.getSchedules.assert_called_once_with(n_results="inf")
    text = output.getvalue()
    assert "True" in text
    assert "False" in text
    assert "REGISTERING" in text
    assert "(!) Error" not in text
    assert json.loads((tmp_path / "queries_scheduled_dev.json").read_text()) == schedules


@pytest.mark.parametrize("source", ['-q "SELECT $value"', "-t template-1"])
def test_create_schedule_uses_active_sandbox_and_parameters(shell, source):
    instance, service, output = shell
    service.createSchedule.return_value = {"id": "schedule-1", "state": "REGISTERING"}
    instance.onecmd(
        f'create_query_scheduled {source} -n "Daily accounts" -d "Daily load" '
        '-a "value=a=b,table=accounts" -sch "@daily" '
        '-sd "2026-11-01T10:00:00+02:00" -ed "2026-12-01T08:00:00Z"'
    )
    query = {
        "dbName": "dev:all",
        "name": "Daily accounts",
        "description": "Daily load",
        "queryParameters": {"value": "a=b", "table": "accounts"},
    }
    query.update({"sql": "SELECT $value"} if source.startswith("-q") else {"templateId": "template-1"})
    service.createSchedule.assert_called_once_with(
        scheduleQuery={
            "query": query,
            "schedule": {
                "schedule": "@daily",
                "startDate": "2026-11-01T08:00:00.000Z",
                "endDate": "2026-12-01T08:00:00.000Z",
            },
        }
    )
    assert "schedule-1" in output.getvalue()
    assert "REGISTERING" in output.getvalue()


def test_create_schedule_omits_optional_fields(shell):
    instance, service, output = shell
    service.createSchedule.return_value = {"id": "schedule-1", "state": "REGISTERING"}
    instance.onecmd('create_query_scheduled -q "SELECT 1" -sch "@once" -sd "2026-11-01T00:00:00Z"')
    service.createSchedule.assert_called_once_with(
        scheduleQuery={
            "query": {"dbName": "dev:all", "sql": "SELECT 1"},
            "schedule": {"schedule": "@once", "startDate": "2026-11-01T00:00:00.000Z"},
        }
    )


def test_create_schedule_preserves_fractional_timestamp_precision(shell):
    instance, service, output = shell
    service.createSchedule.return_value = {"id": "schedule-1", "state": "REGISTERING"}
    instance.onecmd(
        'create_query_scheduled -q "SELECT 1" -sch "@once" '
        '-sd "2026-11-01T00:00:00.000123Z" -ed "2026-11-01T00:00:00.000124Z"'
    )
    schedule = service.createSchedule.call_args.kwargs["scheduleQuery"]["schedule"]
    assert schedule["startDate"] == "2026-11-01T00:00:00.000123Z"
    assert schedule["endDate"] == "2026-11-01T00:00:00.000124Z"


@pytest.mark.parametrize(
    "arguments",
    [
        '',
        '-sch "@daily" -sd "2026-11-01T00:00:00Z"',
        '-q "SELECT 1" -t template-1 -sch "@daily" -sd "2026-11-01T00:00:00Z"',
        '-q "SELECT 1" -sd "2026-11-01T00:00:00Z"',
        '-q "SELECT 1" -sch "@daily"',
        '-q "SELECT 1" -sch "@daily" -sd "not-a-date"',
        '-q "SELECT 1" -sch "@daily" -sd "2026-11-01T00:00:00"',
        '-q "SELECT 1" -sch "@daily" -sd "2026-11-01T00:00:00Z" -ed "2026-10-01T00:00:00Z"',
        '-q "SELECT 1" -sch "@daily" -sd "2026-11-01T00:00:00Z" -a "invalid"',
        '-q "SELECT 1" -sch "@daily" -sd "2026-11-01T00:00:00Z" -a "=value"',
        '-q "" -sch "@daily" -sd "2026-11-01T00:00:00Z"',
    ],
)
def test_create_schedule_rejects_invalid_input(shell, arguments, capsys):
    instance, service, output = shell
    instance.onecmd(f"create_query_scheduled {arguments}")
    cli.queryservice.QueryService.assert_not_called()
    assert "error:" in capsys.readouterr().err


@pytest.mark.parametrize("action", ["enable", "disable"])
def test_schedule_state_change_reports_acceptance(shell, action):
    instance, service, output = shell
    method = getattr(service, f"{action}Schedule")
    method.return_value = {"message": "Request to patch accepted", "statusCode": 202}
    instance.onecmd(f"{action}_query_scheduled schedule-1")
    method.assert_called_once_with(scheduleId="schedule-1")
    assert "accepted" in output.getvalue()
    assert "(!) Error" not in output.getvalue()


@pytest.mark.parametrize("action", ["enable", "disable"])
def test_schedule_state_change_does_not_report_success_on_api_error(shell, action):
    instance, service, output = shell
    getattr(service, f"{action}Schedule").return_value = {"statusCode": 400, "errorMessage": "Inactive schedule"}
    instance.onecmd(f"{action}_query_scheduled schedule-1")
    text = output.getvalue()
    assert "(!) Error" in text
    assert "Inactive schedule" in text
    assert "successfully" not in text
    assert "accepted" not in text


def test_create_schedule_does_not_report_success_on_api_error(shell):
    instance, service, output = shell
    service.createSchedule.return_value = {"errorMessage": "Invalid SQL"}
    instance.onecmd('create_query_scheduled -q "SELECT 1" -sch "@daily" -sd "2026-11-01T00:00:00Z"')
    assert "Invalid SQL" in output.getvalue()
    assert "(!) Error" in output.getvalue()
    assert "accepted" not in output.getvalue()


def test_query_metadata(shell):
    instance, service, output = shell
    service.getQuery.return_value = {"id": "query-1", "state": "SUCCESS"}
    instance.onecmd("get_query query-1")
    service.getQuery.assert_called_once_with(queryId="query-1")
    assert "query-1" in output.getvalue()


def test_query_history_filters_and_exports_without_duplicate_rows(shell, monkeypatch, tmp_path):
    instance, service, output = shell

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 14, 12, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(cli, "datetime", FixedDatetime)
    service.getQueries.return_value = [
        {"id": "query-1", "client": "Adobe Query Service UI", "created": "2026-10-14T11:30:00Z", "elapsedTime": 42},
        {"id": "query-2", "client": "Generic PostgreSQL", "created": "2026-10-14T11:45:00Z", "elapsedTime": 12},
        {"id": "query-3", "client": "other"},
    ]
    instance.onecmd("get_queries -ds dataset-1 -st running -H 1")
    service.getQueries.assert_called_once_with(
        property="created>=2026-10-14T11:00:00Z,referenced_datasets==dataset-1,state==IN_PROGRESS",
        orderby="-created",
    )
    exported = pd.read_csv(tmp_path / "dev_queries.csv")
    assert exported["id"].tolist() == ["query-1", "query-2"]
    assert "(!) Error" not in output.getvalue()


@pytest.mark.parametrize("arguments", ["-mn -1", "-st unknown"])
def test_query_history_rejects_invalid_filters(shell, arguments, capsys):
    instance, service, output = shell
    instance.onecmd(f"get_queries {arguments}")
    cli.queryservice.QueryService.assert_not_called()
    assert "error:" in capsys.readouterr().err


def test_interactive_query_preserves_small_result_export(shell, monkeypatch, tmp_path):
    instance, service, output = shell
    interactive = Mock()
    interactive.query.return_value = pd.DataFrame({"value": [1, 2]})
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd('query "SELECT 1" -fn sample')
    interactive.query.assert_called_once_with(sql="SELECT 1")
    assert pd.read_csv(tmp_path / "sample.csv")["value"].tolist() == [1, 2]


def test_audience_population_forwards_arguments(shell, monkeypatch, tmp_path):
    instance, service, output = shell
    interactive = Mock()
    interactive.queryAudiencePopulation.return_value = pd.DataFrame({"count": [10]})
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_audience_population audience-1 audience-2 -ef email -c -fn population")
    interactive.queryAudiencePopulation.assert_called_once_with(
        audienceId=["audience-1", "audience-2"], extraFields="email", count=True
    )
    assert pd.read_csv(tmp_path / "population.csv")["count"].tolist() == [10]


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), INTERACTIVE_REPORTS)
def test_interactive_reports_export_display_and_close(shell, monkeypatch, tmp_path, command, method, kwargs, filename):
    instance, service, output = shell
    interactive = Mock()
    getattr(interactive, method).return_value = pd.DataFrame({"metric": [10, 20]})
    factory = Mock(return_value=interactive)
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", factory)
    instance.onecmd(command)
    factory.assert_called_once_with(service.connection.return_value, config=instance.config)
    getattr(interactive, method).assert_called_once_with(**kwargs)
    interactive.close.assert_called_once_with()
    assert pd.read_csv(tmp_path / filename).to_dict("list") == {"metric": [10, 20]}
    assert "metric" in output.getvalue()
    assert filename in output.getvalue()
    assert "(!) Error" not in output.getvalue()


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), INTERACTIVE_REPORTS)
@pytest.mark.parametrize(("option", "name"), [("-fn", "custom report"), ("--filename", "custom report.csv")])
def test_interactive_reports_accept_custom_filenames(shell, monkeypatch, tmp_path, command, method, kwargs, filename, option, name):
    instance, service, output = shell
    interactive = Mock()
    getattr(interactive, method).return_value = pd.DataFrame({"metric": [10]})
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd(f'{command} {option} "{name}"')
    assert (tmp_path / "custom report.csv").exists()
    assert not (tmp_path / filename).exists()
    interactive.close.assert_called_once_with()


@pytest.mark.parametrize(
    ("command", "method", "kwargs"),
    [
        ('query_namespaces_trend -ns "Email"', "queryNamespacesTrend", {"namespace": "Email"}),
        ('query_namespaces_trend --namespace "CRM ID"', "queryNamespacesTrend", {"namespace": "CRM ID"}),
        ('query_audience_population_trend -a "VIP Customers"', "queryAudiencePopulationTrend", {"segment": "VIP Customers"}),
        ("query_audience_population_trend --audience audience-1", "queryAudiencePopulationTrend", {"segment": "audience-1"}),
    ],
)
def test_interactive_report_filters_are_forwarded(shell, monkeypatch, command, method, kwargs):
    instance, service, output = shell
    interactive = Mock()
    getattr(interactive, method).return_value = pd.DataFrame({"metric": [10]})
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd(command)
    getattr(interactive, method).assert_called_once_with(**kwargs)


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), INTERACTIVE_REPORTS)
def test_interactive_reports_close_and_report_query_errors(shell, monkeypatch, tmp_path, command, method, kwargs, filename):
    instance, service, output = shell
    interactive = Mock()
    getattr(interactive, method).side_effect = RuntimeError("Query failed")
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd(command)
    interactive.close.assert_called_once_with()
    assert "(!) Error: Query failed" in output.getvalue()
    assert "exported" not in output.getvalue()
    assert not (tmp_path / filename).exists()


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), INTERACTIVE_REPORTS)
def test_interactive_reports_handle_empty_results(shell, monkeypatch, tmp_path, command, method, kwargs, filename):
    instance, service, output = shell
    interactive = Mock()
    getattr(interactive, method).return_value = pd.DataFrame(columns=["metric"])
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd(command)
    assert pd.read_csv(tmp_path / filename).empty
    assert "No rows returned." in output.getvalue()
    assert "(!) Error" not in output.getvalue()
    interactive.close.assert_called_once_with()


def test_interactive_reports_close_and_report_export_errors(shell, monkeypatch):
    instance, service, output = shell
    interactive = Mock()
    interactive.queryProfilesTrend.return_value = pd.DataFrame({"metric": [10]})
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    monkeypatch.setattr(pd.DataFrame, "to_csv", Mock(side_effect=OSError("Export denied")))
    instance.onecmd("query_profiles_trend")
    interactive.close.assert_called_once_with()
    assert "(!) Error: Export denied" in output.getvalue()
    assert "exported" not in output.getvalue()


def test_interactive_reports_report_connection_errors(shell, monkeypatch, tmp_path):
    instance, service, output = shell
    service.connection.side_effect = RuntimeError("Connection denied")
    factory = Mock()
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", factory)
    instance.onecmd("query_profiles_trend")
    factory.assert_not_called()
    assert "(!) Error: Connection denied" in output.getvalue()
    assert "exported" not in output.getvalue()
    assert not list(tmp_path.glob("*.csv"))


@pytest.mark.parametrize(
    "command",
    ["query_history_meta", "query_profiles_trend --unknown", "query_namespaces_trend -ns", "query_audience_population_trend -a"],
)
def test_interactive_reports_reject_invalid_arguments(shell, command, capsys):
    instance, service, output = shell
    instance.onecmd(command)
    cli.queryservice.QueryService.assert_not_called()
    assert "error:" in capsys.readouterr().err


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), INTERACTIVE_REPORTS[1:])
def test_report_plots_are_optional_and_preserve_exports(shell, trend_figures, monkeypatch, tmp_path, command, method, kwargs, filename):
    instance, service, output = shell
    result = pd.DataFrame({
        "DATE_KEY": [20261003, 20261001, 20261002], "COUNT_OF_PROFILES": [30, 10, 20],
        "NAMESPACE": ["Email"] * 3, "NAMESPACE_DESCRIPTION": ["Email"] * 3,
        "AUDIENCE_NAME": ["VIP Customers"] * 3, "AUDIENCE_ID": ["audience-1"] * 3,
    })
    original = result.copy(deep=True)
    interactive = Mock()
    getattr(interactive, method).return_value = result
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd(command)
    assert not trend_figures
    assert "Namespace profile distribution" not in output.getvalue()
    instance.onecmd(f"{command} --plot")
    if method == "queryNamespacesDistribution":
        assert "Namespace profile distribution" in output.getvalue()
        assert not trend_figures
    else:
        from matplotlib import pyplot as plt
        assert len(trend_figures) == 1
        assert trend_figures[0].axes[0].get_ylabel() == "COUNT_OF_PROFILES"
        assert trend_figures[0].axes[0].get_xlabel() == "Date"
        assert not plt.fignum_exists(trend_figures[0].number)
    assert "(!) Error" not in output.getvalue()
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / filename), original)
    pd.testing.assert_frame_equal(result, original)
    assert interactive.close.call_count == 2


@pytest.mark.parametrize(
    "dates",
    [[20261010, 20261001, 20261003], ["2026-10-10", "2026-10-01", "2026-10-03"], pd.to_datetime(["2026-10-10", "2026-10-01", "2026-10-03"])],
)
def test_trend_lines_use_sorted_calendar_dates(shell, trend_figures, monkeypatch, dates):
    from matplotlib import dates as mdates
    instance, service, output = shell
    interactive = Mock()
    interactive.queryProfilesTrend.return_value = pd.DataFrame({"DATE_KEY": dates, "COUNT_OF_PROFILES": [10, 0, 5]})
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_profiles_trend --plot")
    axes = trend_figures[0].axes[0]
    line = axes.lines[0]
    assert line.get_xdata(orig=False).tolist() == mdates.date2num(pd.to_datetime(["2026-10-01", "2026-10-03", "2026-10-10"])).tolist()
    assert line.get_ydata().tolist() == [0, 5, 10]
    assert isinstance(axes.xaxis.get_major_formatter(), mdates.ConciseDateFormatter)
    assert "(!) Error" not in output.getvalue()


@pytest.mark.parametrize(
    ("command", "method", "columns"),
    [
        ("query_namespaces_trend", "queryNamespacesTrend", {"NAMESPACE": ["Email", "Email", "CRM", "CRM"]}),
        ("query_audience_population_trend", "queryAudiencePopulationTrend",
         {"AUDIENCE_NAME": ["VIP"] * 4, "AUDIENCE_ID": ["audience-1", "audience-1", "audience-2", "audience-2"]}),
    ],
)
def test_trend_lines_keep_each_series_separate_on_the_same_axes(shell, trend_figures, monkeypatch, command, method, columns):
    instance, service, output = shell
    interactive = Mock()
    getattr(interactive, method).return_value = pd.DataFrame({
        "DATE_KEY": [20261002, 20261001, 20261001, 20261002], "COUNT_OF_PROFILES": [20, 10, 40, 30], **columns,
    })
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd(f"{command} --plot")
    axes = trend_figures[0].axes[0]
    assert [line.get_ydata().tolist() for line in axes.lines] == [[10, 20], [40, 30]]
    assert len({line.get_label() for line in axes.lines}) == 2
    assert axes.get_legend() is not None


@pytest.mark.parametrize("values", [[0], [0, 0, 0], [10, 10, 10], [-2.5, 0, 1.5]])
def test_trend_lines_preserve_single_constant_and_fractional_values(shell, trend_figures, monkeypatch, values):
    instance, service, output = shell
    interactive = Mock()
    interactive.queryProfilesTrend.return_value = pd.DataFrame({
        "DATE_KEY": pd.date_range("2026-10-01", periods=len(values)), "COUNT_OF_PROFILES": values,
    })
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_profiles_trend --plot")
    assert trend_figures[0].axes[0].lines[0].get_ydata().tolist() == values
    assert "(!) Error" not in output.getvalue()


def test_trend_lines_retain_unmapped_namespaces(shell, trend_figures, monkeypatch):
    instance, service, output = shell
    interactive = Mock()
    interactive.queryNamespacesTrend.return_value = pd.DataFrame({
        "DATE_KEY": [20261001, 20261002], "NAMESPACE": [None, None], "COUNT_OF_PROFILES": [10, 20],
    })
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_namespaces_trend --plot")
    line = trend_figures[0].axes[0].lines[0]
    assert line.get_label() == "Unknown"
    assert line.get_ydata().tolist() == [10, 20]
    assert "(!) Error" not in output.getvalue()


def test_namespace_bars_are_sorted_and_scaled_to_the_largest_count(shell, monkeypatch):
    instance, service, output = shell
    interactive = Mock()
    interactive.queryNamespacesDistribution.return_value = pd.DataFrame({
        "NAMESPACE_DESCRIPTION": ["Empty", "CRM", "Email"], "COUNT_OF_PROFILES": [0, 50, 100],
    })
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_namespaces_distribution --plot")
    chart = output.getvalue().split("Namespace profile distribution", 1)[1]
    assert chart.index("Email") < chart.index("CRM") < chart.index("Empty")
    for name, length in [("Email", 30), ("CRM", 15), ("Empty", 0)]:
        line = next(line for line in chart.splitlines() if name in line)
        assert line.count("\u2588") == length


def test_namespace_bars_handle_all_zero_counts_and_literal_names(shell, monkeypatch):
    instance, service, output = shell
    interactive = Mock()
    interactive.queryNamespacesDistribution.return_value = pd.DataFrame({
        "NAMESPACE_DESCRIPTION": ["Email [work]", "CRM"], "COUNT_OF_PROFILES": [0, 0],
    })
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_namespaces_distribution --plot")
    assert "Email [work]" in output.getvalue().split("Namespace profile distribution", 1)[1]
    assert "(!) Error" not in output.getvalue()


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), INTERACTIVE_REPORTS[1:])
def test_report_plots_handle_empty_data(shell, trend_figures, monkeypatch, command, method, kwargs, filename):
    instance, service, output = shell
    interactive = Mock()
    getattr(interactive, method).return_value = pd.DataFrame(columns=["COUNT_OF_PROFILES"])
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd(f"{command} --plot")
    assert "No rows returned." in output.getvalue()
    assert "(!) Error" not in output.getvalue()
    assert not trend_figures
    interactive.close.assert_called_once_with()


@pytest.mark.parametrize(
    "data",
    [
        {"COUNT_OF_PROFILES": [10]},
        {"DATE_KEY": [20261001]},
        {"DATE_KEY": ["invalid"], "COUNT_OF_PROFILES": [10]},
        {"DATE_KEY": [None], "COUNT_OF_PROFILES": [10]},
        *[{"DATE_KEY": [20261001], "COUNT_OF_PROFILES": [value]} for value in [float("nan"), float("inf"), "invalid"]],
    ],
)
def test_plot_errors_are_explicit_and_do_not_lose_the_csv(shell, trend_figures, monkeypatch, tmp_path, data):
    instance, service, output = shell
    interactive = Mock()
    interactive.queryProfilesTrend.return_value = pd.DataFrame(data)
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_profiles_trend --plot")
    assert "(!) Error:" in output.getvalue()
    assert not trend_figures
    assert (tmp_path / "dev_profiles_trend.csv").exists()
    interactive.close.assert_called_once_with()


def test_namespace_bars_support_legacy_windows_encodings(shell, monkeypatch):
    instance, service, output = shell

    class LegacyOutput(StringIO):
        @property
        def encoding(self):
            return "cp1252"

    output = LegacyOutput()
    monkeypatch.setattr(cli, "console", Console(file=output, width=80, color_system=None))
    interactive = Mock()
    data = pd.DataFrame({
        "COUNT_OF_PROFILES": [0, 10], "NAMESPACE_DESCRIPTION": ["Email", "CRM"],
    })
    interactive.queryNamespacesDistribution.return_value = data
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_namespaces_distribution --plot")
    output.getvalue().encode("ascii")
    assert "#" in output.getvalue()
    assert "(!) Error" not in output.getvalue()


def test_trend_lines_preserve_all_observations(shell, trend_figures, monkeypatch):
    instance, service, output = shell
    monkeypatch.setattr(cli, "console", Console(file=output, width=40, color_system=None))
    interactive = Mock()
    interactive.queryProfilesTrend.return_value = pd.DataFrame({
        "DATE_KEY": pd.date_range("2026-01-01", periods=80), "COUNT_OF_PROFILES": list(range(80)),
    })
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_profiles_trend --plot")
    assert trend_figures[0].axes[0].lines[0].get_ydata().tolist() == list(range(80))
    assert "(!) Error" not in output.getvalue()


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), INTERACTIVE_REPORTS[1:])
def test_chart_help_describes_the_plot_option(shell, command, method, kwargs, filename, capsys):
    instance, service, output = shell
    instance.onecmd(f"{command} -h")
    assert "--plot" in capsys.readouterr().out
    cli.queryservice.QueryService.assert_not_called()


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), TREND_REPORTS)
@pytest.mark.parametrize("metric", ["COUNT_OF_IDENTITIES", "count_of_identities"])
def test_trend_metric_selection_uses_the_returned_values(shell, trend_figures, monkeypatch, tmp_path, command, method, kwargs, filename, metric):
    instance, service, output = shell
    result = pd.DataFrame({
        "DATE_KEY": [20261002, 20261001], "COUNT_OF_PROFILES": [10, 20], "COUNT_OF_IDENTITIES": [30, 50],
        "NAMESPACE": ["Email"] * 2, "AUDIENCE_NAME": ["VIP"] * 2, "AUDIENCE_ID": ["audience-1"] * 2,
    })
    interactive = Mock()
    getattr(interactive, method).return_value = result
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd(f"{command} --plot --metric {metric}")
    axes = trend_figures[0].axes[0]
    assert axes.get_ylabel() == "COUNT_OF_IDENTITIES"
    assert axes.lines[0].get_ydata().tolist() == [50, 30]
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / filename), result)
    assert "(!) Error" not in output.getvalue()


def test_trend_metric_accepts_new_numeric_columns_and_decimal_values(shell, trend_figures, monkeypatch):
    instance, service, output = shell
    interactive = Mock()
    interactive.queryProfilesTrend.return_value = pd.DataFrame({
        "DATE_KEY": [20261001, 20261002], "NEW_METRIC": [Decimal("1.5"), Decimal("2.5")],
    })
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd("query_profiles_trend --plot --metric NEW_METRIC")
    axes = trend_figures[0].axes[0]
    assert axes.get_ylabel() == "NEW_METRIC"
    assert axes.lines[0].get_ydata().tolist() == [1.5, 2.5]
    assert "(!) Error" not in output.getvalue()


@pytest.mark.parametrize("metric", ["UNKNOWN", "DATE_KEY", "NAMESPACE", "IS_DEFAULT", '""'])
def test_invalid_trend_metrics_list_available_numeric_columns(shell, trend_figures, monkeypatch, tmp_path, metric):
    instance, service, output = shell
    interactive = Mock()
    interactive.queryProfilesTrend.return_value = pd.DataFrame({
        "DATE_KEY": [20261001], "COUNT_OF_PROFILES": [10], "COUNT_OF_IDENTITIES": [20],
        "NAMESPACE": ["Email"], "IS_DEFAULT": [True],
    })
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    instance.onecmd(f"query_profiles_trend --plot --metric {metric}")
    text = output.getvalue()
    assert "(!) Error:" in text
    assert "Available metrics: COUNT_OF_PROFILES, COUNT_OF_IDENTITIES" in text
    assert not trend_figures
    assert (tmp_path / "dev_profiles_trend.csv").exists()


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), TREND_REPORTS)
def test_trend_metric_requires_plotting(shell, command, method, kwargs, filename, capsys):
    instance, service, output = shell
    instance.onecmd(f"{command} --metric COUNT_OF_IDENTITIES")
    cli.queryservice.QueryService.assert_not_called()
    assert "--metric requires --plot" in capsys.readouterr().err


@pytest.mark.parametrize(("command", "method", "kwargs", "filename"), TREND_REPORTS)
def test_trend_help_describes_metric_selection(shell, command, method, kwargs, filename, capsys):
    instance, service, output = shell
    instance.onecmd(f"{command} -h")
    text = capsys.readouterr().out
    assert "--metric" in text
    assert "COUNT_OF_PROFILES" in text
    cli.queryservice.QueryService.assert_not_called()


def test_trend_window_failures_close_the_figure_and_preserve_the_csv(shell, trend_figures, monkeypatch, tmp_path):
    from matplotlib import pyplot as plt
    instance, service, output = shell
    interactive = Mock()
    interactive.queryProfilesTrend.return_value = pd.DataFrame({"DATE_KEY": [20261001], "COUNT_OF_PROFILES": [10]})
    monkeypatch.setattr(cli.queryservice, "InteractiveQuery2", Mock(return_value=interactive))
    monkeypatch.setattr(plt, "show", Mock(side_effect=RuntimeError("Window unavailable")))
    instance.onecmd("query_profiles_trend --plot")
    assert "(!) Error: Window unavailable" in output.getvalue()
    assert not plt.get_fignums()
    assert (tmp_path / "dev_profiles_trend.csv").exists()
    interactive.close.assert_called_once_with()


@pytest.mark.parametrize(
    ("arguments", "default_only"),
    [
        ("", False),
        ("-d", True),
        ("--defaultOnly", True),
        ("-d True", True),
        ("--defaultOnly True", True),
        ("--defaultOnly true", True),
        ("--defaultOnly TRUE", True),
        ("--defaultOnly=True", True),
        ("-d False", False),
        ("--defaultOnly False", False),
        ("--defaultOnly false", False),
        ("--defaultOnly=False", False),
        ("-d 1", True),
        ("-d 0", False),
    ],
)
def test_snapshot_datasets_accept_optional_boolean(shell, monkeypatch, tmp_path, arguments, default_only):
    instance, service, output = shell
    catalog = Mock()
    catalog.getProfileSnapshotDatasets.return_value = [
        {
            "id": "snapshot-1",
            "mergePolicyName": "Default profile",
            "defaultPolicy": True,
            "tags": {
                "adobe/pqs/table": ["profile_snapshot"],
                "unifiedProfile": ["mergePolicyId:policy-1"],
            },
            "extensions": {"adobe_lakeHouse": {"metrics": {"rowCount": 42}}},
        }
    ]
    monkeypatch.setattr(cli.catalog, "Catalog", Mock(return_value=catalog))

    instance.onecmd(f"get_snapshot_datasets {arguments}")

    catalog.getProfileSnapshotDatasets.assert_called_once_with(
        explicitMergePolicy=True, flatten=True, defaultOnly=default_only
    )
    assert pd.read_csv(tmp_path / "dev_snapshot_datasets.csv")["id"].tolist() == ["snapshot-1"]
    text = output.getvalue()
    assert "snapshot-1" in text
    assert "Row Count" in text
    assert "42" in text
    assert "(!) Error" not in text


@pytest.mark.parametrize("value", ["invalid", "2", '""'])
def test_snapshot_datasets_reject_invalid_boolean(shell, monkeypatch, tmp_path, capsys, value):
    instance, service, output = shell
    catalog_factory = Mock()
    monkeypatch.setattr(cli.catalog, "Catalog", catalog_factory)

    instance.onecmd(f"get_snapshot_datasets --defaultOnly {value}")

    catalog_factory.assert_not_called()
    assert "Boolean value expected." in capsys.readouterr().err
    assert not (tmp_path / "dev_snapshot_datasets.csv").exists()


def test_snapshot_datasets_help_describes_optional_boolean(shell, monkeypatch, capsys):
    instance, service, output = shell
    catalog_factory = Mock()
    monkeypatch.setattr(cli.catalog, "Catalog", catalog_factory)

    instance.onecmd("get_snapshot_datasets -h")

    assert "--defaultOnly [BOOL]" in capsys.readouterr().out
    catalog_factory.assert_not_called()


def test_descriptor_is_displayed_and_optionally_exported(shell, monkeypatch, tmp_path):
    instance, service, output = shell
    schema = Mock()
    descriptor = {"@id": "descriptor-1", "@type": "xdm:descriptorIdentity"}
    schema.getDescriptor.return_value = descriptor
    monkeypatch.setattr(cli.schema, "Schema", Mock(return_value=schema))
    instance.onecmd("get_descriptor descriptor-1")
    assert not (tmp_path / "descriptor_descriptor-1.json").exists()
    instance.onecmd("get_descriptor descriptor-1 -sv")
    schema.getDescriptor.assert_called_with(descriptorId="descriptor-1")
    assert json.loads((tmp_path / "descriptor_descriptor-1.json").read_text()) == descriptor


@pytest.mark.parametrize("identifier", ["dataset-1", '"Dataset name"'])
def test_dataset_lookup_by_name_or_id(shell, monkeypatch, tmp_path, identifier):
    instance, service, output = shell
    catalog = Mock()
    catalog.getDataSets.return_value = [{"id": "dataset-1", "name": "Dataset name"}]
    dataset = {"dataset-1": {"name": "Dataset name"}}
    catalog.getDataSet.return_value = dataset
    monkeypatch.setattr(cli.catalog, "Catalog", Mock(return_value=catalog))
    instance.onecmd(f"get_dataset {identifier}")
    catalog.getDataSet.assert_called_once_with("dataset-1")
    assert json.loads((tmp_path / "dataset_dataset-1.json").read_text()) == dataset


@pytest.mark.parametrize(
    ("command", "module_name", "class_name", "method_name"),
    [
        ("get_descriptor descriptor-1 -sv", "schema", "Schema", "getDescriptor"),
        ("get_dataset dataset-1", "catalog", "Catalog", "getDataSet"),
        ("get_query_template template-1", "queryservice", "QueryService", "getTemplate"),
        ("get_query query-1", "queryservice", "QueryService", "getQuery"),
    ],
)
def test_definition_commands_report_api_errors_without_exporting(shell, monkeypatch, tmp_path, command, module_name, class_name, method_name):
    instance, service, output = shell
    api = Mock()
    api.getDataSets.return_value = [{"id": "dataset-1", "name": "Dataset name"}]
    getattr(api, method_name).return_value = {"errorMessage": "Permission denied"}
    monkeypatch.setattr(getattr(cli, module_name), class_name, Mock(return_value=api))
    instance.onecmd(command)
    assert "(!) Error" in output.getvalue()
    assert "Permission denied" in output.getvalue()
    assert not list(tmp_path.glob("*.json"))


def test_missing_dataset_does_not_retrieve_or_export(shell, monkeypatch, tmp_path):
    instance, service, output = shell
    catalog = Mock()
    catalog.getDataSets.return_value = []
    monkeypatch.setattr(cli.catalog, "Catalog", Mock(return_value=catalog))
    instance.onecmd("get_dataset missing")
    catalog.getDataSet.assert_not_called()
    assert "not found" in output.getvalue()
    assert not list(tmp_path.glob("*.json"))


def test_new_commands_have_grouped_and_detailed_help(shell, capsys):
    instance, service, output = shell
    groups = instance.get_grouped_commands()
    assert set(QUERY_COMMANDS) <= set(groups["Queries"])
    assert "get_descriptor" in groups["Schema"]
    assert "get_dataset" in groups["Datasets"]
    for command in QUERY_COMMANDS:
        instance.onecmd(f"{command} -h")
        assert f"usage: {command}" in capsys.readouterr().out
    cli.queryservice.QueryService.assert_not_called()
