# Copyright (c) 2013 SUSE Linux Products GmbH.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect

import fixtures

import hacking.checks.git
import hacking.tests


def _fake_none_commit_title(self):
    return None


class HackingGitTestCase(hacking.tests.TestCase):
    def test_run_outside_git(self):
        """Verify that GitChecks don't fail if no .git available."""

        with fixtures.MonkeyPatch(
                'hacking.checks.git.GitCheck._get_commit_title',
                _fake_none_commit_title):

            for name, obj in inspect.getmembers(hacking.checks.git):
                if (inspect.isclass(obj) and
                   isinstance(obj(None), hacking.checks.git.GitCheck)):
                    obj(None).run_once()
