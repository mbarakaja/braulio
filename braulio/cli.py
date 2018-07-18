import click
from braulio.version import validate_version_str
from braulio.release import release as _release
from braulio.files import get_file_path, create_file
from braulio.config import get_config


@click.group()
@click.pass_context
def cli(ctx):

    config = get_config()

    ctx.default_map = {
        'release': {
            'tag_flag': config.tag,
            'commit_flag': config.commit,
            'confirm_flag': config.confirm,
        }
    }


@cli.command()
def init():
    click.echo('Initializing changelog')

    file_path = get_file_path()

    if not file_path:
        msg = 'No changelog file was found. Do you want to create a new one?'

        if click.confirm(msg):
            create_file()
    else:
        click.echo(f'{file_path.name} file found')


def bump_callback(ctx, param, value):
    if not value or validate_version_str(value):
        return value
    click.echo(f'{value} is not a valid version number')
    ctx.abort()


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
@click.option('-y', 'confirm_flag', is_flag=True, default=False)
def release(bump_version_to, bump_type, commit_flag, tag_flag, confirm_flag):

    _release(
        bump_version_to=bump_version_to or bump_type,
        add_commit_flag=commit_flag,
        add_tag_flag=tag_flag,
        confirm_flag=confirm_flag,
    )
