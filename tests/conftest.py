import pytest
from pathlib import Path
from braulio.git import _extract_commit_texts, Commit


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
