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

from hacking import core

RE_RELATIVE_IMPORT = re.compile(r'^from\s*[.]')


@core.flake8ext
def hacking_import_rules(logical_line, filename, noqa):
    r"""Check for imports.

    OpenStack HACKING guide recommends one import per line:
    Do not import more than one module per line

    Examples:
    Okay: from nova.compute import api
    H301: from nova.compute import api, utils


    Do not use wildcard import

    Do not make relative imports

    Examples:
    Okay: from os import path
    Okay: from os import path as p
    Okay: from os import (path as p)
    Okay: import os.path
    Okay: from nova.compute import rpcapi
    Okay: from six.moves.urllib import parse
    H303: from os.path import *
    H304: from .compute import rpcapi
    """
    # TODO(jogo): make the following doctests pass:
    #            H301: import os, sys
    # TODO(mordred: We need to split this into different checks so that they
    # can be disabled by command line switches properly

    if noqa:
        return

    split_line = logical_line.split()
    split_line_len = len(split_line)
    if (split_line_len > 1 and split_line[0] in ('import', 'from') and
            not core.is_import_exception(split_line[1])):
        pos = logical_line.find(',')
        if pos != -1:
            if split_line[0] == 'from':
                yield pos, "H301: one import per line"
        pos = logical_line.find('*')
        if pos != -1:
            yield pos, "H303: No wildcard (*) import."
            return

        if split_line_len in (2, 4, 6) and split_line[1] != "__future__":
            if 'from' == split_line[0] and split_line_len > 3:
                mod = '.'.join((split_line[1], split_line[3]))
                if core.is_import_exception(mod):
                    return
                if RE_RELATIVE_IMPORT.search(logical_line):
                    yield logical_line.find('.'), (
                        "H304: No relative imports. '%s' is a relative import"
                        % logical_line)
                    return


@core.flake8ext
def hacking_import_alphabetical(logical_line, blank_before, previous_logical,
                                indent_level, previous_indent_level):
    r"""Check for imports in alphabetical order.

    OpenStack HACKING guide recommendation for imports:
    imports in human alphabetical order

    Okay: import os\nimport sys\n\nimport nova\nfrom nova import test
    Okay: import os\nimport sys
    H306: import sys\nimport os
    Okay: import sys\n\n# foo\nimport six
    """
    # handle import x
    # use .lower since capitalization shouldn't dictate order
    if blank_before < 1 and indent_level == previous_indent_level:
        split_line = core.import_normalize(logical_line.
                                           strip()).lower().split()
        split_previous = core.import_normalize(previous_logical.
                                               strip()).lower().split()
        length = [2, 4]
        if (len(split_line) in length and len(split_previous) in length and
                split_line[0] == "import" and split_previous[0] == "import"):
            if split_line[1] < split_previous[1]:
                yield (0, "H306: imports not in alphabetical order (%s, %s)"
                       % (split_previous[1], split_line[1]))
