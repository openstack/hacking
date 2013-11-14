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

import fixtures

from hacking import config
from hacking import core
from hacking import tests


TEST_TOX_INI = """[hacking]
import_exceptions =
    a.b.c
    z.x
"""


class ImportExceptionsTest(tests.TestCase):
    def _setUpConfig(self, content):
        tox_ini_path = os.path.join(self.useFixture(fixtures.TempDir()).path,
                                    'tox.ini')

        with open(tox_ini_path, 'w') as tox_ini:
            tox_ini.write(content)

        return config.Config('hacking', tox_ini_path)

    def setUp(self):
        super(ImportExceptionsTest, self).setUp()

    def test_default_import_exceptions(self):
        conf = self._setUpConfig("")
        self.assertEqual(core.DEFAULT_IMPORT_EXCEPTIONS,
                         conf.get_multiple(
                             'import_exceptions',
                             default=core.DEFAULT_IMPORT_EXCEPTIONS))

    def test_import_exceptions(self):
        conf = self._setUpConfig(TEST_TOX_INI)
        self.assertEqual(['a.b.c', 'z.x'],
                         conf.get_multiple('import_exceptions'))
