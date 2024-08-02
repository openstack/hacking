#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

# module cannot be called except since that is a reserved word

import ast
import re

from hacking import core

RE_ASSERT_RAISES_EXCEPTION = re.compile(r"self\.assertRaises\(Exception[,\)]")
RE_ASSERT_TRUE_INST = re.compile(
    r"(.)*assertTrue\(isinstance\((\w|\.|\'|\"|\[|\])+, "
    r"(\w|\.|\'|\"|\[|\])+\)\)")
RE_ASSERT_EQUAL_TYPE = re.compile(
    r"(.)*assertEqual\(type\((\w|\.|\'|\"|\[|\])+\), "
    r"(\w|\.|\'|\"|\[|\])+\)")
RE_ASSERT_EQUAL_IN_START_WITH_TRUE_OR_FALSE = re.compile(
    r"assertEqual\("
    r"(True|False), (\w|[][.'\"])+ in (\w|[][.'\", ])+\)")
RE_ASSERT_RAISES_REGEXP = re.compile(r"assertRaisesRegexp\(")
# NOTE(snikitin): Next two regexes weren't united to one for more readability.
#                 asse_true_false_with_in_or_not_in regex checks
#                 assertTrue/False(A in B) cases where B argument has no spaces
#                 asse_true_false_with_in_or_not_in_spaces regex checks cases
#                 where B argument has spaces and starts/ends with [, ', ".
#                 For example: [1, 2, 3], "some string", 'another string'.
#                 We have to separate these regexes to escape a false positives
#                 results. B argument should have spaces only if it starts
#                 with [, ", '. Otherwise checking of string
#                 "assertFalse(A in B and C in D)" will be false positives.
#                 In this case B argument is "B and C in D".
RE_ASSERT_TRUE_FALSE_WITH_IN_OR_NOT_IN = re.compile(
    r"assert(True|False)\("
    r"(\w|[][.'\"])+( not)? in (\w|[][.'\",])+(, .*)?\)")
RE_ASSERT_TRUE_FALSE_WITH_IN_OR_NOT_IN_SPACES = re.compile(
    r"assert(True|False)"
    r"\((\w|[][.'\"])+( not)? in [\[|'|\"](\w|[][.'\", ])+"
    r"[\[|'|\"](, .*)?\)")
RE_ASSERT_EQUAL_IN_END_WITH_TRUE_OR_FALSE = re.compile(
    r"assertEqual\("
    r"(\w|[][.'\"])+ in (\w|[][.'\", ])+, (True|False)\)")


@core.flake8ext
def hacking_except_format(logical_line, noqa):
    r"""Check for 'except:'.

    OpenStack HACKING guide recommends not using except:
    Do not write "except:", use "except Exception:" at the very least

    Okay: try:\n    pass\nexcept Exception:\n    pass
    H201: try:\n    pass\nexcept:\n    pass
    Okay: try:\n    pass\nexcept:  # noqa\n    pass
    """
    if noqa:
        return
    if logical_line.startswith("except:"):
        yield 6, "H201: no 'except:' at least use 'except Exception:'"


@core.flake8ext
def hacking_except_format_assert(logical_line, noqa):
    r"""Check for 'assertRaises(Exception'.

    OpenStack HACKING guide recommends not using assertRaises(Exception...):
    Do not use overly broad Exception type

    Okay: self.assertRaises(NovaException, foo)
    Okay: self.assertRaises(ExceptionStrangeNotation, foo)
    H202: self.assertRaises(Exception, foo)
    H202: self.assertRaises(Exception)
    Okay: self.assertRaises(Exception)  # noqa
    Okay: self.assertRaises(Exception, foo)  # noqa
    """
    if noqa:
        return
    if RE_ASSERT_RAISES_EXCEPTION.search(logical_line):
        yield 1, "H202: assertRaises Exception too broad"


def is_none(node):
    '''Check whether an AST node corresponds to None.'''
    return isinstance(node, ast.Constant) and node.value is None


def _get_local_func_name(node):
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    elif isinstance(node.func, ast.Name):
        return node.func.id
    else:
        return None


class NoneArgChecker(ast.NodeVisitor):
    '''NodeVisitor to check function calls for None arguments.

    :param func_name: only check calls to functions with this name
    :param num_args:  number of arguments to check for None

    self.none_found will be True if any None arguments were found.
    '''

    def __init__(self, func_name, num_args=2):
        self.func_name = func_name
        self.num_args = num_args
        self.none_found = False

    def visit_Call(self, node):
        local_func_name = _get_local_func_name(node)

        if local_func_name == self.func_name:
            args_to_check = node.args[:self.num_args]
            self.none_found |= any(is_none(x) for x in args_to_check)
        self.generic_visit(node)


@core.flake8ext
@core.off_by_default
def hacking_assert_is_none(logical_line, noqa):
    """Use assertIs(Not)None to check for None in assertions.

    Okay: self.assertEqual('foo', 'bar')
    Okay: self.assertNotEqual('foo', {}.get('bar', None))
    Okay: self.assertIs('foo', 'bar')
    Okay: self.assertIsNot('foo', 'bar', None)
    Okay: foo(self.assertIsNot('foo', 'bar'))
    H203: self.assertEqual(None, 'foo')
    H203: self.assertNotEqual('foo', None)
    H203: self.assertIs(None, 'foo', 'bar')
    H203: self.assertIsNot('foo', None, 'bar')
    H203: foo(self.assertIsNot('foo', None, 'bar'))
    Okay: self.assertEqual(None, 'foo')  # noqa
    Okay: self.assertIs(None, 'foo')  # noqa
    Okay: self.assertIsNone('foo')
    """
    if noqa:
        return
    for func_name in ('assertEqual', 'assertIs', 'assertNotEqual',
                      'assertIsNot'):
        try:
            start = logical_line.index('.%s(' % func_name) + 1
        except ValueError:
            continue
        checker = NoneArgChecker(func_name)
        try:
            parsed_logical_line = ast.parse(logical_line)
        except SyntaxError:
            # let flake8 catch this itself
            # https://github.com/PyCQA/flake8/issues/1948
            continue
        checker.visit(parsed_logical_line)
        if checker.none_found:
            yield start, "H203: Use assertIs(Not)None to check for None"


class AssertTrueFalseChecker(ast.NodeVisitor):
    '''NodeVisitor to find "assert[True|False](some comparison)" statements.

    :param method_names: methods to look for: assertTrue and/or assertFalse
    :param ops: list of comparisons we want to look for (objects from the ast
                module)
    '''

    def __init__(self, method_names, ops):
        self.method_names = method_names
        self.ops = tuple(ops)
        self.error = False

    def visit_Call(self, node):
        # No need to keep visiting the AST if we already found something.
        if self.error:
            return

        self.generic_visit(node)

        local_func_name = _get_local_func_name(node)

        if (local_func_name in self.method_names and
                len(node.args) == 1 and
                isinstance(node.args[0], ast.Compare) and
                len(node.args[0].ops) == 1 and
                isinstance(node.args[0].ops[0], self.ops)):
            self.error = True


@core.flake8ext
@core.off_by_default
def hacking_assert_equal(logical_line, noqa):
    r"""Check that self.assertEqual and self.assertNotEqual are used.

    Okay: self.assertEqual(x, y)
    Okay: self.assertNotEqual(x, y)
    H204: self.assertTrue(x == y)
    H204: self.assertTrue(x != y)
    H204: self.assertFalse(x == y)
    H204: self.assertFalse(x != y)
    """
    if noqa:
        return

    methods = ['assertTrue', 'assertFalse']
    for method in methods:
        start = logical_line.find('.%s' % method) + 1
        if start != 0:
            break
    else:
        return
    comparisons = [ast.Eq, ast.NotEq]
    checker = AssertTrueFalseChecker(methods, comparisons)
    try:
        parsed_logical_line = ast.parse(logical_line)
    except SyntaxError:
        # let flake8 catch this itself
        # https://github.com/PyCQA/flake8/issues/1948
        return
    checker.visit(parsed_logical_line)
    if checker.error:
        yield start, 'H204: Use assert(Not)Equal()'


@core.flake8ext
@core.off_by_default
def hacking_assert_greater_less(logical_line, noqa):
    r"""Check that self.assert{Greater,Less}[Equal] are used.

    Okay: self.assertGreater(x, y)
    Okay: self.assertGreaterEqual(x, y)
    Okay: self.assertLess(x, y)
    Okay: self.assertLessEqual(x, y)
    H205: self.assertTrue(x > y)
    H205: self.assertTrue(x >= y)
    H205: self.assertTrue(x < y)
    H205: self.assertTrue(x <= y)
    """
    if noqa:
        return

    methods = ['assertTrue', 'assertFalse']
    for method in methods:
        start = logical_line.find('.%s' % method) + 1
        if start != 0:
            break
    else:
        return
    comparisons = [ast.Gt, ast.GtE, ast.Lt, ast.LtE]
    checker = AssertTrueFalseChecker(methods, comparisons)
    try:
        parsed_logical_line = ast.parse(logical_line)
    except SyntaxError:
        # let flake8 catch this itself
        # https://github.com/PyCQA/flake8/issues/1948
        return
    checker.visit(parsed_logical_line)
    if checker.error:
        yield start, 'H205: Use assert{Greater,Less}[Equal]'


@core.flake8ext
def hacking_assert_true_instance(logical_line):
    """Check for assertTrue(isinstance(a, b)) sentences

    H211
    """
    if RE_ASSERT_TRUE_INST.match(logical_line):
        yield (
            0,
            "H211: Use assert{Is,IsNot}instance")


@core.flake8ext
def hacking_assert_equal_type(logical_line):
    """Check for assertEqual(type(A), B) sentences

    H212
    """
    if RE_ASSERT_EQUAL_TYPE.match(logical_line):
        yield (
            0,
            "H211: Use assert{Is,IsNot}instance")


@core.flake8ext
def hacking_assert_raises_regexp(logical_line):
    """Check for usage of deprecated assertRaisesRegexp

    H213
    """
    res = RE_ASSERT_RAISES_REGEXP.search(logical_line)
    if res:
        yield (
            0,
            "H213: assertRaisesRegex must be used instead "
            "of assertRaisesRegexp")


@core.flake8ext
def hacking_assert_true_or_false_with_in(logical_line):
    """Check for assertTrue/False(A in B), assertTrue/False(A not in B),

    assertTrue/False(A in B, message) or assertTrue/False(A not in B, message)
    sentences.
    H214
    """
    res = (RE_ASSERT_TRUE_FALSE_WITH_IN_OR_NOT_IN.search(logical_line)
           or RE_ASSERT_TRUE_FALSE_WITH_IN_OR_NOT_IN_SPACES.search
           (logical_line))
    if res:
        yield (
            0,
            "H214: Use assertIn/NotIn(A, B) rather than "
            "assertTrue/False(A in/not in B) when checking collection "
            "contents.")


@core.flake8ext
def hacking_assert_equal_in(logical_line):
    """Check for assertEqual(A in B, True), assertEqual(True, A in B),

    assertEqual(A in B, False) or assertEqual(False, A in B) sentences

    H215
    """
    res = (RE_ASSERT_EQUAL_IN_START_WITH_TRUE_OR_FALSE.search(logical_line) or
           RE_ASSERT_EQUAL_IN_END_WITH_TRUE_OR_FALSE.search(logical_line))
    if res:
        yield (
            0,
            "H215: Use assertIn/NotIn(A, B) rather than "
            "assertEqual(A in B, True/False) when checking collection "
            "contents.")
