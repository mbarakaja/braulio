Configuration
=============

Most of the options that let you configure Braulio's behavior, are available through the
command line tool or a :ref:`config-file` with a few exceptions.

The options provided through the CLI have precedence over those specified in the
configuration file.


.. _config-file:

Config file
-----------

Currently, only the file **setup.cfg** can be used to configure the application.
All the options must be under the section ``[braulio]``. There is a special section:
``[braulio.stages]`` which is used solely to configure the stages of the project.

A config file would look like this:

.. code-block:: ini

    [braulio]
    commit = False
    Tag = False
    confirm = True

    [braulio.stages]
    alpha = {major}.{minor}.{patch}a{n}
    beta  = {major}.{minor}.{patch}b{n}
    final = {major}.{minor}.{patch}


Options
-------

Next, we have a table with all the options for the release subcommand. If an
option is not available through an input method, the cell will be empty.

+------------------------+-----------------+---------------------------------------------------+
| CLI                    | config file     | Descriptions                                      |
+========================+=================+===================================================+
| --major                |                 | Major version bump.                               |
+------------------------+-----------------+---------------------------------------------------+
| --minor                |                 | Minor version bump.                               |
+------------------------+-----------------+---------------------------------------------------+
| --patch                |                 | Patch version bump.                               |
+------------------------+-----------------+---------------------------------------------------+
| --bump                 |                 | Bump to a given version arbitrarily.              |
+------------------------+-----------------+---------------------------------------------------+
| --commit / --no-commit | commit          | Enable/disable release commit                     |
+------------------------+-----------------+---------------------------------------------------+
| --message              | message         | Customizes commit message.                        |
+------------------------+-----------------+---------------------------------------------------+
| --tag / --no-tag       | tag             | Enable/disable version tagging.                   |
+------------------------+-----------------+---------------------------------------------------+
| --changelog-file       | changelog_file  | Specify the changelog file.                       |
+------------------------+-----------------+---------------------------------------------------+
| --label-position       | label_position  | Where the label is located in the commit message. |
+------------------------+-----------------+---------------------------------------------------+
| --label-pattern        | label_pattern   | Pattern to identify labels in commit messages.    |
+------------------------+-----------------+---------------------------------------------------+
| --tag-pattern          | tag_pattern     | Pattern for Git tags that represent versions      |
+------------------------+-----------------+---------------------------------------------------+
| --current-version      | current_version | Manually specify the curren version.              |
+------------------------+-----------------+---------------------------------------------------+
| --stage                |                 | Select a stage where to bump                      |
+------------------------+-----------------+---------------------------------------------------+
| --merge-pre            |                 | Merge pre-release changelogs.                     |
+------------------------+-----------------+---------------------------------------------------+
| -y                     | confirm         | Don't ask for confirmation                        |
+------------------------+-----------------+---------------------------------------------------+
| files (argument)       | files           | Don't ask for confirmation                        |
+------------------------+-----------------+---------------------------------------------------+
| --help                 |                 | Show this message and exit.                       |
+------------------------+-----------------+---------------------------------------------------+


.. _option-bump:

bump
````

+------------+-------------+---------+
| CLI        | Config File | Default |
+============+=============+=========+
| ``--bump`` |             |         |
+------------+-------------+---------+

Takes a valid version string and bump the project version.


.. _option-major:

major
`````

+-------------+-------------+---------+
| CLI         | Config File | Default |
+=============+=============+=========+
| ``--major`` |             |         |
+-------------+-------------+---------+

Perform a major release bumping the major part of the current version.


.. _option-minor:

minor
`````

+-------------+-------------+---------+
| CLI         | Config File | Default |
+=============+=============+=========+
| ``--minor`` |             |         |
+-------------+-------------+---------+

Perform a major release bumping the major part of the current version.


.. _option-patch:

patch
`````

+-------------+-------------+---------+
| CLI         | Config File | Default |
+=============+=============+=========+
| ``--patch`` |             |         |
+-------------+-------------+---------+

Perform a major release bumping the major part of the current version.


.. _option-current-version:

current_version
```````````````

+-----------------------+-----------------+---------+
| CLI                   | Config File     | Default |
+=======================+=================+=========+
| ``--current-version`` | current_version |         |
+-----------------------+-----------------+---------+

Determines the current version of the project. If this option is present in the
configuration file, it will be updated on each new release.


.. _option-tag-pattern:

tag_pattern
```````````

+-------------------+-------------+----------------+
| CLI               | Config File | Default        |
+===================+=============+================+
| ``--tag--patern`` | tag_pattern | ``v{version}`` |
+-------------------+-------------+----------------+

Parse and render Git tag names.

It is used to find Git tags that mark a release, as well as to render tag name
for new releases.

The pattern string must have the :ref:`placeholder <placeholders>` ``{version}``,
which determines where a version string is located in a tag name.

Examples:

The tag pattern ``version{version}`` would match ``version1.0.0``.
The tag pattern ``release-{version}`` would match ``release-1.0.0``.

As stated above, any time a new version is released, the same pattern
will be used to render the new Git tag name.


.. _option-label-position:

label_position
``````````````

+----------------------+----------------+------------+
| CLI                  | Config File    | Default    |
+======================+================+============+
| ``--label-position`` | label_position | ``footer`` |
+----------------------+----------------+------------+

Determines where the commit analyzer must look for commit labels. The available
values are **header** and **footer**.


.. _option-label-pattern:

label_pattern
`````````````

+---------------------+---------------+---------------------+
| CLI                 | Config File   | Default             |
+=====================+===============+=====================+
| ``--label-pattern`` | label_pattern | ``!{type}:{scope}`` |
+---------------------+---------------+---------------------+

The format of label inside commit messages. This uses the next :ref:`placeholders
<placeholders>` to extract metadata information.:

- **{type}**: The type of the commit (fix, feat, chore, etc). Required.
- **{scope}**: The scope where a commit belong. Optional.
- **{subject}**: The subject of the message. Required when the label is located in
  the header.


.. _option-commit:

commit
``````

+--------------------------+-------------+---------+
| CLI                      | Config File | Default |
+==========================+=============+=========+
| ``--commit/--no-commit`` | commit      | True    |
+--------------------------+-------------+---------+

Enable/disable commit of the changes produced by a version bump. If this is
enabled, it will commit only the changelog file and the files provided through
the :ref:`files <option-files>` option.


.. _option-tag:

tag
```

+--------------------+-------------+---------+
| CLI                | Config File | Default |
+====================+=============+=========+
| ``--tag/--no-tag`` | tag         | True    |
+--------------------+-------------+---------+

Enable/disable a release tag after a version bump.

.. _option-message:

message
```````

+---------------+-------------+---------------------------------+
| CLI           | Config File | Default                         |
+===============+=============+=================================+
| ``--message`` | message     | "Release version {new_version}" |
+---------------+-------------+---------------------------------+

If the release commit is enabled, this is used for the message.

This is a template string containing replacement fields. The available fields
are **{new_version}** and **{current_version}**. ``{new_version}`` is
mandatory, while ``{current_version}`` is optional.


.. _option-changelog-file:

changelog_file
``````````````

+----------------------+----------------+---------+
| CLI                  | Config File    | Default |
+======================+================+=========+
| ``--changelog-file`` | changelog_file |         |
+----------------------+----------------+---------+

Path to the changelog file.


.. _option-files:

files
`````

+----------------------+-------------+---------+
| CLI                  | Config File | Default |
+======================+=============+=========+
| ``files (argument)`` | files       |         |
+----------------------+-------------+---------+

List of files to update with a new version string.

Note that in the case of the CLI this is a positional argument and must
be place at the end of the command.

.. code-block:: shell

    $ brau release --bump=4.0.0 file1.py file2.py folder/file3.py

Each file path must be separated by an space.

Through a configuration file, each file path must be in a new line like
the example belog.

.. code-block:: ini

    [braulio]
    files =
        file1.py
        file2.py
        folder/file3.py


.. _option-stage:

stage
`````

+-------------+-------------+---------+
| CLI         | Config File | Default |
+=============+=============+=========+
| ``--stage`` |             |         |
+-------------+-------------+---------+

Determines in what stage a new release must be made.

.. _option-stages:

stages
``````

+-----+------------------+-------------------------------------+
| CLI | Config File      | Default                             |
+=====+==================+=====================================+
|     | [braulio.stages] | ``final = {major}.{minor}.{patch}`` |
+-----+------------------+-------------------------------------+

Only available through a configuration file, this determines the stages of a
project development cycle.

By default the only stage defined is **final**, which must always present:

.. code-block:: console

    [braulio.stages]
    final = {major}.{minor}.{patch}

For more information, read the :ref:`pre-releases` section.
