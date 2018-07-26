braulio
=======


.. image:: https://img.shields.io/pypi/v/braulio.svg
        :target: https://pypi.python.org/pypi/braulio

.. image:: https://img.shields.io/travis/mbarakaja/braulio.svg
        :target: https://travis-ci.org/mbarakaja/braulio

.. image:: https://readthedocs.org/projects/braulio/badge/?version=latest
        :target: https://braulio.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status



Simplify software release by handling version bump and updating changelog file.

Braulio inspects each commit message and determines the next version to be
release based on a couple of conventions. Each commit message must have a tag
in the footer with the format ``!<Type>:<scope>``, where ``<type>`` represents
the commit type. There is no restriction on what value ``<type>`` can be at this
time, but **feat** and **fix** are special, since commit with those types are
included in the **changelog** file and determines the next version.

A commit example:

.. code-block:: text

    Add music please

    Ok, I am going to change it

    !feat:music



Installing
----------

Install and update using pip:

.. code-block:: bash

    pip install -U braulio


Usage
-----

.. code-block:: bash

    brau --help



* Free software: MIT license
