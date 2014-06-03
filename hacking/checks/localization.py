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


FORMAT_RE = re.compile("%(?:"
                       "%|"           # Ignore plain percents
                       "(\(\w+\))?"   # mapping key
                       "([#0 +-]?"    # flag
                       "(?:\d+|\*)?"  # width
                       "(?:\.\d+)?"   # precision
                       "[hlL]?"       # length mod
                       "\w))")        # type


class LocalizationError(Exception):
    pass


def check_i18n():
    """Generator that checks token stream for localization errors.

    Expects tokens to be ``send``ed one by one.
    Raises LocalizationError if some error is found.
    """
    while True:
        try:
            token_type, text, _, _, line = yield
        except GeneratorExit:
            return

        if text == "def" and token_type == tokenize.NAME:
            # explicitly ignore function definitions, as oslo defines these
            return
        if (token_type == tokenize.NAME and
                text in ["_", "_LI", "_LW", "_LE", "_LC"]):

            while True:
                token_type, text, start, _, _ = yield
                if token_type != tokenize.NL:
                    break
            if token_type != tokenize.OP or text != "(":
                continue  # not a localization call

            format_string = ''
            while True:
                token_type, text, start, _, _ = yield
                if token_type == tokenize.STRING:
                    format_string += eval(text)
                elif token_type == tokenize.NL:
                    pass
                else:
                    break

            if not format_string:
                raise LocalizationError(
                    start, "H701: Empty localization string")
            if token_type != tokenize.OP:
                raise LocalizationError(
                    start, "H701: Invalid localization call")
            if text != ")":
                if text == "%":
                    raise LocalizationError(
                        start,
                        "H702: Formatting operation should be outside"
                        " of localization method call")
                elif text == "+":
                    raise LocalizationError(
                        start,
                        "H702: Use bare string concatenation instead of +")
                else:
                    raise LocalizationError(
                        start, "H702: Argument to _, _LI, _LW, _LC, or _LE "
                        "must be just a string")

            format_specs = FORMAT_RE.findall(format_string)
            positional_specs = [(key, spec) for key, spec in format_specs
                                if not key and spec]
            # not spec means %%, key means %(smth)s
            if len(positional_specs) > 1:
                raise LocalizationError(
                    start, "H703: Multiple positional placeholders")


@core.flake8ext
def hacking_localization_strings(logical_line, tokens, noqa):
    r"""Check localization in line.

    Okay: _("This is fine")
    Okay: _LI("This is fine")
    Okay: _LW("This is fine")
    Okay: _LE("This is fine")
    Okay: _LC("This is fine")
    Okay: _("This is also fine %s")
    Okay: _("So is this %s, %(foo)s") % {foo: 'foo'}
    H701: _('')
    Okay: def _(msg):\n    pass
    Okay: def _LE(msg):\n    pass
    H701: _LI('')
    H701: _LW('')
    H701: _LE('')
    H701: _LC('')
    Okay: _('')  # noqa
    H702: _("Bob" + " foo")
    H702: _LI("Bob" + " foo")
    H702: _LW("Bob" + " foo")
    H702: _LE("Bob" + " foo")
    H702: _LC("Bob" + " foo")
    Okay: _("Bob" + " foo")  # noqa
    H702: _("Bob %s" % foo)
    H702: _LI("Bob %s" % foo)
    H702: _LW("Bob %s" % foo)
    H702: _LE("Bob %s" % foo)
    H702: _LC("Bob %s" % foo)
    # H703 check is not quite right, disabled by removing colon
    H703 _("%s %s" % (foo, bar))
    """
    # TODO(sdague) actually get these tests working
    if noqa:
        return
    gen = check_i18n()
    next(gen)
    try:
        list(map(gen.send, tokens))
        gen.close()
    except LocalizationError as e:
        yield e.args

# TODO(jogo) Dict and list objects
