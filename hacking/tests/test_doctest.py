#!/usr/bin/env python
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

from flake8 import engine
import pep8
import pkg_resources
import six
import testscenarios
from testtools import content
from testtools import matchers

import hacking
import hacking.tests

SELFTEST_REGEX = re.compile(r'\b(Okay|[HEW]\d{3}):\s(.*)')
# Each scenario is (name, dict(lines=.., options=..., code=...))
file_cases = []


class HackingTestCase(hacking.tests.TestCase):

    scenarios = file_cases

    def test_pep8(self):
        report = pep8.BaseReport(self.options)
        checker = pep8.Checker(lines=self.lines, options=self.options,
                               report=report)
        checker.check_all()
        self.addDetail('doctest', content.text_content(self.raw))
        if self.code == 'Okay':
            self.assertThat(
                len(report.counters),
                matchers.Not(matchers.GreaterThan(
                    len(self.options.benchmark_keys))),
                "incorrectly found %s" % ', '.join(
                    [key for key in report.counters
                     if key not in self.options.benchmark_keys]))
        else:
            self.addDetail('reason',
                           content.text_content("Failed to trigger rule %s" %
                                                self.code))
            self.assertIn(self.code, report.counters)


def _get_lines(check):
    for line in check.__doc__.splitlines():
        line = line.lstrip()
        match = SELFTEST_REGEX.match(line)
        if match is None:
            continue
        yield (line, match.groups())


def load_tests(loader, tests, pattern):

    flake8_style = engine.get_style_guide(parse_argv=False,
                                          # Ignore H104 otherwise it's
                                          # raised on doctests.
                                          ignore=('F', 'H104'))
    options = flake8_style.options

    for entry in pkg_resources.iter_entry_points('flake8.extension'):
        if not entry.module_name.startswith('hacking.'):
            continue
        check = entry.load()
        name = entry.attrs[0]
        if check.skip_on_py3 and six.PY3:
            continue
        for (lineno, (raw, (code, source))) in enumerate(_get_lines(check)):
            lines = [part.replace(r'\t', '\t') + '\n'
                     for part in source.split(r'\n')]
            file_cases.append(("%s-line-%s" % (name, lineno),
                              dict(lines=lines, raw=raw, options=options,
                                   code=code)))
    return testscenarios.load_tests_apply_scenarios(loader, tests, pattern)
