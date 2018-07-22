import pytest
from unittest.mock import patch
from datetime import date
from pathlib import Path
from braulio.git import Commit, Version
from braulio.release import _organize_commits
from braulio.files import DEFAULT_CHANGELOG, KNOWN_CHANGELOG_FILES, \
    _make_title, _make_sublist, _make_list, _make_release_markup, \
    update_changelog, update_files


parametrize = pytest.mark.parametrize


def test_default_changelog():
    assert DEFAULT_CHANGELOG == 'HISTORY.rst'


def test_known_changelog_files():
    assert len(KNOWN_CHANGELOG_FILES) == 3
    assert 'HISTORY.rst' in KNOWN_CHANGELOG_FILES
    assert 'CHANGELOG.rst' in KNOWN_CHANGELOG_FILES
    assert 'CHANGES.rst' in KNOWN_CHANGELOG_FILES


@parametrize(
    'level, expected',
    [
        (1, 'Title\n=====\n\n'),
        (2, 'Title\n-----\n\n'),
        (3, 'Title\n~~~~~\n\n'),
    ],
)
def test_make_title(level, expected):
    output = _make_title('Title', level)
    assert output == expected


def test_make_sublist(commit_text_registry):
    reg = commit_text_registry
    commits = [
        Commit(reg['80a9e0e']),
        Commit(reg['0a10908']),
        Commit(reg['eaedb93']),
    ]

    markup = _make_sublist(commits)

    assert markup == (
        f'  - {commits[0].subject}\n'
        f'  - {commits[1].subject}\n'
        f'  - {commits[2].subject}\n'
    )


def test_make_list(commit_text_registry):
    reg = commit_text_registry

    commits = [
        Commit(reg['80a9e0e']),
        Commit(reg['0a10908']),
        Commit(reg['eaedb93']),
    ]

    scope_dict = {
        'scopeless': [
            commits[0],
            commits[1],
        ],
        'scope1': [
            commits[0],
            commits[1],
        ],
        'scope2': [commits[1]],
        'scope3': [
            commits[0],
            commits[1],
        ],
    }

    markup = _make_list(scope_dict)

    assert markup == (
        f'* {commits[0].subject}\n'
        f'* {commits[1].subject}\n'
        '* scope1\n\n'
        f'  - {commits[0].subject}\n'
        f'  - {commits[1].subject}\n'
        f'* scope2 - {commits[1].subject}\n'
        '* scope3\n\n'
        f'  - {commits[0].subject}\n'
        f'  - {commits[1].subject}\n\n'
    )


class Test_make_release_markup:

    def test_release_with_fixes_and_features(self, commit_list):
        version = Version(major=10, minor=3, patch=0)
        commits = _organize_commits(commit_list)
        markup = _make_release_markup(
            version,
            grouped_commits=commits['by_action'],
        )

        assert markup == (
            f'10.3.0 ({str(date.today())})\n'
            '-------------------\n\n'
            'Bug Fixes\n'
            '~~~~~~~~~\n\n'
            '* thing - Fix a thing\n\n'
            'Features\n'
            '~~~~~~~~\n\n'
            '* Add a thing\n'
            '* music\n\n'
            '  - Add more music please\n'
            '  - Add cool musics :D\n'
            '* cli - Add a cli tool\n\n'
        )

    def test_release_with_fixes(self, commit_registry):
        reg = commit_registry
        commit_list = [reg['4d17c1a']]
        commits = _organize_commits(commit_list)
        version = Version(major=10, minor=3, patch=0)

        markup = _make_release_markup(
            version,
            grouped_commits=commits['by_action'],
        )

        assert markup == (
            f'10.3.0 ({str(date.today())})\n'
            '-------------------\n\n'
            'Bug Fixes\n'
            '~~~~~~~~~\n\n'
            '* thing - Fix a thing\n\n'
        )

    def test_release_with_features(self, commit_registry):
        reg = commit_registry
        version = Version(major=10, minor=3, patch=0)
        commit_list = [reg['ccaa185'], reg['bc0bcab'], reg['a6b655f']]
        commits = _organize_commits(commit_list)
        markup = _make_release_markup(
            version,
            grouped_commits=commits['by_action'],
        )

        assert markup == (
            f'10.3.0 ({str(date.today())})\n'
            '-------------------\n\n'
            'Features\n'
            '~~~~~~~~\n\n'
            '* Add a thing\n'
            '* music - Add more music please\n'
            '* cli - Add a cli tool\n\n'
        )


class TestUpdateChangelog:

    @patch('braulio.files._make_release_markup')
    def test_write_to_changelog_file(
        self, mock_make_release_markup, isolated_filesystem
    ):
        mock_make_release_markup.return_value = 'New Content'

        with isolated_filesystem:
            with open('CHANGELOG.rst', 'w') as f:
                f.write(
                    f'{_make_title("History")}'
                    'Content'
                )

            version = Version()
            organized_commits = {}
            path = Path.cwd() / 'CHANGELOG.rst'

            update_changelog(path, version, organized_commits)

            text = Path('CHANGELOG.rst').read_text()

            assert text == (
                'History\n'
                '=======\n\n'
                'New Content'
                'Content'
            )

            mock_make_release_markup.assert_called_with(
                version, organized_commits
            )


class TestUpdateFiles:

    def test_files_missing_version_string(self, fake_repository):
        paths = ['setup.py', 'black/__init__.py']

        with fake_repository('black'):
            message = 'Unable to find a version string to update in "setup.py"'

            with pytest.raises(ValueError, match=message):
                update_files(paths, '4.0.0', '4.1.0')

    def test_file_update(self, fake_repository):
        paths = ['setup.py', 'black/__init__.py']

        with fake_repository('black'):

            update_files(paths, '4.1.3', '5.0.0')

            __init__file = (Path.cwd() / 'black' / '__init__.py').read_text()
            setup_file = (Path.cwd() / 'setup.py').read_text()

        assert setup_file == (
            "from setuptools import setup\n"
            "\n"
            "setup(\n"
            "    name='black',\n"
            "    author='Mr. Black',\n"
            "    description='Jus an example',\n"
            "    version='5.0.0',\n"
            "    zip_safe=False,\n"
            ")\n"
        )

        assert __init__file == (
            "'''\n"
            "    Black project\n"
            "    ~~~~~~~~~~~~~\n"
            "'''\n"
            "\n"
            "__author__ = 'Mr. Black'\n"
            "__email__ = 'black@example.test'\n"
            "__version__ = '5.0.0'\n"
            "\n"
            "\n"
            "def example():\n"
            "    pass\n"
        )
