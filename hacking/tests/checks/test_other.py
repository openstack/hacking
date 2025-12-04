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

from hacking.checks import other
from hacking import tests


@ddt.ddt
class OthersTestCase(tests.TestCase):
    """This tests hacking checks from the 'other' group."""

    @ddt.unpack
    @ddt.data(
        (False, 'LOG.debug("Test %s" % foo)', None),
        (True, 'LOG.info("Test %s", foo)', None),
        (False, 'LOG.info("Test {}".format(foo))', None),
        (True, 'LOG.error("Test %s" % foo)', '# noqa'),
        (False, 'LOG.debug("Test %s" % "foo")', None),
        (True, 'LOG.debug("Test %s", "foo")', None),
        (True, 'LOG.warning("Test %s", ",".join("%s:%s" % (a, b)))', None),
        (True, "LOG.warning('Testing some stuff')", None))
    def test_H904_hacking_delayed_string_interpolation(
            self, passes, line, noqa):
        if passes:
            self.assertCheckPasses(other.hacking_delayed_string_interpolation,
                                   line, noqa)
        else:
            self.assertCheckFails(other.hacking_delayed_string_interpolation,
                                  line, noqa)

    @ddt.unpack
    @ddt.data(
        (False, 'import os\r\nimport sys'),
        (True, 'import os\nimport sys'))
    def test_H903_hacking_no_cr(self, passes, line):
        if passes:
            self.assertCheckPasses(other.hacking_no_cr, line)
        else:
            self.assertCheckFails(other.hacking_no_cr, line)

    @ddt.unpack
    @ddt.data(
        (False, 'LOG.warn("LOG.warn is deprecated")'),
        (True, 'LOG.warning("LOG.warn is deprecated")'))
    def test_H905_no_log_warn(self, passes, line):
        if passes:
            self.assertCheckPasses(other.hacking_no_log_warn, line)
        else:
            self.assertCheckFails(other.hacking_no_log_warn, line)
