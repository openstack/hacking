Introduction
============

hacking is a set of flake8 plugins that test and enforce the `OpenStack
Style Guidlines <http://docs.openstack.org/developer/hacking>`_.

Installation
============

hacking is available from pypi, so just run:

  ``pip install hacking``

This will install ``flake8`` with the ``hacking`` and ``pyflake`` plugins

Origin
======

Most of the additional style guidelines that OpenStack has taken on came from
the Google Python Style Guide.

- http://google-styleguide.googlecode.com/svn/trunk/pyguide.html

Since then, a few more OpenStack specific ones have been added or modified.


Versioning
==========

hacking uses the major.minor.maintenance release notation, where maintenance
releases cannot contain new checks.  This way projects can gate on hacking
by pinning on the major.minor number while accepting maintenance updates
without being concerned that a new version will break the gate with a new
check.


Adding additional checks
========================

Each check is a pep8 plugin so read

- https://github.com/jcrocholl/pep8/blob/master/docs/developer.rst#contribute

The focus of new or changed rules should be to do one of the following

- Substantially increase the reviewability of the code (eg: H301,2,3
  as they make it easy to understand where symbols come from)
- Catch a common programming error that may arrise in the future (H201)
- Prevent a situation that would 100% of the time be -1ed by
  developers (H903)

But, as always, remember that these are Guidelines. Treat them as
such. There are always times for exceptions. All new rules should
support noqa.


Requirements
------------
- The check must already have community support. We do not want to dictate style, only enforce it.
- The canonical source of the OpenStack Style Guidelines is
  `HACKING.rst
  <http://docs.openstack.org/developer/hacking>`_, and hacking just enforces
  them; so when adding a new check, it must be in ``HACKING.rst``
- False negatives are ok, but false positives are not
- Cannot be project specific, project specific checks should be `Local Checks`_
- Docstring tests
- Registered as entry_points in `setup.cfg <setup.cfg>`_
- Error code must be in the relevant ``Hxxx`` group


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
