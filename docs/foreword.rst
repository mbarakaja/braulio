Foreword
========

This is a brief introduction about how this tool works and what it can do, so
you can know if it is right for your project.


How it works
------------

Braulio walks through all commits of your Git project and classifies them to
determine what should be the next version and generate a proper changelog. To
do so, it collects only Commits that follow a given
:ref:`message convention <convention>`.


Release steps:
~~~~~~~~~~~~~~

- :ref:`Determine the current version <determine-current-version>`.
- Collect unreleased changes.
- Classify them by type and scope.
- :ref:`Determine the new version<auto-versioning>`.
- Generate the changelog.
- Update files with the new version string.
- Commit and tag.



Version schema
--------------

This tool works with the **major.minor.patch** version scheme and most of the
features of `Semantic Versioning 2.0`_ are supported. If you use
`Calendar Versioning`_ or another version schema, this tool is not for you.

It works with final releases as well as **pre-releases**, although you have to
configure the :ref:`stages of your project first <pre-releases>`.

`PEP440`_ dictates how pre-release segments should look. This tool does not
enforce anything about the pre-release segment format, but you can configure it
to fit PEP440.


Changelog
---------

The changelog is generated using the subject extracted from the commit
messages. The output is in ReStructuredText format and can not be
customized at this moment.

Project Status
--------------

This is still in development, and things may change, but you can give it a try
if you want.


.. _Semantic Versioning 2.0: https://semver.org/#semantic-versioning-200
.. _Calendar Versioning: https://calver.org
.. _PEP440: https://www.python.org/dev/peps/pep-0440/#pre-releases
