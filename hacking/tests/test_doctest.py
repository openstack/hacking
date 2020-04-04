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

import os
import re
import subprocess
import sys
import tempfile

import pkg_resources
import testscenarios
from testtools import content

import hacking.tests

SELFTEST_REGEX = re.compile(r'\b(Okay|[HEW]\d{3}):\s(.*)')
# Each scenario is (name, {lines=.., raw=..., code=...})
file_cases = []


class HackingTestCase(hacking.tests.TestCase):

    scenarios = file_cases

    def test_flake8(self):

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(''.join(self.lines))

        cmd = [sys.executable, '-mflake8', '--isolated',
               '--select=%s' % self.code, '--ignore=F',
               '--format=%(code)s\t%(path)s\t%(row)d', f.name]
        out, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()

        out = out.decode('utf-8')

        if self.code == 'Okay':
            self.assertEqual('', out)
        else:
            self.addDetail('reason',
                           content.text_content("Failed to trigger rule %s" %
                                                self.code))
            self.assertNotEqual('', out)
            self.assertEqual(self.code, out.split('\t')[0].rstrip(':'), out)

        os.remove(f.name)


def _get_lines(check):
    for line in check.__doc__.splitlines():
        line = line.lstrip()
        match = SELFTEST_REGEX.match(line)
        if match is None:
            continue
        yield line, match.groups()


def load_tests(loader, tests, pattern):

    for entry in pkg_resources.iter_entry_points('flake8.extension'):
        if not entry.module_name.startswith('hacking.'):
            continue

        check = entry.load()
        if check.skip_on_py3:
            continue

        name = entry.attrs[0]
        for lineno, (raw, (code, source)) in enumerate(_get_lines(check)):
            lines = [part.replace(r'\t', '\t') + '\n'
                     for part in source.split(r'\n')]
            file_cases.append((
                '%s-%s-line-%s' % (entry.name, name, lineno),
                {'lines': lines, 'raw': raw, 'code': code},
            ))

    return testscenarios.load_tests_apply_scenarios(loader, tests, pattern)
