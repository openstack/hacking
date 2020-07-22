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

import ddt

from hacking.checks import mock_checks
from hacking import tests


@ddt.ddt
class MockingTestCase(tests.TestCase):
    """This tests hacking checks related to the use of mocking."""

    @ddt.unpack
    @ddt.data(
        (1, 'import mock', None),
        (0, 'from unittest import mock', None),
        (1, 'from mock import patch', None),
        (0, 'from unittest.mock import patch', None),
        (0, 'from mock', '# noqa'))
    def test_H216_hacking_no_third_party_mock(self, err_count, line, noqa):
        if err_count > 0:
            self.assertCheckFails(mock_checks.hacking_no_third_party_mock,
                                  line, noqa)
        else:
            self.assertCheckPasses(mock_checks.hacking_no_third_party_mock,
                                   line, noqa)
