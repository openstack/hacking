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
import logging
import os
import re
import subprocess
import sys

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
