import re
from subprocess import run, PIPE


hash_pattern = re.compile('(?<=commit )\w{40}$', re.M)
task_pattern = re.compile('!\w+:\w*')


def _run_command(command):
    captured = run(command, stdout=PIPE)
    return captured.stdout.decode()


def add_tag(tag_name):
    name = f'{tag_name}'
    return _run_command(['git', 'tag', '-a', name, '-m', '""'])


def add_commit(message):
    _run_command(['git', 'add', 'HISTORY.rst'])
    _run_command(['git', 'commit', '-m', f'"{message}"'])


def _run_git_tag_command():
    command = [
        'git',
        'tag',
        '--sort=creatordate',
        '--format=%(creatordate:short)%09%(refname:strip=2)',
    ]
    return _run_command(command)


def _run_git_log_command(unreleased=False):
    command = ['git', 'log']

    if unreleased and git.tags:
        last_tag = git.tags[0].name
        command = ['git', 'log', f'{last_tag}..HEAD']

    return _run_command(command)


def _get_tags():

    tags_text = _run_git_tag_command()

    if tags_text == '':
        return []

    if tags_text[-1] == '\n':
        tags_text = tags_text[:-1]

    tag_text_list = tags_text.split('\n')
    tag_list = [Tag(text) for text in tag_text_list]

    return list(reversed(tag_list))


class Version:
    def __init__(self, major=0, minor=0, patch=0):
        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)

        self._text_repr()

    def increase(self, part):
        if part == 'major':
            self.major += 1
            self.minor, self.patch = 0, 0
        elif part == 'minor':
            self.minor += 1
            self.patch = 0
        else:
            self.patch += 1

        self._text_repr()

    def _text_repr(self):
        self.version = f'{self.major}.{self.minor}.{self.patch}'

    def __str__(self):
        return self.version


class Tag:
    def __init__(self, text):
        self.date = text[:10]
        self.name = re.search('v\d+[.]\d+[.]\d+', text).group(0)
        self.number = self.name[1:]

        major, minor, patch = self.number.split('.')

        self.version = Version(major, minor, patch)

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


def _get_commits(unreleased=False):
    git_log_text = _run_git_log_command(unreleased=unreleased)
    commit_text_lst = _extract_commit_texts(git_log_text)

    return [Commit(commit_text) for commit_text in commit_text_lst]


class Git:

    def __init__(self):
        self._commits = []
        self._tags = []

    @property
    def commits(self):
        if not self._commits:
            self._commits = _get_commits()
        return self._commits

    @property
    def tags(self):
        if not self._tags:
            self._tags = _get_tags()
        return self._tags

    def get_commits(self, unreleased=False):
        return _get_commits(unreleased=unreleased)

    def add_commit(self, message):
        return add_commit(message)

    def add_tag(self, tag_name):
        return add_tag(tag_name)


git = Git()
