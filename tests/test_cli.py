import pytest
from configparser import ConfigParser
from unittest.mock import patch
from pathlib import Path
from click.testing import CliRunner
from braulio.cli import cli
from braulio.git import Tag, Version
from braulio.files import DEFAULT_CHANGELOG, KNOWN_CHANGELOG_FILES


parametrize = pytest.mark.parametrize


@pytest.fixture(params=KNOWN_CHANGELOG_FILES)
def known_changelog_file(request):
    return request.param


class TestInit:

    @parametrize('_input', ['CUSTOM.rst', None])
    def test_empty_repository(self, _input):
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'], input=_input)

            assert result.exit_code == 0
            assert 'Enter a name for the changelog' in result.output

            filename = DEFAULT_CHANGELOG if not _input else _input
            changelog_path = Path.cwd() / filename

            assert changelog_path.exists()

    def test_changelog_filename_option(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            command = ['init', '--changelog-file=CUSTOM.rst']
            result = runner.invoke(cli, command, input='y')

            changelog_path = Path.cwd() / 'CUSTOM.rst'
            config_path = Path.cwd() / 'setup.cfg'

            assert result.exit_code == 0, result.exception
            assert 'CUSTOM.rst created succesfully.' in result.output
            assert 'Updated setup.cfg changelog_file option' in result.output

            assert changelog_path.exists()
            assert config_path.exists()

            config = ConfigParser()
            config.read('setup.cfg')

            assert config.has_section('braulio')
            assert config.get('braulio', 'changelog_file') == 'CUSTOM.rst'

    @pytest.mark.parametrize('_input', ['y', 'n'])
    @patch('braulio.cli.create_changelog_file', autospec=True)
    def test_known_changelog_found(
            self, mock_create_changelog_file, known_changelog_file, _input):

        runner = CliRunner()

        with runner.isolated_filesystem():
            file_path = Path.cwd() / known_changelog_file
            file_path.touch()

            result = runner.invoke(cli, ['init'], input=_input)

            assert f'{known_changelog_file} was found' in result.output
            assert 'Is this the changelog file?' in result.output

            if _input == 'y':
                mock_create_changelog_file.assert_not_called()
            else:
                mock_create_changelog_file.assert_called()


class TestRelease:

    @parametrize(
        'tag_list, from_arg',
        [
            ([], None),
            ([Tag('v0.2.0')], 'v0.2.0'),
            ([Tag('v0.3.3'), Tag('v0.3.2')], 'v0.3.3'),
        ]
    )
    @patch('braulio.release.Git', autospec=True)
    def test_call_to_git_log_method(self, MockGit, tag_list, from_arg):
        mock_git = MockGit()
        mock_git.tags = tag_list
        mock_git.log.return_value = []
        runner = CliRunner()

        result = runner.invoke(cli, ['release'])

        assert 'Nothing to release' in result.output
        mock_git.log.assert_called_with(_from=from_arg)

    @patch('braulio.release.Git', autospec=True)
    def test_no_commits(self, MockGit):
        mock_git = MockGit()
        mock_git.log.return_value = []
        runner = CliRunner()

        result = runner.invoke(cli, ['release'])

        assert 'Nothing to release' in result.output

        mock_git.commit.assert_not_called()
        mock_git.tag.assert_not_called()

    @parametrize('_input', ['y', 'n'])
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.Git', autospec=True)
    def test_confirmation_prompt(self, MockGit, mock_update_changelog, _input):
        runner = CliRunner()

        result = runner.invoke(cli, ['release'], input=_input)
        assert result.exit_code == 0
        assert 'Continue? [y/N]' in result.output

        mock_git = MockGit()

        called = True if _input == 'y' else False

        assert mock_update_changelog.called is called
        assert mock_git.commit.called is called
        assert mock_git.tag.called is called

    @parametrize(
        'option, tags, expected',
        [
            ('--major', [Tag('2015-10-15 v0.10.1')], '1.0.0',),
            ('--minor', [Tag('2015-10-15 v0.10.1')], '0.11.0',),
            ('--patch', [Tag('2015-10-15 v0.10.1')], '0.10.2',),
            ('--major', [], '1.0.0',),
            ('--minor', [], '0.1.0',),
            ('--patch', [], '0.0.1',),
            ('--bump=4.0.0', [Tag('2015-10-15 v2.0.1')], '4.0.0',),
            ('--bump=3.0.0', [], '3.0.0',),
        ],
    )
    @patch('braulio.release.update_changelog', autospec=True)
    @patch('braulio.release.Git', autospec=True)
    def test_manual_version_bump(
            self, MockGit, mock_update_changelog, option, tags, expected):

        mock_git = MockGit()
        mock_git.tags = tags

        runner = CliRunner()
        result = runner.invoke(cli, ['release', option], input='y')

        assert result.exit_code == 0

        mock_update_changelog.assert_called()

        # Check what version was passed to update_changelog function
        passed_args = mock_update_changelog.call_args[1]
        assert passed_args['version'] == Version(expected)

        mock_git.commit.assert_called_with(
            f'Release version {expected}',
            files=['HISTORY.rst'],
        )
        mock_git.tag.assert_called_with(f'v{expected}')

    @parametrize(
        'hash_lst, tags, expected',
        [
            (['4d17c1a', '80a9e0e'], [Tag('2016-10-03 v0.7.6')], '0.7.7'),
            (['4d17c1a', 'ccaa185'], [Tag('2016-10-03 v0.7.6')], '0.8.0'),
            (['8c8dcb7', 'ccaa185'], [Tag('2016-10-03 v0.7.6')], '1.0.0'),
            (['4d17c1a', '80a9e0e'], None, '0.0.1'),
            (['4d17c1a', 'ccaa185'], None, '0.1.0'),
            (['8c8dcb7', 'ccaa185'], None, '1.0.0'),
        ],
    )
    @patch('braulio.release.update_changelog', autospec=True)
    @patch('braulio.release.Git', autospec=True)
    def test_determine_next_version_from_commit_messages(
        self,
        MockGit,
        mocked_update_changelog,
        hash_lst,
        tags,
        expected,
        commit_registry,
    ):
        mock_git = MockGit()
        mock_git.tags = tags
        mock_git.log.return_value = [
            commit_registry[short_hash] for short_hash in hash_lst
        ]

        runner = CliRunner()

        result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 0, result.exception

        mocked_update_changelog.assert_called()

        # Check what version was passed to update_changelog function
        passed_args = mocked_update_changelog.call_args[1]
        assert passed_args['version'] == Version(expected)

        mock_git.commit.assert_called_with(
            f'Release version {expected}',
            files=['HISTORY.rst'],
        )
        mock_git.tag.assert_called_with(f'v{expected}')

    @patch('braulio.release._organize_commits')
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.get_next_version')
    @patch('braulio.release.Git', autospec=True)
    def test_call_to_update_changelog(
        self,
        MockGit,
        mock_get_next_version,
        mock_update_changelog,
        mock_organize_commits,
    ):
        runner = CliRunner()
        result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 0

        mock_git = MockGit()
        mock_git.log.assert_called()

        mock_organize_commits.assert_called_with(
            mock_git.log()
        )

        mock_get_next_version.assert_called_with(
            mock_organize_commits()['bump_version_to'],
            mock_git.tags[0].version
        )

        mock_update_changelog.assert_called_with(
            Path('HISTORY.rst'),
            version=mock_get_next_version(),
            grouped_commits=mock_organize_commits()['by_action']
        )

    @patch('braulio.release.Git', autospec=True)
    def test_changelog_not_found(self, MockGit):
        runner = CliRunner()

        with runner.isolated_filesystem():

            result = runner.invoke(cli, ['release', '-y'])

            assert result.exit_code == 1, result.exc_info
            assert 'Unable to find HISTORY.rst' in result.output
            assert 'Run "$ brau init" to create one' in result.output

            mock_git = MockGit()
            mock_git.commit.assert_not_called()
            mock_git.tag.assert_not_called()

    @patch('braulio.release.Git', autospec=True)
    @patch('braulio.release.update_files', autospec=True)
    def test_files_argument_from_command_line(
        self, mock_update_files, MockGit, fake_repository
    ):

        runner = CliRunner()
        mock_git = MockGit()
        mock_git.tags = []

        with fake_repository('black'):
            files = ['black/__init__.py', 'setup.py']
            result = runner.invoke(cli, ['release', '-y'] + files)

        assert result.exit_code == 0, result.exception
        mock_update_files.assert_called_with(
            ('black/__init__.py', 'setup.py'),
            '0.0.0',
            '0.0.1'
        )

    @patch('braulio.release.Git', autospec=True)
    @patch('braulio.release.update_files', autospec=True)
    def test_files_argument_from_config_file(
        self, mock_update_files, MockGit, fake_repository
    ):

        runner = CliRunner()
        mock_git = MockGit()
        mock_git.tags = []

        with fake_repository('white'):
            result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 0
        mock_update_files.assert_called_with(
            ('white/__init__.py', 'setup.py'),
            '0.0.0',
            '0.0.1'
        )

    @patch('braulio.release.Git', autospec=True)
    @patch('braulio.release.update_files', autospec=True)
    def test_added_files_to_release_commit(
        self, mock_update_files, MockGit, fake_repository
    ):

        runner = CliRunner()
        mock_git = MockGit()
        mock_git.tags = []

        with fake_repository('white'):
            result = runner.invoke(cli, ['release', '--commit', '-y'])

        assert result.exit_code == 0
        mock_git.commit.assert_called_with(
            'Release version 0.0.1',
            files=['HISTORY.rst', 'white/__init__.py', 'setup.py']
        )


@parametrize(
    'flag, config, called',
    [
        ([], {}, True,),
        ([], {'commit': False}, False,),
        (['--no-commit'], {'commit': True}, False,),
        (['--commit'], {'commit': False}, True,),
    ],
)
@patch('braulio.release.Git', autospec=True)
def test_commit_flag(MockGit, flag, config, called, isolated_filesystem):
    """Test commit flag picked from CLI or configuration file"""

    mock_git = MockGit()
    runner = CliRunner()

    with isolated_filesystem:
        Path('HISTORY.rst').touch()

        with open('setup.cfg', 'w') as config_file:
            config_parser = ConfigParser()
            config_parser['braulio'] = config
            config_parser.write(config_file)

        command = ['release'] + flag + ['-y']
        result = runner.invoke(cli, command)

    assert result.exit_code == 0
    assert mock_git.tag.called is True
    assert mock_git.commit.called is called


@parametrize(
    'flag, cfg_value, called',
    [
        ([], {}, True,),
        ([], {'tag': False}, False,),
        (['--no-tag'], {'tag': True}, False,),
        (['--tag'], {'tag': False}, True,),
    ],
)
@patch('braulio.release.Git', autospec=True)
def test_tag_flag(MockGit, flag, cfg_value, called, isolated_filesystem):
    """Test tag flag picked from CLI or configuration file"""

    mock_git = MockGit()
    runner = CliRunner()

    with isolated_filesystem:
        Path('HISTORY.rst').touch()

        with open('setup.cfg', 'w') as config_file:
            config_parser = ConfigParser()
            config_parser['braulio'] = cfg_value
            config_parser.write(config_file)

        command = ['release'] + flag + ['-y']
        result = runner.invoke(cli, command)

    assert result.exit_code == 0
    assert mock_git.tag.called is called
    assert mock_git.commit.called is True
