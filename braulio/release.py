import click
from braulio.git import Git
from braulio.files import update_changelog, update_files
from braulio.version import Version, get_next_version


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
    ctx,
    bump_version_to=None,
    add_commit_flag=True,
    add_tag_flag=True,
    confirm_flag=False,
    changelog_file=None,
    files=(),
):

    git = Git()

    last_tag = git.tags[0].name if git.tags else None
    commit_list = git.log(_from=last_tag)

    if not commit_list:
        click.echo('Nothing to release')
        return False

    commits = _organize_commits(commit_list)
    bump_version_to = bump_version_to or commits['bump_version_to']
    current_version = git.tags[0].version if git.tags else Version()

    new_version = get_next_version(bump_version_to, current_version)

    if confirm_flag or click.confirm('Continue?'):

        try:
            update_changelog(
                changelog_file,
                version=new_version,
                grouped_commits=commits['by_action'],
            )
        except FileNotFoundError:
            mark = click.style('✗', fg='red', bold=True)
            filename = click.style(changelog_file.name, fg='blue', bold=True)
            click.echo(
                f' {mark} Unable to find {filename}\n'
                '   Run "$ brau init" to create one'
            )
            ctx.abort()

        try:
            update_files(files, str(current_version), str(new_version))
        except ValueError as e:
            click.echo(e)
            ctx.abort()

        if add_commit_flag:
            files = [str(changelog_file)] + list(files)
            git.commit(
                f'Release version {new_version.string}',
                files=files,
            )

        if add_tag_flag:
            git.tag('v' + new_version.string)
