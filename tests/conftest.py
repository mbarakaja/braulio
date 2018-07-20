import os
import pytest
from shutil import copytree
from pathlib import Path
from braulio.git import _extract_commit_texts, Commit


class IsolatedFilesystem:

    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def __enter__(self):
        self.original_dir = self.tmpdir.chdir()
        return self

    def __exit__(self, *args):
        os.chdir(self.original_dir)


class FakeRepository:

    repository_dir = Path.cwd() / 'tests' / 'repos'

    def __init__(self, tmpdir, repository_name):
        self.tmpdir = tmpdir
        self.temporal_dir = Path(tmpdir) / 'repo'
        self.original_dir = Path.cwd()
        self.repository_name = repository_name

    def __enter__(self):
        # Copy fake repository to temporal directory
        copytree(
            src=self.repository_dir / self.repository_name,
            dst=self.temporal_dir
        )

        # Switch to temporal directory
        os.chdir(self.temporal_dir)

    def __exit__(self, *args):
        # Switch back to original directory
        os.chdir(self.original_dir)


@pytest.fixture
def fake_repository(tmpdir):

    def _repository(repository_name):
        return FakeRepository(tmpdir, repository_name)

    return _repository


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
