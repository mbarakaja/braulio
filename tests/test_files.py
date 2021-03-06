import pytest
from unittest.mock import patch
from collections import namedtuple
from datetime import date
from pathlib import Path
from braulio.version import Version
from braulio.git import commit_analyzer
from braulio.files import (
    DEFAULT_CHANGELOG,
    KNOWN_CHANGELOG_FILES,
    _render_title,
    _render_subtitle,
    _render_list,
    _render_release,
    update_chglog,
    update_files,
    is_title,
    _split_chglog,
    ReleaseDataTree,
)


parametrize = pytest.mark.parametrize


def test_default_changelog():
    assert DEFAULT_CHANGELOG == "HISTORY.rst"


def test_known_changelog_files():
    assert len(KNOWN_CHANGELOG_FILES) == 3
    assert "HISTORY.rst" in KNOWN_CHANGELOG_FILES
    assert "CHANGELOG.rst" in KNOWN_CHANGELOG_FILES
    assert "CHANGES.rst" in KNOWN_CHANGELOG_FILES


class TestReleaseDataTree:

    FakeSemanticCommit = namedtuple(
        "FakeSemanticCommit", ["type", "scope", "message"]
    )

    @pytest.mark.parametrize(
        "semantic_commits, expected",
        [
            (
                [
                    FakeSemanticCommit(type="fix", scope=None, message=""),
                    FakeSemanticCommit(
                        type="refactor", scope=None, message="BREAKING CHANGES"
                    ),
                ],
                "major",
            ),
            (
                [
                    FakeSemanticCommit(type="fix", scope=None, message=""),
                    FakeSemanticCommit(type="feat", scope=None, message=""),
                ],
                "minor",
            ),
            (
                [
                    FakeSemanticCommit(type="fix", scope=None, message=""),
                    FakeSemanticCommit(type="refactor", scope=None, message=""),
                ],
                "patch",
            ),
        ],
    )
    def test_bump_version_to(self, semantic_commits, expected):

        release = ReleaseDataTree(semantic_commits)

        assert release.bump_version_to == expected

    def test_commit_grouping_by_action_and_scope(self, commit_list):
        semantic_commits = commit_analyzer(
            commit_list, label_pattern="!{type}:{scope}"
        )
        release_data = ReleaseDataTree(semantic_commits)

        assert len(release_data["fix"]["thing"]) == 1
        assert len(release_data["feat"]["scopeless"]) == 1
        assert len(release_data["feat"]["cli"]) == 1
        assert len(release_data["feat"]["music"]) == 2
        assert len(release_data["refactor"]["music"]) == 1
        assert len(release_data["refactor"]["lorem"]) == 1


@parametrize(
    "level, expected",
    [(1, "Title\n=====\n\n"), (2, "Title\n-----\n\n"), (3, "Title\n~~~~~\n\n")],
)
def test_render_title(level, expected):
    output = _render_title("Title", level)
    assert output == expected


def test_render_sublist(commit_registry):

    FakeSemanticCommit = namedtuple("FakeSemanticCommit", ["subject"])

    semantic_commits = [
        FakeSemanticCommit(subject="subject 1"),
        FakeSemanticCommit(subject="subject 2"),
        FakeSemanticCommit(subject="subject 3"),
    ]

    markup = _render_subtitle(semantic_commits)

    assert markup == (
        f"  - {semantic_commits[0].subject}\n"
        f"  - {semantic_commits[1].subject}\n"
        f"  - {semantic_commits[2].subject}\n"
    )


def test_render_list(commit_text_registry):

    FakeSemanticCommit = namedtuple("FakeSemanticCommit", ["subject"])

    commits = [
        FakeSemanticCommit(subject="subject 1"),
        FakeSemanticCommit(subject="subject 2"),
        FakeSemanticCommit(subject="subject 3"),
    ]

    release_data_tree = {
        "scopeless": [commits[0], commits[1]],
        "scope1": [commits[0], commits[1]],
        "scope2": [commits[1]],
        "scope3": [commits[0], commits[1]],
    }

    markup = _render_list(release_data_tree)

    assert markup == (
        f"* {commits[0].subject}\n"
        f"* {commits[1].subject}\n"
        "* scope1\n\n"
        f"  - {commits[0].subject}\n"
        f"  - {commits[1].subject}\n"
        f"* scope2 - {commits[1].subject}\n"
        "* scope3\n\n"
        f"  - {commits[0].subject}\n"
        f"  - {commits[1].subject}\n\n"
    )


@parametrize(
    "first, second, third, expected",
    [
        (None, None, None, False),
        (None, None, "-----\n", False),
        (None, "title\n", "-----\n", False),
        ("title\n", "-----\n", "\n", True),
        ("title\n", "-----\n", None, True),
        ("\n", "title\n", "-----\n", True),
        ("-----\n", "title\n", "-----\n", True),
        ("---------\n", "  title  \n", "---------\n", True),
        ("title\n", "-----\n", "Paragraphs.", True),
        ("Paragrah.", "title\n", "-----\n", False),
        ("-----\n", "title\n", "Paragraphs.", False),
    ],
)
def test_is_title(first, second, third, expected):
    assert is_title(first, second, third) is expected


rst_file1 = """
.. currentmodule:: mymodule

Title
=====

-------------
Section title
-------------

Some Other Content

"""

rst_file2 = """
Title
=====

This is a paragraph.

Another paragraph.

Section title
-------------

Some Other Content

"""

rst_file3 = """Section title
~~~~~~~~~~~~~

"""

rst_file4 = "Paragrah 1.\nParagrah 2.\nParagrah 3."

rst_file5 = ""


@parametrize(
    "file_content, endswith, startswith",
    [
        (rst_file1, "=====\n\n", "-------------"),
        (rst_file2, "Another paragraph.\n\n", "Section title"),
        (rst_file3, "", "Section title"),
        (rst_file4, "Paragrah 3.", ""),
        (rst_file5, "", ""),
    ],
    ids=[
        "Main title without paragraph",
        "Main title with paragraph",
        "Empty content",
        "Without title",
        "empty file",
    ],
)
def test_split_chglog(isolated_filesystem, file_content, endswith, startswith):

    with isolated_filesystem:
        path = Path("document.rst")
        path.write_text(file_content)

        top, bottom = _split_chglog(path, "Section title")

        assert top.endswith(endswith)
        assert bottom.startswith(startswith)


class Test_render_release:
    def test_release_with_fixes_and_features(self, commit_list):
        version = Version(major=10, minor=3, patch=0)
        semantic_commits = commit_analyzer(
            commit_list, label_pattern="!{type}:{scope}"
        )
        release_data = ReleaseDataTree(semantic_commits)
        markup = _render_release(version, release_data=release_data)

        assert markup == (
            f"10.3.0 ({str(date.today())})\n"
            "-------------------\n\n"
            "Bug Fixes\n"
            "~~~~~~~~~\n\n"
            "* thing - Fix a thing\n\n"
            "Features\n"
            "~~~~~~~~\n\n"
            "* Add a thing\n"
            "* music\n\n"
            "  - Add more music please\n"
            "  - Add cool musics :D\n"
            "* cli - Add a cli tool\n\n"
        )

    def test_release_with_fixes(self, commit_registry):
        semantic_commits = commit_analyzer(
            [commit_registry["4d17c1a"]], label_pattern="!{type}:{scope}"
        )
        release_data = ReleaseDataTree(semantic_commits)
        version = Version(major=10, minor=3, patch=0)

        markup = _render_release(version, release_data=release_data)

        assert markup == (
            f"10.3.0 ({str(date.today())})\n"
            "-------------------\n\n"
            "Bug Fixes\n"
            "~~~~~~~~~\n\n"
            "* thing - Fix a thing\n\n"
        )

    def test_release_with_features(self, commit_registry):
        reg = commit_registry
        version = Version(major=10, minor=3, patch=0)
        semantic_commits = commit_analyzer(
            [reg["ccaa185"], reg["bc0bcab"], reg["a6b655f"]],
            label_pattern="!{type}:{scope}",
        )
        release_data = ReleaseDataTree(semantic_commits)
        markup = _render_release(version, release_data=release_data)

        assert markup == (
            f"10.3.0 ({str(date.today())})\n"
            "-------------------\n\n"
            "Features\n"
            "~~~~~~~~\n\n"
            "* Add a thing\n"
            "* music - Add more music please\n"
            "* cli - Add a cli tool\n\n"
        )


@parametrize(
    "file_content, expected",
    [
        ("", "New Content\n"),
        (
            ("Changelog\n" "=========\n" "\n" "1.0.0\n" "~~~~~\n" "Content\n"),
            (
                "Changelog\n"
                "=========\n"
                "\n"
                "New Content\n"
                "1.0.0\n"
                "~~~~~\n"
                "Content\n"
            ),
        ),
        (
            ("One Paragraph.\n" "Two Paragraphs.\n" "\n" "Another Paragraph\n"),
            (
                "One Paragraph.\n"
                "Two Paragraphs.\n"
                "\n"
                "Another Paragraph\n"
                "New Content\n"
            ),
        ),
    ],
    ids=["Empty file", "File with a release section", "File without release section"],
)
@patch("braulio.files._render_release", return_value="New Content\n")
def test_update_chglog(
    mock_render_release, isolated_filesystem, file_content, expected
):
    cur_version = Version("1.0.0")
    new_version = Version("2.0.0")

    with isolated_filesystem:
        path = Path.cwd() / "CHANGELOG.rst"
        path.write_text(file_content)

        update_chglog(path, cur_version, new_version, {})

        mock_render_release.assert_called_with(new_version, {})

        text = path.read_text()

        assert text == expected


def test_remove_block_from_changelog(isolated_filesystem):
    cur_version = Version("1.0.0")
    new_version = Version("2.0.0")

    with isolated_filesystem:
        path = Path.cwd() / "CHANGELOG.rst"
        path.write_text(
            "line 1\n" "line 2\n" "line 3\n" "line 4\n" "line 5\n" "line 6\n"
        )

        update_chglog(path, cur_version, new_version, {}, ["line 2", "line 5"])

        text = path.read_text()

        assert "line 1" in text
        assert "line 2" not in text
        assert "line 3" not in text
        assert "line 4" not in text
        assert "line 5" in text
        assert "line 6" in text


class Test_update_files:
    def test_files_missing_version_string(self, fake_repository):
        paths = ["setup.py", "black/__init__.py"]

        with fake_repository("black"):
            message = 'Unable to find a version string to update in "setup.py"'

            with pytest.raises(ValueError, match=message):
                update_files(paths, "4.0.0", "4.1.0")

    def test_file_update(self, fake_repository):
        paths = ["setup.py", "black/__init__.py"]

        with fake_repository("black"):

            update_files(paths, "4.1.3", "5.0.0")

            __init__file = (Path.cwd() / "black" / "__init__.py").read_text()
            setup_file = (Path.cwd() / "setup.py").read_text()

        assert setup_file == (
            "from setuptools import setup\n"
            "\n"
            "setup(\n"
            "    name='black',\n"
            "    author='Mr. Black',\n"
            "    description='Jus an example',\n"
            "    version='5.0.0',\n"
            "    zip_safe=False,\n"
            ")\n"
        )

        assert __init__file == (
            "'''\n"
            "    Black project\n"
            "    ~~~~~~~~~~~~~\n"
            "'''\n"
            "\n"
            "__author__ = 'Mr. Black'\n"
            "__email__ = 'black@example.test'\n"
            "__version__ = '5.0.0'\n"
            "\n"
            "\n"
            "def example():\n"
            "    pass\n"
        )
