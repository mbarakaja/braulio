import click
from pathlib import Path
from configparser import ConfigParser
from braulio.files import DEFAULT_CHANGELOG


DEFAULT_CONFIG = ConfigParser()
DEFAULT_CONFIG.read_dict(
    {
        "braulio": {
            "commit": "True",
            "tag": "True",
            "confirm": "False",
            "changelog_file": DEFAULT_CHANGELOG,
            "files": "",
            "label_pattern": "!{action}:{scope}",
            "label_position": "footer",
            "tag_pattern": "v{version}",
        }
    }
)


class Config:

    cfg_file_options = {}

    def __init__(self):

        cfg = self._load_config_file()

        self.config_parser = cfg
        self._commit = cfg.getboolean("braulio", "commit")
        self._tag = cfg.getboolean("braulio", "tag")
        self._confirm = cfg.getboolean("braulio", "confirm")
        self._changelog_file = Path(cfg.get("braulio", "changelog_file").strip())
        self._label_pattern = cfg.get("braulio", "label_pattern").strip()
        self._label_position = cfg.get("braulio", "label_position").strip()
        self._tag_pattern = cfg.get("braulio", "tag_pattern").strip()
        self._current_version = cfg.get("braulio", "current_version", fallback=None)

        files_value = cfg.get("braulio", "files").strip()

        if files_value == "":
            self._files = ()
            return

        if "\n" in files_value:
            files_value = files_value.replace("\n", "")

        file_path_list = files_value.split(",")

        self._files = tuple(fp.strip() for fp in file_path_list)

    def _load_config_file(self):
        path = Path.cwd() / "setup.cfg"
        setup_cfg = ConfigParser()

        if path.exists() and path.is_file():
            setup_cfg.read(path)

            if setup_cfg.has_section("braulio"):
                self.cfg_file_options = dict(setup_cfg.items("braulio"))

        cfg = ConfigParser()
        cfg.read_dict(DEFAULT_CONFIG)
        cfg.read_dict(setup_cfg)

        return cfg

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

    @property
    def label_pattern(self):
        return self._label_pattern

    @property
    def label_position(self):
        return self._label_position

    @property
    def tag_pattern(self):
        return self._tag_pattern

    @property
    def current_version(self):
        return self._current_version


def update_config_file(option, value):
    path = Path.cwd() / "setup.cfg"
    setup_config = ConfigParser()

    if not path.exists():
        path.touch()

    setup_config.read(path)

    if not setup_config.has_section("braulio"):
        setup_config.add_section("braulio")

    setup_config.set("braulio", option, value)

    with path.open("w") as f:
        setup_config.write(f)

    mark = click.style("✓", fg="green", bold=True)
    filename = click.style("setup.cfg", bold=True, fg="blue")
    click.echo(f" {mark} Updated {filename} {option} option with {value}")
