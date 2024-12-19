Introduction
============

hacking is a set of flake8 plugins that test and enforce the
`OpenStack StyleGuide <https://docs.openstack.org/hacking/latest/user/hacking.html#styleguide>`_

Hacking pins its dependencies, as a new release of some dependency can break
hacking based gating jobs. This is because new versions of dependencies can
introduce new rules, or make existing rules stricter.

Installation
============

hacking is available from pypi, so just run::

  pip install hacking

This will install specific versions of ``flake8`` with the ``hacking``,
``pep8``, ``mccabe`` and ``pyflakes`` plugins.

Origin
======

Hacking started its life out as a text file in Nova's first commit. It was
initially based on the `Google Python Style Guide`_, and over time more
OpenStack specific rules were added. Hacking serves several purposes:

1. Agree on a common style guide so reviews don't get bogged down on style
   nit picks. (example: docstring guidelines)
2. Make code written by many different authors easier to read by making the
   style more uniform. (example: unix vs windows newlines)
3. Call out dangerous patterns and avoid them. (example: shadowing built-in
   or reserved words)

Initially the hacking style guide was enforced manually by reviewers, but this
was a big waste of time so hacking, the tool, was born to automate
the process and remove the extra burden from human reviewers.

.. _`Google Python Style Guide`: https://google.github.io/styleguide/pyguide.html

Versioning
==========

hacking uses the ``major.minor.maintenance`` release notation, where maintenance
releases cannot contain new checks.  This way projects can gate on hacking
by pinning on the ``major.minor`` number while accepting maintenance updates
without being concerned that a new version will break the gate with a new
check.

For example a project can depend on ``hacking>=0.10.0,<0.11.0``, and can know
that ``0.10.1`` will not fail in places where ``0.10.0`` passed.


Adding additional checks
========================

Each check is a pep8 plugin so read

- https://github.com/jcrocholl/pep8/blob/master/docs/developer.rst#contribute

The focus of new or changed rules should be to do one of the following

- Substantially increase the reviewability of the code (eg: H301, H303)
  as they make it easy to understand where symbols come from)
- Catch a common programming error that may arise in the future (H201)
- Prevent a situation that would 100% of the time be -1ed by
  developers (H903)

But, as always, remember that these are Guidelines. Treat them as
such. There are always times for exceptions. All new rules should
support noqa.

If a check needs to be staged in, or it does not apply to every project or its
branch, it can be added as off by default.

Requirements
------------
- The check must already have community support. We do not want to dictate
  style, only enforce it.
- The canonical source of the OpenStack Style Guidelines is
  `StyleGuide <https://docs.openstack.org/hacking/latest/user/hacking.html#styleguide>`_,
  and hacking just enforces
  them; so when adding a new check, it must be in ``HACKING.rst``
- False negatives are ok, but false positives are not
- Cannot be project specific, project specific checks should be `Local Checks`_
- Include extensive tests
- Registered as entry_points in ``setup.cfg``
- Error code must be in the relevant ``Hxxx`` group
- The check should not attempt to import modules from the code being checked.
  Importing random modules, has caused all kinds of trouble for us in the past.


Enabling off-by-default checks
==============================

Some of the available checks are disabled by default. These checks are:

- [H106] Don't put vim configuration in source files.
- [H203] Use assertIs(Not)None to check for None.
- [H204] Use assert(Not)Equal to check for equality.
- [H205] Use assert(Greater|Less)(Equal) for comparison.
- [H210] Require 'autospec', 'spec', or 'spec_set' in
  mock.patch/mock.patch.object calls
- [H904] Delay string interpolations at logging calls.

To enable these checks, edit the ``flake8`` section of the ``tox.ini`` file.
For example to enable H106 and H203:

.. code-block:: ini

  [flake8]
  enable-extensions = H106,H203

Local Checks
============

hacking supports having local changes in a source tree. They need to
be registered individually in tox.ini:

Add to tox.ini a new section ``flake8:local-plugins`` and list each plugin with
its entry-point. Additionally, you can add the path to the files
containing the plugins so that the repository does not need to be
installed with the ``paths`` directive.

.. code-block:: ini

   [flake8:local-plugins]
   extension =
     N307 = checks:import_no_db_in_virt
     N325 = checks:CheckForStrUnicodeExc
   paths =
     ./nova/hacking

The plugins, in the example above they live in
``nova/hacking/checks.py``, need to annotate all functions with ``@core.flake8ext``

.. code-block:: python

   from hacking import core
   ...
   @core.flake8ext
   def import_no_db_in_virt(logical_line, filename):
       ...

   class CheckForStrUnicodeExc(BaseASTChecker):
      name = "check_for_str_unicode_exc"
      version = "1.0"
      ...

Further details are part of the `flake8 documentation
<https://flake8.pycqa.org/en/latest/plugin-development/index.html>`_.
