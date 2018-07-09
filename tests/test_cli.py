import pytest
from unittest.mock import patch
from pathlib import Path
from click.testing import CliRunner
from braulio.cli import cli
from braulio.git import Tag, Version
from braulio.changelog import _make_title


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

    @patch('braulio.git.git.get_commits', return_value=[])
    def test_no_commits(self, mocked_get_commits):
        runner = CliRunner()

        result = runner.invoke(cli, ['release'])

        assert 'Nothing to release' in result.output
        mocked_get_commits.assert_called_with(unreleased=True)

    @parametrize(
        'short_hash_list, tags, xyz',
        [
            (
                ['eaedb93', '4d17c1a', '264af1b'],
                [],
                '0.0.1',
            ),
            (
                ['eaedb93', 'ccaa185'],
                [Tag('2015-11-18 v0.10.2'), Tag('2015-10-15 v0.10.1')],
                '0.11.0',
            ),
            (
                ['eaedb93', '8c8dcb7'],
                [Tag('2015-11-18 v2.10.2'), Tag('2015-10-15 v2.10.1')],
                '3.0.0',
            ),
        ],
        ids=['patch release', 'minor release', 'major release'],
    )
    @patch('braulio.release.git')
    def test_new_release_version(
        self, mock_git, commit_registry, short_hash_list, xyz, tags
    ):
        mock_git.tags = tags
        reg = commit_registry
        mock_git.get_commits.return_value = [reg[h] for h in short_hash_list]
        runner = CliRunner()

        with runner.isolated_filesystem():
            with open('HISTORY.rst', 'w') as f:
                f.write('')

            runner.invoke(cli, ['release'])

            mock_git.add_commit.assert_called_with(f'Release version {xyz}')
            mock_git.add_tag.assert_called_with(f'v{xyz}')

    @patch('braulio.release.git')
    def test_missing_changelog_file(self, mock_git, commit_list):
        mock_git.get_commits.return_value = commit_list
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['release'])
            assert result.output == (
                'Unable to find a changelog file\n'
                'Run "$ brau init" to create one\n'
            )

    @patch('braulio.release.git')
    @patch('braulio.changelog._make_release_markup')
    def test_write_to_changelog_file(
        self, mock_make_release_markup,  mock_git, commit_list
    ):
        mock_git.get_commits.return_value = commit_list
        mock_make_release_markup.return_value = 'New Content'
        runner = CliRunner()

        with runner.isolated_filesystem():
            with open('CHANGELOG.rst', 'w') as f:
                f.write(
                    f'{_make_title("History")}'
                    'Content'
                )

            runner.invoke(cli, ['release'])

            text = Path('CHANGELOG.rst').read_text()

            assert text == (
                'History\n'
                '=======\n\n'
                'New Content'
                'Content'
            )

            mock_make_release_markup.assert_called()
            mock_git.add_commit.assert_called()
            mock_git.add_tag.assert_called()
