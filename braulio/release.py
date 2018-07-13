import click
from braulio.git import get_tags, get_commits, add_commit, add_tag
from braulio.changelog import update_changelog
from braulio.version import get_next_version


def _organize_commits(commit_list):
    by_action = {}
    has_breaking_changes = False

    for commit in commit_list:
        if commit.action:

            has_breaking_changes = (
                has_breaking_changes or 'BREAKING CHANGE' in commit.message
            )

            action = commit.action
            scope = commit.scope

            if action not in by_action:
                by_action[action] = {'scopeless': []}

            if not scope:
                by_action[action]['scopeless'].append(commit)
                continue
            else:
                if scope not in by_action[action]:
                    by_action[action][commit.scope] = []

                by_action[action][scope].append(commit)

    bump_type = 'major' if has_breaking_changes else \
                'minor' if 'feat' in by_action else \
                'patch'

    return {
        'bump_version_to': bump_type,
        'by_action': by_action,
    }


def release(
    bump_version_to=None, add_commit_flag=True, add_tag_flag=True, y_flag=False
):

    commit_list = get_commits(unreleased=True)

    if not commit_list:
        click.echo('Nothing to release')
        return False

    tag_list = get_tags()
    commits = _organize_commits(commit_list)
    bump_version_to = bump_version_to or commits['bump_version_to']
    last_version = tag_list[0].version if tag_list else None

    new_version = get_next_version(bump_version_to, last_version)

    if y_flag or click.confirm('Continue?'):

        update_changelog(
            version=new_version,
            grouped_commits=commits['by_action'],
        )

        if add_commit_flag:
            add_commit(f'Release version {new_version.string}')

        if add_tag_flag:
            add_tag('v' + new_version.string)
