import pytest
from unittest.mock import patch, Mock
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

    @pytest.mark.parametrize(
        'file_name',
        ['HISTORY.rst', 'CHANGELOG.rst'],
    )
    def test_known_changelog_files(self, file_name):
        runner = CliRunner()

        with runner.isolated_filesystem():
            with open(file_name, 'w') as f:
                f.write('')

            result = runner.invoke(cli, ['init'])

            assert f'{file_name} file found' in result.output


class TestRelease:

    @patch('braulio.release.get_commits', return_value=[])
    def test_no_commits(self, mocked_get_commits):
        runner = CliRunner()

        result = runner.invoke(cli, ['release'])

        assert 'Nothing to release' in result.output
        mocked_get_commits.assert_called_with(unreleased=True)

    @patch('braulio.release.get_commits')
    @patch('braulio.release.add_tag')
    @patch('braulio.release.add_commit')
    @patch('braulio.release.update_changelog')
    def test_pass_no_to_confirmation_prompt(
        self,
        mocked_update_changelog,
        mocked_add_commit,
        mocked_add_tag,
        mocked_get_commits
    ):
        runner = CliRunner()

        result = runner.invoke(cli, ['release'])

        assert result.exit_code == 0
        assert 'Continue? [y/N]' in result.output

        mocked_update_changelog.assert_not_called()
        mocked_add_commit.assert_not_called()
        mocked_add_tag.assert_not_called()

    @patch('braulio.release.get_commits')
    @patch('braulio.release.add_tag')
    @patch('braulio.release.add_commit')
    @patch('braulio.release.update_changelog')
    def test_pass_yes_to_confirmation_prompt(
        self,
        mocked_update_changelog,
        mocked_add_commit,
        mocked_add_tag,
        mocked_get_commits,
    ):
        runner = CliRunner()

        result = runner.invoke(cli, ['release'], input='y')
        assert result.exit_code == 0
        assert 'Continue? [y/N]' in result.output

        mocked_update_changelog.assert_called()
        mocked_add_commit.assert_called()
        mocked_add_tag.assert_called()

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
    @patch('braulio.release.add_tag')
    @patch('braulio.release.add_commit')
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.get_tags')
    @patch('braulio.release.get_commits')
    def test_manual_version_bump(
        self,
        mocked_get_commits,
        mocked_get_tags,
        mocked_update_changelog,
        mocked_add_commit,
        mocked_add_tag,
        option,
        tags,
        expected,
        commit_list,
    ):
        mocked_get_commits.return_value = commit_list
        mocked_get_tags.return_value = tags

        runner = CliRunner()
        result = runner.invoke(cli, ['release', option], input='y')

        assert result.exit_code == 0

        mocked_update_changelog.assert_called()

        # Check what version was passed to update_changelog function
        passed_args = mocked_update_changelog.call_args[1]
        assert passed_args['version'] == Version(expected)

        mocked_add_commit.assert_called_with(f'Release version {expected}')
        mocked_add_tag.assert_called_with(f'v{expected}')

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
    @patch('braulio.release.add_tag')
    @patch('braulio.release.add_commit')
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.get_tags')
    @patch('braulio.release.get_commits')
    def test_determine_next_version_from_commit_messages(
        self,
        mocked_get_commits,
        mocked_get_tags,
        mocked_update_changelog,
        mocked_add_commit,
        mocked_add_tag,
        hash_lst,
        tags,
        expected,
        commit_registry,
    ):
        mocked_get_tags.return_value = tags
        mocked_get_commits.return_value = [
            commit_registry[short_hash] for short_hash in hash_lst
        ]

        runner = CliRunner()

        result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 0, result.exception

        mocked_update_changelog.assert_called()

        # Check what version was passed to update_changelog function
        passed_args = mocked_update_changelog.call_args[1]
        assert passed_args['version'] == Version(expected)

        mocked_add_commit.assert_called_with(f'Release version {expected}')
        mocked_add_tag.assert_called_with(f'v{expected}')

    @patch('braulio.release._organize_commits')
    @patch('braulio.release.add_tag')
    @patch('braulio.release.add_commit')
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.get_tags')
    @patch('braulio.release.get_commits')
    @patch('braulio.release.get_next_version')
    def test_update_changelog(
        self,
        mocked_get_next_version,
        mocked_get_commits,
        mocked_get_tags,
        mocked_update_changelog,
        mocked_add_commit,
        mocked_add_tag,
        mocked_organize_commits,
    ):
        runner = CliRunner()
        result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 0

        mocked_get_commits.assert_called_with(unreleased=True)

        mocked_organize_commits.assert_called_with(
            mocked_get_commits()
        )

        mocked_get_next_version.assert_called_with(
            mocked_organize_commits()['bump_version_to'],
            mocked_get_tags()[0].version
        )

        mocked_update_changelog.assert_called_with(
            version=mocked_get_next_version(),
            grouped_commits=mocked_organize_commits()['by_action']
        )

    @patch('braulio.release.add_tag')
    @patch('braulio.release.add_commit')
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.get_tags', return_value=[])
    @patch('braulio.release.get_commits')
    def test_no_commit_flag(
        self,
        mocked_get_commits,
        mocked_get_tags,
        mocked_update_changelog,
        mocked_add_commit,
        mocked_add_tag,
        commit_list,
    ):
        mocked_get_commits.return_value = commit_list

        runner = CliRunner()
        result = runner.invoke(cli, ['release', '--no-commit', '-y'])

        assert result.exit_code == 0

        mocked_add_commit.assert_not_called()
        mocked_add_tag.assert_called()

    @patch('braulio.release.add_tag')
    @patch('braulio.release.add_commit')
    @patch('braulio.release.update_changelog')
    @patch('braulio.release.get_tags', return_value=[])
    @patch('braulio.release.get_commits')
    def test_no_tag_flag(
        self,
        mocked_get_commits,
        mocked_get_tags,
        mocked_update_changelog,
        mocked_add_commit,
        mocked_add_tag,
        commit_list,
    ):
        mocked_get_commits.return_value = commit_list

        runner = CliRunner()
        result = runner.invoke(cli, ['release', '--no-tag', '-y'])

        assert result.exit_code == 0

        mocked_add_commit.assert_called()
        mocked_add_tag.assert_not_called()
