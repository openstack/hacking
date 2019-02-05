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
    def test_H102_none(self):
        """Verify that the H102 check finds an SPDX header"""
        self.assertEqual(
            (0, 'H102: Apache 2.0 license header not found'),
            comments.hacking_has_license(
                None,
                None,
                [
                    '# foo',
                    '# bar',
                    '# foo',
                    '# bar',
                    '# foo',
                    '# bar',
                    '# foo',
                    '# bar',
                    '# foo',
                    '# bar',
                    '# foo',
                    '# bar',
                ],
                1,
            ),
        )

    def test_H102_full(self):
        """Verify that the H102 check finds an SPDX header"""
        self.assertIsNone(comments.hacking_has_license(
            None,
            None,
            [
                '# foo',
                '# Licensed under the Apache License, Version 2.0',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
            ],
            1,
        ))

    def test_H102_SPDX(self):
        """Verify that the H102 check finds an SPDX header"""
        self.assertIsNone(comments.hacking_has_license(
            None,
            None,
            [
                '# foo',
                '# SPDX-License-Identifier: Apache-2.0',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
            ],
            1,
        ))

    def test_H103_full_fail(self):
        """Verify that the H103 check finds an SPDX header"""
        self.assertEqual(
            (2, 'H103: Header does not match Apache 2.0 License notice'),
            comments.hacking_has_correct_license(
                None,
                None,
                [
                    '# foo',
                    '# Licensed under the Apache License, Version 2.0',
                    '# foo',
                    '# bar',
                    '# foo',
                    '# bar',
                    '# foo',
                    '# bar',
                    '# foo',
                    '# bar',
                    '# foo',
                    '# bar',
                ],
                1,
            ),
        )

    def test_H103_full(self):
        """Verify that the H103 check finds an SPDX header"""
        self.assertIsNone(comments.hacking_has_correct_license(
            None,
            None,
            [
                """
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
                """  # noqa
            ],
            1,
        ))

    def test_H103_SPDX(self):
        """Verify that the H103 check finds an SPDX header"""
        self.assertIsNone(comments.hacking_has_correct_license(
            None,
            None,
            [
                '# foo',
                '# SPDX-License-Identifier: Apache-2.0',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
                '# foo',
                '# bar',
            ],
            1,
        ))

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

    def test_H105(self):
        self.assertTrue(comments.hacking_no_author_tags(
            '# @author: Foo Bar'))

        self.assertTrue(comments.hacking_no_author_tags(
            '# @Author: Foo Bar'))

        self.assertTrue(comments.hacking_no_author_tags(
            '# author: Foo Bar'))

        self.assertTrue(comments.hacking_no_author_tags(
            '# authors: Foo Bar'))

        self.assertTrue(comments.hacking_no_author_tags(
            '# Author: Foo Bar'))

        self.assertTrue(comments.hacking_no_author_tags(
            '# Authors: Foo Bar'))

        self.assertTrue(comments.hacking_no_author_tags(
            '.. moduleauthor:: Foo Bar'))
