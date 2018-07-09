import pytest
from datetime import date
from unittest.mock import patch, call
from braulio.git import Commit, Version
from braulio.changelog import _make_title, _make_sublist, _make_list, \
    _make_release_markup, update_changelog


parametrize = pytest.mark.parametrize


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


class Test_generate:

    def test_release_with_fixes_and_features(self, commit_registry):
        commits = [commit for key, commit in commit_registry.items()]
        version = Version(major=10, minor=3, patch=0)

        markup = _make_release_markup(version, commits=commits)

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
        commits = [reg['4d17c1a']]
        version = Version(major=10, minor=3, patch=0)

        markup = _make_release_markup(version, commits=commits)

        assert markup == (
            f'10.3.0 ({str(date.today())})\n'
            '-------------------\n\n'
            'Bug Fixes\n'
            '~~~~~~~~~\n\n'
            '* thing - Fix a thing\n\n'
        )

    def test_release_with_features(self, commit_registry):
        reg = commit_registry
        commits = [reg['ccaa185'], reg['bc0bcab'], reg['a6b655f']]
        version = Version(major=10, minor=3, patch=0)

        markup = _make_release_markup(version, commits=commits)

        assert markup == (
            f'10.3.0 ({str(date.today())})\n'
            '-------------------\n\n'
            'Features\n'
            '~~~~~~~~\n\n'
            '* Add a thing\n'
            '* music - Add more music please\n'
            '* cli - Add a cli tool\n\n'
        )
