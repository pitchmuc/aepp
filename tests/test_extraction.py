import json
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import aepp
from aepp import catalog, customerprofile, datatypemanager, fieldgroupmanager, identity, schema, schemamanager, tags


@pytest.fixture
def extraction_apis(monkeypatch):
    schema_api = Mock()
    schema_api.getTenantId.return_value = 'tenant'
    schema_api.getSchemas.return_value = [{'$id': 'tenant/schema'}]
    schema_api.getSchema.return_value = {'title': 'Schema'}
    schema_api.getFieldGroups.return_value = [{'$id': 'tenant/fieldgroup'}]
    schema_api.getFieldGroupsGlobal.return_value = []
    schema_api.getFieldGroup.return_value = {'title': 'FieldGroup'}
    schema_api.getDataTypes.return_value = [{'$id': 'tenant/datatype'}]
    schema_api.getDataTypesGlobal.return_value = []
    schema_api.getDataType.return_value = {'title': 'DataType'}
    schema_api.getClasses.return_value = [{'$id': 'tenant/class'}]
    schema_api.getClassesGlobal.return_value = []
    schema_api.getClass.return_value = {
        'title': 'Class',
        'meta:extends': ['https://ns.adobe.com/xdm/data/record'],
    }
    schema_api.getBehavior.return_value = {'title': 'Record'}
    monkeypatch.setattr(schema, 'Schema', Mock(return_value=schema_api))

    schema_manager = SimpleNamespace(
        fieldGroupIds=['tenant/fieldgroup'],
        classId='tenant/class',
        getDescriptors=Mock(return_value=[]),
    )
    monkeypatch.setattr(schemamanager, 'SchemaManager', Mock(return_value=schema_manager))
    fieldgroup_manager = SimpleNamespace(
        dataTypes={'tenant/datatype': {}},
        classIds=[],
        getDescriptors=Mock(return_value=[]),
    )
    monkeypatch.setattr(fieldgroupmanager, 'FieldGroupManager', Mock(return_value=fieldgroup_manager))
    monkeypatch.setattr(datatypemanager, 'DataTypeManager', Mock(return_value=SimpleNamespace(dataTypes={})))

    catalog_api = Mock()
    catalog_api.getDataSets.return_value = {
        'dataset-id': {'name': 'Dataset', 'schemaRef': {'id': 'tenant/schema'}},
    }
    monkeypatch.setattr(catalog, 'Catalog', Mock(return_value=catalog_api))
    tags_api = Mock()
    tags_api.getTags.return_value = []
    monkeypatch.setattr(tags, 'Tags', Mock(return_value=tags_api))
    return SimpleNamespace(
        sandbox=SimpleNamespace(org_id='org', sandbox='sandbox'),
        schema_api=schema_api,
        schema_manager=schema_manager,
    )


@pytest.mark.parametrize('artifact_type,artifact', [('schema', 'tenant/schema'), ('dataset', 'dataset-id')])
@pytest.mark.parametrize('verbose', [None, False, True])
def test_extract_artifact_writes_dependencies(tmp_path, extraction_apis, capsys, artifact_type, artifact, verbose):
    options = {} if verbose is None else {'verbose': verbose}
    aepp.extractSandboxArtifact(
        extraction_apis.sandbox, tmp_path, artifact, artifact_type, retry=7, **options
    )

    for folder, title in [
        ('schema', 'Schema'),
        ('fieldgroup', 'FieldGroup'),
        ('datatype', 'DataType'),
        ('class', 'Class'),
        ('behaviour', 'Record'),
    ]:
        definition = json.loads((tmp_path / folder / f'{title}.json').read_text())
        assert definition['title'] == title
    if artifact_type == 'dataset':
        assert (tmp_path / 'dataset' / 'Dataset.json').is_file()
    output = capsys.readouterr().out
    if verbose:
        assert 'Extracting schema tenant/schema' in output
        assert 'Extracting field group tenant/fieldgroup' in output
        assert 'Extracting data type tenant/datatype' in output
    else:
        assert output == ''
    for call in schema.Schema.call_args_list[1:]:
        assert call.kwargs['retry'] == 7


@pytest.mark.parametrize('helper', ['__extractFieldGroup__', '__extractDataType__'])
@pytest.mark.parametrize('verbose', [False, True])
def test_extract_artifact_propagates_worker_errors(tmp_path, extraction_apis, monkeypatch, helper, verbose):
    monkeypatch.setattr(aepp, helper, Mock(side_effect=RuntimeError('dependency failed')))
    with pytest.raises(RuntimeError, match='dependency failed'):
        aepp.extractSandboxArtifact(
            extraction_apis.sandbox, tmp_path, 'tenant/schema', 'schema', verbose=verbose
        )


def test_extract_schema_handles_circular_relationship(tmp_path, extraction_apis):
    extraction_apis.schema_manager.getDescriptors.return_value = [
        {'@id': 'relationship', 'xdm:destinationSchema': 'tenant/schema'},
    ]
    aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, 'tenant/schema', 'schema')
    extraction_apis.schema_api.getSchema.assert_called_once()
    assert (tmp_path / 'descriptor' / 'relationship.json').is_file()


def test_extract_artifact_deduplicates_shared_dependencies(tmp_path, extraction_apis):
    extraction_apis.schema_manager.fieldGroupIds = [
        'tenant/fieldgroup', 'FieldGroup', '_tenant.fieldgroup',
    ]
    extraction_apis.schema_api.getFieldGroups.return_value = [
        {'$id': 'tenant/fieldgroup', 'title': 'FieldGroup', 'meta:altId': '_tenant.fieldgroup'},
    ]
    extraction_apis.schema_api.getDataTypes.return_value = [
        {'$id': 'tenant/datatype', 'title': 'DataType', 'meta:altId': '_tenant.datatype'},
    ]
    fieldgroupmanager.FieldGroupManager.return_value.dataTypes = {
        'tenant/datatype': {}, 'DataType': {}, '_tenant.datatype': {},
    }
    fieldgroupmanager.FieldGroupManager.return_value.classIds = ['tenant/class']

    aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, 'tenant/schema', 'schema')

    for method in ['getFieldGroup', 'getDataType', 'getClass', 'getBehavior',
                   'getFieldGroups', 'getDataTypes', 'getClasses']:
        getattr(extraction_apis.schema_api, method).assert_called_once()
    fieldgroupmanager.FieldGroupManager.assert_called_once()
    datatypemanager.DataTypeManager.assert_called_once()


def test_extract_artifact_shares_dependencies_between_parallel_workers(tmp_path, extraction_apis):
    extraction_apis.schema_manager.fieldGroupIds = ['tenant/first', 'tenant/second']
    extraction_apis.schema_api.getFieldGroups.return_value = [
        {'$id': 'tenant/first'}, {'$id': 'tenant/second'},
    ]
    extraction_apis.schema_api.getFieldGroup.side_effect = lambda resource_id, **kwargs: {
        'title': resource_id.rsplit('/', 1)[-1],
    }
    fieldgroup_manager = fieldgroupmanager.FieldGroupManager.return_value
    fieldgroup_manager.classIds = ['tenant/class']
    workers_ready = Barrier(2)

    def create_fieldgroup_manager(*args, **kwargs):
        workers_ready.wait(timeout=5)
        return fieldgroup_manager

    fieldgroupmanager.FieldGroupManager.side_effect = create_fieldgroup_manager

    aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, 'tenant/schema', 'schema')

    assert extraction_apis.schema_api.getFieldGroup.call_count == 2
    extraction_apis.schema_api.getDataTypes.assert_called_once()
    extraction_apis.schema_api.getDataType.assert_called_once()
    extraction_apis.schema_api.getClass.assert_called_once()
    extraction_apis.schema_api.getBehavior.assert_called_once()
    for title in ['first', 'second']:
        assert (tmp_path / 'fieldgroup' / f'{title}.json').is_file()


def test_extract_datatype_handles_circular_dependencies(tmp_path, extraction_apis):
    extraction_apis.schema_api.getDataTypes.return_value = [
        {'$id': 'tenant/first', 'meta:altId': '_tenant.first'},
        {'$id': 'tenant/second', 'meta:altId': '_tenant.second'},
    ]
    extraction_apis.schema_api.getDataType.side_effect = lambda resource_id, **kwargs: {
        'title': resource_id.rsplit('/', 1)[-1],
    }
    dependencies = {'tenant/first': '_tenant.second', 'tenant/second': '_tenant.first'}
    datatypemanager.DataTypeManager.side_effect = lambda resource_id, **kwargs: SimpleNamespace(
        dataTypes={dependencies[resource_id]: {}},
    )

    aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, '_tenant.first', 'datatype')

    assert extraction_apis.schema_api.getDataType.call_count == 2
    assert datatypemanager.DataTypeManager.call_count == 2
    extraction_apis.schema_api.getDataTypes.assert_called_once()
    for title in ['first', 'second']:
        assert (tmp_path / 'datatype' / f'{title}.json').is_file()


def test_extract_mergepolicy_shares_schema_and_preserves_cached_datasets(tmp_path, extraction_apis, monkeypatch):
    datasets = {
        'dataset-id': {
            'name': 'Dataset', 'schemaRef': {'id': 'tenant/schema'}, 'unifiedTags': ['tag-id'],
        },
        'other-dataset-id': {'name': 'Other', 'schemaRef': {'id': 'tenant/schema'}},
    }
    catalog.Catalog.return_value.getDataSets.return_value = datasets
    tags.Tags.return_value.getTags.return_value = [{'id': 'tag-id', 'name': 'Tag'}]
    profile_api = Mock()
    profile_api.getMergePolicies.return_value = [{
        'id': 'mergepolicy-id',
        'attributeMerge': {
            'type': 'dataSetPrecedence',
            'order': ['dataset-id', 'Dataset', 'other-dataset-id'],
        },
    }]
    monkeypatch.setattr(customerprofile, 'Profile', Mock(return_value=profile_api))

    aepp.extractSandboxArtifact(
        extraction_apis.sandbox, tmp_path, 'mergepolicy-id', 'mergepolicy', retry=7,
    )

    catalog.Catalog.return_value.getDataSets.assert_called_once()
    extraction_apis.schema_api.getSchema.assert_called_once()
    extraction_apis.schema_api.getClass.assert_called_once()
    for call in schema.Schema.call_args_list:
        assert call.kwargs['retry'] == 7
    assert datasets['dataset-id']['unifiedTags'] == ['tag-id']
    assert 'id' not in datasets['dataset-id']
    saved_dataset = json.loads((tmp_path / 'dataset' / 'Dataset.json').read_text())
    assert saved_dataset['unifiedTags'] == ['Tag']
    assert (tmp_path / 'dataset' / 'Other.json').is_file()


def test_extract_artifact_writes_shared_descriptors_and_identities_once(tmp_path, extraction_apis, monkeypatch):
    descriptor = {
        '@id': 'shared', '@type': 'xdm:descriptorIdentity', 'xdm:namespace': 'email',
    }
    fieldgroupmanager.FieldGroupManager.return_value.getDescriptors.return_value = [descriptor]
    extraction_apis.schema_manager.getDescriptors.return_value = [
        descriptor,
        {'@id': 'other', '@type': 'xdm:descriptorIdentity', 'xdm:namespace': 'Email Address'},
    ]
    identity_definition = {'code': 'Email', 'name': 'Email Address'}
    identity_api = Mock()
    identity_api.getIdentities.return_value = [identity_definition]
    monkeypatch.setattr(identity, 'Identity', Mock(return_value=identity_api))
    dump = Mock(wraps=json.dump)
    monkeypatch.setattr(aepp.json, 'dump', dump)

    aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, 'tenant/schema', 'schema')

    identity_api.getIdentities.assert_called_once()
    written_definitions = [call.args[0] for call in dump.call_args_list]
    assert written_definitions.count(descriptor) == 1
    assert written_definitions.count(identity_definition) == 1
    assert (tmp_path / 'identity' / 'Email.json').is_file()


def test_extract_artifact_shares_behaviour_between_distinct_classes(tmp_path, extraction_apis):
    extraction_apis.schema_api.getClasses.return_value = [
        {'$id': 'tenant/class'}, {'$id': 'tenant/other-class'},
    ]
    extraction_apis.schema_api.getClass.side_effect = lambda resource_id, **kwargs: {
        'title': resource_id.rsplit('/', 1)[-1],
        'meta:extends': ['https://ns.adobe.com/xdm/data/record'],
    }
    fieldgroupmanager.FieldGroupManager.return_value.classIds = ['tenant/other-class']

    aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, 'tenant/schema', 'schema')

    assert extraction_apis.schema_api.getClass.call_count == 2
    extraction_apis.schema_api.getClasses.assert_called_once()
    extraction_apis.schema_api.getBehavior.assert_called_once()
    for title in ['class', 'other_class']:
        assert (tmp_path / 'class' / f'{title}.json').is_file()


@pytest.mark.parametrize('first_fails', [False, True])
def test_extract_artifact_starts_fresh_on_each_call(tmp_path, extraction_apis, first_fails):
    if first_fails:
        extraction_apis.schema_api.getDataType.side_effect = RuntimeError('dependency failed')
        with pytest.raises(RuntimeError, match='dependency failed'):
            aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, 'tenant/schema', 'schema')
        extraction_apis.schema_api.getDataType.side_effect = None
    else:
        aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, 'tenant/schema', 'schema')

    aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, 'tenant/schema', 'schema')

    assert extraction_apis.schema_api.getSchema.call_count == 2
    assert extraction_apis.schema_api.getFieldGroup.call_count == 2
    assert extraction_apis.schema_api.getDataType.call_count == 2
    assert extraction_apis.schema_api.getDataTypes.call_count == 2
    assert (tmp_path / 'datatype' / 'DataType.json').is_file()


@pytest.mark.parametrize('artifact', ['http://schema.org/GeoShape', '_schema.org.GeoShape'])
def test_extract_datatype_deduplicates_geometry_aliases(tmp_path, extraction_apis, artifact):
    extraction_apis.schema_api.getDataTypes.return_value = []
    extraction_apis.schema_api.getDataTypesGlobal.return_value = [{
        '$id': 'http://schema.org/GeoShape', 'meta:altId': '_schema.org.GeoShape',
    }]
    datatypemanager.DataTypeManager.return_value.dataTypes = {'http://schema.org/GeoShape': {}}

    aepp.extractSandboxArtifact(extraction_apis.sandbox, tmp_path, artifact, 'datatype')

    extraction_apis.schema_api.getDataType.assert_called_once_with(
        '_schema.org.GeoShape', full=True, xtype='xed',
    )
    datatypemanager.DataTypeManager.assert_called_once()
    assert (tmp_path / 'datatype' / 'global' / 'DataType.json').is_file()