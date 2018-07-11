import pytest
from subprocess import PIPE
from unittest.mock import patch, Mock, call
from braulio.git import _run_git_tag_command, _run_git_log_command, \
    get_tags, get_commits, _run_command, add_tag, add_commit, \
    Commit, Tag


parametrize = pytest.mark.parametrize


@patch('braulio.git.run')
def test_run_command(mocked_run):
    mocked_capture = Mock()
    mocked_capture.stdout.decode.return_value = 'output value'
    mocked_run.return_value = mocked_capture

    output = _run_command(['command', 'subcomand'])

    assert output == 'output value'
    mocked_run.assert_called_with(['command', 'subcomand'], stdout=PIPE)


@patch('braulio.git._run_command')
def test_run_git_tag(mocked_run_command):
    mocked_run_command.return_value = 'Stdout text'

    result = _run_git_tag_command()

    mocked_run_command.assert_called_with(
        [
            'git',
            'tag',
            '--sort=creatordate',
            '--format=%(creatordate:short)%09%(refname:strip=2)',
        ],
    )
    assert result == 'Stdout text'


@patch('braulio.git._run_command')
def test_add_tag(mocked_run_command):
    add_tag('tagname')

    mocked_run_command.assert_called_with(
        ['git', 'tag', '-a', 'tagname', '-m', '""'],
    )


@patch('braulio.git._run_command')
def test_add_commit(mocked_run_command):
    add_commit('A message')

    assert mocked_run_command.call_count == 2
    assert mocked_run_command.call_args_list[0] == call(
        ['git', 'add', 'HISTORY.rst'],
    )
    assert mocked_run_command.call_args_list[1] == call(
        ['git', 'commit', '-m', '"A message"'],
    )


@parametrize(
    'unreleased, command, tags',
    [
        (False, ['git', 'log'], [Tag('2015-10-15 v0.0.1')]),
        (False, ['git', 'log'], []),
        (True, ['git', 'log', 'v0.0.1..HEAD'], [Tag('2015-10-15 v0.0.1')]),
        (True, ['git', 'log'], []),
    ]
)
@patch('braulio.git.get_tags')
@patch('braulio.git._run_command')
def test_run_git_log_command(
    mocked_run_command,
    mocked_get_tags,
    unreleased,
    command,
    tags
):
    mocked_run_command.return_value = 'Stdout text'
    mocked_get_tags.return_value = tags

    result = _run_git_log_command(unreleased=unreleased)

    mocked_run_command.assert_called_with(command)
    assert result == 'Stdout text'


class Test_get_commits:

    @patch('braulio.git._run_git_log_command')
    def test_get_all_commits(self, mock_run_git_log, fake_git_log_output):
        mock_run_git_log.return_value = fake_git_log_output

        commits = get_commits()

        mock_run_git_log.assert_called_with(unreleased=False)
        assert len(commits) == 12

        first = commits[0]
        assert first.header == 'Fix lorem ipsum dolor sit amet'

        last = commits[-1]
        assert last.header == 'Add additional information (#26)'

    @patch('braulio.git._run_git_log_command')
    def test_get_unreleased_commits(
        self,
        mock_run_git_log,
        fake_git_log_output
    ):

        mock_run_git_log.return_value = fake_git_log_output

        commits = get_commits(unreleased=True)

        mock_run_git_log.assert_called_with(unreleased=True)
        assert len(commits) == 12

        first = commits[0]
        assert first.header == 'Fix lorem ipsum dolor sit amet'

        last = commits[-1]
        assert last.header == 'Add additional information (#26)'


@parametrize(
    'text, date, name',
    [
        ('2015-10-15      v10.0.1', '2015-10-15', 'v10.0.1'),
        ('2016-02-26      v0.10.13', '2016-02-26', 'v0.10.13'),
        ('2016-07-06      v0.0.5', '2016-07-06', 'v0.0.5'),
        ('2016-10-03      v0.70.6', '2016-10-03', 'v0.70.6'),
    ]
)
def test_tag_class(text, date, name):
    tag = Tag(text)

    assert tag.name == name
    assert tag.date == date


class Test_get_tags:

    @patch('braulio.git._run_git_tag_command')
    def test_without_tags(self, mock_run_git_tag):
        mock_run_git_tag.return_value = ''
        tag_list = get_tags()
        assert tag_list == []

    @patch('braulio.git._run_git_tag_command')
    def test_with_tags(self, mock_run_git_tag):
        mock_run_git_tag.return_value = (
            '2015-10-15      v0.0.1\n'
            '2015-11-18      v0.0.2\n'
            '2016-02-26      v0.0.3\n'
            '2016-03-22      v0.0.4\n'
            '2016-07-06      v0.0.5\n'
            '2016-10-03      v0.0.6\n'
        )

        tag_list = get_tags()

        mock_run_git_tag.assert_called()

        for _tag in tag_list:
            assert type(_tag) == Tag

        assert len(tag_list) == 6
        assert tag_list[0].name == 'v0.0.6'
        assert tag_list[5].name == 'v0.0.1'


class TestCommit:

    @parametrize(
        'short_hash, expected',
        [
            ('eaedb93', 'eaedb9320c7aad581daa05f1510b64393c082dbb'),
            ('80a9e0e', '80a9e0edf6208b3c1c9bc28bfb1a5f04b1f59e1d'),
        ],
        ids=[
            'eaedb9320c7aad581daa05f1510b64393c082dbb',
            '80a9e0edf6208b3c1c9bc28bfb1a5f04b1f59e1d',
        ],
    )
    def test_hash(self, commit_text_registry, short_hash, expected):
        text = commit_text_registry[short_hash]
        assert Commit(text).hash == expected

    @parametrize(
        'short_hash, expected',
        [
            ('eaedb93', 'Fix lorem ipsum dolor sit amet'),
            ('80a9e0e', 'Stop being lazy'),
            ('2f9be68', 'Add more lorem ipsum text'),
            ('0a10908', 'Add additional information (#26)'),
        ],
        ids=[
            'with body',
            'without line break',
            'without body',
            'with multiple paragraphs',
        ],
    )
    def test_header(self, commit_text_registry, short_hash, expected):
        text = commit_text_registry[short_hash]
        assert Commit(text).header == expected

    @parametrize(
        'short_hash',
        ['80a9e0e', '2f9be68'],
        ids=['no line break before header', 'without body'],
    )
    def test_message_with_invalid_body(self, commit_text_registry, short_hash):
        text = commit_text_registry[short_hash]
        assert Commit(text).body is None

    @parametrize(
        'short_hash, expected',
        [
            (
                'eaedb93',
                (
                    'Consectetur adipiscing elit, sed do\n'
                    'eiusmod tempor incididunt ut labore et\n'
                    'dolore magna aliqua.'
                )
            ),
            (
                '82f0d12',
                (
                    'What? Make it yourself.\n'
                    '\n'
                    'Sudo make me a sandwich.'
                )
            ),
            (
                '0a10908',
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
    def test_messages_with_valid_body(
        self,
        commit_text_registry,
        short_hash,
        expected
    ):
        text = commit_text_registry[short_hash]
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
