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

import os
import re
import subprocess

from hacking import core


class GitCheck(core.GlobalCheck):
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
