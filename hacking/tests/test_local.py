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

from flake8 import engine
import pep8

import hacking.tests


def check(physical_line):
    """Test check to make sure local-checks are working."""
    if physical_line.strip() == "#this-is-the-test-phrase":
        return (0, "L100: Found local-check test case")


class HackingTestCase(hacking.tests.TestCase):
    def test_local_check(self):
        flake8_style = engine.get_style_guide(parse_argv=False, ignore='F')
        report = pep8.BaseReport(flake8_style.options)
        line = ["#this-is-the-test-phrase"]
        checker = pep8.Checker(lines=line, options=flake8_style.options,
                               report=report)
        checker.check_all()
        self.assertIn("L100", report.counters)
