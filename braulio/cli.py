import click
from pathlib import Path
from click import style
from braulio.git import Git
from braulio.version import Version, validate_version_str, get_next_version
from braulio.config import Config, update_config_file
from braulio.files import find_chglog_file, create_chglog_file, \
    update_chglog, update_files, ReleaseDataTree, DEFAULT_CHANGELOG


prefix_mark = style(' › ', fg='blue', bold=True)
check_mark = click.style('✓', fg='green', bold=True)
x_mark = click.style('✗', fg='red', bold=True)


def msg(message, prefix=prefix_mark, suffix='', silence=False, nl=True):

    if not silence:
        click.echo(f'{prefix}{message}{suffix}', nl=nl)


def label(text):
    spaces = ' ' * (17 - len(text))
    return style(f'{text}{spaces}:', fg="blue", bold=True)


@click.group()
@click.pass_context
def cli(ctx):

    config = Config()
    ctx.obj = config

    ctx.default_map = {
        'release': {
            'tag_flag': config.tag,
            'commit_flag': config.commit,
            'confirm_flag': config.confirm,
        }
    }


@cli.command()
@click.option('--changelog-file', 'changelog_name',
              help='A name for the changelog file to be created')
def init(changelog_name):

    changelog_path = find_chglog_file()
    create_changelog_flag = True
    mark = style('?', fg='blue', bold=True)

    if not changelog_name:
        if changelog_path:
            filename = style(changelog_path.name, fg='blue', bold=True)
            message = (
                f' {mark} {filename} was found.'
                ' Is this the changelog file?'
            )

            if click.confirm(message):
                changelog_name = changelog_path.name
                create_changelog_flag = False

        if create_changelog_flag:
            message = f' {mark} Enter a name for the changelog:'
            changelog_name = click.prompt(message, default=DEFAULT_CHANGELOG)

    if create_changelog_flag:
        create_chglog_file(changelog_name)

    if changelog_name and create_changelog_flag:
        update_config_file('changelog_file', changelog_name)


def bump_callback(ctx, param, value):
    if not value or validate_version_str(value):
        return value
    click.echo(f'{value} is not a valid version number')
    ctx.abort()


def files_callback(ctx, param, value):
    if value:
        return value

    config = ctx.obj
    return config.files


def changelog_file_callback(ctx, param, value):
    '''Return --changelog-file input as Path object if provided, otherwise
    Config.changelog_file.'''

    if value:
        return Path(value)

    config = ctx.obj
    return config.changelog_file


@cli.command()
@click.option('--major', 'bump_type', flag_value='major',
              help='Major version bump')
@click.option('--minor', 'bump_type', flag_value='minor',
              help='Minor version bump')
@click.option('--patch', 'bump_type', flag_value='patch',
              help='Patch version bump')
@click.option('--bump', callback=bump_callback,
              is_eager=True)
@click.option('--commit/--no-commit', 'commit_flag', default=True)
@click.option('--tag/--no-tag', 'tag_flag', default=True)
@click.option('--changelog-file', 'changelog_file',
              type=click.Path(exists=True),
              callback=changelog_file_callback,
              help='Specify where to digest the changelog content')
@click.option('-y', 'confirm_flag', is_flag=True, default=False)
@click.argument('files', nargs=-1, type=click.Path(exists=True),
                callback=files_callback)
@click.pass_context
def release(ctx, bump, bump_type, commit_flag, tag_flag,
            confirm_flag, changelog_file, files):

    git = Git()
    current_version = None
    last_tag_name = None

    if git.tags:
        last_tag_name = git.tags[0].name
        current_version = git.tags[0].version

    commit_list = git.log(_from=last_tag_name)

    msg(f'{label("Current version")} {current_version}')
    msg(f'{label("Commits found")} {len(commit_list)} since last release')

    if not commit_list:
        click.echo(' › Nothing to release.')
        ctx.exit()

    release_data = ReleaseDataTree(commit_list)

    # --bump must have precedence over any of --major, --minor or --patch
    bump_version_to = bump or bump_type

    # Any manual bump must have precedence over bump part determined from
    # commit messages
    bump_version_to = bump_version_to or release_data.bump_version_to

    # If there is no tag in the repository, assume version 0.0.0
    current_version = current_version or Version()

    new_version = get_next_version(bump_version_to, current_version)

    msg(f'{label("New version")} {new_version}')
    msg(f'{label("Changelog file")} {changelog_file.name}')

    # Messages about what tasks will be performed
    msg('Braulio will perform the next tasks :')
    msg(f'        Update {len(files) + 1} files.', prefix='')
    msg('        Add a release commit.', prefix='', silence=not commit_flag)
    msg(f'        Tag the repository with v{new_version.string}', prefix='',
        silence=not tag_flag)

    msg('', prefix='')  # Print just a new line

    if confirm_flag or click.confirm(f'{prefix_mark}Continue?'):

        msg('Update changelog ', nl=False)

        try:
            update_chglog(
                changelog_file,
                new_version=new_version,
                current_version=current_version,
                release_data=release_data,
            )
        except FileNotFoundError:
            msg(x_mark, prefix='')
            filename = click.style(changelog_file.name, fg='blue', bold=True)
            click.echo(
                f' {x_mark} Unable to find {filename}\n'
                '   Run "$ brau init" to create one'
            )
            ctx.abort()

        msg(check_mark, prefix='')

        try:
            update_files(files, str(current_version), str(new_version))
        except ValueError as e:
            click.echo(e)
            ctx.abort()

        if commit_flag:
            commit_message = f'Release version {new_version.string}'

            msg(f'Add commit: {commit_message}', nl=False)

            files = [str(changelog_file)] + list(files)
            git.commit(commit_message, files=files)
            msg(f' {check_mark}', prefix='')

        if tag_flag:
            tagname = 'v' + new_version.string
            msg(f'Add tag {tagname}', nl=False)
            git.tag(tagname)
            msg(f' {check_mark}', prefix='')

        msg(f'Version {new_version} released successfully', suffix=' 🎉')

        return
    ctx.abort()
