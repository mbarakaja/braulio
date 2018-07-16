import pytest
from configparser import ConfigParser
from braulio.config import get_config


def test_default_config(isolated_filesystem):

    with isolated_filesystem:
        config = get_config()

    assert config.tag is True
    assert config.commit is True
    assert config.confirm is False


@pytest.mark.parametrize('cfg_value, expected', [
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
