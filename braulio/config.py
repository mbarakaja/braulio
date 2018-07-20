from pathlib import Path
from configparser import ConfigParser
from braulio.files import DEFAULT_CHANGELOG


DEFAULT_CONFIG = ConfigParser()
DEFAULT_CONFIG.read_dict({
    'braulio': {
        'commit': 'True',
        'tag': 'True',
        'confirm': 'False',
        'changelog_file': DEFAULT_CHANGELOG,
        'files': '',
    }
})


class Config:

    def __init__(self):

        config = self._load_config_file()

        self.config_parser = config
        self._commit = config.getboolean('braulio', 'commit')
        self._tag = config.getboolean('braulio', 'tag')
        self._confirm = config.getboolean('braulio', 'confirm')
        changelog_path = config.get('braulio', 'changelog_file').strip()
        self._changelog_file = Path(changelog_path)

        files_value = config.get('braulio', 'files').strip()

        if files_value == '':
            self._files = ()
            return

        if '\n' in files_value:
            files_value = files_value.replace('\n', '')

        file_path_list = files_value.split(',')

        self._files = tuple(fp.strip() for fp in file_path_list)

    def _load_config_file(self):
        path = Path.cwd() / 'setup.cfg'
        setup_config = ConfigParser()

        if path.exists() and path.is_file():
            setup_config.read(path)

        config = ConfigParser()
        config.read_dict(DEFAULT_CONFIG)
        config.read_dict(setup_config)

        return config

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
    def changelog_file(self):
        return self._changelog_file

    @property
    def files(self):
        return self._files
