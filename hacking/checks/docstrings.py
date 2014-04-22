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

import tokenize

from hacking import core

START_DOCSTRING_TRIPLE = ['u"""', 'r"""', '"""', "u'''", "r'''", "'''"]
END_DOCSTRING_TRIPLE = ['"""', "'''"]


@core.flake8ext
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


@core.flake8ext
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


@core.flake8ext
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


@core.flake8ext
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


@core.flake8ext
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
