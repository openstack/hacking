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

from hacking.checks import imports
from hacking import tests


@ddt.ddt
class ImportsTestCase(tests.TestCase):
    """This tests hacking checks from the 'imports' group."""

    @ddt.unpack
    @ddt.data(
        (True, 'import eventlet', None),
        (True, 'from eventlet import monkey_patch', None),
        (True, 'from eventlet.green import socket', None),
        (True, '    import eventlet  # with indentation', None),
        (True, '    from eventlet import something', None),
        (False, 'import eventlet  # noqa', '# noqa'),
        (False, 'import asyncio', None),
        (False, 'import threading', None),
        (False, 'from threading import Thread', None),
        (False, 'import concurrent.futures', None),
        (False, 'import some_other_module', None),
        (False, 'import not_eventlet', None),
        (False, 'from not_eventlet import something', None),
    )
    def test_H905_hacking_no_eventlet(self, should_fail, line, noqa):
        if should_fail:
            self.assertCheckFails(imports.hacking_no_eventlet, line, noqa)
        else:
            self.assertCheckPasses(imports.hacking_no_eventlet, line, noqa)
