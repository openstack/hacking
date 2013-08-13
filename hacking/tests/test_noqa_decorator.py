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

from hacking.core import allownoqa, HackingDecoratorError
from testtools import ExpectedException

import hacking.tests


@allownoqa
def method_with_physical_line_argument(physical_line):
    return "method_with_physical_line_argument"


@allownoqa
def method_without_physical_line_argument():
    return "method_without_physical_line_argument"


class NoqaDecoratorTestCase(hacking.tests.TestCase):
    def test_with_physical_line_argument(self):
        result = method_with_physical_line_argument("blah")
        self.assertEqual(result, "method_with_physical_line_argument")

    def test_without_physical_line_argument(self):
        with ExpectedException(HackingDecoratorError, "Missing physical_line "
                               "argument for decorated function"):
            method_without_physical_line_argument()
