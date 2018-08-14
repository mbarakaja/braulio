History
=======

0.3.0b0 (2018-08-14)
--------------------

Bug Fixes
~~~~~~~~~

* release

  - Abort when a lower version is passed to --bump
  - Stop aborting when user inputs No to confirmation prompt
  - Ensure --bump works with versions without minor and patch parts.
  - Validate tag_pattern value
* git - Fix Tag's __repr__ and __str__ methods

Features
~~~~~~~~

* release

  - Support pre-release versions
  - Add option to customize the commit message
  - Add option to specify the current version
  - Add support to custom git tag names
  - Add support to custom commit message conventions
* cli - Add --version option to output current version

0.2.0 (2018-07-25)
------------------

Bug Fixes
~~~~~~~~~

* changelog - Fix release markup being inserted in the wrong place

Features
~~~~~~~~

* release

  - Show useful info while running release subcommand
  - Add support to custom change log file names
  - Support version string update on selected files
* init - Add interactive config and changelog files creation

0.1.0 (2018-07-13)
------------------

Features
~~~~~~~~

* release

  - Add --no-commit and --no-tag options
  - Add options for manual version bump

