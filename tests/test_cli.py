import pytest
from click.testing import CliRunner
from braulio.cli import cli


class TestInit:

    def test_when_changelog_file_is_not_found(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'])

            assert 'Do you want to create a new one?' in result.output
            assert '[y/N]:' in result.output

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
