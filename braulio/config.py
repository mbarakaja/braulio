from pathlib import Path
from configparser import ConfigParser


class Config:

    def __init__(self, config):
        self.c = config
        self._commit = config.getboolean('braulio', 'commit')
        self._tag = config.getboolean('braulio', 'tag')
        self._confirm = config.getboolean('braulio', 'confirm')

    @property
    def commit(self):
        return self._commit

    @property
    def tag(self):
        return self._tag

    @property
    def confirm(self):
        return self._confirm


DEFAULT_CONFIG = ConfigParser()
DEFAULT_CONFIG.read_dict({
    'braulio': {
        'commit': 'True',
        'tag': 'True',
        'confirm': 'False',
    }
})


def get_config():
    path = Path.cwd() / 'setup.cfg'
    setup_config = ConfigParser()

    if path.exists() and path.is_file():
        setup_config.read(path)

    config = ConfigParser()
    config.read_dict(DEFAULT_CONFIG)
    config.read_dict(setup_config)

    return Config(config)
