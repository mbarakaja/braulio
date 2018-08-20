import click
from pathlib import Path
from click import style
from braulio.git import Git, commit_analyzer, tag_analyzer
from braulio.version import Version, get_next_version
from braulio.config import Config, update_config_file
from braulio.files import (
    find_chglog_file,
    create_chglog_file,
    update_chglog,
    update_files,
    ReleaseDataTree,
    DEFAULT_CHANGELOG,
)


prefix_mark = style(" › ", fg="blue", bold=True)
check_mark = click.style("✓", fg="green", bold=True)
x_mark = click.style("✗", fg="red", bold=True)


def msg(message, prefix=prefix_mark, suffix="", silence=False, nl=True):

    if not silence:
        click.echo(f"{prefix}{message}{suffix}", nl=nl)


def label(text):
    spaces = " " * (17 - len(text))
    return style(f"{text}{spaces}:", fg="blue", bold=True)


@click.group()
@click.version_option(prog_name="Braulio")
@click.pass_context
def cli(ctx):

    config = Config()
    ctx.obj = config

    try:
        Version.set_stages(config.stages.items())
    except ValueError as e:
        ctx.fail(e)

    ctx.default_map = {
        "release": {
            "tag_flag": config.tag,
            "commit_flag": config.commit,
            "confirm_flag": config.confirm,
            "label_position": config.label_position,
            "label_pattern": config.label_pattern,
            "tag_pattern": config.tag_pattern,
            "current_version": config.current_version,
            "changelog_file": config.changelog_file,
            "message": config.message,
        }
    }


@cli.command()
@click.option(
    "--changelog-file",
    "changelog_name",
    help="A name for the changelog file to be created",
)
def init(changelog_name):
    """Setup your project."""

    changelog_path = find_chglog_file()
    create_changelog_flag = True
    mark = style("?", fg="blue", bold=True)

    if not changelog_name:
        if changelog_path:
            filename = style(changelog_path.name, fg="blue", bold=True)
            message = f" {mark} {filename} was found." " Is this the changelog file?"

            if click.confirm(message):
                changelog_name = changelog_path.name
                create_changelog_flag = False

        if create_changelog_flag:
            message = f" {mark} Enter a name for the changelog:"
            changelog_name = click.prompt(message, default=DEFAULT_CHANGELOG)

    if create_changelog_flag:
        create_chglog_file(changelog_name)

    if changelog_name and create_changelog_flag:
        update_config_file("changelog_file", changelog_name)


def bump_option_validator(ctx, param, value):
    """In case a value is provided checks that it is a valid version string. If
    is not thrown :class:`click.UsageError`.

    Return a :class:`~braulio.version.Version` object or **None**.
    """

    if value:
        try:
            value = Version(value)
        except ValueError:
            ctx.fail(f"{x_mark} {value} is not a valid version string")

    return value


def files_callback(ctx, param, value):
    if value:
        return value

    config = ctx.obj
    return config.files


def changelog_file_option_validator(ctx, param, value):
    """Checks that the given file path exists in the current working directory.

    Returns a :class:`~pathlib.Path` object. If the file does not exist raises
    a :class:`~click.UsageError` exception.
    """

    path = Path(value)

    if not path.exists():
        filename = click.style(path.name, fg="blue", bold=True)
        ctx.fail(
            "\n"
            f" {x_mark} Unable to find {filename}\n"
            '   Run "$ brau init" to create one'
        )

    return path


def message_option_validator(ctx, param, value):
    """A commit template must have the **{new_version}** placeholder."""

    if not value or "{new_version}" not in value:
        ctx.fail("Missing {new_version} placeholder in " f"{value}.")

    return value


def tag_pattern_option_validator(ctx, param, value):
    """The provided string must contain **{version}** placeholder in order to
    be valid. Otherwise :class:`click.UsageError` is raised.
    """

    if not value or "{version}" not in value:
        ctx.fail("Missing {version} placeholder in tag_pattern.")

    return value


def current_version_option_validator(ctx, param, value):
    """If a version string is provided, validates it. Otherwise it tries
    to determine the current version from the last Git tag that matches
    ``tag_pattern`` option.

    Return a :class:`~braulio.version.Version` object or **None**.
    """

    current_version = None

    if value:
        try:
            current_version = Version(value)
        except ValueError:
            ctx.fail(f"{value} is not a valid version string")

    # Look for the last git tag for the curren version
    git = Git()
    tag_pattern = ctx.params["tag_pattern"]
    versions = tag_analyzer(git.tags, tag_pattern, Version)

    # User provided current version. Try to find a tag that match it.
    if current_version:
        for version in versions:
            if version == current_version:
                current_version = version
                break
    elif versions:
        current_version = versions[0]

    ctx.params["current_tag"] = current_version.tag if current_version else None
    ctx.params["versions"] = versions

    return current_version


def label_pattern_option_validator(ctx, param, value):
    """Checks that a given string has all the required placeholders. The
    possible placeholders are **{action}**, **{scope}** and **{subject}**.

    ``{action}`` are always required, ``{scope}`` is optional and
    ``{subject}`` are required only when ``label_position`` option is set to
    ``header``.

    If the pattern is invalid, raises :class:`click.UsageError`.
    """

    missings = []
    label_position = ctx.params["label_position"]

    if "{action}" not in value:
        missings.append(style("{action}", fg="red", bold=True))

    if label_position == "header" and "{subject}" not in value:
        missings.append(style("{subject}", fg="red", bold=True))

    if missings:
        message = "\n"

        for placeholder in missings:
            message += f"  {x_mark} Missing {placeholder} placeholder.\n"

        ctx.fail(message)

    return value


def stage_option_validator(ctx, param, value):
    if value:
        for key, stage in Version.stages.items():
            if key == value or stage.label == value:
                return key

        ctx.fail(f"Unknown pre-release stage {value}")

    return value


@cli.command()
@click.option("--major", "bump_type", flag_value="major", help="Major version bump.")
@click.option("--minor", "bump_type", flag_value="minor", help="Minor version bump.")
@click.option("--patch", "bump_type", flag_value="patch", help="Patch version bump.")
@click.option(
    "--bump",
    callback=bump_option_validator,
    help="Bump to a given version arbitrarily.",
)
@click.option(
    "--commit/--no-commit",
    "commit_flag",
    default=True,
    help="Enable/disable release commit",
)
@click.option(
    "--message", callback=message_option_validator, help="Customizes commit message."
)
@click.option(
    "--tag/--no-tag", "tag_flag", default=True, help="Enable/disable version tagging."
)
@click.option(
    "--changelog-file",
    "changelog_file",
    type=click.Path(),
    callback=changelog_file_option_validator,
    help="Specify the changelog file.",
)
@click.option(
    "--label-position",
    type=click.Choice(["header", "footer"]),
    is_eager=True,
    help="Where the label is located in the commit message.",
)
@click.option(
    "--label-pattern",
    callback=label_pattern_option_validator,
    help="Pattern to identify labels in commit messages.",
)
@click.option(
    "--tag-pattern",
    callback=tag_pattern_option_validator,
    is_eager=True,
    help="Pattern for Git tags that represent versions",
)
@click.option(
    "--current-version",
    help="Manually specify the curren version.",
    callback=current_version_option_validator,
)
@click.option("--stage", callback=stage_option_validator, help="User-defined stage")
@click.option(
    "--merge-pre", flag_value=True, default=False, help="Merge pre-release changelogs."
)
@click.option(
    "-y", "confirm_flag", is_flag=True, default=False, help="Don't ask for confirmation"
)
@click.argument(
    "files", nargs=-1, type=click.Path(exists=True), callback=files_callback
)
@click.pass_context
def release(
    ctx,
    bump,
    bump_type,
    commit_flag,
    message,
    tag_flag,
    confirm_flag,
    changelog_file,
    files,
    label_pattern,
    label_position,
    tag_pattern,
    current_version,
    stage,
    merge_pre,
    current_tag=None,
    versions=None,
):

    """Release a new version.

    Determines the next version by inspecting commit messages, updates the
    changelog, commit the changes and tag the repository with the new version.
    """
    # If there isn't a current version, assume version 0.0.0
    current_version = current_version or Version()

    git = Git()
    from_tag = current_tag.name if current_tag else None

    # Delimiter of the block to be removed from the changelog file
    remove_pre_chglog = None

    # Look for the last final release version if the user want it
    if merge_pre and current_version.stage != "final":
        remove_pre_chglog = [current_version.string]

        for version in versions:
            if version.stage == "final":
                from_tag = version.tag.name
                remove_pre_chglog.append(version.string)
                break

    commit_list = git.log(_from=from_tag)

    msg(f'{label("Current version")} {current_version}')
    msg(f'{label("Commits found")} {len(commit_list)} since last release')

    if not commit_list:
        click.echo(" › Nothing to release.")
        ctx.exit()

    semantic_commits = commit_analyzer(commit_list, label_pattern, label_position)

    release_data = ReleaseDataTree(semantic_commits)

    bump_version_to = None

    # --bump, --major, --minor, --patch or commit message based version
    # are taken into account only if the current version is in final stage.
    if current_version.stage == "final":

        # --bump have precedence over any of --major, --minor or --patch
        bump_version_to = bump.string if bump else bump_type

        # Any manual bump have precedence over commit message based versions.
        bump_version_to = bump_version_to or release_data.bump_version_to

    try:
        new_version = get_next_version(current_version, bump_version_to, stage)
    except ValueError as e:
        ctx.fail(e)

    if not new_version:
        msg("The release of a lower versions is not supported for now.")
        ctx.abort()

    new_tag_name = tag_pattern.format(version=new_version.string)

    msg(f'{label("New version")} {new_version}')
    msg(f'{label("Changelog file")} {changelog_file.name}')

    # Messages about what tasks will be performed
    msg("Braulio will perform the next tasks :")
    msg(f"        Update {len(files) + 1} files.", prefix="")
    msg("        Add a release commit.", prefix="", silence=not commit_flag)
    msg(
        f"        Tag the repository with {new_tag_name}",
        prefix="",
        silence=not tag_flag,
    )

    msg("", prefix="")  # Print just a new line

    if confirm_flag or click.confirm(f"{prefix_mark}Continue?"):

        msg("Update changelog ", nl=False)

        update_chglog(
            changelog_file,
            new_version=new_version,
            current_version=current_version,
            release_data=release_data,
            remove=remove_pre_chglog,
        )

        msg(check_mark, prefix="")

        try:
            update_files(files, str(current_version), str(new_version))
        except ValueError as e:
            click.echo(e)
            ctx.abort()

        if commit_flag:
            message_args = {"new_version": new_version.string}

            if "{current_version}" in message:
                message_args["current_version"] = current_version.string

            commit_message = message.format(**message_args)

            msg(f"Add commit: {commit_message}", nl=False)

            files = [str(changelog_file)] + list(files)
            git.commit(commit_message, files=files)
            msg(f" {check_mark}", prefix="")

        if tag_flag:
            msg(f"Add tag {new_tag_name}", nl=False)
            git.tag(new_tag_name)
            msg(f" {check_mark}", prefix="")

        if "current_version" in ctx.obj.cfg_file_options:
            update_config_file("current_version", new_version.string)

        msg(f"Version {new_version} released successfully", suffix=" 🎉")
