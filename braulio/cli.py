from pathlib import Path
import os
import click

file_names = ('HISTORY.rst', 'CHANGELOG.rst',)
default_file_name = file_names[0]


def _get_file_name():
    for file_name in file_names:
        if os.path.isfile(file_name):
            return file_name

    return None


def create_file():
    Path(default_file_name).touch()
    click.echo(f'{default_file_name} created succesfully.')


@click.group()
def cli():
    pass


@cli.command()
def init():
    click.echo('Initializing changelog')

    file_name = _get_file_name()

    if not file_name:
        msg = 'No changelog file was found. Do you want to create a new one?'

        if click.confirm(msg):
            create_file()
    else:
        click.echo(f'{file_name} file found')
