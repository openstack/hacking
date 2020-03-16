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

import re
import tokenize

from hacking import core

RE_OCTAL = re.compile(r"0+([1-9]\d*)")
RE_PRINT = re.compile(r"\bprint(?:$|\s+[^\(])")


@core.skip_on_py3
@core.flake8ext
def hacking_python3x_except_compatible(logical_line, noqa):
    r"""Check for except statements to be Python 3.x compatible

    As of Python 3.x, the construct 'except x,y:' has been removed.
    Use 'except x as y:' instead.


    Okay: try:\n    pass\nexcept Exception:\n    pass
    Okay: try:\n    pass\nexcept (Exception, AttributeError):\n    pass
    H231: try:\n    pass\nexcept AttributeError, e:\n    pass
    Okay: try:\n    pass\nexcept AttributeError, e:  # noqa\n    pass
    """
    if noqa:
        return

    def is_old_style_except(logical_line):
        return (',' in logical_line and
                ')' not in logical_line.rpartition(',')[2])

    if (logical_line.startswith("except ") and
            logical_line.endswith(':') and
            is_old_style_except(logical_line)):
        yield 0, "H231: Python 3.x incompatible 'except x,y:' construct"


@core.skip_on_py3
@core.flake8ext
def hacking_python3x_octal_literals(logical_line, tokens, noqa):
    r"""Check for octal literals in Python 3.x compatible form.

    As of Python 3.x, the construct "0755" has been removed.
    Use "0o755" instead".


    Okay: f(0o755)
    Okay: 'f(0755)'
    Okay: f(755)
    Okay: f(0)
    Okay: f(000)
    Okay: MiB = 1.0415
    H232: f(0755)
    Okay: f(0755)  # noqa
    """
    if noqa:
        return

    for token_type, text, _, _, _ in tokens:
        if token_type == tokenize.NUMBER:
            match = RE_OCTAL.match(text)
            if match:
                yield 0, ("H232: Python 3.x incompatible octal %s should be "
                          "written as 0o%s " %
                          (match.group(0)[1:], match.group(1)))


@core.skip_on_py3
@core.flake8ext
def hacking_python3x_print_function(logical_line, noqa):
    r"""Check that all print occurrences look like print functions.

    Check that all occurrences of print look like functions, not
    print operator. As of Python 3.x, the print operator has
    been removed.


    Okay: print(msg)
    Okay: print (msg)
    Okay: print msg  # noqa
    Okay: print()
    H233: print msg
    H233: print >>sys.stderr, "hello"
    H233: print msg,
    H233: print
    """
    if noqa:
        return
    for match in RE_PRINT.finditer(logical_line):
        yield match.start(0), (
            "H233: Python 3.x incompatible use of print operator")


@core.flake8ext
def hacking_no_assert_equals(logical_line, tokens, noqa):
    r"""assert(Not)Equals() is deprecated, use assert(Not)Equal instead.

    Okay: self.assertEqual(0, 0)
    Okay: self.assertNotEqual(0, 1)
    H234: self.assertEquals(0, 0)
    H234: self.assertNotEquals(0, 1)
    Okay: self.assertEquals(0, 0)  # noqa
    Okay: self.assertNotEquals(0, 1)  # noqa
    """

    if noqa:
        return
    for token_type, text, start_index, _, _ in tokens:

        if token_type == tokenize.NAME:
            if text == "assertEquals" or text == "assertNotEquals":
                yield (start_index[1],
                       "H234: %s is deprecated, use %s" % (text, text[:-1]))


@core.flake8ext
def hacking_no_assert_underscore(logical_line, tokens, noqa):
    r"""assert_() is deprecated, use assertTrue instead.

    Okay: self.assertTrue(foo)
    H235: self.assert_(foo)
    Okay: self.assert_(foo)  # noqa
    """
    if noqa:
        return
    for token_type, text, start_index, _, _ in tokens:

        if token_type == tokenize.NAME and text == "assert_":
            yield (
                start_index[1],
                "H235: assert_ is deprecated, use assertTrue")


@core.flake8ext
def hacking_python3x_metaclass(logical_line, noqa):
    r"""Check for metaclass to be Python 3.x compatible.

    Okay: @six.add_metaclass(Meta)\nclass Foo(object):\n    pass
    Okay: @six.with_metaclass(Meta)\nclass Foo(object):\n    pass
    Okay: class Foo(object):\n    '''docstring\n\n    __metaclass__ = Meta\n'''
    H236: class Foo(object):\n    __metaclass__ = Meta
    H236: class Foo(object):\n    foo=bar\n    __metaclass__ = Meta
    H236: class Foo(object):\n    '''docstr.'''\n    __metaclass__ = Meta
    H236: class Foo(object):\n    __metaclass__ = \\\n        Meta
    Okay: class Foo(object):\n    __metaclass__ = Meta  # noqa
    """
    if noqa:
        return
    split_line = logical_line.split()
    if(len(split_line) > 2 and split_line[0] == '__metaclass__' and
       split_line[1] == '='):
        yield (logical_line.find('__metaclass__'),
               "H236: Python 3.x incompatible __metaclass__, "
               "use six.add_metaclass()")


# NOTE(guochbo): This is removed module list:
# http://python3porting.com/stdlib.html#removed-modules
removed_modules = [
    'audiodev', 'Bastion', 'bsddb185', 'bsddb3',
    'Canvas', 'cfmfile', 'cl', 'commands', 'compiler'
    'dircache', 'dl', 'exception', 'fpformat',
    'htmllib', 'ihooks', 'imageop', 'imputil'
    'linuxaudiodev', 'md5', 'mhlib', 'mimetools'
    'MimeWriter', 'mimify', 'multifile', 'mutex',
    'new', 'popen2', 'posixfile', 'pure', 'rexec'
    'rfc822', 'sha', 'sgmllib', 'sre', 'stat'
    'stringold', 'sunaudio' 'sv', 'test.testall',
    'thread', 'timing', 'toaiff', 'user'
]


@core.flake8ext
def hacking_no_removed_module(logical_line, noqa):
    r"""Check for removed modules in Python 3.

    Examples:
    Okay: from os import path
    Okay: from os import path as p
    Okay: from os import (path as p)
    Okay: import os.path
    H237: import thread
    Okay: import thread  # noqa
    H237: import commands
    H237: import md5 as std_md5
    """
    if noqa:
        return
    line = core.import_normalize(logical_line.strip())
    if line and line.split()[0] == 'import':
        module_name = line.split()[1].split('.')[0]
        if module_name in removed_modules:
            yield 0, ("H237: module %s is "
                      "removed in Python 3" % module_name)


RE_NEW_STYLE_CLASS = re.compile(r"^class [^(]+\(.+\):")


@core.flake8ext
@core.off_by_default
def hacking_no_old_style_class(logical_line, noqa):
    r"""Check for old style classes.

    Examples:
    Okay: class Foo(object):\n    pass
    Okay: class Foo(Bar, Baz):\n    pass
    Okay: class Foo(object, Baz):\n    pass
    Okay: class Foo(somefunc()):\n    pass
    H238: class Bar:\n    pass
    H238: class Bar():\n    pass
    """
    if noqa:
        return
    line = core.import_normalize(logical_line.strip())
    if line.startswith("class ") and not RE_NEW_STYLE_CLASS.match(line):
        yield (0, "H238: old style class declaration, "
               "use new style (inherit from `object`)")
