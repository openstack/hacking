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

from hacking import core


@core.flake8ext
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


@core.flake8ext
def hacking_no_backslash_line_continuation(logical_line, tokens):
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
