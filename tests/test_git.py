import pytest
from pathlib import Path
from subprocess import PIPE
from unittest.mock import patch, Mock
from braulio.git import _get_commits, _extract_commit_texts, \
    Commit

parametrize = pytest.mark.parametrize


@pytest.fixture(scope='module')
def git_log():
    return Path('tests/data/commits.txt').read_text()


@pytest.fixture(scope='module')
def commit_text_list(git_log):
    return _extract_commit_texts(git_log)


@patch('braulio.git.run')
def test_get_commits(mock_run, git_log):
    mock_captured = Mock()
    mock_captured.stdout.decode.return_value = git_log
    mock_run.return_value = mock_captured

    commits = _get_commits()
    mock_run.assert_called_with(['git', 'log'], stdout=PIPE)

    assert len(commits) == 5

    first = commits[0]
    assert first.header == 'Fix lorem ipsum dolor sit amet'
    assert first.body == (
        'Consectetur adipiscing elit, sed do\n'
        'eiusmod tempor incididunt ut labore et\n'
        'dolore magna aliqua.'
    )

    last = commits[-1]
    assert last.header == 'Add additional information (#26)'
    assert last.body == (
        'But I must explain to you how all this mistaken\n'
        'idea of denouncing pleasure and praising pain was\n'
        'born.\n'
        '\n'
        'Who avoids a pain that produces no resultant pleasure?.'
    )


commits = commit_text_list(git_log())


class TestCommit:

    @parametrize(
        'text, expected',
        [
            (commits[0], 'eaedb9320c7aad581daa05f1510b64393c082dbb'),
            (commits[1], '80a9e0edf6208b3c1c9bc28bfb1a5f04b1f59e1d'),
        ],
        ids=[
            'eaedb9320c7aad581daa05f1510b64393c082dbb',
            '80a9e0edf6208b3c1c9bc28bfb1a5f04b1f59e1d',
        ],
    )
    def test_hash(self, text, expected):
        assert Commit(text).hash == expected

    @parametrize(
        'text, expected',
        [
            (commits[0], 'Fix lorem ipsum dolor sit amet'),
            (commits[1], 'Stop being lazy'),
            (commits[2], 'Add more lorem ipsum text'),
            (commits[-1], 'Add additional information (#26)'),
        ],
        ids=[
            'with body',
            'without line break',
            'without body',
            'with multiple paragraphs',
        ],
    )
    def test_header(self, text, expected):
        assert Commit(text).header == expected

    @parametrize(
        'text',
        (commits[1], commits[2]),
        ids=['no line break before header', 'without body'],
    )
    def test_messages_with_invalid_body(self, text):
        assert Commit(text).body is None

    @parametrize(
        'text, expected',
        [
            (
                commits[0],
                (
                    'Consectetur adipiscing elit, sed do\n'
                    'eiusmod tempor incididunt ut labore et\n'
                    'dolore magna aliqua.'
                )
            ),
            (
                commits[3],
                (
                    'What? Make it yourself.\n'
                    '\n'
                    'Sudo make me a sandwich.'
                )
            ),
            (
                commits[-1],
                (
                    'But I must explain to you how all this mistaken\n'
                    'idea of denouncing pleasure and praising pain was\n'
                    'born.\n'
                    '\n'
                    'Who avoids a pain that produces no resultant pleasure?.'
                )
            ),
        ],
        ids=[
            'Single paragraph',
            'multiple single line paragraphs',
            'multiple paragraphs',
        ],
    )
    def test_messages_with_valid_body(self, text, expected):
        assert Commit(text).body == expected

    @parametrize(
        'last_line, action, scope',
        [
            ('Random text', None, None),
            ('!feat:cli', 'feat', 'cli'),
            ('!feat:cli and some more text', 'feat', 'cli'),
            ('Closed #2 and fixed #3 !feat:cli', 'feat', 'cli'),
            ('!feat:', 'feat', None),
            ('!feat: and some more text', 'feat', None),
            ('Closed #2 and fixed #3 !feat:', 'feat', None),
        ],
    )
    def test_action_and_scope_lookup(self, last_line, action, scope):

        text = (
            'commit eaedb9320c7aad581daa05f1510b64393c082dbb\n'
            'Author: René Descartes <rene.decartes@xyz.test>\n'
            'Date:   Thu Apr 19 14:11:05 2018 +0100\n'
            '\n'
            '    Fix lorem ipsum dolor sit amet\n'
            '\n'
            '    Consectetur adipiscing elit, sed do\n'
            '    eiusmod tempor incididunt ut labore et\n'
            '    dolore magna aliqua.\n'
            '\n'
            f'    {last_line}\n\n'
        )

        commit = Commit(text)

        assert commit.scope == scope
        assert commit.action == action
