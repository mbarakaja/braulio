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
released based on a couple of conventions. Each commit message must have a label
with metadata information about the action and optionally the scope of the code
being introduced.


Commit message convention
-------------------------
Braulio looks for commits that follow a given convention. The convention is
defined by setting up the options ``label_pattern`` and ``label_position``, which
are available through the CLI tool also.

``label_position =``
  The posible values are **header** or **footer** (default). This option tell to
  Braulio where to look for metatada information. 

``label_pattern =``
  This is not a regular expression, but instead is a pattern using placeholders,
  where each placeholder represents a metadata information that should be
  extracted from the commit message. The available placeholders are **{action}**,
  **{scope}** and **{subject}**. ``{action}`` are always required, ``{scope}`` is
  optional and  ``{subject}`` is required only if **label_position** is set to
  ``header``. Everything else is treated in a literal way.


Examples
~~~~~~~~
Given the next setup.cfg file:

.. code-block:: ini

    [braulio]
    label_position = header
    label_pattern = [{action}] {subject}

The config above defines that the label must be localed in the header of the
commit message and must meet the pattern ``[{action}] {subject}``. The next
commit message header must match the pattern:

.. code-block:: bash

    [feat] Add music please

    Ok, I am going to change it

The commit matches the message convention and the extracted information is:

.. code-block:: python

    {
        'action': 'feat',
        'scope': None,
        'subject': 'Add music please'
    }

If the label is located in the footer, ``{subject}`` must be ommited since the
entire header will be used as the subject value. 


Custom Git tag names
--------------------

+-----------------------+--------------------+-------------------------------+
|          CLI          |      Config File   |              Default          |
+-----------------------+--------------------+-------------------------------+
|   ``--tag--patern``   |    tag_pattern     |            v{version}         |
+-----------------------+--------------------+-------------------------------+

Pattern used to get and add release git tags. This is not a regular expression,
Instead it must have the placehold field ``version`` surrounded by curly braces.
The placeholder determines where a version string is located in a given tag
name. Anything that is not contained in braces is considered literal text.

Example
~~~~~~~

In order to match the tag ``release-1.0.0``, ``release-3`` and ``release-35.2``,
the pattern must be ``release-{version}``. As stated above, any time a new
version is released, the same pattern will be used as template to generate the
new Git tag name. The new version string will fill the ``{version}`` placeholder.


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
