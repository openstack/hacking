================================================
hacking: OpenStack Hacking Guideline Enforcement
================================================

hacking is a set of flake8 plugins that test and enforce the :ref:`StyleGuide`.

Hacking pins its dependencies, as a new release of some dependency can break
hacking based gating jobs. This is because new versions of dependencies can
introduce new rules, or make existing rules stricter.

* Contributing: If you are a new contributor to Hacking please refer: :doc:`contributor/contributing`


.. toctree::
   :maxdepth: 3

   user/index

.. toctree::
   :hidden:

   contributor/contributing
