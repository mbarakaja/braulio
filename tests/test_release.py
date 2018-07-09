from unittest.mock import patch
from braulio.release import release


class Test_release:

    @patch('braulio.git.git.get_commits', return_value=[])
    def test_no_commits(self, mocked_get_commits):

        assert release() is False

        mocked_get_commits.assert_called_with(unreleased=True)
