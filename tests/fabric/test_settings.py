from unittest import mock

import pytest

from nephos.fabric.settings import check_cluster, get_namespace, load_config


class TestCheckCluster:
    @mock.patch('nephos.fabric.settings.context_get')
    def test_check_cluster(self, mock_context_get):
        mock_context_get.side_effect = [
            {'context': {'cluster': 'a-cluster'}}
        ]
        check_cluster('a-cluster')
        mock_context_get.assert_called_once_with()

    @mock.patch('nephos.fabric.settings.context_get')
    def test_check_cluster_fail(self, mock_context_get):
        with pytest.raises(ValueError):
            check_cluster('a-cluster')
        mock_context_get.side_effect = [
            {'context': {'cluster': 'another-cluster'}}
        ]
        mock_context_get.assert_called_once_with()


class TestGetNamespace:
    OPTS = {
        'core': {'namespace': 'core-namespace'},
        'msps': {
            'namespaced_MSP': {'namespace': 'msp-namespace'},
            'core_MSP': {}
        },
        'cas': {
            'a-ca': {'namespace': 'ca-namespace'},
            'core-ca': {}
        }
    }

    def test_get_namespace_empty(self):
        result = get_namespace(self.OPTS)
        assert result == 'core-namespace'

    def test_get_namespace_msp(self):
        result = get_namespace(self.OPTS, 'namespaced_MSP')
        assert result == 'msp-namespace'

    def test_get_namespace_msp_core(self):
        result = get_namespace(self.OPTS, 'core_MSP')
        assert result == 'core-namespace'

    def test_get_namespace_msp_error(self):
        with pytest.raises(KeyError):
            get_namespace(self.OPTS, 'nonexistent_MSP')

    def test_get_namespace_ca(self):
        result = get_namespace(self.OPTS, ca='a-ca')
        assert result == 'ca-namespace'

    def test_get_namespace_ca_core(self):
        result = get_namespace(self.OPTS, ca='core-ca')
        assert result == 'core-namespace'

    def test_get_namespace_ca_error(self):
        with pytest.raises(KeyError):
            get_namespace(self.OPTS, ca='nonexistent-ca')


class TestLoadHlfConfig:
    @mock.patch('nephos.fabric.settings.yaml')
    @mock.patch('nephos.fabric.settings.path')
    @mock.patch('nephos.fabric.settings.open')
    @mock.patch('nephos.fabric.settings.check_cluster')
    def test_load_config(self, mock_check_cluster, mock_open, mock_path, mock_yaml):
        mock_yaml.load.side_effect = [
            {
                'core': {
                    'chart_repo': 'a-repo',
                    'cluster': 'a-cluster',
                    'dir_config': './a_dir',
                    'dir_values': './another_dir'
                }
             }
        ]
        mock_path.isdir.side_effect = [False]
        mock_path.abspath.side_effect = ['/home/user/a_dir', '/home/user/another_dir']
        load_config('./some_settings.yaml')
        mock_open.assert_called_once_with('./some_settings.yaml')
        mock_yaml.load.assert_called_once()
        mock_check_cluster.assert_called_once_with('a-cluster')
        mock_path.isdir.assert_called_once_with('a-repo')
        assert mock_path.expanduser.call_count == 2
        assert mock_path.abspath.call_count == 2

    @mock.patch('nephos.fabric.settings.yaml')
    @mock.patch('nephos.fabric.settings.path')
    @mock.patch('nephos.fabric.settings.open')
    @mock.patch('nephos.fabric.settings.check_cluster')
    def test_load_config_repodir(self, mock_check_cluster, mock_open, mock_path, mock_yaml):
        mock_yaml.load.side_effect = [
            {
                'core': {
                    'chart_repo': './a_repo_dir',
                    'dir_config': './a_dir',
                    'dir_values': './another_dir'
                }
            }
        ]
        mock_path.isdir.side_effect = [True]
        mock_path.abspath.side_effect = ['/home/user/a_repo_dir', '/home/user/a_dir', '/home/user/another_dir']
        load_config('./some_settings.yaml')
        mock_open.assert_called_once_with('./some_settings.yaml')
        mock_yaml.load.assert_called_once()
        mock_check_cluster.assert_not_called()
        mock_path.isdir.assert_called_once_with('./a_repo_dir')
        assert mock_path.expanduser.call_count == 3
        assert mock_path.abspath.call_count == 3
