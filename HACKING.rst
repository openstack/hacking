OpenStack Style Guidelines
==========================

OpenStack has a set of style guidelines for clarity. OpenStack is a
very large code base (over 1 Million lines of python), spanning dozens
of git trees, with over a thousand developers contributing every 12
months. As such common style helps developers understand code in
reviews, move between projects smoothly, and overall make the code
more maintainable.


Step 0
------

- Step 1: Read http://www.python.org/dev/peps/pep-0008/
- Step 2: Read http://www.python.org/dev/peps/pep-0008/ again
- Step 3: Read on


General
-------
- [H903] Use only UNIX style newlines (``\n``), not Windows style (``\r\n``)
- It is prefered to wrap long lines in parentheses and not a backslash
  for line continuation.
- [H201] Do not write ``except:``, use ``except Exception:`` at the very least
- [H101] Include your name with TODOs as in ``# TODO(yourname)``
- [H105] Don't use author tags.
- Do not shadow a built-in or reserved word. Example::

    def list():
        return [1, 2, 3]

    mylist = list() # BAD, shadows `list` built-in

    class Foo(object):
        def list(self):
            return [1, 2, 3]

    mylist = Foo().list() # OKAY, does not shadow built-in


Imports
-------
- Do not import objects, only modules (*)
- [H301] Do not import more than one module per line (*)
- [H303] Do not use wildcard ``*`` import (*)
- [H304] Do not make relative imports
- [H306] Order your imports by the full module path
- Organize your imports according to the `Import order
  template`_ and `Real-world Import Order Examples`_ below.

(*) exceptions are:

- imports from ``migrate`` package
- imports from ``sqlalchemy`` package
- imports from ``oslo-incubator.openstack.common.gettextutils`` module

Import order template
^^^^^^^^^^^^^^^^^^^^^

::

  {{stdlib imports in human alphabetical order}}
  \n
  {{third-party lib imports in human alphabetical order}}
  \n
  {{project imports in human alphabetical order}}
  \n
  \n
  {{begin your code}}

Real-world Import Order Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Example::

  import httplib
  import logging
  import random
  import StringIO
  import time
  import unittest

  import eventlet
  import webob.exc

  import nova.api.ec2
  from nova.api import manager
  from nova.api import openstack
  from nova.auth import users
  from nova.endpoint import cloud
  import nova.flags
  from nova import test


Docstrings
----------
- [H401] Docstrings should not start with a space.
- [H403] Multi line docstrings should end on a new line.
- [H404] Multi line docstrings should start without a leading new line.
- [H405] Multi line docstrings should start with a one line summary followed
  by an empty line.

Example::

  """A multi line docstring has a one-line summary, less than 80 characters.

  Then a new paragraph after a newline that explains in more detail any
  general information about the function, class or method. Example usages
  are also great to have here if it is a complex class or function.

  When writing the docstring for a class, an extra line should be placed
  after the closing quotations. For more in-depth explanations for these
  decisions see http://www.python.org/dev/peps/pep-0257/

  If you are going to describe parameters and return values, use Sphinx, the
  appropriate syntax is as follows.

  :param foo: the foo parameter
  :param bar: the bar parameter
  :returns: return_type -- description of the return value
  :returns: description of the return value
  :raises: AttributeError, KeyError
  """


Dictionaries/Lists
------------------
If a dictionary (dict) or list object is longer than 80 characters, its items
should be split with newlines. Embedded iterables should have their items
indented. Additionally, the last item in the dictionary should have a trailing
comma. This increases readability and simplifies future diffs.

Example::

  my_dictionary = {
      "image": {
          "name": "Just a Snapshot",
          "size": 2749573,
          "properties": {
              "user_id": 12,
              "arch": "x86_64",
          },
          "things": [
              "thing_one",
              "thing_two",
          ],
          "status": "ACTIVE",
      },
  }


- [H501] Do not use ``locals()`` or ``self.__dict__`` for formatting strings,
   it is not clear as using explicit dictionaries and can hide errors during
   refactoring.

Calling Methods
---------------
Calls to methods 80 characters or longer should format each argument with
newlines. This is not a requirement, but a guideline::

    unnecessarily_long_function_name('string one',
                                     'string two',
                                     kwarg1=constants.ACTIVE,
                                     kwarg2=['a', 'b', 'c'])


Rather than constructing parameters inline, it is better to break things up::

    list_of_strings = [
        'what_a_long_string',
        'not as long',
    ]

    dict_of_numbers = {
        'one': 1,
        'two': 2,
        'twenty four': 24,
    }

    object_one.call_a_method('string three',
                             'string four',
                             kwarg1=list_of_strings,
                             kwarg2=dict_of_numbers)


Internationalization (i18n) Strings
-----------------------------------
In order to support multiple languages, we have a mechanism to support
automatic translations of exception and log strings.

Example::

    msg = _("An error occurred")
    raise HTTPBadRequest(explanation=msg)

- [H702] If you have a variable to place within the string, first
  internationalize the template string then do the replacement.

  Example::

      msg = _LE("Missing parameter: %s") % ("flavor")
      LOG.error(msg)

- [H703] If you have multiple variables to place in the string, use keyword
  parameters. This helps our translators reorder parameters when needed.

  Example::

      msg = _LE("The server with id %(s_id)s has no key %(m_key)s")
      LOG.error(msg % {"s_id": "1234", "m_key": "imageId"})

.. seealso::

   * `oslo.i18n Guidelines <http://docs.openstack.org/developer/oslo.i18n/guidelines.html>`__

Python 3.x compatibility
------------------------
OpenStack code should become Python 3.x compatible. That means all Python 2.x-only
constructs or dependencies should be avoided. In order to start making code
Python 3.x compatible before it can be is fully Python 3.x compatible, we have checks for Python 2.x-only constructs:

- [H231] ``except``. Instead of::

    except x,y:

  Use::

    except x as y:

- [H232] Python 3.x has become more strict regarding octal string
  literals. Use ``0o755`` instead of ``0755``. Similarly, explicit use of long
  literals (``01234L``) should be avoided.

- [H233] The ``print`` operator can be avoided by using::

    from __future__ import print_function

  at the top of your module.

- [H234] ``assertEquals()`` logs a DeprecationWarning in Python 3.x, use
  ``assertEqual()`` instead. The same goes for ``assertNotEquals()``.

- [H235] ``assert_()`` is deprecated in Python 3.x, use ``assertTrue()`` instead.

- [H236] Use ``six.add_metaclass`` instead of ``__metaclass__``.

  Example::

    import six

    @six.add_metaclass(Meta)
    class YourClass():

- [H237] Don't use modules that were removed in Python 3. Removed module list:
  http://python3porting.com/stdlib.html#removed-modules

- [H238] Old style classes are deprecated and no longer available in Python 3
  (they are converted to new style classes). In order to avoid any unwanted side
  effects all classes should be declared using new style. See `the new-style
  class documentation <https://www.python.org/doc/newstyle/>`_ for reference on
  the differences.

  Example::

    class Foo(object):
        pass

Creating Unit Tests
-------------------
For every new feature, unit tests should be created that both test and
(implicitly) document the usage of said feature. If submitting a patch for a
bug that had no unit test, a new passing unit test should be added. If a
submitted bug fix does have a unit test, be sure to add a new one that fails
without the patch and passes with the patch.

Unit Tests and assertRaises
---------------------------

A properly written test asserts that particular behavior occurs. This can
be a success condition or a failure condition, including an exception.
When asserting that a particular exception is raised, the most specific
exception possible should be used.

- [H202] Testing for ``Exception`` being raised is almost always a
  mistake since it will match (almost) every exception, even those
  unrelated to the exception intended to be tested.

  This applies to catching exceptions manually with a try/except block,
  or using ``assertRaises()``.

  Example::

      self.assertRaises(exception.InstanceNotFound, db.instance_get_by_uuid,
                            elevated, instance_uuid)


oslo-incubator
----------------

A number of modules from oslo-incubator are imported into the project.

These modules are "incubating" in oslo-incubator and are kept in sync
with the help of oslo-incubator's update.py script. See:

  https://wiki.openstack.org/wiki/Oslo#Incubation


The copy of the code should never be directly modified here. Please
always update oslo-incubator first and then run the script to copy
the changes across.


OpenStack Trademark
-------------------

OpenStack is a registered trademark of the OpenStack Foundation, and uses the
following capitalization:

   OpenStack


OpenStack Licensing
-------------------

- [H102 H103] Newly contributed Source Code should be licensed under the
  Apache 2.0 license. All source files should have the following header::

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

- [H104] Files with no code shouldn't contain any license header nor comments,
  and must be left completely empty.

Commit Messages
---------------
Using a common format for commit messages will help keep our git history
readable.

For further information on constructing high quality commit messages,
and how to split up commits into a series of changes, consult the
project wiki:

   https://wiki.openstack.org/GitCommitMessages
