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

Built as a sets of pycodestyle checks using flake8.
"""

import gettext
import sys

from hacking import config

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
    if not hasattr(f, 'off_by_default'):
        f.off_by_default = False
    return f


def off_by_default(f):
    """Decorator to turn check off by default.

    To enable the check use the flake8 select setting in
    tox.ini.

    flake8 documentation:
    http://flake8.readthedocs.org/en/latest/extensions.html.
    """
    f.off_by_default = True
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


def is_import_exception(mod):
    """Check module name to see if import has been whitelisted.

       Import based rules should not run on any whitelisted module
       """
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


class GlobalCheck(object):
    """Base class for checks that should be run only once."""

    name = None
    version = '0.0.1'
    skip_on_py3 = False
    _has_run = set()

    def __init__(self, tree, *args):
        pass

    def run(self):
        """Make run a no-op if run() has been called before.

        Store in a global registry the list of checks we've run. If we have
        run that one before, just skip doing anything the subsequent times.
        This way, since pycodestyle is file/line based, we don't wind
        up re-running a check on a git commit message over and over again.
        """
        if self.name and self.name not in self.__class__._has_run:
            self.__class__._has_run.add(self.name)
            ret = self.run_once()
            if ret is not None:
                yield ret

    def run_once(self):
        pass
