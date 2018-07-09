import click
from braulio import release as _release
from braulio.changelog import get_file_path, create_file


@click.group()
def cli():
    pass


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


@cli.command()
def release():
    _release.release()
