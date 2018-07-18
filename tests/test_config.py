import pytest
from configparser import ConfigParser
from braulio.config import DEFAULT_CONFIG, Config, get_config


parametrize = pytest.mark.parametrize


def test_default_config(isolated_filesystem):

    with isolated_filesystem:
        config = get_config()

    assert config.tag is True
    assert config.commit is True
    assert config.confirm is False
    assert config.files == ()


@parametrize('cfg_value, expected', [
   (
       {}, {'tag': True, 'commit': True, 'confirm': False}
   ),
   (
       {'tag': False}, {'tag': False, 'commit': True, 'confirm': False}
   ),
   (
       {'commit': False}, {'tag': True, 'commit': False, 'confirm': False}
   ),
   (
       {'confirm': True}, {'tag': True, 'commit': True, 'confirm': True}
   ),
])
def test_merge_defaults_with_config_file(
    cfg_value, expected, isolated_filesystem
):

    with isolated_filesystem:
        with open('setup.cfg', 'w') as config_file:
            config_parser = ConfigParser()
            config_parser['braulio'] = cfg_value
            config_parser.write(config_file)

        config = get_config()

    assert config.tag is expected['tag']
    assert config.commit is expected['commit']
    assert config.confirm is expected['confirm']


@parametrize(
    'files_value, expected',
    [
        ('', (),),
        (' ', (),),
        ('folder/file.py', ('folder/file.py',)),
        (' folder/file.py, file.py ', ('folder/file.py', 'file.py',)),
        (
            ' folder/file.py , \nfolder/module.py ,\n   file.py  ',
            ('folder/file.py', 'folder/module.py', 'file.py',)
        )
    ],
)
def test_files_key_value_parsing(files_value, expected):
    config_parser = ConfigParser()
    config_parser.read_dict(DEFAULT_CONFIG)
    config_parser['braulio']['files'] = files_value

    config = Config(config_parser)

    assert type(config.files) == tuple
    assert config.files == expected
