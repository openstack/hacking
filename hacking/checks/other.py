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


log_string_interpolation = re.compile(r".*LOG\.(?:error|warn|warning|info"
                                      r"|critical|exception|debug)"
                                      r"\([^,]*%[^,]*[,)]")


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
@core.off_by_default
def hacking_delayed_string_interpolation(logical_line, noqa):
    r"""String interpolation should be delayed at logging calls.

    H904: LOG.debug('Example: %s' % 'bad')
    Okay: LOG.debug('Example: %s', 'good')
    """
    msg = ("H904: String interpolation should be delayed to be "
           "handled by the logging code, rather than being done "
           "at the point of the logging call. "
           "Use ',' instead of '%'.")

    if noqa:
        return

    if log_string_interpolation.match(logical_line):
        yield 0, msg
