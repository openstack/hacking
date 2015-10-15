Introduction
============

hacking is a set of flake8 plugins that test and enforce the `StyleGuide`_.

Hacking pins its dependencies, as a new release of some dependency can break
hacking based gating jobs. This is because new versions of dependencies can
introduce new rules, or make existing rules stricter.

.. _`StyleGuide`: http://docs.openstack.org/developer/hacking/#openstack-style-guidelines

Installation
============

hacking is available from pypi, so just run:

  ``pip install hacking``

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

.. _`Google Python Style Guide`: http://google-styleguide.googlecode.com/svn/trunk/pyguide.html

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
- The `StyleGuide`_ is the canonical source of the OpenStack Style; hacking just enforces them. 
  When adding a new check, it must be in ``HACKING.rst``.
- False negatives are ok, but false positives are not
- Cannot be project specific, project specific checks should be `Local Checks`_
- Include extensive tests
- Registered as entry_points in `setup.cfg <setup.cfg>`_
- Error code must be in the relevant ``Hxxx`` group
- The check should not attempt to import modules from the code being checked.
  Importing random modules, has caused all kinds of trouble for us in the past.


Local Checks
============

hacking supports having local changes in a source tree. They can be configured
to run in two different ways. They can be registered individually, or with
a factory function.

For individual registration, put a comma separated list of pep8 compatible
check functions into the hacking section of tox.ini. E.g.:

.. code-block:: ini

  [hacking]
  local-check = nova.tests.hacking.bad_code_is_terrible

Alternately, you can specify the location of a callable that will be called
at registration time and will be passed the registration function. The callable
should expect to call the passed in function on everything if wants to
register. Such as:

.. code-block:: ini

  [hacking]
  local-check-factory = nova.tests.hacking.factory
