import re
import click
from collections import UserDict
from datetime import date
from pathlib import Path


KNOWN_CHANGELOG_FILES = ('HISTORY.rst', 'CHANGELOG.rst', 'CHANGES.rst')
DEFAULT_CHANGELOG = KNOWN_CHANGELOG_FILES[0]


class ReleaseDataTree(UserDict):
    """Takes a list of :class:`~braulio.git.Commit` objects, and classify them
    by type of action (feat, fix, refactor, etc) and then by the scope of the
    commit.

    This is a dict like class, so, the found actions can be accessed normally
    by the key name.

    Commits without an specified action are filter out.
    """

    def __init__(self, commit_list):

        self.data = {}

        # If this release is braking thing
        is_breaking = False

        for commit in commit_list:
            if commit.action:

                is_breaking = (
                    is_breaking or 'BREAKING CHANGE' in commit.message
                )

                action, scope = commit.action, commit.scope

                if action not in self:
                    self[action] = {'scopeless': []}

                if not scope:
                    self[action]['scopeless'].append(commit)
                    continue
                else:
                    if scope not in self[action]:
                        self[action][commit.scope] = []

                    self[action][scope].append(commit)

        bump_type = 'major' if is_breaking else \
                    'minor' if 'feat' in self else \
                    'patch'

        self._bump_version_to = bump_type

    @property
    def bump_version_to(self):
        return self._bump_version_to


def find_chglog_file():
    for file_name in KNOWN_CHANGELOG_FILES:
        path = Path.cwd() / file_name

        if path.is_file():
            return path
    return None


def create_chglog_file(name=None):
    file_name = name or DEFAULT_CHANGELOG
    path = (Path.cwd() / file_name)
    path.touch()
    path.write_text(_render_title('History'))

    mark = click.style('✓', fg='green')
    click.echo(f' {mark} {file_name} created succesfully.')


def _render_title(title, level=1):
    underlines = ['=', '-', '~']
    underline = underlines[level - 1] * len(title)
    return f'{title}\n{underline}\n\n'


def _render_subtitle(commits):
    markup = ''

    for commit in commits:
        markup += f'  - {commit.subject}\n'

    return markup


def _render_list(scope_dict):
    markup = ''

    for commit in scope_dict['scopeless']:
        markup += f'* {commit.subject}\n'

    del scope_dict['scopeless']

    for scope_name, commit_lst in scope_dict.items():
        markup += f'* {scope_name}'

        if len(commit_lst) > 1:
            markup += '\n\n' + _render_subtitle(commit_lst)
        else:
            markup += f' - {commit_lst[0].subject}\n'

    return markup + '\n'


def _render_release(version, release_data):
    today = str(date.today())
    title = f'{version.string} ({today})'
    markup = _render_title(title, level=2)

    if 'fix' in release_data:
        markup += _render_title('Bug Fixes', level=3)
        markup += _render_list(release_data['fix'])

    if 'feat' in release_data:
        markup += _render_title('Features', level=3)
        markup += _render_list(release_data['feat'])

    return markup


title_adornment_pattern = re.compile("^(?:=|~|-|\*|`|')+$")


def is_title(first, second, third):

    if not first or not second:
        return False

    if (title_adornment_pattern.match(first) and
       len(first) == len(second) and
       first == third):
        return True

    if first == '\n' and third:
        first, second = second, third

    if len(first) == len(second) and title_adornment_pattern.match(second):
        return True

    return False


def _split_chglog(path, title):
    """Split a RST file text in two parts. The title argument determine the
    split point. The given title goes in the bottom part. If the title is not
    found everything goes in the top part.

    Return a tuple with the top and bottom parts.
    """

    with path.open() as f:
        doc = f.readlines()

    has_title = False

    for idx, curr_line in enumerate(doc):

        if title in curr_line:
            prev_line = doc[idx - 1] if idx - 1 < len(doc) else '\n'
            next_line = doc[idx + 1] if idx + 1 < len(doc) else None

            if is_title(prev_line, curr_line, next_line):
                idx = idx if prev_line == '\n' else idx - 1
                has_title = True
                break

    if has_title:
        top, bottom = doc[:idx], doc[idx:]
    else:
        top, bottom = doc, []

    return ''.join(top), ''.join(bottom)


def update_chglog(path, current_version, new_version, release_data):
    top, bottom = _split_chglog(path, title=current_version.string)
    markup = _render_release(new_version, release_data)

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
