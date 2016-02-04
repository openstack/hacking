# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import re

from hacking import core


vim_header_re = re.compile(r"^#\s+vim?:.+")


@core.flake8ext
@core.off_by_default
def no_vim_headers(physical_line, line_number, lines):
    r"""Check for vim editor configuration in source files.

    By default vim modelines can only appear in the first or
    last 5 lines of a source file.

    Examples:
    H106: # vim: set tabstop=4 shiftwidth=4\n#\n#\n#\n#\n#
    H106: # Lic\n# vim: set tabstop=4 shiftwidth=4\n#\n#\n#\n#\n#
    H106: # Lic\n#\n#\n#\n#\n#\n#\n#\n#\n# vim: set tabstop=4 shiftwidth=4
    Okay: # Lic\n#\n#\n#\n#\n#\n#\n#
    Okay: # viminal hill is located in Rome
    Okay: # vim, ze nemluvis cesky
    """
    if ((line_number <= 5 or line_number > len(lines) - 5) and
            vim_header_re.match(physical_line)):
        return 0, "H106: Don't put vim configuration in source files"
