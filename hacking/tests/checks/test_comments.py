# Copyright (c) 2013 eNovance
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

from hacking.checks import comments
from hacking import tests


class CoreTestCase(tests.TestCase):
    def test_H104_regex(self):
        """Verify that the H104 regex matches correct lines."""
        self.assertTrue(comments.hacking_has_only_comments(
            None,
            None,
            ['# foo',
             '# bar'],
            1))
        self.assertTrue(comments.hacking_has_only_comments(
            None,
            None,
            ['# foo',
             '# bar',
             ''],
            1))
        self.assertTrue(comments.hacking_has_only_comments(
            None,
            None,
            ['# foo',
             '   ',
             '# bar'],
            1))

        self.assertIsNone(comments.hacking_has_only_comments(
            None,
            None,
            ['# foo',
             '   ',
             '"""foobar"""'],
            1))
        self.assertIsNone(comments.hacking_has_only_comments(
            None,
            None,
            ['# foo',
             '',
             'print(42)'],
            1))
        self.assertIsNone(comments.hacking_has_only_comments(
            None,
            None,
            ['# foo'],
            100))
