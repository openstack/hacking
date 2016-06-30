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


LOCALS_TEXT_MAP = {
    'locals': 'locals()',
    'self': 'self.__dict__'
}


@core.flake8ext
def hacking_no_locals(logical_line, tokens, noqa):
    """Do not use locals() or self.__dict__ for string formatting.

    Okay: 'locals()'
    Okay: 'locals'
    Okay: locals()
    Okay: print(locals())
    H501: print("%(something)" % locals())
    H501: LOG.info(_("%(something)") % self.__dict__)
    Okay: print("%(something)" % locals())  # noqa
    """
    if noqa:
        return
    for_formatting = False
    for token_type, text, start, _, _ in tokens:
        if text == "%" and token_type == tokenize.OP:
            for_formatting = True
        if for_formatting and token_type == tokenize.NAME:
            for k, v in LOCALS_TEXT_MAP.items():
                if text == k and v in logical_line:
                    yield (start[1],
                           "H501: Do not use %s for string formatting" % v)
