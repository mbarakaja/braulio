import click
from pathlib import Path
from click import style
from braulio.version import validate_version_str
from braulio.release import release as _release
from braulio.config import Config, update_config_file
from braulio.files import find_chglog_file, create_chglog_file, \
    DEFAULT_CHANGELOG


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
@click.option('--bump', 'bump_version_to', callback=bump_callback,
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
def release(ctx, bump_version_to, bump_type, commit_flag, tag_flag,
            confirm_flag, changelog_file, files):

    _release(
        ctx,
        bump_version_to=bump_version_to or bump_type,
        add_commit_flag=commit_flag,
        add_tag_flag=tag_flag,
        confirm_flag=confirm_flag,
        changelog_file=changelog_file,
        files=files,
    )
