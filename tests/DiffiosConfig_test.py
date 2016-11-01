#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

import pytest

THIS_DIR = os.path.dirname(__file__)
sys.path.append(os.path.abspath("."))

from diffios import DiffiosConfig


def test_default_ignore_filename(dc):
    expected = os.path.join(os.getcwd(), "diffios_ignore")
    actual = dc.ignore_filename
    assert expected == actual


def test_alternative_ignore_filename(config):
    alt_ignore_path = os.path.join(THIS_DIR, "alt_diffios_ignore")
    actual = DiffiosConfig(config, ignores=alt_ignore_path).ignore_filename
    assert alt_ignore_path == actual


def test_raises_error_if_ignore_file_does_not_exist(config):
    with pytest.raises(RuntimeError):
        DiffiosConfig(config, ignores="alt_ignore_file")


def test_ignore_filename_is_None_if_ignores_is_False(config):
    assert DiffiosConfig(config, ignores=False).ignore_filename is None


def test_ignore_filename_is_None_if_ignores_is_empty_list(config):
    assert DiffiosConfig(config, ignores=[]).ignore_filename is None


def test_ignore_filename_is_None_if_ignores_is_empty_string(config):
    assert DiffiosConfig(config, ignores="").ignore_filename is None


def test_ignore_filename_is_None_if_ignores_is_zero(config):
    assert DiffiosConfig(config, ignores=0).ignore_filename is None


def test_config_filename(dc, config):
    assert dc.config_filename == config


def test_config(dc, config):
    pytest.skip('config property now removes invalid lines')
    expected = [l.rstrip() for l in open(config).readlines()]
    assert expected, dc.config


def test_hostname(dc):
    assert "BASELINE01" == dc.hostname


def test_blocks(dc, baseline_blocks):
    assert baseline_blocks == dc.config_blocks


def test_ignore_lines(dc):
    ignore_file = open("diffios_ignore").readlines()
    expected = [l.strip().lower() for l in ignore_file]
    assert expected == dc.ignores


def test_ignored(dc, baseline_partition):
    expected = baseline_partition.ignored
    assert expected == dc.ignored


def test_recorded(dc, baseline_partition):
    expected = baseline_partition.recorded
    assert expected == dc.recorded


def test_parent_line_is_ignored():
    config = ['hostname ROUTER']
    ignores = ['hostname']
    d = DiffiosConfig(config=config, ignores=ignores)
    assert d.recorded == []
    assert d.ignored == [['hostname ROUTER']]


def test_child_line_is_ignored():
    config = [
        'interface FastEthernet0/1',
        ' description **Link to Core**',
        ' ip address 192.168.0.1 255.255.255.0'
    ]
    ignores = [' description']
    d = DiffiosConfig(config=config, ignores=ignores)
    assert d.recorded == [['interface FastEthernet0/1',
                           ' ip address 192.168.0.1 255.255.255.0']]
    assert d.ignored == [' description **Link to Core**']
