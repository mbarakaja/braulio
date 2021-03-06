import pytest
from collections import namedtuple
from subprocess import CalledProcessError, PIPE
from unittest.mock import patch
from braulio.git import _run_command, Git, Commit, Tag, commit_analyzer, tag_analyzer
from braulio.version import Version


parametrize = pytest.mark.parametrize


class TestRunCommand:
    @patch("braulio.git.run")
    def test_call_to_subprocess_run(self, mocked_run):

        output = _run_command(["command", "subcomand"])

        mocked_run.assert_called_with(
            ["command", "subcomand"], stdout=PIPE, stderr=PIPE, check=True
        )

        assert output == mocked_run().stdout.decode()

    def test_non_zero_exit_code(self, isolated_filesystem):
        with isolated_filesystem:
            with pytest.raises(CalledProcessError):
                _run_command(["git", "status"])


class TestTag:
    @parametrize(
        "text, date, name",
        [
            ("2015-10-15  v10.0.1", "2015-10-15", "v10.0.1"),
            ("2016-02-26   v0.10.13", "2016-02-26", "v0.10.13"),
            ("2016-07-06   save-point", "2016-07-06", "save-point"),
        ],
    )
    def test_parse_name_and_date_string(self, text, date, name):
        tag = Tag(text)

        assert tag.name == name
        assert tag.date == date

    def test_str(self):
        tag = Tag("2015-10-15  v10.0.1")
        assert str(tag) == "v10.0.1"

    def test_repr(self):
        tag = Tag("2015-10-15  v10.0.1")
        assert repr(tag) == 'Tag("2015-10-15  v10.0.1")'


class TestCommitClass:
    @parametrize(
        "short_hash, expected",
        [
            ("eaedb93", "eaedb9320c7aad581daa05f1510b64393c082dbb"),
            ("80a9e0e", "80a9e0edf6208b3c1c9bc28bfb1a5f04b1f59e1d"),
        ],
        ids=[
            "eaedb9320c7aad581daa05f1510b64393c082dbb",
            "80a9e0edf6208b3c1c9bc28bfb1a5f04b1f59e1d",
        ],
    )
    def test_hash(self, commit_text_registry, short_hash, expected):
        text = commit_text_registry[short_hash]
        assert Commit(text).hash == expected

    @parametrize(
        "short_hash, expected",
        [
            ("eaedb93", "Fix lorem ipsum dolor sit amet"),
            ("80a9e0e", "Stop being lazy"),
            ("2f9be68", "Add more lorem ipsum text"),
            ("0a10908", "Add additional information (#26)"),
        ],
        ids=[
            "with body",
            "without line break",
            "without body",
            "with multiple paragraphs",
        ],
    )
    def test_header(self, commit_text_registry, short_hash, expected):
        text = commit_text_registry[short_hash]
        assert Commit(text).header == expected

    @parametrize(
        "short_hash, expected",
        [
            ("4d17c1a", "!fix:thing Fixes #1"),
            ("8c8dcb7", "!refactor:lorem"),
            ("82f0d12", "Sudo make me a sandwich."),
        ],
    )
    def test_footer(self, commit_text_registry, short_hash, expected):
        text = commit_text_registry[short_hash]
        assert Commit(text).footer == expected

    @parametrize(
        "short_hash",
        ["80a9e0e", "2f9be68"],
        ids=["no line break before header", "without body"],
    )
    def test_message_with_invalid_body(self, commit_text_registry, short_hash):
        text = commit_text_registry[short_hash]
        assert Commit(text).body is None

    @parametrize(
        "short_hash, expected",
        [
            (
                "eaedb93",
                (
                    "Consectetur adipiscing elit, sed do\n"
                    "eiusmod tempor incididunt ut labore et\n"
                    "dolore magna aliqua."
                ),
            ),
            ("82f0d12", ("What? Make it yourself.\n" "\n" "Sudo make me a sandwich.")),
            (
                "0a10908",
                (
                    "But I must explain to you how all this mistaken\n"
                    "idea of denouncing pleasure and praising pain was\n"
                    "born.\n"
                    "\n"
                    "Who avoids a pain that produces no resultant pleasure?."
                ),
            ),
        ],
        ids=[
            "Single paragraph",
            "multiple single line paragraphs",
            "multiple paragraphs",
        ],
    )
    def test_messages_with_valid_body(self, commit_text_registry, short_hash, expected):
        text = commit_text_registry[short_hash]
        assert Commit(text).body == expected


class TestGitAdd:
    @parametrize(
        "files, expected",
        [
            (["module.py"], ("module.py",)),
            (["module.py", "folder/file.py"], ("module.py", "folder/file.py")),
        ],
    )
    @patch("braulio.git._run_command", autospec=True)
    def test_run_command_call(self, mocked_run_command, files, expected):
        git = Git()
        git.add(*files)

        command = ("git", "add")
        mocked_run_command.assert_called_with(command + expected)

    def test_when_provided_files_does_not_exits(self):
        git = Git()

        error = "No such file or directory: this_does_not_exist.py"
        with pytest.raises(FileNotFoundError, match=error):
            git.add("this_does_not_exist.py")


class TestGitCommit:
    @patch("braulio.git._run_command", autospec=True)
    def test_call_to_run_command(self, mocked_run_command):
        git = Git()
        git.commit("A message")

        command = ["git", "commit", "-m", '"A message"']
        mocked_run_command.assert_called_with(command)

    @patch("braulio.git._run_command", autospec=True)
    @patch("braulio.git.Git.add", autospec=True)
    def test_pass_files_to_commit(self, mocked_git_add, mocked_run_command):
        git = Git()
        git.commit("A good message", files=["file1.py", "file2.py"])

        # When autospec is used on a class method, the self parameter
        # must be passed to too.
        git.add.assert_called_with(git, "file1.py", "file2.py")

        command = ["git", "commit", "-m", '"A good message"']
        mocked_run_command.assert_called_with(command)


class TestGitLog:
    @patch("braulio.git._run_command", autospec=True)
    def test_log_all_commits(self, mocked_run_command, fake_git_log_output):
        mocked_run_command.return_value = fake_git_log_output

        git = Git()
        commits = git.log()

        mocked_run_command.assert_called_with(["git", "log"])
        assert len(commits) == 12
        assert isinstance(commits[0], Commit)

        first = commits[0]
        assert first.header == "Fix lorem ipsum dolor sit amet"

        last = commits[-1]
        assert last.header == "Add additional information (#26)"

    @parametrize(
        "f, t, revision_range",
        [
            (None, None, []),
            (None, "tag2", []),
            ("tag1", None, ["tag1..HEAD"]),
            ("tag1", "tag2", ["tag1..tag2"]),
        ],
    )
    @patch("braulio.git._run_command", return_value="", autospec=True)
    def test_log_range(self, mocked_run_command, f, t, revision_range):

        git = Git()
        git.log(_from=f, to=t)

        mocked_run_command.assert_called_with(["git", "log"] + revision_range)


git_tag_output = (
    "2015-10-15      v0.0.1\n"
    "2015-11-18      v0.0.2\n"
    "2016-02-26      v0.0.3\n"
    "2016-03-22      v0.0.4\n"
    "2016-07-06      v0.0.5\n"
    "2016-10-03      v0.0.6\n"
)


class TestGitTag:
    @parametrize(
        "command_output, expected", [("", 0), ("  ", 0), ("\n", 0), (git_tag_output, 6)]
    )
    @patch("braulio.git._run_command", autospec=True)
    def test_get_tags(self, mocked_run_command, command_output, expected):
        mocked_run_command.return_value = command_output

        git = Git()
        lst = git.tag()

        mocked_run_command.assert_called_with(
            [
                "git",
                "tag",
                "-l",
                "--sort=creatordate",
                "--format=%(creatordate:short)%09%(refname:strip=2)",
            ]
        )

        assert type(lst) == list
        assert len(lst) == expected

        if expected > 0:
            for _tag in lst:
                assert type(_tag) == Tag

            assert lst[0].name == "v0.0.6"
            assert lst[5].name == "v0.0.1"

    @patch("braulio.git._run_command", autospec=True)
    def test_add_tag(self, mocked_run_command):
        git = Git()
        git.tag("tagname")

        mocked_run_command.assert_called_with(
            ["git", "tag", "-a", "tagname", "-m", '""']
        )


class Test_commit_analyzer:

    # A substitution to braulio.git.Commit for test purpose
    Commit = namedtuple("Commit", ["header", "footer", "message"])

    @parametrize(
        "label_pattern, header",
        [
            ("!{type}:{scope} {subject}", "!fix:cli Make it work"),
            ("[{type}:{scope}] {subject}", "[fix:cli] Make it work"),
            ("{type}({scope}): {subject}", "fix(cli): Make it work"),
            ("{type}({scope}): {subject}", "fix(cli): Make it work"),
        ],
    )
    def test_label_in_header(self, isolated_filesystem, label_pattern, header):

        commit = self.Commit(header=header, footer=None, message="")

        with isolated_filesystem:

            lst = commit_analyzer(
                [commit], label_pattern=label_pattern, label_position="header"
            )

            assert len(lst) == 1
            assert lst[0].subject == "Make it work"
            assert lst[0].scope == "cli"
            assert lst[0].type == "fix"

    @parametrize(
        "label_pattern, footer",
        [
            ("!{type}:{scope}", "!fix:cli"),
            ("[{type}:{scope}]", "[fix:cli]"),
            ("{type}({scope}):", "fix(cli):"),
            ("{type}({scope})", "fix(cli) Fixes #45 and closes #67"),
        ],
    )
    def test_label_in_the_footer(self, isolated_filesystem, label_pattern, footer):

        commit = self.Commit(header="Make it work", footer=footer, message="")

        with isolated_filesystem:

            lst = commit_analyzer(
                [commit], label_pattern=label_pattern, label_position="footer"
            )

            assert len(lst) == 1
            assert lst[0].subject == "Make it work"
            assert lst[0].scope == "cli"
            assert lst[0].type == "fix"

    @parametrize(
        "label_pattern, header",
        [
            ("!{type}:{scope} {subject}", "!fix: Make it work"),
            ("[{type}:{scope}] {subject}", "[fix:] Make it work"),
            ("{type}({scope}): {subject}", "fix(): Make it work"),
        ],
    )
    def test_scopeless_labels(self, isolated_filesystem, label_pattern, header):

        commit = self.Commit(header=header, footer=None, message="")

        with isolated_filesystem:

            lst = commit_analyzer(
                [commit], label_pattern=label_pattern, label_position="header"
            )

            assert len(lst) == 1
            assert lst[0].subject == "Make it work"
            assert lst[0].scope is None
            assert lst[0].type == "fix"

    def test_scopeless_label_pattern(self, isolated_filesystem):

        commit = self.Commit(header="Make it work", footer="!fix", message="")

        with isolated_filesystem:

            lst = commit_analyzer(
                [commit], label_pattern="!{type}", label_position="footer"
            )

            assert len(lst) == 1
            assert lst[0].subject == "Make it work"
            assert lst[0].scope is None
            assert lst[0].type == "fix"


def test_tag_analyzer():

    tags = [
        Tag("2016-10-15   v10.0.1"),
        Tag("2016-08-26   v0.10.13"),
        Tag("2016-05-06   save-point"),
        Tag("2016-04-26   v0.9.7"),
    ]

    result = tag_analyzer(tags, "v{version}", Version)

    assert result == [Version("10.0.1"), Version("0.10.13"), Version("0.9.7")]

    assert result[0].tag.name == "v10.0.1"
