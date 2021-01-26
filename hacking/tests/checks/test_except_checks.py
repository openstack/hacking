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

import textwrap
from unittest import mock

import pycodestyle

from hacking.checks import except_checks
from hacking import tests


class ExceptChecksTest(tests.TestCase):

    def _assert_has_errors(self, code, checker, expected_errors=None,
                           filename=None):
        actual_errors = [e[:3] for e in
                         self._run_check(code, checker, filename)]
        self.assertEqual(expected_errors or [], actual_errors)

    # We are patching pycodestyle so that only the check under test is actually
    # installed.
    @mock.patch('pycodestyle._checks',
                {'physical_line': {}, 'logical_line': {}, 'tree': {}})
    def _run_check(self, code, checker, filename=None):
        pycodestyle.register_check(checker)

        lines = textwrap.dedent(code).lstrip().splitlines(True)

        checker = pycodestyle.Checker(filename=filename, lines=lines)
        # NOTE(sdague): the standard reporter has printing to stdout
        # as a normal part of check_all, which bleeds through to the
        # test output stream in an unhelpful way. This blocks that printing.
        with mock.patch('pycodestyle.StandardReport.get_file_results'):
            checker.check_all()
        checker.report._deferred_print.sort()
        return checker.report._deferred_print

    def test_hacking_assert_true_instance(self):
        self.assertEqual(
            len(list(except_checks.hacking_assert_true_instance(
                "self.assertTrue(isinstance(e, "
                "exception.BuildAbortException))"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_instance(
                "self.assertTrue()"
            ))),
            0)

    def test_hacking_assert_equal_in(self):
        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual(a in b, True)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual('str' in 'string', True)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual(any(a==1 for a in b), True)"
            ))),
            0)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual(a in b, True)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual('str' in 'string', True)"
            ))),
            1)

        self.assertEqual(len(list(except_checks.hacking_assert_equal_in(
            "self.assertEqual(any(a==1 for a in b, True))"
        ))),
            0)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual(a in b, False)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual('str' in 'string', False)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual(any(a==1 for a in b), False)"
            ))),
            0)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual(a in b, False)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual('str' in 'string', False)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_in(
                "self.assertEqual(any(a==1 for a in b, False))"
            ))),
            0)

    def test_hacking_assert_true_or_false_with_in_or_not_in(self):
        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertTrue(A in B)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertFalse(A in B)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertTrue(A not in B)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertFalse(A not in B)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertTrue(A in B, 'some message')"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertFalse(A in B, 'some message')"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertTrue(A not in B, 'some message')"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertFalse(A not in B, 'some message')"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertTrue(A in 'some string with spaces')"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertTrue(A in ['1', '2', '3'])"
            ))),
            1)

        self.assertEqual(len(
            list(except_checks.hacking_assert_true_or_false_with_in(
                 "self.assertTrue(A in [1, 2, 3])"
                 ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertTrue(any(A > 5 for A in B))"
            ))),
            0)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertTrue(any(A > 5 for A in B), 'some message')"
            ))),
            0)

        self.assertEqual(
            len(list(except_checks.hacking_assert_true_or_false_with_in(
                "self.assertFalse(some in list1 and some2 in list2)"
            ))),
            0)

    def test_hacking_oslo_assert_raises_regexp(self):
        code = """
               self.assertRaisesRegexp(ValueError,
                                       "invalid literal for.*XYZ'$",
                                       int,
                                       'XYZ')
               """
        self._assert_has_errors(
            code,
            except_checks.hacking_assert_raises_regexp, expected_errors=[
                (1, 0, "H213")
            ])

    def test_hacking_assert_equal_type(self):
        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_type(
                "self.assertEqual(type(als['QuicAssist']), list)"
            ))),
            1)

        self.assertEqual(
            len(list(except_checks.hacking_assert_equal_type(
                "self.assertTrue()"
            ))),
            0)
