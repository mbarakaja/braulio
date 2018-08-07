import pytest
from configparser import ConfigParser
from pathlib import Path
from click.testing import CliRunner
from braulio.config import Config, update_config_file


parametrize = pytest.mark.parametrize


class TestConfig:
    def check_default_options(self, config):
        assert config.tag is True
        assert config.commit is True
        assert config.message == "Release version {new_version}"
        assert config.confirm is False
        assert config.files == ()
        assert config.changelog_file == Path("HISTORY.rst")
        assert config.label_position == "footer"
        assert config.label_pattern == "!{action}:{scope}"
        assert config.tag_pattern == "v{version}"
        assert config.current_version is None

    def test_default_options(self, isolated_filesystem):

        with isolated_filesystem:
            config = Config()
            self.check_default_options(config)

    def test_cfg_file_property(self, isolated_filesystem):

        with isolated_filesystem:
            file_path = Path.cwd() / "setup.cfg"
            file_path.write_text(
                "[braulio]\n" "option1 = value1\n" "option2 = value2\n"
            )

            config = Config()
            config.cfg_file_options == {"option1": "value1", "option2": "value2"}

    def test_config_file_with_not_braulio_section(self, isolated_filesystem):
        config_file_content = "[section]\n" "option1 = value1\n" "option2 = value2\n"

        with isolated_filesystem:
            file_path = Path.cwd() / "setup.cfg"
            file_path.write_text(config_file_content)

            config = Config()
            self.check_default_options(config)

    def test_merge_options_from_config_file(self, isolated_filesystem):
        config_file_content = (
            "[braulio]\n" "commit = False\n" "tag = False\n" "confirm = True\n"
        )

        with isolated_filesystem:
            file_path = Path.cwd() / "setup.cfg"
            file_path.write_text(config_file_content)

            config = Config()

        assert config.tag is False
        assert config.commit is False
        assert config.confirm is True
        assert config.files == ()

    @parametrize(
        "files_value, expected",
        [
            ("", ()),
            (" ", ()),
            ("folder/file.py", ("folder/file.py",)),
            (" folder/file.py, file.py ", ("folder/file.py", "file.py")),
            (
                " folder/file.py , \n    folder/module.py ,\n    file.py  ",
                ("folder/file.py", "folder/module.py", "file.py"),
            ),
        ],
        ids=[
            "empty value",
            "empty space",
            "single file",
            "multiple files in a single line",
            "multiple files in multiple lines",
        ],
    )
    def test_files_option(self, isolated_filesystem, files_value, expected):
        config_file_content = "[braulio]\n" f"files = {files_value}\n"
        with isolated_filesystem:
            file_path = Path.cwd() / "setup.cfg"
            file_path.write_text(config_file_content)

            config = Config()

        assert type(config.files) == tuple
        assert config.files == expected

    @parametrize(
        "options, expected",
        [
            ({}, {"tag": True, "commit": True, "confirm": False}),
            ({"tag": False}, {"tag": False, "commit": True, "confirm": False}),
            ({"commit": False}, {"tag": True, "commit": False, "confirm": False}),
            ({"confirm": True}, {"tag": True, "commit": True, "confirm": True}),
        ],
    )
    def test_merge_config_file_options_on_default_options(
        self, isolated_filesystem, options, expected
    ):
        """Test to make sure that the options in configuration files have
        precedence over the default configuration.
        """

        with isolated_filesystem:

            # Write a config file to the file system
            with open("setup.cfg", "w") as config_file:
                config_parser = ConfigParser()
                config_parser["braulio"] = options
                config_parser.write(config_file)

            config = Config()

        assert config.tag is expected["tag"]
        assert config.commit is expected["commit"]
        assert config.confirm is expected["confirm"]

    def test_current_version_option(self, isolated_filesystem):
        with isolated_filesystem:
            file_path = Path.cwd() / "setup.cfg"
            file_path.write_text("[braulio]\n" "current_version = 4.9.3\n")

            config = Config()
            config.current_version == "4.9.3"

    def test_message_option(self, isolated_filesystem):
        with isolated_filesystem:
            file_path = Path.cwd() / "setup.cfg"
            file_path.write_text("[braulio]\n" "message = Release: {new_version}\n")

            config = Config()
            config.current_version == "Release: {new_version}"


class TestUpdateConfigFile:
    def test_empty_directory(self, isolated_filesystem):
        runner = CliRunner()

        with runner.isolated_filesystem():
            setup_cfg_path = Path.cwd() / "setup.cfg"

            update_config_file("option1", "value1")

            assert setup_cfg_path.exists()

            config_parser = ConfigParser()
            config_parser.read("setup.cfg")
            assert config_parser.has_section("braulio")
            assert config_parser.get("braulio", "option1") == "value1"

    def test_setup_cfg_exists(self, isolated_filesystem):
        runner = CliRunner()

        with runner.isolated_filesystem():
            setup_cfg_path = Path.cwd() / "setup.cfg"
            setup_cfg_path.write_text(
                "[section1]\n" "option1 = value1\n" "option2 = value2\n"
            )

            update_config_file("option3", "value3")

            config_parser = ConfigParser()
            config_parser.read("setup.cfg")
            assert config_parser.has_section("braulio")
            assert config_parser.get("braulio", "option3") == "value3"
