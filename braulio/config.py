from pathlib import Path
from configparser import ConfigParser


class Config:

    def __init__(self, config):
        self.c = config
        self._commit = config.getboolean('braulio', 'commit')
        self._tag = config.getboolean('braulio', 'tag')
        self._confirm = config.getboolean('braulio', 'confirm')

        files_value = config.get('braulio', 'files').strip()

        if files_value == '':
            self._files = ()
            return

        if '\n' in files_value:
            files_value = files_value.replace('\n', '')

        file_path_list = files_value.split(',')

        self._files = tuple(fp.strip() for fp in file_path_list)

    @property
    def commit(self):
        return self._commit

    @property
    def tag(self):
        return self._tag

    @property
    def confirm(self):
        return self._confirm

    @property
    def files(self):
        return self._files


DEFAULT_CONFIG = ConfigParser()
DEFAULT_CONFIG.read_dict({
    'braulio': {
        'commit': 'True',
        'tag': 'True',
        'confirm': 'False',
        'files': '',
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
