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
import tokenize

from hacking import core


@core.flake8ext
def hacking_todo_format(physical_line, tokens):
    """Check for 'TODO()'.

    OpenStack HACKING guide recommendation for TODO:
    Include your name with TODOs as in "# TODO(termie)"

    Okay: # TODO(sdague)
    H101: # TODO fail
    H101: # TODO
    H101: # TODO (jogo) fail
    Okay: TODO = 5
    """
    # TODO(jogo): make the following doctests pass:
    #            H101: #TODO(jogo fail
    #            H101: #TODO(jogo
    # TODO(jogo): make this check docstrings as well (don't have to be at top
    # of function)
    for token_type, text, start_index, _, _ in tokens:
        if token_type == tokenize.COMMENT:
            pos = text.find('TODO')
            pos1 = text.find('TODO(')
            if (pos != pos1):
                return pos + start_index[1], "H101: Use TODO(NAME)"


@core.flake8ext
def hacking_has_license(physical_line, filename, lines, line_number):
    """Check for Apache 2.0 license.

    H102 license header not found
    """
    # don't work about init files for now
    # TODO(sdague): enforce license in init file if it's not empty of content
    license_found = False

    # skip files that are < 10 lines, which isn't enough for a license to fit
    # this allows us to handle empty files, as well as not fail on the Okay
    # doctests.
    if line_number is 1 and len(lines) > 10 and _project_is_apache():
        for idx, line in enumerate(lines):
            # if it's more than 10 characters in, it's probably not in the
            # header
            if 0 <= line.find('Licensed under the Apache License') < 10:
                    license_found = True
        if not license_found:
            return (0, "H102: Apache 2.0 license header not found")


@core.flake8ext
def hacking_has_correct_license(physical_line, filename, lines, line_number):
    """Check for Apache 2.0 license.

    H103 header does not match Apache 2.0 License notice
    """
    # don't work about init files for now
    # TODO(sdague): enforce license in init file if it's not empty of content

    # skip files that are < 10 lines, which isn't enough for a license to fit
    # this allows us to handle empty files, as well as not fail on the Okay
    # doctests.
    if line_number is 1 and len(lines) > 10 and _project_is_apache():
        for idx, line in enumerate(lines):
            column = line.find('Licensed under the Apache License')
            if (0 < column < 10 and not
                    _check_for_exact_apache(idx, lines)):
                return (column, "H103: Header does not match Apache 2.0 "
                        "License notice")


EMPTY_LINE_RE = re.compile("^\s*(#.*|$)")


@core.flake8ext
def hacking_has_only_comments(physical_line, filename, lines, line_number):
    """Check for empty files with only comments

    H104 empty file with only comments
    """
    if line_number == 1 and all(map(EMPTY_LINE_RE.match, lines)):
        return (0, "H104: File contains nothing but comments")


_is_apache_cache = None


def _project_is_apache():
    """Determine if a project is Apache.

    Look for a key string in a set of possible license files to figure out
    if a project looks to be Apache. This is used as a precondition for
    enforcing license headers.
    """

    global _is_apache_cache
    if _is_apache_cache is not None:
        return _is_apache_cache
    license_files = ["LICENSE"]
    for filename in license_files:
        try:
            with open(filename, "r") as file:
                for line in file:
                    if re.search('Apache License', line):
                        _is_apache_cache = True
                        return True
        except IOError:
            pass
    _is_apache_cache = False
    return False


def _check_for_exact_apache(start, lines):
    """Check for the Apache 2.0 license header.

    We strip all the newlines and extra spaces so this license string
    should work regardless of indentation in the file.
    """
    APACHE2 = """
Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License."""

    # out of all the formatting I've seen, a 12 line version seems to be the
    # longest in the source tree. So just take the 12 lines starting with where
    # the Apache starting words were found, strip all the '#' and collapse the
    # spaces.
    content = ''.join(lines[start:(start + 12)])
    content = re.sub('\#', '', content)
    content = re.sub('\s+', ' ', content).strip()
    stripped_apache2 = re.sub('\s+', ' ', APACHE2).strip()

    if stripped_apache2 in content:
        return True
    else:
        print ("<license>!=<apache2>:\n'%s' !=\n'%s'" %
               (content, stripped_apache2))
        return False
