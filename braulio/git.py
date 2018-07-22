import re
from pathlib import Path
from subprocess import run, PIPE, CalledProcessError
from braulio.version import Version

hash_pattern = re.compile('(?<=commit )\w{40}$', re.M)
task_pattern = re.compile('!\w+:\w*')


def _run_command(command):
    captured = run(command, stdout=PIPE, stderr=PIPE, check=True)
    return captured.stdout.decode()


def _run_git_tag_command():
    command = [
        'git',
        'tag',
        '--sort=creatordate',
        '--format=%(creatordate:short)%09%(refname:strip=2)',
    ]
    return _run_command(command)


class Tag:
    def __init__(self, text):
        self.date = text[:10]
        self.name = re.search('v\d+[.]\d+[.]\d+', text).group(0)
        self.number = self.name[1:]

        self.version = Version(self.name[1:])

    def __str__(self):
        return f'Tag({self.version})'

    def __repr__(self):
        return f'Tag({self.version})'


class Commit:

    def __init__(self, text):
        # Remove EOL characters from the end of the text
        self.text = text[:-2] if text[-2:] == '\n\n' else text[:-1]

        text_lines = self.text.split('\n')

        # Commit hash
        self.hash = text_lines[0][7:]

        # Commit message
        msg_lines = [line[4:] for line in text_lines[4:]]
        self.message = '\n'.join(msg_lines)

        # Commit message header
        self.header = msg_lines[0]
        self.subject = self.header

        # Commit message body
        self.body = None
        self.scope = None
        self.action = None

        if len(msg_lines) > 2 and msg_lines[1] == '':
            self.body = '\n'.join(msg_lines[2:])

            match = re.search(task_pattern, msg_lines[-1])

            if match:
                task = match.group(0)
                action, scope = task.split(':')
                scope = None if scope == '' else scope

                self.action, self.scope = action[1:], scope

    def __repr__(self):
        return f'Commit(\'{self.header}\')'


patter = re.compile('^commit (?:.+?(?=commit \w{40})|.+$)', flags=re.M | re.S)


def _extract_commit_texts(git_log_text):
    return re.findall(patter, git_log_text)


class Git:

    def add(self, *files):
        """Add one or more files to the index running git-add."""

        try:
            _run_command(('git', 'add') + files)
        except CalledProcessError:
            # Only if the command fails we check if the files
            # exist, because git-add most of the time fails when
            # the provided files are not found.
            for f in files:
                if not Path(f).exists():
                    raise FileNotFoundError(f'No such file or directory: {f}')

    def commit(self, message, files=None):
        """Run git-commit."""

        if files:
            self.add(*files)

        return _run_command(['git', 'commit', '-m', f'"{message}"'])

    def log(self, _from=None, to=None):
        """Run git-log."""

        command = ['git', 'log']

        if _from:
            to = 'HEAD' if not to else to
            revision_range = f'{_from}..{to}'
            command.append(revision_range)

        git_log_text = _run_command(command)
        commit_text_lst = _extract_commit_texts(git_log_text)

        return [Commit(commit_text) for commit_text in commit_text_lst]

    def tag(self, name=None):
        """Create and list tag objects running git-tag command"""

        command = ['git', 'tag']

        if not name:
            command.extend([
                '-l',
                '--sort=creatordate',
                '--format=%(creatordate:short)%09%(refname:strip=2)',
            ])

            command_output = _run_command(command).strip()

            if command_output == '':
                return []

            tag_text_list = command_output.split('\n')
            tag_list = [Tag(text) for text in tag_text_list]

            return list(reversed(tag_list))

        command.extend(['-a', name, '-m', '""'])
        return _run_command(command)

    @property
    def tags(self):
        if not hasattr(self, '_tag_list'):
            self._tag_list = self.tag()
        return self._tag_list
