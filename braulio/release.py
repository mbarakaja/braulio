import click
from braulio.git import Version, git
from braulio.changelog import update_changelog


def release():
    commits = git.get_commits(unreleased=True)

    if not commits:
        click.echo('Nothing to release')
        return False

    has_major = []
    has_minor = []
    has_patch = []
    commits_to_log = []

    # Filter only relevant commits
    for commit in commits:
        if commit.action:
            commits_to_log.append(commit)

            has_patch.append(commit.action == 'fix')
            has_minor.append(commit.action == 'feat')
            has_major.append(
                'BREAKING CHANGE' in commit.message
                or 'BREAKING CHANGES' in commit.message
            )

    has_major = any(has_major)
    has_minor = any(has_minor)
    has_patch = any(has_patch)
    last_tag = git.tags[0] if git.tags else None

    next_version = Version()

    if last_tag:
        next_version.major = last_tag.version.major
        next_version.minor = last_tag.version.minor
        next_version.patch = last_tag.version.patch

    if has_major:
        next_version.increase('major')

    if not has_major and has_minor:
        next_version.increase('minor')

    if not has_major and not has_minor and has_patch:
        next_version.increase('patch')

    update_changelog(
        version=next_version,
        commits=commits_to_log,
    )

    git.add_commit(f'Release version {next_version.version}')
    git.add_tag('v' + next_version.version)
