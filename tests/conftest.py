import os
import pytest
from pathlib import Path
from configparser import ConfigParser
from braulio.git import _extract_commit_texts, Commit


class IsolatedFilesystem:

    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def __enter__(self):
        self.original_dir = self.tmpdir.chdir()

    def __exit__(self, *args):
        os.chdir(self.original_dir)


@pytest.fixture
def isolated_filesystem(tmpdir):
    return IsolatedFilesystem(tmpdir)


@pytest.fixture(scope='session')
def fake_git_log_output():
    return Path('tests/data/commits.txt').read_text()


@pytest.fixture(scope='session')
def commit_text_list(fake_git_log_output):
    return _extract_commit_texts(fake_git_log_output)


@pytest.fixture(scope='session')
def commit_list(commit_text_list):
    return [Commit(text) for text in commit_text_list]


@pytest.fixture(scope='session')
def commit_text_registry(commit_text_list):
    return {c[7:14]: c for c in commit_text_list}


@pytest.fixture(scope='session')
def commit_registry(commit_list):
    return {commit.hash[:7]: commit for commit in commit_list}
