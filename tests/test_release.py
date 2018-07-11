import pytest
from braulio.release import _organize_commits


class TestOrganizedCommits:

    @pytest.mark.parametrize(
        'hash_list, expected',
        [
            (['eaedb93', '8c8dcb7'], 'major'),
            (['ccaa185', '264af1b'], 'minor'),
            (['4d17c1a', '80a9e0e'], 'patch'),
        ],
    )
    def test_bump_version_to(self, commit_registry, hash_list, expected):
        commit_list = [
            commit_registry[short_hash] for short_hash in hash_list
        ]
        commits = _organize_commits(commit_list)
        assert commits['bump_version_to'] == expected

    def test_commit_grouping_by_action_and_scope(self, commit_list):
        commits = _organize_commits(commit_list)

        grouped_commits = commits['by_action']

        assert len(grouped_commits['fix']['thing']) == 1
        assert len(grouped_commits['feat']['scopeless']) == 1
        assert len(grouped_commits['feat']['cli']) == 1
        assert len(grouped_commits['feat']['music']) == 2
        assert len(grouped_commits['refactor']['music']) == 1
        assert len(grouped_commits['refactor']['lorem']) == 1
