# Copyright (c) 2014 Red Hat, Inc.
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

import mock
import six

from hacking.checks import imports
from hacking import tests


def fake_find_module(module, path):
    # Behave as though we're running in the oslo.db project
    if path is None and module == 'oslo':
        # The oslo namespace module won't be found
        raise ImportError
    elif module == 'oslo' and path[0] == '.':
        return (None, './oslo', None)
    elif module == 'db' and path[0] == './oslo':
        return (None, './oslo/db', None)
    elif './oslo/db' in path[0] and module != '_':
        return (None, '%s/%s' % (path[0], module), None)
    raise ImportError


if six.PY3:
    import_name = 'builtins.__import__'
else:
    import_name = '__builtin__.__import__'


class ImportTestCase(tests.TestCase):
    @mock.patch(import_name)
    @mock.patch('imp.find_module')
    def test_namespace_module(self, find_module, mock_import):
        find_module.side_effect = fake_find_module
        self.assertEqual('third-party', imports._get_import_type('oslo.i18n'))
        self.assertEqual('project', imports._get_import_type('oslo.db'))

    @mock.patch(import_name)
    @mock.patch('imp.find_module')
    def test_non_module(self, find_module, mock_import):
        find_module.side_effect = fake_find_module
        mock_import.side_effect = ImportError
        mod_name = 'oslo.db.openstack.common.gettextutils._'
        self.assertEqual('project', imports._get_import_type(mod_name))
