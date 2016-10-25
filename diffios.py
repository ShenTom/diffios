#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
from collections import namedtuple


PARTIALS = [
    "^(?P<non_var> ip address )\d+\.\d+\.\d+\.\d+\s\d+\.\d+\.\d+\.\d+",
    "^(?P<non_var> description ).+",
    "(?P<non_var>ip dhcp snooping vlan ).+",
    "(?P<non_var>ip default-gateway ).+",
    "(?P<non_var>switchport trunk allowed vlan ).+"
]


class DiffiosConfig(object):

    """TODO: Docstring for DiffiosConf. """

    def __init__(self, config, ignores=None):
        """TODO: Docstring for __init__.

        Args:
            config_filename (TODO): TODO

        Kwargs:
            ignore_filename (TODO): TODO

        Returns: TODO

        """
        self.ignore_filename = False
        self.config_filename = False
        self.ignores = None
        self.config = None

        if ignores is None:
            if os.path.exists(os.path.join(os.getcwd(), "diffios_ignore")):
                ignores = os.path.join(os.getcwd(), "diffios_ignore")
            else:
                ignores = None

        if bool(ignores):
            if isinstance(ignores, list):
                self.ignores = ignores
            elif os.path.isfile(os.path.abspath(ignores)):
                try:
                    with open(os.path.abspath(ignores)) as f:
                        self.ignores = [line.strip().lower() for line in f.readlines()]
                except IOError:
                    print("[FATAL] Diffios could not open '{}".format(config))
                    raise RuntimeError
                else:
                    self.ignore_filename = ignores
            else:
                raise RuntimeError(
                    "[FATAL] DiffiosConfig() received an invalid argument\n")

        if isinstance(config, list):
            self.config = self._remove_invalid_lines(config)
        elif os.path.isfile(os.path.abspath(config)):
            try:
                with open(os.path.abspath(config)) as f:
                    self.config = self._remove_invalid_lines(f.readlines())
            except IOError:
                print("[FATAL] Diffios could not open '{}".format(config))
                raise RuntimeError
            else:
                self.config_filename = config
        else:
            raise RuntimeError(
                "[FATAL] DiffiosConfig() received an invalid argument\n")

    def _remove_invalid_lines(self, lines):
        """TODO: Docstring for _remove_invalid_lines.

        Returns: TODO

        """
        return [l.rstrip() for l in lines if self._valid_line(l)]

    def _valid_line(self, line):
        """TODO: Docstring for _valid_line.

        Args:
            line (TODO): TODO

        Returns: TODO

        """
        lstrip = line.strip()
        return len(lstrip) > 0 and not lstrip.startswith("!")

    def _group_into_blocks(self, config):
        """TODO: Docstring for _group_into_blocks.

        Args:
            config (TODO): TODO

        Returns: TODO

        """
        previous, groups = [], []
        for i, line in enumerate(config):
            if line.startswith(" "):
                previous.append(line)
            else:
                groups.append(previous)
                previous = [line]
        return sorted(groups)[1:]

    @property
    def config_blocks(self):
        """TODO: Docstring for blocks.

        Returns: TODO

        """
        return self._group_into_blocks(self.config)

    @property
    def hostname(self):
        """TODO: Docstring for _hostname.

        Returns: TODO

        """
        for line in self.config:
            if "hostname" in line.lower():
                return line.split()[1]

    def _partition(self):
        """TODO: Docstring for partition.

        Returns: TODO

        """
        Partition = namedtuple("Partition", "ignored recorded")
        ignore = self.ignores
        config_blocks = self._group_into_blocks(self.config)
        ignored = []
        for i, block in enumerate(config_blocks):
            for j, line in enumerate(block):
                for line_to_ignore in ignore:
                    if re.findall(line_to_ignore, line.lower()):
                        if j == 0:
                            ignored.append(config_blocks[i])
                            config_blocks[i] = []
                        else:
                            ignored.append(block[j])
                            block[j] = ""
        recorded = [line for line in config_blocks if line]
        return Partition(ignored, recorded)

    @property
    def ignored(self):
        """TODO: Docstring for ignored.

        Returns: TODO

        """
        return self._partition().ignored

    @property
    def recorded(self):
        """TODO: Docstring for recorded.

        Returns: TODO

        """
        return self._partition().recorded


class DiffiosDiff(object):

    """Docstring for DiffiosDiff. """

    def __init__(self, baseline=None, comparison=None, ignore_file=None):
        """TODO: Docstring for __init__.

        Kwargs:
            baseline (TODO): TODO
            comparison (TODO): TODO
            ignore_file (TODO): TODO

        """
        # TODO: make it so DiffiosConf objects can be passed in also
        # TODO: confirm existence of files
        self.baseline = DiffiosConfig(baseline, ignore_file)
        self.comparison = DiffiosConfig(comparison, ignore_file)
        self.partials = PARTIALS

    def _translate_block(self, block):
        """TODO: Docstring for _translate_block.

        Args:
            block (TODO): TODO

        Returns: TODO

        """
        post_translation_block = []
        for i, line in enumerate(block):
            match = None
            for pattern in self.partials:
                if re.search(pattern, line):
                    match = re.search(pattern, line).group('non_var')
                    post_translation_block.append(match)
            if match is None:
                post_translation_block.append(line)
        return post_translation_block

    def _translated(self, data):
        """TODO: Docstring for _translated.

        Args:
            data (TODO): TODO

        Returns: TODO

        """
        return [self._translate_block(block) for block in data]

    def _changes(self, dynamic, static):
        """TODO: Docstring for _changes.

        Args:
            dynamic (TODO): TODO
            static (TODO): TODO

        Returns: TODO

        """
        translated_dynamic = self._translated(dynamic)
        translated_static = self._translated(static)
        head = [line[0] for line in static]
        changes = []
        for dynamic_index, dynamic_block in enumerate(translated_dynamic):
            if len(dynamic_block) == 1:
                if dynamic_block not in translated_static:
                    changes.append(dynamic[dynamic_index])
            else:
                first_line = dynamic_block[0]
                if first_line in head:
                    static_block = translated_static[head.index(first_line)]
                    additional = [first_line]
                    for dynamic_block_index, line in enumerate(dynamic_block):
                        if line not in static_block:
                            additional.append(
                                dynamic[dynamic_index][dynamic_block_index])
                    if len(additional) > 1:
                        changes.append(additional)
                else:
                    changes.append(dynamic[dynamic_index])
        return sorted(changes)

    def _format_changes(self, data):
        """TODO: Docstring for _format_changes.

        Args:
            data (TODO): TODO

        Returns: TODO

        """
        return "\n\n".join("\n".join(lines) for lines in data)

    @property
    def additional(self):
        """TODO: Docstring for additional.

        Returns: TODO

        """
        comparison = self.comparison.recorded
        baseline = self.baseline.recorded
        additional = self._changes(comparison, baseline)
        return additional

    @property
    def missing(self):
        """TODO: Docstring for missing.

        Returns: TODO

        """
        comparison = self.comparison.recorded
        baseline = self.baseline.recorded
        missing = self._changes(baseline, comparison)
        return missing

    @property
    def pprint_additional(self):
        """TODO: Docstring for pprint_additional.

        Returns: TODO

        """
        return self._format_changes(self.additional)

    @property
    def pprint_missing(self):
        """TODO: Docstring for pprint_missing.

        Returns: TODO

        """
        return self._format_changes(self.missing)

    def diff(self):
        """TODO: Docstring for diff.

        Returns: TODO

        """
        print("\nComparing {comparison} against baseline: {baseline}".format(
            comparison=os.path.basename(self.comparison.config),
            baseline=os.path.basename(self.baseline.config)
        ))
        print("\n[+] additional [+]\n")
        print("{}".format(self.pprint_additional()))
        print("\n[-] missing [-]\n")
        print("{}".format(self.pprint_missing()))
        print("\n--- END ---\n")
