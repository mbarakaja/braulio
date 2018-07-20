import re
import click
from datetime import date
from pathlib import Path


file_names = ('HISTORY.rst', 'CHANGELOG.rst',)
DEFAULT_CHANGELOG = file_names[0]


def get_file_path():

    for file_name in file_names:
        path = Path.cwd() / file_name

        if path.is_file():
            return path

    return None


def _make_title(title, level=1):
    underlines = ['=', '-', '~']
    underline = underlines[level - 1] * len(title)
    return f'{title}\n{underline}\n\n'


def create_file():
    path = (Path.cwd() / DEFAULT_CHANGELOG)
    path.touch()

    path.write_text(
        _make_title('History')
    )

    click.echo(f'{DEFAULT_CHANGELOG} created succesfully.')


def _make_sublist(commits):
    markup = ''

    for commit in commits:
        markup += f'  - {commit.subject}\n'

    return markup


def _make_list(scope_dict):
    markup = ''

    for commit in scope_dict['scopeless']:
        markup += f'* {commit.subject}\n'

    del scope_dict['scopeless']

    for scope_name, commit_lst in scope_dict.items():
        markup += f'* {scope_name}'

        if len(commit_lst) > 1:
            markup += '\n\n' + _make_sublist(commit_lst)
        else:
            markup += f' - {commit_lst[0].subject}\n'

    return markup + '\n'


def _make_release_markup(version, grouped_commits):
    today = str(date.today())
    title = f'{version.string} ({today})'
    markup = _make_title(title, level=2)

    if 'fix' in grouped_commits:
        markup += _make_title('Bug Fixes', level=3)
        markup += _make_list(grouped_commits['fix'])

    if 'feat' in grouped_commits:
        markup += _make_title('Features', level=3)
        markup += _make_list(grouped_commits['feat'])

    return markup


def update_changelog(path, version, grouped_commits):

    markup = _make_release_markup(version, grouped_commits)
    lines = []

    with path.open() as f:
        for line in f:
            lines.append(line)

    top = ''.join(lines[:3])
    bottom = ''.join(lines[3:])

    path.write_text(top + markup + bottom)


version_pattern = re.compile("_?_?version_?_?\s?=\s?(?:'|\")")


def update_files(paths, current_version, new_version):
    path_list = [Path(p) for p in paths]

    for path in path_list:
        if not path.is_file():
            click.echo(f'The file {path} is invalid or does not exist')

        text = ''
        string_found = False

        with path.open() as f:
            for line in f:
                if version_pattern.search(line) and current_version in line:
                    line = line.replace(current_version, new_version)
                    string_found = True

                text += line

        if not string_found:
            raise ValueError(
                f'Unable to find a version string to update in "{path}"'
            )

        path.write_text(text)
