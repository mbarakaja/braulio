import click
from pathlib import Path
from collections import OrderedDict
from configparser import ConfigParser
from braulio.files import DEFAULT_CHANGELOG


DEFAULT_CONFIG = ConfigParser()
DEFAULT_CONFIG.read_dict(
    {
        "braulio": {
            "commit": "True",
            "message": "Release version {new_version}",
            "tag": "True",
            "confirm": "False",
            "changelog_file": DEFAULT_CHANGELOG,
            "files": "",
            "label_pattern": "!{type}:{scope}",
            "label_position": "footer",
            "tag_pattern": "v{version}",
        },
        "braulio.stages": {"final": "{major}.{minor}.{patch}"},
    }
)


class Config:

    cfg_file_options = {}

    def __init__(self):

        cfg = self._load_config_file()

        self.config_parser = cfg
        self._commit = cfg.getboolean("braulio", "commit")
        self._message = cfg.get("braulio", "message")
        self._tag = cfg.getboolean("braulio", "tag")
        self._confirm = cfg.getboolean("braulio", "confirm")
        self._changelog_file = Path(cfg.get("braulio", "changelog_file").strip())
        self._label_pattern = cfg.get("braulio", "label_pattern").strip()
        self._label_position = cfg.get("braulio", "label_position").strip()
        self._tag_pattern = cfg.get("braulio", "tag_pattern").strip()
        self._current_version = cfg.get("braulio", "current_version", fallback=None)

        self._stages = OrderedDict(cfg["braulio.stages"])

        # files
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
        user_config = ConfigParser()

        if path.exists() and path.is_file():
            user_config.read(path)

            if user_config.has_section("braulio"):
                self.cfg_file_options = OrderedDict(user_config.items("braulio"))

        merged_config = ConfigParser()
        merged_config.read_dict(DEFAULT_CONFIG)

        # Since ConfigParser uses OrderedDict, we need to remove
        # [braulio.stages] default section before merge the user defined
        # section to preserve the order of the options.
        if user_config.has_section("braulio.stages"):
            merged_config.remove_section("braulio.stages")

        merged_config.read_dict(user_config)

        return merged_config

    @property
    def commit(self):
        return self._commit

    @property
    def message(self):
        return self._message

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

    @property
    def stages(self):
        return self._stages


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
