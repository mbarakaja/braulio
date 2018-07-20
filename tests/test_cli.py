import pytest
from configparser import ConfigParser
from unittest.mock import patch
from pathlib import Path
from click.testing import CliRunner
from braulio.cli import cli
from braulio.git import Tag, Version


parametrize = pytest.mark.parametrize


class TestInit:

    def test_when_changelog_file_is_not_found(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'])

            assert 'Do you want to create a new one?' in result.output
            assert '[y/N]:' in result.output

    def test_create_changelog_file(self):

        runner = CliRunner()

        with runner.isolated_filesystem():
            path = Path.cwd() / 'HISTORY.rst'
            assert not path.exists()

            runner.invoke(cli, ['init'], input='y')

            assert path.exists()

    @pytest.mark.parametrize('file_name', ['HISTORY.rst', 'CHANGELOG.rst'])
    def test_known_changelog_files(self, file_name):
        runner = CliRunner()

        with runner.isolated_filesystem():
            with open(file_name, 'w') as f:
                f.write('')

            result = runner.invoke(cli, ['init'])

            assert f'{file_name} file found' in result.output


class TestRelease:

    @patch('braulio.release.Git', spec=True)
    def test_no_commits(self, MockGit):
        mock_git = MockGit()
        mock_git.get_commits.return_value = []
        runner = CliRunner()

        result = runner.invoke(cli, ['release'])

        assert 'Nothing to release' in result.output
        mock_git.get_commits.assert_called_with(unreleased=True)
        mock_git.add_commit.assert_not_called()
        mock_git.add_tag.assert_not_called()

    @parametrize('_input', ['y', 'n'])
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.Git', spec=True)
    def test_confirmation_prompt(self, MockGit, mock_update_changelog, _input):
        runner = CliRunner()

        result = runner.invoke(cli, ['release'], input=_input)
        assert result.exit_code == 0
        assert 'Continue? [y/N]' in result.output

        mock_git = MockGit()

        if _input == 'y':
            mock_update_changelog.assert_called()
            mock_git.add_commit.assert_called()
            mock_git.add_tag.assert_called()
        else:
            mock_git = MockGit()
            mock_git.add_commit.assert_not_called()
            mock_git.add_tag.assert_not_called()

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
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.Git', spec=True)
    def test_manual_version_bump(
        self,
        MockGit,
        mock_update_changelog,
        option,
        tags,
        expected,
        commit_list,
    ):
        mock_git = MockGit()
        mock_git.get_commits.return_value = commit_list
        mock_git.get_tags.return_value = tags

        runner = CliRunner()
        result = runner.invoke(cli, ['release', option], input='y')

        assert result.exit_code == 0

        mock_update_changelog.assert_called()

        # Check what version was passed to update_changelog function
        passed_args = mock_update_changelog.call_args[1]
        assert passed_args['version'] == Version(expected)

        mock_git.add_commit.assert_called_with(
            f'Release version {expected}',
            files=['HISTORY.rst'],
        )
        mock_git.add_tag.assert_called_with(f'v{expected}')

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
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.Git', spec=True)
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
        mock_git.get_tags.return_value = tags
        mock_git.get_commits.return_value = [
            commit_registry[short_hash] for short_hash in hash_lst
        ]

        runner = CliRunner()

        result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 0, result.exception

        mocked_update_changelog.assert_called()

        # Check what version was passed to update_changelog function
        passed_args = mocked_update_changelog.call_args[1]
        assert passed_args['version'] == Version(expected)

        mock_git.add_commit.assert_called_with(
            f'Release version {expected}',
            files=['HISTORY.rst'],
        )
        mock_git.add_tag.assert_called_with(f'v{expected}')

    @patch('braulio.release._organize_commits')
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.get_next_version')
    @patch('braulio.release.Git', spec=True)
    def test_update_changelog(
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
        mock_git.get_commits.assert_called_with(unreleased=True)

        mock_organize_commits.assert_called_with(
            mock_git.get_commits()
        )

        mock_get_next_version.assert_called_with(
            mock_organize_commits()['bump_version_to'],
            mock_git.get_tags()[0].version
        )

        mock_update_changelog.assert_called_with(
            Path('HISTORY.rst'),
            version=mock_get_next_version(),
            grouped_commits=mock_organize_commits()['by_action']
        )

    @patch('braulio.release.Git')
    def test_changelog_not_found(self, MockGit):
        runner = CliRunner()

        with runner.isolated_filesystem():

            result = runner.invoke(cli, ['release', '-y'])

            assert result.exit_code == 1, result.exc_info
            assert 'Unable to find HISTORY.rst' in result.output
            assert 'Run "$ brau init" to create one' in result.output

            mock_git = MockGit()
            mock_git.add_commit.assert_not_called()
            mock_git.add_tag.assert_not_called()

    @patch('braulio.release.Git')
    @patch('braulio.release.update_files')
    def test_files_argument_from_command_line(
        self, mock_update_files, MockGit, fake_repository
    ):

        runner = CliRunner()
        mock_git = MockGit()
        mock_git.get_tags.return_value = []

        with fake_repository('black'):
            files = ['black/__init__.py', 'setup.py']
            result = runner.invoke(cli, ['release', '-y'] + files)

        assert result.exit_code == 0, result.exception
        mock_update_files.assert_called_with(
            ('black/__init__.py', 'setup.py'),
            '0.0.0',
            '0.0.1'
        )

    @patch('braulio.release.Git')
    @patch('braulio.release.update_files')
    def test_files_argument_from_config_file(
        self, mock_update_files, MockGit, fake_repository
    ):

        runner = CliRunner()
        mock_git = MockGit()
        mock_git.get_tags.return_value = []

        with fake_repository('white'):
            result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 0
        mock_update_files.assert_called_with(
            ('white/__init__.py', 'setup.py'),
            '0.0.0',
            '0.0.1'
        )

    @patch('braulio.release.Git')
    @patch('braulio.release.update_files')
    def test_added_files_to_release_commit(
        self, mock_update_files, MockGit, fake_repository
    ):

        runner = CliRunner()
        mock_git = MockGit()
        mock_git.get_tags.return_value = []

        with fake_repository('white'):
            result = runner.invoke(cli, ['release', '--commit', '-y'])

        assert result.exit_code == 0
        mock_git.add_commit.assert_called_with(
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
@patch('braulio.release.Git', spec=True)
def test_commit_flag(MockGit, flag, config, called, isolated_filesystem):
    """Test commit flag picked from CLI or configuration file"""

    mock_git = MockGit()
    runner = CliRunner()

    with isolated_filesystem:
        changelog_path = Path('HISTORY.rst')
        changelog_path.touch()

        with open('setup.cfg', 'w') as config_file:
            config_parser = ConfigParser()
            config_parser['braulio'] = config
            config_parser.write(config_file)

        command = ['release'] + flag + ['-y']
        result = runner.invoke(cli, command)

    assert result.exit_code == 0
    assert mock_git.add_tag.called is True
    assert mock_git.add_commit.called is called


@parametrize(
    'flag, cfg_value, called',
    [
        ([], {}, True,),
        ([], {'tag': False}, False,),
        (['--no-tag'], {'tag': True}, False,),
        (['--tag'], {'tag': False}, True,),
    ],
)
@patch('braulio.release.Git', spec=True)
def test_tag_flag(MockGit, flag, cfg_value, called, isolated_filesystem):
    """Test tag flag picked from CLI or configuration file"""

    mock_git = MockGit()
    runner = CliRunner()

    with isolated_filesystem:
        changelog_path = Path('HISTORY.rst')
        changelog_path.touch()

        with open('setup.cfg', 'w') as config_file:
            config_parser = ConfigParser()
            config_parser['braulio'] = cfg_value
            config_parser.write(config_file)

        command = ['release'] + flag + ['-y']
        result = runner.invoke(cli, command)

    assert result.exit_code == 0
    assert mock_git.add_tag.called is called
    assert mock_git.add_commit.called is True
