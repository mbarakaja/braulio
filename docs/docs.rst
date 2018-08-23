Usage
=====


Releasing a new version
-----------------------

To perform a new release use the **release** subcommand:

.. code-block:: console

    $ brau release

You can let the tool determine the :ref:`new version <auto-versioning>` for you or do
a :ref:`manual <manual-versioning>` version release.

Releasing a pre-release version.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To start a pre-release series, Braulio needs a little bit of your help.

Suppose you want the stages of your project to be **dev**, **beta** and
**final**, all of them compatible with PEP440. :ref:`Go first and set them up
<pre-releases>`.


Now, let's suppose the current version of your project is ``1.6.3`` and you
want to start working on a new feature, the next version should be ``1.7.0``.
So to release that version into the **dev** stage run:

.. code-block:: console

    $ brau relase --minor --stage=dev

or using the :ref:`--bump <option-bump>` option:

.. code-block:: console

    $ brau relase --bump=1.7.0dev0

From that point, each time you pass **dev** to :ref:`--stage <option-stage>`,
the numerical part of the pre-release segment will be increased.

.. code-block:: console

    $ brau relase --stage=dev

The current version is now ``1.7.0.dev1``, if you run it again the version will
be ``1.7.0.dev2`` and so on.

When you are ready to release your first **beta** version, just do it like
this:

.. code-block:: console

    $ brau relase --stage=beta

The current version is now ``1.7.0b0``. The numerical part of pre-release
segments always **starts from 0**.

Finally to release the final version, just run the command without any argument.

.. code-block:: console

    $ brau relase

Braulio knows that the project is currently in a pre-release stage of the
version ``1.7.0`` and will release that final version correctly.


.. _determine-current-version:

How the current version is found
--------------------------------

The application will look for the last **Git tag** that matches
:ref:`option-tag-pattern` option, unless :ref:`option-current-version` is
provided by the user either via command line or a configuration file.


.. _auto-versioning:

How the next version is determined
----------------------------------

If you follow the :ref:`Commit Message Convention <convention>` defined for
your project, Braulio will be able to know what type of changes introduces
each commit and based on that determine what should be the next version.

This table shows what type of commit determines the type of release:

+---------------+-----------------------------------------------------+
| Release type  | Commit message metadata                             |
+===============+=====================================================+
| Major release | Commits containing the phrase ``BREAKING CHANGE``   |
+---------------+-----------------------------------------------------+
| Minor release | ``feat`` type commits.                              |
+---------------+-----------------------------------------------------+
| Patch release | ``fix``, ``refactor`` or any other commit type,     |
|               | including those that doesn't follow the convention. |
+---------------+-----------------------------------------------------+

Right now, only the types ``feat`` and ``fix`` are relevant when deciding which
version will be the next.


.. _manual-versioning:

Manual version bump
-------------------

There are 4 options through the command line interface;
:ref:`--patch <option-patch>`, :ref:`--minor <option-minor>`,
:ref:`--major <option-major>` and :ref:`--bump <option-bump>`.

Let' supose your current project version is ``1.6.3``.

+---------+-------------------------------------------------------+
| Option  | Usage                                                 |
+=========+=======================================================+
| --patch | ``$ brau release --patch`` releases to ``1.6.4``.     |
+---------+-------------------------------------------------------+
| --minor | ``$ brau release --minor`` releases to ``1.7.0``.     |
+---------+-------------------------------------------------------+
| --major | ``$ brau release --major`` releases to ``2.0.0``      |
+---------+-------------------------------------------------------+
| --bump  | ``$ brau release --bump=3.0.0`` releases to ``3.0.0`` |
+---------+-------------------------------------------------------+




.. _convention:

Commit Message Convention
-------------------------

Commit messages must have a **label** in a predetermined position. Let's see
the default behavior using the example below.:

.. code-block:: console

    Change the boring music playlist

    Here you have a new list of music:
        - La Grange
        - Fuel
        - Sad but true

    !fix:music

Above, the label is ``!fix:music``. By default, a label must follow the format
``!{type}:{scope}`` and be in the footer. From the previous example the
metadata information extracted from the message is as follow.:

- **subject**: Change the boring music playlist
- **type**: fix
- **scope**: music

The subject is important because it appears in the changelog.

The label format and position are customizable via the options
:ref:`option-label-position` and :ref:`option-label-pattern`. At this moment, a
label can be located only in the **header** or **footer**.

To **customize the label format** use the :ref:`placeholders <placeholders>`
**{type}**, **{scope}**, and **{subject}**. ``{type}`` is mandatory while
``{scope}`` is optional. ``{subject}`` must be used only when the label is in
the message header.

A very popular commit message convention is from the AngularJS project. Here a
commit message extracted from their repository.::

    chore(travis): use Firefox 47

    This commit also adds a new capability to the protractor configs that
    ensures that all angularjs.org tests run correctly on Firefox. See
    SeleniumHQ/selenium#1202

For Braulio to understand the above message, we can add the following options
to the :ref:`configuration file <config-file>`.

.. code-block:: ini

    [braulio]
    label_position = header
    label_pattern  = {type}({scope}): {subject}

Note that we use **{subject}** because the label is in the header and Braulio
needs to know where the subject is to extract it properly. In this case the
subject is ``use Firefox 47``, the scope is ``travis`` and the commit type is
``chore``.

.. topic:: Important

    If the label is located in the footer, **{subject}** must be omitted since
    the entire header will be used as the subject of the commit message.


Since **{scope}** is optional the next Commit header would be valid::

    chore(): use Firefox 47

In this case, the Commit does not have a specific scope, maybe because the code
introduced is too broad.

Breaking changes
~~~~~~~~~~~~~~~~

At this moment, the only way to let Braulio know that a commit introduces
incompatible changes to the codebase is by placing the phrase ``BREAKING CHANGE``
or ``BREAKING CHANGES`` somewhere in the body of the message.

No matter what type of commit is specified with the commit label, this phrase
will instruct Braulio to perform a major version release.

No matter what type of commit you specify in the commit label, this phrase will
instruct Braulio to perform a major version release.


.. _pre-releases:

Setting up pre-releases
-----------------------

To support alpha, beta or any other pre-release version, add them under the
section ``[braulio.stages]`` of your project :ref:`configuration file
<config-file>`.

Each option under that section is considered a stage of your project and their
value must follow the supported version string format (most on that later).
Those version formats will be used to parse version strings and serialize them
back.

.. code-block:: ini

    [braulio.stages]
    dev   = {major}.{minor}.{patch}.dev{n}
    beta  = {major}.{minor}.{patch}b{n}
    final = {major}.{minor}.{patch}

The above indicates that the project release cycle has 3 stages: **dev**,
**beta**, and **final** and the order in which they may happen. The name of
the options acts as the label of the stage and will be used as the argument
for the :ref:`--stage <option-stage>` option when needed.

The order in which stages are defined matters because it determines which
stages are prior to others. The first defined stages are lower.

You can always release to another stage forward, but not backward. For example,
if the current version is ``1.5.0beta6``, an attemp to make a dev release
``1.5.0.dev0`` will fail. If dev and beta were defined in the reverse order,
the release would work.

You can bypass a stage, for example, a release from dev (``0.10.0.dev10``)
stage to a final stage  to (``0.10.0``) will work.

Braulio does not enforce anything about the literal text of the pre-release
segments, so you can have something like this::

    hi = {major}.{minor}.{patch}hello{n}

Here another example with alpha and release candidate stages:

.. code-block:: ini

    [braulio.stages]
    alpha = {major}.{minor}.{patch}a{n}
    rc    = {major}.{minor}.{patch}rc{n}
    final = {major}.{minor}.{patch}

Finally but not less important, **the final stage should be always included**.

Version string format
~~~~~~~~~~~~~~~~~~~~~

The versions string format is defined using :ref:`placeholders <placeholders>`
and the available ones are:

- **{major}** - Major version part.
- **{minor}** - Minor version part.
- **{patch}** - Patch version part.
- **{n}**     - Numerical component that defines the order of releases in
  a pre-release serie.

The first 3 are always mandatory and must be separated by a dot character.::

    {major}.{minor}.{patch}

Following then, any word or character can be present. **{n}** must be at the
end of the string pattern. The next examples are all valid.:

.. code-block:: ini

    # alpha release
    {major}.{minor}.{patch}a{n}

    # Another alpha release style
    {major}.{minor}.{patch}a{n}

    # This have a dot (.) after the patch part
    {major}.{minor}.{patch}.dev{n}

    # Withou a dot (.)
    {major}.{minor}.{patch}dev{n}


.. _placeholders:

About placeholders
------------------

This tool uses string patterns in many of the options it has, but they are not
`Regular Expressions`_.

Instead, it uses placeholders surrounded by curly braces {} as the `Python
Format String Syntax`_. Anything that is not contained in braces is treated as
literal text.

They are used not only to render new strings but also to extract information.

For example, :ref:`option-tag-pattern` is used to find all Git tags that
represent a released version and requires the placeholder ``{version}``. If the
pattern is ``release-{version}``, ``release-2.0.1`` will match but
``released-2.0.1`` won't because the literal part is not equal.

The extracted placeholder information in the above example is ``2.0.1``. When a
new version is released, ``2.2.0`` for example, the new tag name will be
rendered to ``release-2.2.0``.



.. _Regular Expressions: https://en.wikipedia.org/wiki/Regular_expression
.. _Python Format String Syntax: https://docs.python.org/3/library/string.html#format-string-syntax
