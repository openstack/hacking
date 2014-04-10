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

# module cannot be called except since that is a reserved word

import re

from hacking import core

RE_ASSERT_RAISES_EXCEPTION = re.compile(r"self\.assertRaises\(Exception[,\)]")


@core.flake8ext
def hacking_except_format(logical_line, physical_line, noqa):
    r"""Check for 'except:'.

    OpenStack HACKING guide recommends not using except:
    Do not write "except:", use "except Exception:" at the very least

    Okay: try:\n    pass\nexcept Exception:\n    pass
    H201: try:\n    pass\nexcept:\n    pass
    H201: except:
    Okay: try:\n    pass\nexcept:  # noqa\n    pass
    """
    if noqa:
        return
    if logical_line.startswith("except:"):
        yield 6, "H201: no 'except:' at least use 'except Exception:'"


@core.flake8ext
def hacking_except_format_assert(logical_line, physical_line, noqa):
    r"""Check for 'assertRaises(Exception'.

    OpenStack HACKING guide recommends not using assertRaises(Exception...):
    Do not use overly broad Exception type

    Okay: self.assertRaises(NovaException, foo)
    Okay: self.assertRaises(ExceptionStrangeNotation, foo)
    H202: self.assertRaises(Exception, foo)
    H202: self.assertRaises(Exception)
    Okay: self.assertRaises(Exception)  # noqa
    Okay: self.assertRaises(Exception, foo)  # noqa
    """
    if noqa:
        return
    if RE_ASSERT_RAISES_EXCEPTION.search(logical_line):
        yield 1, "H202: assertRaises Exception too broad"
