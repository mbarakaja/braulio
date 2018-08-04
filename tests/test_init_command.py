import pytest
from configparser import ConfigParser
from unittest.mock import patch
from pathlib import Path
from click.testing import CliRunner
from braulio.cli import cli
from braulio.files import DEFAULT_CHANGELOG, KNOWN_CHANGELOG_FILES


parametrize = pytest.mark.parametrize


@pytest.fixture(params=KNOWN_CHANGELOG_FILES)
def known_changelog_file(request):
    return request.param


@parametrize('_input', ['CUSTOM.rst', None])
def test_empty_repository(_input):
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['init'], input=_input)

        assert result.exit_code == 0
        assert 'Enter a name for the changelog' in result.output

        filename = DEFAULT_CHANGELOG if not _input else _input
        changelog_path = Path.cwd() / filename

        assert changelog_path.exists()


def test_changelog_filename_option():
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
@patch('braulio.cli.create_chglog_file', autospec=True)
def test_known_changelog_found(
        mock_create_changelog_file, known_changelog_file, _input):

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
