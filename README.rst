Braulio
=======


.. image:: https://img.shields.io/pypi/v/braulio.svg
        :target: https://pypi.python.org/pypi/braulio

.. image:: https://img.shields.io/travis/mbarakaja/braulio.svg
        :target: https://travis-ci.org/mbarakaja/braulio

.. image:: https://ci.appveyor.com/api/projects/status/dtf3v3m4gchrnt6b?svg=true
        :target: https://ci.appveyor.com/project/mbarakaja/braulio

.. image:: https://readthedocs.org/projects/braulio/badge/?version=latest
        :target: https://braulio.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Simplify software release by handling versioning and changelogs.

Braulio walks through all commits of your Git project and classifies them
to determine what should be the next version and generate a proper changelog.
To do so, it collects only Commits that follow a given message convention.

Read the `documentation`_ to know how it works.


Highlights
----------

* Determine the next version automatically.
* Update the Changelog with new changes.
* Customizable Commit message convention.
* Support pre-releases.
* Can merge pre-release changelogs.



Installing
----------

Install and update using pip:

.. code-block:: bash

    $ pip install -U braulio


Usage
-----

To setup your project

.. code-block:: bash

    $ brau init

To release a new version

.. code-block:: bash

    $ brau release


* Free software: MIT license


.. _documentation: https://braulio.readthedocs.io/en/latest/
