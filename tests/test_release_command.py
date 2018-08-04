import pytest
from click import Context
from collections import namedtuple
from configparser import ConfigParser
from unittest.mock import patch
from pathlib import Path
from click.testing import CliRunner
from braulio.cli import cli, release, current_version_callback
from braulio.git import Tag
from braulio.version import Version


parametrize = pytest.mark.parametrize


FakeTag = namedtuple('FakeTag', ['name'])


@parametrize(
    'tag_list, from_arg',
    [
        ([], None),
        ([FakeTag(name='v0.2.0')], 'v0.2.0'),
        ([FakeTag(name='v0.3.3'), FakeTag(name='v0.3.2')], 'v0.3.3'),
    ]
)
@patch('braulio.cli.Git', autospec=True)
def test_call_to_git_log_method(MockGit, tag_list, from_arg):
    mock_git = MockGit()
    mock_git.tags = tag_list
    mock_git.log.return_value = []
    runner = CliRunner()

    result = runner.invoke(cli, ['release'])

    assert result.exit_code == 0
    mock_git.log.assert_called_with(_from=from_arg)


@patch('braulio.cli.Git', autospec=True)
def test_commitless_repository(MockGit):
    mock_git = MockGit()
    mock_git.log.return_value = []
    runner = CliRunner()

    result = runner.invoke(cli, ['release'])

    assert ' › Nothing to release.' in result.output

    mock_git.commit.assert_not_called()
    mock_git.tag.assert_not_called()


@parametrize('_input', ['y', 'n'])
@patch('braulio.cli.update_chglog')
@patch('braulio.cli.Git', autospec=True)
def test_confirmation_prompt(MockGit, mock_update_chglog, _input):
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['release'], input=_input)

        exit_code = 0 if _input == 'y' else 1
        assert result.exit_code == exit_code, result.output
        assert ' › Continue? [y/N]' in result.output

        mock_git = MockGit()

        called = True if _input == 'y' else False
        assert mock_update_chglog.called is called
        assert mock_git.commit.called is called
        assert mock_git.tag.called is called


@parametrize(
    'option, tags, current_version, expected',
    [
        ('--major', [FakeTag('v0.10.1')], Version('0.10.1'), '1.0.0',),
        ('--minor', [FakeTag('v0.10.1')], Version('0.10.1'), '0.11.0',),
        ('--patch', [FakeTag('v0.10.1')], Version('0.10.1'), '0.10.2',),
        ('--major', [], Version(), '1.0.0',),
        ('--minor', [], Version(), '0.1.0',),
        ('--patch', [], Version(), '0.0.1',),
        ('--bump=4.0.0', [FakeTag('v2.0.1')], Version('2.0.1'), '4.0.0',),
        ('--bump=3.0.0', [], Version(), '3.0.0',),
    ],
)
@patch('braulio.cli.update_chglog', autospec=True)
@patch('braulio.cli.Git', autospec=True)
def test_manual_version_bump(MockGit, mock_update_chglog, option,
                             tags, current_version, expected):

    mock_git = MockGit()
    mock_git.tags = tags
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['release', option], input='y')

        assert result.exit_code == 0

        # Check what version was passed to update_chglog function
        mock_update_chglog.assert_called_with(
            Path('HISTORY.rst'),
            current_version=current_version,
            new_version=Version(expected),
            release_data={},
        )

        mock_git.commit.assert_called_with(
            f'Release version {expected}',
            files=['HISTORY.rst'],
        )
        mock_git.tag.assert_called_with(f'v{expected}')


@parametrize(
    'hash_lst, tags, expected',
    [
        (['4d17c1a', '80a9e0e'], [FakeTag('v0.7.6')], '0.7.7'),
        (['4d17c1a', 'ccaa185'], [FakeTag('v0.7.6')], '0.8.0'),
        (['8c8dcb7', 'ccaa185'], [FakeTag('v0.7.6')], '1.0.0'),
        (['4d17c1a', '80a9e0e'], [], '0.0.1'),
        (['4d17c1a', 'ccaa185'], [], '0.1.0'),
        (['8c8dcb7', 'ccaa185'], [], '1.0.0'),
    ],
)
@patch('braulio.cli.update_chglog', autospec=True)
@patch('braulio.cli.Git', autospec=True)
def test_determine_next_version_from_commit_messages(
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

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 0, result.exception

        mocked_update_changelog.assert_called()

        # Check what version was passed to update_chglog function
        passed_args = mocked_update_changelog.call_args[1]
        assert passed_args['new_version'] == Version(expected)

        mock_git.commit.assert_called_with(
            f'Release version {expected}',
            files=['HISTORY.rst'],
        )
        mock_git.tag.assert_called_with(f'v{expected}')


@patch('braulio.cli.ReleaseDataTree')
@patch('braulio.cli.commit_analyzer')
@patch('braulio.cli.update_chglog', autospec=True)
@patch('braulio.cli.get_next_version')
@patch('braulio.cli.Git', autospec=True)
def test_call_to_update_changelog(
    MockGit,
    mock_get_next_version,
    mock_update_chglog,
    mock_commit_analyzer,
    MockReleaseDataTree,
):
    runner = CliRunner()
    mock_git = MockGit()
    mock_git.tags = []

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 0

        mock_git.log.assert_called()

        mock_commit_analyzer.assert_called_with(
            mock_git.log(),
            '!{action}:{scope}',
            'footer',
        )

        MockReleaseDataTree.assert_called_with(
            mock_commit_analyzer()
        )

        release_data = MockReleaseDataTree()

        mock_get_next_version.assert_called_with(
            release_data.bump_version_to,
            Version()
        )

        mock_update_chglog.assert_called_with(
            Path('HISTORY.rst'),
            current_version=Version(),
            new_version=mock_get_next_version(),
            release_data=release_data
        )


@patch('braulio.cli.Git', autospec=True)
def test_changelog_not_found(MockGit):
    runner = CliRunner()

    with runner.isolated_filesystem():

        result = runner.invoke(cli, ['release', '-y'])

        assert result.exit_code == 1, result.exc_info
        assert 'Unable to find HISTORY.rst' in result.output
        assert 'Run "$ brau init" to create one' in result.output

        mock_git = MockGit()
        mock_git.commit.assert_not_called()
        mock_git.tag.assert_not_called()


@patch('braulio.cli.Git', autospec=True)
@patch('braulio.cli.update_files', autospec=True)
def test_files_argument_from_command_line(
    mock_update_files, MockGit, fake_repository
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


@patch('braulio.cli.Git', autospec=True)
@patch('braulio.cli.update_files', autospec=True)
def test_files_argument_from_config_file(
    mock_update_files, MockGit, fake_repository
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


@patch('braulio.cli.Git', autospec=True)
@patch('braulio.cli.update_files', autospec=True)
def test_added_files_to_release_commit(
    mock_update_files, MockGit, fake_repository
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
    'options',
    [
        ['--no-commit', '--bump=0.2.1'],
        ['--no-tag'],
    ],
)
@patch('braulio.cli.Git', autospec=True)
def test_output_after_confirmation_prompt(
        MockGit, isolated_filesystem, commit_list, options):

    runner = CliRunner()
    mock_git = MockGit()
    mock_git.tags = [FakeTag('v0.2.0')]
    mock_git.log.return_value = commit_list

    with isolated_filesystem:
        result = runner.invoke(cli, ['release'] + options)

        assert result.exit_code == 1, result.output

        assert ' › Current version  : 0.2.0' in result.output
        assert f' › Commits found    : {len(commit_list)}' in result.output
        assert ' › New version      :' in result.output
        assert ' › Braulio will perform the next tasks :' in result.output

        if '--no-tag' not in options:
            assert 'Tag the repository with v0.2.1' in result.output

        if '--no-commit' not in options:
            assert 'Add a release commit' in result.output

        assert ' › Continue?' in result.output


@parametrize(
    'options',
    [
        ['--no-commit', '--bump=0.2.1'],
        ['--no-tag', '--bump=0.2.1'],
    ],
)
@patch('braulio.cli.Git', autospec=True)
def test_output_before_confirmation_prompt(
        MockGit, isolated_filesystem, commit_list, options):

    runner = CliRunner()
    mock_git = MockGit()
    mock_git.tags = [Tag('v0.2.0')]
    mock_git.log.return_value = commit_list

    with isolated_filesystem:
        Path('HISTORY.rst').touch()

        result = runner.invoke(cli, ['release'] + options, input='y')

        assert result.exit_code == 0, result.output
        assert 'Update changelog ✓' in result.output

        if '--no-tag' not in options:
            assert ' › Add tag v0.2.1 ✓' in result.output

        if '--no-commit' not in options:
            assert ' › Add commit: Release version 0.2.1 ✓' \
                    in result.output

        assert 'Version 0.2.1 released successfully 🎉' in result.output


@patch('braulio.cli.commit_analyzer', autospec=True)
@patch('braulio.cli.Git', autospec=True)
def test_label_pattern_option(MockGit, mock_commit_analyzer):
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ['release', '--label-pattern={action}:{scope}']
        )

        assert result.exit_code == 1, result.output

        mock_git = MockGit()

        mock_commit_analyzer.assert_called_with(
            mock_git.log(),
            '{action}:{scope}',
            'footer',
        )


@parametrize(
    'label_pattern, label_position, err',
    [
        (' ', 'header', '{action} placeholder are required'),
        (' ', 'footer', '{action} placeholder are required'),
        ('{scope}', 'header', '{action} placeholder are required'),
        ('{scope}', 'footer', '{action} placeholder are required'),
        ('{action}', 'header', '{subject} placeholder are required'),
    ]
)
@patch('braulio.cli.Git', autospec=True)
def test_invalid_label_pattern_option(
        MockGit, label_pattern, label_position, err):

    runner = CliRunner()

    with runner.isolated_filesystem():
        options = [f'--label-pattern={label_pattern}',
                   f'--label-position={label_position}']
        print(options)
        result = runner.invoke(cli, ['release'] + options)

        assert result.exit_code == 2, result.output
        assert err in result.output


@parametrize(
    'flag, config, called',
    [
        ([], {}, True,),
        ([], {'commit': False}, False,),
        (['--no-commit'], {'commit': True}, False,),
        (['--commit'], {'commit': False}, True,),
    ],
)
@patch('braulio.cli.Git', autospec=True)
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
@patch('braulio.cli.Git', autospec=True)
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


@parametrize(
    'options, cfg_value, expected',
    [
        ([], {}, 'v0.0.1'),
        ([], {'tag_pattern': 'version{version}'}, 'version0.0.1'),
        ([], {'tag_pattern': 'release-{version}'}, 'release-0.0.1'),
        (['--tag-pattern={version}-released'], {}, '0.0.1-released'),
        (
            ['--tag-pattern=version{version}'],
            {'tag_pattern': 'release-{version}'},
            'version0.0.1'
        ),
    ],
)
@patch('braulio.cli.Git', autospec=True)
def test_tag_pattern_option(
        MockGit, isolated_filesystem, options, cfg_value, expected):
    """Test tag options picked from CLI or configuration file"""

    mock_git = MockGit()
    mock_git.tags = []
    runner = CliRunner()

    with isolated_filesystem:
        Path('HISTORY.rst').touch()

        with open('setup.cfg', 'w') as config_file:
            config_parser = ConfigParser()
            config_parser['braulio'] = cfg_value
            config_parser.write(config_file)

        command = ['release'] + options + ['-y']
        result = runner.invoke(cli, command)

    assert result.exit_code == 0
    mock_git.tag.assert_called_with(expected)


@parametrize(
    'options, cfg_value',
    [
        ([], {'tag_pattern': 'version'}),
        (['--tag-pattern=released'], {}),
        (['--tag-pattern=version'], {'tag_pattern': 'release'}),
    ],
)
@patch('braulio.cli.Git', autospec=True)
def test_invalid_tag_pattern_option(MockGit, options, cfg_value):
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path('HISTORY.rst').touch()

        with open('setup.cfg', 'w') as config_file:
            config_parser = ConfigParser()
            config_parser['braulio'] = cfg_value
            config_parser.write(config_file)

        command = ['release'] + options
        result = runner.invoke(cli, command)

        assert result.exit_code == 1
        assert 'Missing {version} placeholder in tag_pattern' in result.output


@parametrize(
    'tags, value, expected_version, expected_tag',
    [
        ([], None, None, None),
        ([], '0.12.0', Version('0.12.0'), None),
        (
            [FakeTag('v2.0.0'), FakeTag('v1.9.10')],
            None,
            Version('2.0.0'),
            FakeTag('v2.0.0'),
        ),
        ([FakeTag('v2.0.0')], '3.0.0', Version('3.0.0'), None),
        ([FakeTag('v4.0.0')], '2.0.0', Version('2.0.0'), None),
        ([FakeTag('save-point')], '3.0.0', Version('3.0.0'), None),
        ([FakeTag('save-point')], None, None, None),
    ],
)
@patch('braulio.cli.Git')
def test_current_version_callback(
        MockGit, tags, value, expected_version, expected_tag):
    mock_git = MockGit()
    mock_git.tags = tags
    ctx = Context(release)
    ctx.params['tag_pattern'] = 'v{version}'

    version = current_version_callback(ctx, {}, value)

    assert version == expected_version

    if expected_tag:
        assert ctx.params['current_tag'] == expected_tag


@parametrize(
    'cfg_value, options',
    [
        ({'current_version': 'invalid'}, []),
        ({'current_version': 'invalid'}, ['--current-version=invalid']),
        ({}, ['--current-version=invalid']),
    ],
)
@patch('braulio.cli.Git')
def test_invalid_current_version_option(MockGit, options, cfg_value):
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path('HISTORY.rst').touch()

        with open('setup.cfg', 'w') as config_file:
            config_parser = ConfigParser()
            config_parser['braulio'] = cfg_value
            config_parser.write(config_file)

        command = ['release'] + options + ['-y']
        result = runner.invoke(cli, command)

        assert result.exit_code == 1
        assert 'invalid is not a valid version string' in result.output


@parametrize(
    'cfg_value, options, expected',
    [
        ({'current_version': '2.0.0'}, [], '2.0.1'),
        ({'current_version': '2.0.0'}, ['--current-version=2.0.0'], '2.0.1'),
        ({}, ['--current-version=2.0.0'], None),
        ({}, [], None),
    ],
)
@patch('braulio.cli.Git')
def test_current_version_cfg_option_update(
        MockGit, cfg_value, options, expected):
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path('HISTORY.rst').touch()

        mock_git = MockGit()
        mock_git.tags = [FakeTag(name='v2.0.0')]

        with open('setup.cfg', 'w') as config_file:
            config_parser = ConfigParser()
            config_parser['braulio'] = cfg_value
            config_parser.write(config_file)

        command = ['release', '-y'] + options
        result = runner.invoke(cli, command)

        assert result.exit_code == 0

        cfg = ConfigParser()
        cfg.read('setup.cfg')

        assert cfg.get('braulio', 'current_version', fallback=None) == expected
