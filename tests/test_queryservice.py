import sys
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest
from requests import Request

from aepp.queryservice import InteractiveQuery, InteractiveQuery2, QueryService


@pytest.fixture
def service():
    instance = QueryService.__new__(QueryService)
    instance.connector = Mock()
    instance.endpoint = "https://platform.adobe.io/data/foundation/query"
    instance.header = {"x-sandbox-name": "dev"}
    return instance


@pytest.mark.parametrize(
    ("method", "key", "path"),
    [("getTemplates", "templates", "/query-templates"), ("getSchedules", "schedules", "/schedules"), ("getQueries", "queries", "/queries")],
)
@pytest.mark.parametrize("link_format", ["object", "string"])
def test_paginated_collections_follow_complete_next_link(service, method, key, path, link_format):
    href = f"{service.endpoint}{path}?start=2026-10-01T12%3A00%3A00Z&limit=1&linkType=next"
    link = {"href": href} if link_format == "object" else href
    service.connector.getData.side_effect = [
        {key: [{"id": "first"}], "_links": {"next": link}},
        {key: [{"id": "second"}]},
    ]
    assert getattr(service, method)(n_results="inf") == [{"id": "first"}, {"id": "second"}]
    last_call = service.connector.getData.call_args
    assert last_call.args[0] == service.endpoint + path
    params = last_call.kwargs["params"]
    query = parse_qs(urlparse(Request("GET", service.endpoint + path, params=params).prepare().url).query)
    assert query["start"] == ["2026-10-01T12:00:00Z"]
    assert query["limit"] == ["1"]
    assert query["linkType"] == ["next"]


@pytest.mark.parametrize(("method", "key"), [("getTemplates", "templates"), ("getSchedules", "schedules"), ("getQueries", "queries")])
def test_collection_limit_is_exact_and_stops_pagination(service, method, key):
    service.connector.getData.return_value = {
        key: [{"id": "first"}, {"id": "second"}],
        "_links": {"next": {"href": f"{service.endpoint}?start=next"}},
    }
    assert getattr(service, method)(n_results=1) == [{"id": "first"}]
    service.connector.getData.assert_called_once()


@pytest.mark.parametrize(("method", "key"), [("getTemplates", "templates"), ("getSchedules", "schedules"), ("getQueries", "queries")])
def test_empty_collections_do_not_require_links(service, method, key):
    service.connector.getData.return_value = {key: []}
    assert getattr(service, method)() == []


@pytest.mark.parametrize("method", ["getTemplates", "getSchedules", "getQueries"])
def test_collection_errors_are_not_silently_empty(service, method):
    service.connector.getData.return_value = {"errorMessage": "Permission denied"}
    with pytest.raises(ValueError, match="Permission denied"):
        getattr(service, method)()


@pytest.mark.parametrize("method", ["getTemplates", "getSchedules", "getQueries"])
def test_ascending_order_and_filters_are_encoded_once(service, method):
    key = {"getTemplates": "templates", "getSchedules": "schedules", "getQueries": "queries"}[method]
    service.connector.getData.return_value = {key: [], "_links": {}}
    property_filter = "created>=2026-10-01T12:00:00Z"
    getattr(service, method)(orderby="+created", property=property_filter)
    params = service.connector.getData.call_args.kwargs["params"]
    query = parse_qs(urlparse(Request("GET", service.endpoint, params=params).prepare().url).query)
    assert query["orderby"] == ["+created"]
    assert query["property"] == [property_filter]


@pytest.mark.parametrize(("method", "action"), [("enableSchedule", "enable"), ("disableSchedule", "disable")])
def test_schedule_state_changes_match_adobe_patch_contract(service, method, action):
    response = {"message": "Request to patch accepted", "statusCode": 202}
    service.connector.patchData.return_value = response
    assert getattr(service, method)(scheduleId="schedule-1") == response
    service.connector.patchData.assert_called_once_with(
        service.endpoint + "/schedules/schedule-1",
        data={"body": [{"op": "replace", "path": "/state", "value": action}]},
        headers=service.header,
    )


def test_create_schedule_forwards_query_and_schedule_payload(service):
    payload = {
        "query": {"dbName": "dev:all", "templateId": "template-1", "queryParameters": {"value": "a=b"}},
        "schedule": {"schedule": "@daily", "startDate": "2026-11-01T00:00:00.000Z"},
    }
    service.connector.postData.return_value = {"id": "schedule-1", "state": "REGISTERING"}
    assert service.createSchedule(scheduleQuery=payload)["id"] == "schedule-1"
    service.connector.postData.assert_called_once_with(service.endpoint + "/schedules", data=payload)


@pytest.mark.parametrize("method", ["getTemplates", "getSchedules", "getQueries"])
@pytest.mark.parametrize("limit", [0, -1, "nan", "1.5"])
def test_collection_rejects_invalid_result_limits(service, method, limit):
    with pytest.raises(ValueError, match="n_results"):
        getattr(service, method)(n_results=limit)
    service.connector.getData.assert_not_called()


@pytest.mark.parametrize(("method", "key"), [("getTemplates", "templates"), ("getSchedules", "schedules"), ("getQueries", "queries")])
def test_collection_detects_repeated_pagination_link(service, method, key):
    service.connector.getData.return_value = {
        key: [{"id": "first"}],
        "_links": {"next": {"href": f"{service.endpoint}?start=unchanged"}},
    }
    with pytest.raises(ValueError, match="repeated pagination"):
        getattr(service, method)(n_results="inf")
    assert service.connector.getData.call_count == 2


@pytest.fixture
def audience_population():
    instance = InteractiveQuery2.__new__(InteractiveQuery2)
    instance.config = SimpleNamespace(sandbox="dev")
    instance.myseg = Mock()
    instance.myseg.getSegment.return_value = {"mergePolicyId": "policy-1"}
    instance.mycat = Mock()
    instance.mycat.getProfileSnapshotDatasets.return_value = {
        "snapshot-1": {
            "tags": {
                "unifiedProfile": ["mergePolicyId:policy-1"],
                "adobe/pqs/table": ["profile_snapshot"],
            },
        },
    }
    instance.query = Mock()
    return instance


@pytest.mark.parametrize(
    ("definition", "expected_count"),
    [
        ({"metrics": {"data": {"totalProfiles": 10}}}, 10),
        ({"metrics": {"data": {"totalProfiles": 0}}}, 0),
        ({}, "No Data Yet"),
    ],
)
def test_audience_population_count_uses_audience_id_without_snapshot_lookup(audience_population, definition, expected_count):
    audience_population.myseg.getSegment.return_value = definition
    result = audience_population.queryAudiencePopulation(audienceId="audience-1", count=True)
    assert result.to_dict("records") == [{"count": expected_count, "audienceId": "audience-1"}]
    audience_population.myseg.getSegment.assert_called_once_with("audience-1")
    audience_population.mycat.getProfileSnapshotDatasets.assert_not_called()
    audience_population.query.assert_not_called()


def test_audience_population_count_combines_audiences_in_order(audience_population):
    audience_population.myseg.getSegment.side_effect = [
        {"metrics": {"data": {"totalProfiles": 10}}},
        {"metrics": {"data": {"totalProfiles": 0}}},
    ]
    result = audience_population.queryAudiencePopulation(audienceId=["audience-1", "audience-2"], count=True)
    assert result.to_dict("records") == [
        {"count": 10, "audienceId": "audience-1"},
        {"count": 0, "audienceId": "audience-2"},
    ]
    assert result.index.tolist() == [0, 1]
    assert [call.args[0] for call in audience_population.myseg.getSegment.call_args_list] == ["audience-1", "audience-2"]
    audience_population.mycat.getProfileSnapshotDatasets.assert_not_called()
    audience_population.query.assert_not_called()


def test_audience_population_count_propagates_api_errors(audience_population):
    audience_population.myseg.getSegment.side_effect = ValueError("Permission denied")
    with pytest.raises(ValueError, match="Permission denied"):
        audience_population.queryAudiencePopulation(audienceId="audience-1", count=True)
    audience_population.mycat.getProfileSnapshotDatasets.assert_not_called()
    audience_population.query.assert_not_called()


@pytest.mark.parametrize(
    ("extra_fields", "expected_selections", "expected_names"),
    [
        (None, [], []),
        ([], [], []),
        ("email", ["email AS email"], ["email"]),
        (["email"], ["email AS email"], ["email"]),
        (["email", "_tenant.score"], ["email AS email", "_tenant.score AS score"], ["email", "score"]),
        ("person.name.firstName", ["person.name.firstName AS first_name"], ["first_name"]),
        (
            ["person.name.firstName", "person.name.lastName", "_tenant.CRMId"],
            ["person.name.firstName AS first_name", "person.name.lastName AS last_name", "_tenant.CRMId AS crm_id"],
            ["first_name", "last_name", "crm_id"],
        ),
    ],
)
def test_audience_population_identity_export_preserves_query_result(audience_population, extra_fields, expected_selections, expected_names):
    expected = pd.DataFrame({"audienceId": ["audience-1"], "id": ["identity-1"]})
    audience_population.query.return_value = expected
    result = audience_population.queryAudiencePopulation(audienceId="audience-1", extraFields=extra_fields)
    assert result is expected
    audience_population.mycat.getProfileSnapshotDatasets.assert_called_once_with()
    audience_population.query.assert_called_once()
    sql = audience_population.query.call_args.args[0]
    assert "FROM profile_snapshot" in sql
    assert "'audience-1' audienceId" in sql
    assert "segmentMembership['ups']['audience-1'].status = 'realized'" in sql
    outer_select, inner_select = sql.split('FROM', 1)
    assert outer_select.split('audienceId', 1)[1].strip() == (
        ', ' + ','.join(expected_names) if expected_names else ''
    )
    for selection in expected_selections:
        assert selection in inner_select
    if extra_fields:
        fields = [extra_fields] if isinstance(extra_fields, str) else extra_fields
        for field in fields:
            if '.' in field:
                assert field not in outer_select


@pytest.mark.parametrize("extra_fields", ["email", ["email"]])
def test_audience_population_identity_export_forwards_fields_for_each_audience(audience_population, extra_fields):
    audience_population.query.side_effect = [
        pd.DataFrame({"audienceId": ["audience-1"], "email": ["first@example.com"]}),
        pd.DataFrame({"audienceId": ["audience-2"], "email": ["second@example.com"]}),
    ]
    result = audience_population.queryAudiencePopulation(audienceId=["audience-1", "audience-2"], extraFields=extra_fields)
    assert result.to_dict("records") == [
        {"audienceId": "audience-1", "email": "first@example.com"},
        {"audienceId": "audience-2", "email": "second@example.com"},
    ]
    assert result.index.tolist() == [0, 1]
    for call, audience_id in zip(audience_population.query.call_args_list, ["audience-1", "audience-2"]):
        assert f"'{audience_id}' audienceId" in call.args[0]
        outer_select, inner_select = call.args[0].split('FROM', 1)
        assert outer_select.split('audienceId', 1)[1].strip() == ', email'
        assert 'email AS email' in inner_select


def test_audience_population_requires_configuration(audience_population):
    audience_population.config = None
    with pytest.raises(Exception, match="Use addConfig"):
        audience_population.queryAudiencePopulation(audienceId="audience-1", count=True)
    audience_population.myseg.getSegment.assert_not_called()


@pytest.fixture(params=[InteractiveQuery, InteractiveQuery2])
def interactive(request):
    instance = request.param.__new__(request.param)
    instance.default_merge_policy_queryId = 42
    instance._mapping_namespace_id_name = {1: "Email", 2: "CRM ID"}
    instance.query = Mock()
    return instance


@pytest.mark.parametrize("interactive_class", [InteractiveQuery, InteractiveQuery2])
def test_interactive_setup_initializes_namespace_mapping(monkeypatch, interactive_class):
    monkeypatch.setitem(sys.modules, "pg", SimpleNamespace(DB=Mock()))
    monkeypatch.setitem(sys.modules, "psycopg2", SimpleNamespace(connect=Mock()))
    responses = [
        pd.DataFrame({"IS_DEFAULT_MERGE_POLICY": [True], "MERGE_POLICY_ID": [42], "MERGE_POLICY": ["policy-1"]}),
        pd.DataFrame({"NAMESPACE_ID": [1, 2], "NAMESPACE_DESCRIPTION": ["Email", "CRM ID"]}),
    ]
    monkeypatch.setattr(interactive_class, "query", Mock(side_effect=responses))
    instance = interactive_class({
        "dbName": "dev:all", "host": "localhost", "port": 5432,
        "username": "test", "token": "test", "websocketHost": "localhost",
    })
    assert instance._mapping_namespace_id_name == {1: "Email", 2: "CRM ID"}
    assert instance.default_merge_policy_queryId == 42
    instance.close()


def test_history_metadata_delegates_to_query(interactive):
    expected = pd.DataFrame({"history_meta": ["snapshot-1"]})
    interactive.query.return_value = expected
    assert interactive.queryHistoryMeta(table="accounts") is expected
    interactive.query.assert_called_once_with("SELECT history_meta('accounts')", output="dataframe")


def test_profiles_trend_is_sorted_and_uses_default_merge_policy(interactive):
    interactive.query.return_value = pd.DataFrame({"DATE_KEY": [20261002, 20261001], "COUNT_OF_PROFILES": [20, 10]})
    result = interactive.queryProfilesTrend()
    assert result["DATE_KEY"].tolist() == [20261001, 20261002]
    sql = interactive.query.call_args.args[0]
    assert "x.merge_policy_id = 42" in sql
    assert "dateadd(DAY, -30" in sql


def test_namespaces_distribution_uses_default_merge_policy(interactive):
    expected = pd.DataFrame({"NAMESPACE": ["Email"], "COUNT_OF_PROFILES": [10]})
    interactive.query.return_value = expected
    assert interactive.queryNamespacesDistribution() is expected
    assert "MERGE_POLICY_ID = 42" in interactive.query.call_args.args[0]


@pytest.mark.parametrize(
    ("namespace", "expected"),
    [(None, ["CRM ID", "Email"]), ("email", ["Email"]), ("EMAIL", ["Email"]), ("crm id", ["CRM ID"]), ("missing", [])],
)
def test_namespace_trend_sql_mapping_and_case_insensitive_filter(interactive, namespace, expected):
    interactive.query.return_value = pd.DataFrame({
        "DATE_KEY": [20261002, 20261001], "NAMESPACE_ID": [1, 2],
        "COUNT_OF_PROFILES": [10, 20], "COUNT_OF_IDENTITIES": [15, 30],
        "COUNT_OF_SINGLE_IDENTITY_PROFILES": [5, 8],
    })
    result = interactive.queryNamespacesTrend(namespace=namespace)
    assert interactive.query.call_args.args[0].strip().startswith("SELECT ")
    assert "MERGE_POLICY_ID = 42" in interactive.query.call_args.args[0]
    assert result["NAMESPACE"].tolist() == expected
    assert result.columns.tolist() == [
        "DATE_KEY", "NAMESPACE", "COUNT_OF_PROFILES", "COUNT_OF_IDENTITIES", "COUNT_OF_SINGLE_IDENTITY_PROFILES",
    ]


@pytest.mark.parametrize(
    ("segment", "expected"),
    [(None, ["VIP Customers", "Prospects"]), ("vip customers", ["VIP Customers"]), ("AUDIENCE-2", ["Prospects"]), ("missing", [])],
)
def test_segment_trend_maps_names_and_ids_and_preserves_selected_metrics(interactive, segment, expected):
    interactive.query.side_effect = [
        pd.DataFrame({
            "DATE_KEY": [20261001, 20261002], "SEGMENT_ID": [1, 2],
            "COUNT_OF_PROFILES": [10, 20], "COUNT_OF_IDENTITIES": [15, 30],
            "COUNT_OF_CALCULATED_REALIZED_PROFILES": [6, 12],
            "COUNT_OF_CALCULATED_EXISTING_PROFILES": [3, 5],
            "COUNT_OF_CALCULATED_EXITED_PROFILES": [1, 3],
        }),
        pd.DataFrame({"SEGMENT_ID": [1, 2], "SEGMENT": ["audience-1", "audience-2"], "SEGMENT_NAME": ["VIP Customers", "Prospects"]}),
    ]
    result = interactive.querySegmentPopulationTrend(segment=segment)
    assert result["SEGMENT_NAME"].tolist() == expected
    assert result.columns.tolist() == [
        "DATE_KEY", "SEGMENT_NAME", "AUDIENCE_ID", "COUNT_OF_PROFILES", "COUNT_OF_IDENTITIES",
        "COUNT_OF_CALCULATED_REALIZED_PROFILES", "COUNT_OF_CALCULATED_EXISTING_PROFILES", "COUNT_OF_CALCULATED_EXITED_PROFILES",
    ]
    assert "MERGE_POLICY_ID = 42" in interactive.query.call_args_list[0].args[0]


@pytest.mark.parametrize("method", ["queryProfilesTrend", "queryNamespacesTrend", "querySegmentPopulationTrend"])
def test_trend_methods_accept_empty_query_results(interactive, method):
    interactive.query.return_value = pd.DataFrame()
    assert getattr(interactive, method)().empty
    interactive.query.assert_called_once()


def test_namespace_filter_accepts_unmapped_namespace(interactive):
    interactive.query.return_value = pd.DataFrame({
        "DATE_KEY": [20261001], "NAMESPACE_ID": [99], "COUNT_OF_PROFILES": [10],
        "COUNT_OF_IDENTITIES": [15], "COUNT_OF_SINGLE_IDENTITY_PROFILES": [5],
    })
    assert interactive.queryNamespacesTrend(namespace="Email").empty


def test_segment_filter_accepts_empty_segment_mapping(interactive):
    interactive.query.side_effect = [
        pd.DataFrame({
            "DATE_KEY": [20261001], "SEGMENT_ID": [99], "COUNT_OF_PROFILES": [10], "COUNT_OF_IDENTITIES": [15],
            "COUNT_OF_CALCULATED_REALIZED_PROFILES": [6], "COUNT_OF_CALCULATED_EXISTING_PROFILES": [3],
            "COUNT_OF_CALCULATED_EXITED_PROFILES": [1],
        }),
        pd.DataFrame(),
    ]
    assert interactive.querySegmentPopulationTrend(segment="missing").empty
