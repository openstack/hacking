# Copyright (c) 2012, Cloudscaling
# All Rights Reserved.
#
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

"""OpenStack HACKING file compliance testing

Built as a sets of pep8 checks using flake8.
"""

import gettext
import imp
import logging
import os
import re
import subprocess
import sys
import tokenize
import traceback

import pbr.util
import pep8

from hacking import config

# Don't need this for testing
logging.disable(logging.CRITICAL)

# Import tests need to inject _ properly into the builtins
kwargs = {}
if sys.version_info[0] < 3:
    # In Python2, ensure that the _() that gets installed into built-ins
    # always returns unicodes. This matches the default behavior under Python
    # 3, although the keyword argument is not present in the Python 3 API.
    kwargs['unicode'] = True
gettext.install('hacking', **kwargs)


def flake8ext(f):
    f.name = __name__
    f.version = '0.0.1'
    f.skip_on_py3 = False
    return f


def skip_on_py3(f):
    f.skip_on_py3 = True
    return f

# Error code block layout

# H1xx comments
# H20x except
# H23x Python 2.x -> 3.x portability issues
# H3xx imports
# H4xx docstrings
# H5xx dictionaries/lists
# H6xx calling methods
# H7xx localization
# H8xx git commit messages
# H9xx other


CONF = config.Config('hacking')


DEFAULT_IMPORT_EXCEPTIONS = [
    'sqlalchemy',
    'migrate',
]

IMPORT_EXCEPTIONS = CONF.get_multiple('import_exceptions', default=[])
IMPORT_EXCEPTIONS += DEFAULT_IMPORT_EXCEPTIONS

# Paste is missing a __init__ in top level directory
START_DOCSTRING_TRIPLE = ['u"""', 'r"""', '"""', "u'''", "r'''", "'''"]
END_DOCSTRING_TRIPLE = ['"""', "'''"]


def is_import_exception(mod):
    return (mod in IMPORT_EXCEPTIONS or
            any(mod.startswith(m + '.') for m in IMPORT_EXCEPTIONS))


def import_normalize(line):
    # convert "from x import y" to "import x.y"
    # handle "from x import y as z" to "import x.y as z"
    split_line = line.split()
    if ("import" in line and line.startswith("from ") and "," not in line and
            split_line[2] == "import" and split_line[3] != "*" and
            split_line[1] != "__future__" and
            (len(split_line) == 4 or
             (len(split_line) == 6 and split_line[4] == "as"))):
        return "import %s.%s" % (split_line[1], split_line[3])
    else:
        return line


modules_cache = dict((mod, True) for mod in tuple(sys.modules.keys())
                     + sys.builtin_module_names)

RE_RELATIVE_IMPORT = re.compile('^from\s*[.]')


@flake8ext
def hacking_import_rules(logical_line, physical_line, filename, noqa):
    r"""Check for imports.

    OpenStack HACKING guide recommends one import per line:
    Do not import more than one module per line

    Examples:
    Okay: from nova.compute import api
    H301: from nova.compute import api, utils


    Imports should usually be on separate lines.

    OpenStack HACKING guide recommends importing only modules:
    Do not import objects, only modules

    Examples:
    Okay: from os import path
    Okay: from os import path as p
    Okay: from os import (path as p)
    Okay: import os.path
    Okay: from nova.compute import rpcapi
    Okay: from os.path import dirname as dirname2  # noqa
    H302: from os.path import dirname as dirname2
    H302: from os.path import (dirname as dirname2)
    H303: from os.path import *
    H304: from .compute import rpcapi
    """
    # TODO(jogo): make the following doctests pass:
    #            H301: import os, sys
    # NOTE(afazekas): An old style relative import example will not be able to
    # pass the doctest, since the relativity depends on the file's locality
    # TODO(mordred: We need to split this into 4 different checks so that they
    # can be disabled by command line switches properly

    if noqa:
        return

    def is_module_for_sure(mod, search_path=sys.path):
        mod = mod.replace('(', '')  # Ignore parentheses
        try:
            mod_name = mod
            while '.' in mod_name:
                pack_name, _sep, mod_name = mod.partition('.')
                f, p, d = imp.find_module(pack_name, search_path)
                search_path = [p]
            imp.find_module(mod_name, search_path)
        except ImportError:
            try:
                # NOTE(vish): handle namespace modules
                if '.' in mod:
                    pack_name, mod_name = mod.rsplit('.', 1)
                    __import__(pack_name, fromlist=[mod_name])
                else:
                    __import__(mod)
            except ImportError:
                # NOTE(imelnikov): import error here means the thing is
                # not importable in current environment, either because
                # of missing dependency, typo in code being checked, or
                # any other reason. Anyway, we have no means to know if
                # it is module or not, so we return True to avoid
                # false positives.
                return True
            except Exception:
                # NOTE(jogo) don't stack trace if unexpected import error,
                # log and continue.
                traceback.print_exc()
                return False
            else:
                # NOTE(imelnikov): we imported the thing; if it was module,
                # it must be there:
                return mod in sys.modules
        return True

    def is_module(mod):
        """Checks for non module imports."""
        if mod in modules_cache:
            return modules_cache[mod]
        res = is_module_for_sure(mod)
        modules_cache[mod] = res
        return res

    current_path = os.path.dirname(filename)
    current_mod = os.path.basename(filename)
    if current_mod[-3:] == ".py":
        current_mod = current_mod[:-3]

    split_line = logical_line.split()
    split_line_len = len(split_line)
    if (split_line_len > 1 and split_line[0] in ('import', 'from') and
            not is_import_exception(split_line[1])):
        pos = logical_line.find(',')
        if pos != -1:
            if split_line[0] == 'from':
                yield pos, "H301: one import per line"
            return  # ',' is not supported by the H302 checker yet
        pos = logical_line.find('*')
        if pos != -1:
            yield pos, "H303: No wildcard (*) import."
            return

        if split_line_len in (2, 4, 6) and split_line[1] != "__future__":
            if 'from' == split_line[0] and split_line_len > 3:
                mod = '.'.join((split_line[1], split_line[3]))
                if is_import_exception(mod):
                        return
                if RE_RELATIVE_IMPORT.search(logical_line):
                    yield logical_line.find('.'), (
                        "H304: No relative imports. '%s' is a relative import"
                        % logical_line)
                    return

                if not is_module(mod):
                    yield 0, ("H302: import only modules."
                              "'%s' does not import a module" % logical_line)
                return

        # NOTE(afazekas): import searches first in the package
        # The import keyword just imports modules
        # The guestfs module now imports guestfs
        mod = split_line[1]
        if (current_mod != mod and not is_module(mod) and
                is_module_for_sure(mod, [current_path])):
            yield 0, ("H304: No relative imports."
                      " '%s' is a relative import" % logical_line)


# Get the location of a known stdlib module
_, p, _ = imp.find_module('imp')
stdlib_path_prefix = os.path.dirname(p)
module_cache = dict()


def _get_import_type(module):
    mod_base, _, _ = module.partition('.')
    if mod_base in module_cache:
        return module_cache[mod_base]

    def cache_type(module_type):
        module_cache[mod_base] = module_type
        return module_type

    # First check if the module is local
    try:
        imp.find_module(mod_base, ['.'])
        # If the previous line succeeded then it must be a project module
        return cache_type('project')
    except ImportError:
        pass

    try:
        _, path, _ = imp.find_module(mod_base)
    except ImportError:
        return cache_type('third-party')

    if path is None:
        # NOTE(imelnikov): python 3 returns None for path of builtin
        # modules, like sys or builtin; they are definitely stdlib
        return cache_type('stdlib')
    if 'site-packages' in path or 'dist-packages' in path:
        return cache_type('third-party')
    if (path.startswith(stdlib_path_prefix) or
            path.startswith(sys.prefix) or
            path == module):
        return cache_type('stdlib')
    return cache_type('third-party')


@flake8ext
def hacking_import_groups(logical_line, blank_lines, previous_logical,
                          indent_level, previous_indent_level, physical_line,
                          noqa):
    r"""Check that imports are grouped correctly.

    OpenStack HACKING guide recommendation for imports:
    imports grouped such that Python standard library imports are together,
    third party library imports are together, and project imports are
    together

    Okay: import os\nimport sys\n\nimport six\n\nimport hacking
    Okay: import six\nimport znon_existent_package
    H305: import hacking\nimport os
    H305: import os\nimport six
    H305: import os\nimport znon_existent_package
    """
    if (noqa or blank_lines > 0 or
            indent_level != previous_indent_level):
        return

    normalized_line = import_normalize(logical_line.strip()).split()
    normalized_previous = import_normalize(previous_logical.strip()).split()
    if normalized_line and normalized_line[0] == 'import':
        current_type = _get_import_type(normalized_line[1])
        if normalized_previous and normalized_previous[0] == 'import':
            previous_type = _get_import_type(normalized_previous[1])
            if current_type != previous_type:
                yield(0, 'H305: imports not grouped correctly '
                      '(%s: %s, %s: %s)' %
                      (normalized_previous[1], previous_type,
                       normalized_line[1], current_type))


@flake8ext
def hacking_import_alphabetical(logical_line, blank_lines, previous_logical,
                                indent_level, previous_indent_level):
    r"""Check for imports in alphabetical order.

    OpenStack HACKING guide recommendation for imports:
    imports in human alphabetical order

    Okay: import os\nimport sys\n\nimport nova\nfrom nova import test
    Okay: import os\nimport sys
    H306: import sys\nimport os
    """
    # handle import x
    # use .lower since capitalization shouldn't dictate order
    split_line = import_normalize(logical_line.strip()).lower().split()
    split_previous = import_normalize(previous_logical.strip()).lower().split()

    if blank_lines < 1 and indent_level == previous_indent_level:
        length = [2, 4]
        if (len(split_line) in length and len(split_previous) in length and
                split_line[0] == "import" and split_previous[0] == "import"):
            if split_line[1] < split_previous[1]:
                yield (0, "H306: imports not in alphabetical order (%s, %s)"
                       % (split_previous[1], split_line[1]))


class ImportGroupData:
    """A class to hold persistent state data for import group checks.

    To verify import grouping, it is necessary to know the current group
    for the current file.  This can not always be known solely from the
    current and previous line, so this class can be used to keep track.
    """

    # NOTE(bnemec): *args is needed because the test code tries to run this
    # as a flake8 check and passes an argument to it.
    def __init__(self, *args):
        self.current_group = None
        self.current_filename = None
        self.current_import = None


together_data = ImportGroupData()


@flake8ext
def hacking_import_groups_together(logical_line, blank_lines, indent_level,
                                   previous_indent_level, line_number,
                                   physical_line, filename, noqa):
    r"""Check that like imports are grouped together.

    OpenStack HACKING guide recommendation for imports:
    Imports should be grouped together by type.

    Okay: import os\nimport sys
    Okay: try:\n    import foo\nexcept ImportError:\n    pass\n\nimport six
    H307: import os\n\nimport sys
    """
    if line_number == 1 or filename != together_data.current_filename:
        together_data.current_group = None
    together_data.current_filename = filename

    if noqa:
        return

    normalized_line = import_normalize(logical_line.strip()).split()
    if normalized_line and normalized_line[0] == 'import':
        current_type = _get_import_type(normalized_line[1])
        previous_import = together_data.current_import
        together_data.current_import = normalized_line[1]
        matched = current_type == together_data.current_group
        together_data.current_group = current_type
        if (matched and indent_level == previous_indent_level and
                blank_lines >= 1):
            yield(0, 'H307: like imports should be grouped together (%s and '
                  '%s from %s are separated by whitespace)' %
                  (previous_import,
                   together_data.current_import,
                   current_type))


def _find_first_of(line, substrings):
    """Find earliest occurrence of one of substrings in line.

    Returns pair of index and found substring, or (-1, None)
    if no occurrences of any of substrings were found in line.
    """
    starts = ((line.find(i), i) for i in substrings)
    found = [(i, sub) for i, sub in starts if i != -1]
    if found:
        return min(found)
    else:
        return -1, None


def is_docstring(tokens, previous_logical):
    """Return found docstring

    'A docstring is a string literal that occurs as the first statement in a
    module, function, class,'
    http://www.python.org/dev/peps/pep-0257/#what-is-a-docstring
    """
    for token_type, text, start, _, _ in tokens:
        if token_type == tokenize.STRING:
            break
        elif token_type != tokenize.INDENT:
            return False
    else:
        return False
    line = text.lstrip()
    start, start_triple = _find_first_of(line, START_DOCSTRING_TRIPLE)
    if (previous_logical.startswith("def ") or
            previous_logical.startswith("class ")):
        if start == 0:
            return text


@flake8ext
def hacking_docstring_start_space(physical_line, previous_logical, tokens):
    r"""Check for docstring not starting with space.

    OpenStack HACKING guide recommendation for docstring:
    Docstring should not start with space

    Okay: def foo():\n    '''This is good.'''
    Okay: def foo():\n    r'''This is good.'''
    Okay: def foo():\n    a = ''' This is not a docstring.'''
    Okay: def foo():\n    pass\n    ''' This is not.'''
    H401: def foo():\n    ''' This is not.'''
    H401: def foo():\n    r''' This is not.'''
    """
    docstring = is_docstring(tokens, previous_logical)
    if docstring:
        start, start_triple = _find_first_of(docstring, START_DOCSTRING_TRIPLE)
        if docstring[len(start_triple)] == ' ':
            # docstrings get tokenized on the last line of the docstring, so
            # we don't know the exact position.
            return (0, "H401: docstring should not start with"
                    " a space")


@flake8ext
def hacking_docstring_one_line(physical_line, previous_logical, tokens):
    r"""Check one line docstring end.

    OpenStack HACKING guide recommendation for one line docstring:
    A one line docstring looks like this and ends in punctuation.

    Okay: def foo():\n    '''This is good.'''
    Okay: def foo():\n    r'''This is good.'''
    Okay: def foo():\n    '''This is good too!'''
    Okay: def foo():\n    '''How about this?'''
    Okay: def foo():\n    a = '''This is not a docstring'''
    Okay: def foo():\n    pass\n    '''This is not a docstring'''
    Okay: def foo():\n    pass\n    r'''This is not a docstring'''
    Okay: class Foo:\n    pass\n    '''This is not a docstring'''
    H402: def foo():\n    '''This is not'''
    H402: def foo():\n    r'''This is not'''
    H402: def foo():\n    '''Bad punctuation,'''
    H402: def foo():\n    '''Bad punctuation:'''
    H402: def foo():\n    '''Bad punctuation;'''
    H402: class Foo:\n    '''Bad punctuation,'''
    H402: class Foo:\n    r'''Bad punctuation,'''
    """
    docstring = is_docstring(tokens, previous_logical)
    if docstring:
        if '\n' in docstring:
            # multi line docstring
            return
        line = physical_line.lstrip()
        end = max([line[-4:-1] == i for i in END_DOCSTRING_TRIPLE])  # end
        if line[-5] not in ['.', '?', '!']:
            return end, "H402: one line docstring needs punctuation."


@flake8ext
def hacking_docstring_multiline_end(physical_line, previous_logical, tokens):
    r"""Check multi line docstring end.

    OpenStack HACKING guide recommendation for docstring:
    Docstring should end on a new line

    Okay: '''foobar\nfoo\nbar\n'''
    Okay: def foo():\n    '''foobar\n\nfoo\nbar\n'''
    Okay: class Foo:\n    '''foobar\n\nfoo\nbar\n'''
    Okay: def foo():\n    a = '''not\na\ndocstring'''
    Okay: def foo():\n    a = '''not\na\ndocstring'''  # blah
    Okay: def foo():\n    pass\n'''foobar\nfoo\nbar\n   d'''
    H403: def foo():\n    '''foobar\nfoo\nbar\ndocstring'''
    H403: def foo():\n    '''foobar\nfoo\nbar\npretend raw: r'''
    H403: class Foo:\n    '''foobar\nfoo\nbar\ndocstring'''\n\n
    """
    docstring = is_docstring(tokens, previous_logical)
    if docstring:
        if '\n' not in docstring:
            # not a multi line
            return
        else:
            last_line = docstring.split('\n')[-1]
        pos = max(last_line.rfind(i) for i in END_DOCSTRING_TRIPLE)
        if len(last_line[:pos].strip()) > 0:
            # Something before the end docstring triple
            return (pos,
                    "H403: multi line docstrings should end on a new line")


@flake8ext
def hacking_docstring_multiline_start(physical_line, previous_logical, tokens):
    r"""Check multi line docstring starts immediately with summary.

    OpenStack HACKING guide recommendation for docstring:
    Docstring should start with a one-line summary, less than 80 characters.

    Okay: '''foobar\n\nfoo\nbar\n'''
    Okay: def foo():\n    a = '''\nnot\na docstring\n'''
    H404: def foo():\n    '''\nfoo\nbar\n'''\n\n
    H404: def foo():\n    r'''\nfoo\nbar\n'''\n\n
    """
    docstring = is_docstring(tokens, previous_logical)
    if docstring:
        if '\n' not in docstring:
            # single line docstring
            return
        start, start_triple = _find_first_of(docstring, START_DOCSTRING_TRIPLE)
        lines = docstring.split('\n')
        if lines[0].strip() == start_triple:
            # docstrings get tokenized on the last line of the docstring, so
            # we don't know the exact position.
            return (0, "H404: multi line docstring "
                    "should start without a leading new line")


@flake8ext
def hacking_docstring_summary(physical_line, previous_logical, tokens):
    r"""Check multi line docstring summary is separated with empty line.

    OpenStack HACKING guide recommendation for docstring:
    Docstring should start with a one-line summary, less than 80 characters.

    Okay: def foo():\n    a = '''\nnot\na docstring\n'''
    Okay: '''foobar\n\nfoo\nbar\n'''
    H405: def foo():\n    '''foobar\nfoo\nbar\n'''
    H405: def foo():\n    r'''foobar\nfoo\nbar\n'''
    H405: def foo():\n    '''foobar\n'''
    """
    docstring = is_docstring(tokens, previous_logical)
    if docstring:
        if '\n' not in docstring:
            # not a multi line docstring
            return
        lines = docstring.split('\n')
        if len(lines) > 1 and len(lines[1].strip()) is not 0:
            # docstrings get tokenized on the last line of the docstring, so
            # we don't know the exact position.
            return (0, "H405: multi line docstring "
                    "summary not separated with an empty line")


@flake8ext
def hacking_no_locals(logical_line, physical_line, tokens, noqa):
    """Do not use locals() for string formatting.

    Okay: 'locals()'
    Okay: 'locals'
    Okay: locals()
    Okay: print(locals())
    H501: print("%(something)" % locals())
    Okay: print("%(something)" % locals())  # noqa
    """
    if noqa:
        return
    for_formatting = False
    for token_type, text, start, _, _ in tokens:
        if text == "%" and token_type == tokenize.OP:
            for_formatting = True
        if (for_formatting and token_type == tokenize.NAME and text ==
                "locals" and "locals()" in logical_line):
            yield (start[1], "H501: Do not use locals() for string formatting")


FORMAT_RE = re.compile("%(?:"
                       "%|"           # Ignore plain percents
                       "(\(\w+\))?"   # mapping key
                       "([#0 +-]?"    # flag
                       "(?:\d+|\*)?"  # width
                       "(?:\.\d+)?"   # precision
                       "[hlL]?"       # length mod
                       "\w))")        # type


class LocalizationError(Exception):
    pass


def check_i18n():
    """Generator that checks token stream for localization errors.

    Expects tokens to be ``send``ed one by one.
    Raises LocalizationError if some error is found.
    """
    while True:
        try:
            token_type, text, _, _, line = yield
        except GeneratorExit:
            return

        if (token_type == tokenize.NAME and text == "_" and
                not line.startswith('def _(msg):')):

            while True:
                token_type, text, start, _, _ = yield
                if token_type != tokenize.NL:
                    break
            if token_type != tokenize.OP or text != "(":
                continue  # not a localization call

            format_string = ''
            while True:
                token_type, text, start, _, _ = yield
                if token_type == tokenize.STRING:
                    format_string += eval(text)
                elif token_type == tokenize.NL:
                    pass
                else:
                    break

            if not format_string:
                raise LocalizationError(
                    start, "H701: Empty localization string")
            if token_type != tokenize.OP:
                raise LocalizationError(
                    start, "H701: Invalid localization call")
            if text != ")":
                if text == "%":
                    raise LocalizationError(
                        start,
                        "H702: Formatting operation should be outside"
                        " of localization method call")
                elif text == "+":
                    raise LocalizationError(
                        start,
                        "H702: Use bare string concatenation instead of +")
                else:
                    raise LocalizationError(
                        start, "H702: Argument to _ must be just a string")

            format_specs = FORMAT_RE.findall(format_string)
            positional_specs = [(key, spec) for key, spec in format_specs
                                if not key and spec]
            # not spec means %%, key means %(smth)s
            if len(positional_specs) > 1:
                raise LocalizationError(
                    start, "H703: Multiple positional placeholders")


@flake8ext
def hacking_localization_strings(logical_line, tokens):
    r"""Check localization in line.

    Okay: _("This is fine")
    Okay: _("This is also fine %s")
    Okay: _("So is this %s, %(foo)s") % {foo: 'foo'}
    H701: _('')
    H702: _("Bob" + " foo")
    H702: _("Bob %s" % foo)
    # H703 check is not quite right, disabled by removing colon
    H703 _("%s %s" % (foo, bar))
    """
    # TODO(sdague) actually get these tests working
    gen = check_i18n()
    next(gen)
    try:
        list(map(gen.send, tokens))
        gen.close()
    except LocalizationError as e:
        yield e.args

# TODO(jogo) Dict and list objects


@flake8ext
def hacking_is_not(logical_line):
    r"""Check for use of 'is not' for testing unequal identities.

    Okay: if x is not y:\n    pass
    H901: if not X is Y
    H901: if not X.B is Y
    """
    split_line = logical_line.split()
    if (len(split_line) == 5 and split_line[0] == 'if' and
            split_line[1] == 'not' and split_line[3] == 'is'):
                yield (logical_line.find('not'), "H901: Use the 'is not' "
                       "operator when testing for unequal identities")


@flake8ext
def hacking_not_in(logical_line):
    r"""Check for use of "not in" for evaluating membership.

    Okay: if x not in y:\n    pass
    Okay: if not (X in Y or X is Z):\n    pass
    Okay: if not (X in Y):\n    pass
    H902: if not X in Y
    H902: if not X.B in Y
    """
    split_line = logical_line.split()
    if (len(split_line) == 5 and split_line[0] == 'if' and
            split_line[1] == 'not' and split_line[3] == 'in' and not
            split_line[2].startswith('(')):
                yield (logical_line.find('not'), "H902: Use the 'not in' "
                       "operator for collection membership evaluation")


@flake8ext
def hacking_no_cr(physical_line):
    r"""Check that we only use newlines not carriage returns.

    Okay: import os\nimport sys
    # pep8 doesn't yet replace \r in strings, will work on an
    # upstream fix
    H903 import os\r\nimport sys
    """
    pos = physical_line.find('\r')
    if pos != -1 and pos == (len(physical_line) - 2):
        return (pos, "H903: Windows style line endings not allowed in code")


@flake8ext
def hacking_no_backsplash_line_continuation(logical_line, tokens):
    r"""Wrap lines in parentheses and not a backslash for line continuation.

    Okay: a = (5 +\n     6)
    H904: b = 5 + \\\n    6
    """
    found = False
    for token_type, text, start_index, stop_index, line in tokens:
        if line.rstrip('\r\n').endswith('\\') and not found:
            found = True
            yield ((start_index[0], start_index[1]+len(line.strip())-1),
                   "H904: Wrap long lines in parentheses instead of a "
                   "backslash")


class GlobalCheck(object):
    """Base class for checks that should be run only once."""

    name = None
    version = '0.0.1'
    _has_run = set()

    def __init__(self, tree, *args):
        pass

    def run(self):
        """Make run a no-op if run() has been called before.

        Store in a global registry the list of checks we've run. If we have
        run that one before, just skip doing anything the subsequent times.
        This way, since pep8 is file/line based, we don't wind up re-running
        a check on a git commit message over and over again.
        """
        if self.name and self.name not in self.__class__._has_run:
            self.__class__._has_run.add(self.name)
            ret = self.run_once()
            if ret is not None:
                yield ret

    def run_once(self):
        pass


class GitCheck(GlobalCheck):
    """Base-class for Git related checks."""

    def _get_commit_title(self):
        # Check if we're inside a git checkout
        try:
            subp = subprocess.Popen(
                ['git', 'rev-parse', '--show-toplevel'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            gitdir = subp.communicate()[0].rstrip()
        except OSError:
            # "git" was not found
            return None

        if not os.path.exists(gitdir):
            return None

        # Get title of most recent commit
        subp = subprocess.Popen(
            ['git', 'log', '--no-merges', '--pretty=%s', '-1'],
            stdout=subprocess.PIPE)
        title = subp.communicate()[0]

        if subp.returncode:
            raise Exception("git log failed with code %s" % subp.returncode)
        return title.decode('utf-8')


class OnceGitCheckCommitTitleBug(GitCheck):
    """Check git commit messages for bugs.

    OpenStack HACKING recommends not referencing a bug or blueprint in first
    line. It should provide an accurate description of the change
    H801
    """
    name = "GitCheckCommitTitleBug"

    # From https://github.com/openstack/openstack-ci-puppet
    #       /blob/master/modules/gerrit/manifests/init.pp#L74
    # Changeid|bug|blueprint
    GIT_REGEX = re.compile(
        r'(I[0-9a-f]{8,40})|'
        '([Bb]ug|[Ll][Pp])[\s\#:]*(\d+)|'
        '([Bb]lue[Pp]rint|[Bb][Pp])[\s\#:]*([A-Za-z0-9\\-]+)')

    def run_once(self):
        title = self._get_commit_title()

        # NOTE(jogo) if match regex but over 3 words, acceptable title
        if (title and self.GIT_REGEX.search(title) is not None
                and len(title.split()) <= 3):
            return (1, 0,
                    "H801: git commit title ('%s') should provide an accurate "
                    "description of the change, not just a reference to a bug "
                    "or blueprint" % title.strip(), self.name)


class OnceGitCheckCommitTitleLength(GitCheck):
    """Check git commit message length.

    HACKING recommends commit titles 50 chars or less, but enforces
    a 72 character limit

    H802 Title limited to 72 chars
    """
    name = "GitCheckCommitTitleLength"

    def run_once(self):
        title = self._get_commit_title()

        if title and len(title) > 72:
            return (
                1, 0,
                "H802: git commit title ('%s') should be under 50 chars"
                % title.strip(),
                self.name)


class OnceGitCheckCommitTitlePeriodEnding(GitCheck):
    """Check the end of the first line of git commit messages.

    The first line of git commit message should not end with a period.

    H803 Commit message should not end with a period
    """
    name = "GitCheckCommitTitlePeriodEnding"

    def run_once(self):
        title = self._get_commit_title()

        if title and title.rstrip().endswith('.'):
            return (
                1, 0,
                "H803: git commit title ('%s') should not end with period"
                % title.strip(),
                self.name)


class ProxyChecks(GlobalCheck):
    """Provide a mechanism for locally defined checks."""
    name = 'ProxyChecker'

    @classmethod
    def add_options(cls, parser):
        # We're looking for local checks, so we need to include the local
        # dir in the search path
        sys.path.append('.')

        local_check = CONF.get_multiple('local-check', default=[])
        for check_path in set(local_check):
            if check_path.strip():
                checker = pbr.util.resolve_name(check_path)
                pep8.register_check(checker)

        local_check_fact = CONF.get('local-check-factory')
        if local_check_fact:
            factory = pbr.util.resolve_name(local_check_fact)
            factory(pep8.register_check)

        sys.path.pop()
