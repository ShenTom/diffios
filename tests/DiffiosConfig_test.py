#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
try:
    from unittest import mock
except ImportError:
    from mock import mock

import pytest

THIS_DIR = os.path.dirname(__file__)
sys.path.append(os.path.abspath("."))

from diffios import DiffiosConfig


DEFAULT_IGNORES_FILENAME = 'diffios_ignore'


def test_raises_error_if_config_not_given():
    """
    Should raise TypeError if no config parameter is given.
    """
    with pytest.raises(TypeError):
        DiffiosConfig()


def test_raises_error_if_not_config_file_does_not_exist():
    """
    Should raise Runtime Error if given config file does not exist.
    """
    with pytest.raises(RuntimeError):
        DiffiosConfig('file_that_does_not_exist')


def test_raises_error_if_config_file_is_dir():
    """
    Should Raise Runtime Error if config file is not a file.
    """
    with pytest.raises(RuntimeError):
        DiffiosConfig(os.getcwd())


def test_raises_error_if_provided_ignore_file_does_not_exist():
    """
    Should raise Runtime Error if given ignores file does not exist.
    """
    config = ['hostname ROUTER']
    with pytest.raises(RuntimeError):
        DiffiosConfig(config, ignores='file_that_does_not_exist')


def test_uses_default_ignores_file_if_it_exists(ignores_file):
    """
    Should use the default ignores file if it exists.
    """
    config = ['hostname ROUTER']
    ignores_data = mock.mock_open(read_data=ignores_file)
    expected = ignores_file.lower().split('\n')
    with mock.patch('diffios.os.path') as mock_path:
        mock_path.exists.return_value = True
        with mock.patch('diffios.open', ignores_data, create=True) as mock_open:
            actual = DiffiosConfig(config).ignores
            mock_open.assert_called_once_with(os.path.join(os.getcwd(), DEFAULT_IGNORES_FILENAME))
            assert expected == actual


def test_ignores_is_empty_list_if_no_default_ignore_file():
    """
    Ignores should be empty if there is no default ignores file,
    and no ignores parameter is passed.
    """
    with mock.patch('diffios.os.path') as mock_path:
        mock_path.exists.return_value = False
        config = ['hostname ROUTER']
        assert DiffiosConfig(config).ignores == []


def test_ignores_is_empty_list_if_passed_empty_list():
    """
    Ignores attribute should be an empty list if ignores parameter
    is an empty list, to avoid default ignores file.
    """
    config = ['hostname ROUTER']
    assert DiffiosConfig(config, ignores=[]).ignores == []


def test_config(baseline, baseline_config):
    """
    Config attribute should return the config with invalid lines removed.
    """
    config = baseline.split('\n')
    expected = baseline_config.split('\n')
    assert expected == DiffiosConfig(config).config


def test_hostname_when_present():
    """
    Should return device hostname if present in the given config.
    """
    config = ['!', 'hostname ROUTER', 'ip default-gateway 192.168.0.1']
    assert "ROUTER" == DiffiosConfig(config).hostname


def test_hostname_is_None_when_not_present():
    """
    Should return None if no hostname found in given config.
    """
    config = ['!', 'ip default-gateway 192.168.0.1']
    assert DiffiosConfig(config).hostname is None


def test_config_blocks_with_list():
    """
    Should return valid config as list of hierarchical blocks,
    from a config given as a list.
    """
    config = [
        'interface Vlan1',
        ' no ip address',
        ' shutdown',
        'hostname ROUTER',
        'interface Vlan2',
        ' ip address 192.168.0.1 255.255.255.0',
        ' no shutdown']
    blocks = sorted([
        ['interface Vlan1', ' no ip address', ' shutdown'],
        ['hostname ROUTER'],
        ['interface Vlan2',
         ' ip address 192.168.0.1 255.255.255.0',
         ' no shutdown']])
    assert blocks == DiffiosConfig(config, ignores=[]).config_blocks


def test_config_blocks_with_file(baseline, baseline_blocks):
    """
    Should return valid config as list of hierarchical blocks,
    from a config given in a file.
    """
    with mock.patch('diffios.os.path.isfile') as mock_isfile:
        mock_isfile.return_value = True
        config_data = mock.mock_open(read_data=baseline)
        with mock.patch('diffios.open', config_data, create=True) as mock_open:
            actual = DiffiosConfig('baseline.conf', ignores=[]).config_blocks
            mock_open.assert_called_once_with('baseline.conf')
            assert baseline_blocks == actual


def test_ignore_lines_from_file(ignores_file):
    """
    Should return the lines in the given ignores file as list of lowercase strings.
    """
    config = ['hostname ROUTER']
    expected = ignores_file.lower().split('\n')
    ignores_data = mock.mock_open(read_data=ignores_file)
    with mock.patch('diffios.os.path.isfile') as mock_isfile:
        mock_isfile.return_value = True
        with mock.patch('diffios.open', ignores_data, create=True) as mock_open:
            actual = DiffiosConfig(config, ignores='ignores_file').ignores
            mock_open.assert_called_once_with('ignores_file')
            assert expected == actual


def test_ignore_lines_from_list(ignores_file):
    """
    Should return the lines in the given ignores list as list of lowercase strings.
    """
    config = ['hostname ROUTER']
    expected = ignores_file.lower().split('\n')
    actual = DiffiosConfig(config, ignores=ignores_file.split('\n')).ignores
    assert expected == actual


def test_ignored(ignores_file, baseline_config, ignored):
    """
    Should return list of hierarchical blocks from config
    that are being ignored.
    """
    ignores = ignores_file.split('\n')
    config = baseline_config.split('\n')
    expected = ignored
    actual = DiffiosConfig(config, ignores).ignored
    assert expected == actual


def test_recorded(ignores_file, baseline_config, recorded):
    """
    Should return list of hierarchical blocks from config
    that are not being ignored.
    """
    ignores = ignores_file.split('\n')
    config = baseline_config.split('\n')
    expected = recorded
    actual = DiffiosConfig(config, ignores).recorded
    assert expected == actual


def test_parent_line_is_ignored():
    """
    Should ignore single line.
    """
    config = ['!', 'hostname ROUTER']
    ignores = ['hostname']
    d = DiffiosConfig(config=config, ignores=ignores)
    assert d.config == ['hostname ROUTER']
    assert d.recorded == []
    assert d.ignored == [['hostname ROUTER']]


def test_child_line_is_ignored():
    """
    Should ignore only line within a hierarchical block.
    """
    config = [
        '!',
        'interface FastEthernet0/1',
        ' description **Link to Core**',
        ' ip address 192.168.0.1 255.255.255.0',
        '!'
    ]
    ignores = [' description']
    d = DiffiosConfig(config=config, ignores=ignores)
    assert d.config == [
        'interface FastEthernet0/1',
        ' description **Link to Core**',
        ' ip address 192.168.0.1 255.255.255.0'
    ]
    assert d.recorded == [['interface FastEthernet0/1',
                           ' ip address 192.168.0.1 255.255.255.0']]
    assert d.ignored == [[' description **Link to Core**']]


def test_whole_block_is_ignored():
    """
    Should ignore whole block if parent line is in ignores list.
    """
    config = [
        'hostname ROUTER',
        '!',
        'interface FastEthernet0/1',
        ' description **Link to Core**',
        ' ip address 192.168.0.1 255.255.255.0',
        '!'
    ]
    ignores = ['fastethernet0/1']
    d = DiffiosConfig(config=config, ignores=ignores)
    assert d.config == [
        'hostname ROUTER',
        'interface FastEthernet0/1',
        ' description **Link to Core**',
        ' ip address 192.168.0.1 255.255.255.0',
    ]
    assert d.ignored == [[
        'interface FastEthernet0/1',
        ' description **Link to Core**',
        ' ip address 192.168.0.1 255.255.255.0',
    ]]
    assert d.recorded == [['hostname ROUTER']]
