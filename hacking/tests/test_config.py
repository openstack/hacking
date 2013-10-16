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
from hacking import tests


TEST_TOX_INI = """[hacking]
option_1 = val_1
option_2 =
    val_2
option_3 =
    val_1,val_2, val_3,
    val_4 , val_5 , val_6,
    val_7
    ,
     val_8
     val_9
"""


class ConfigTest(tests.TestCase):
    def setUp(self):
        tox_ini_path = os.path.join(self.useFixture(fixtures.TempDir()).path,
                                    'tox.ini')

        with open(tox_ini_path, 'w') as tox_ini:
            tox_ini.write(TEST_TOX_INI)
        self.conf = config.Config('hacking', tox_ini_path)
        super(ConfigTest, self).setUp()

    def test_get(self):
        self.assertEqual('val_1', self.conf.get('option_1'))
        self.assertEqual('val_2', self.conf.get('option_2'))
        self.assertEqual('val_3', self.conf.get('option_4', default='val_3'))

    def test_get_multiple(self):
        self.assertEqual(['val_1', 'val_2', 'val_3', 'val_4', 'val_5', 'val_6',
                          'val_7', 'val_8', 'val_9'],
                         self.conf.get_multiple('option_3'))

        self.assertEqual(['val_1', 'val_2'],
                         self.conf.get_multiple('option_4',
                                                default=['val_1', 'val_2']))
