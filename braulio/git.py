import re
from subprocess import run, PIPE
from braulio.version import Version

hash_pattern = re.compile('(?<=commit )\w{40}$', re.M)
task_pattern = re.compile('!\w+:\w*')


def _run_command(command):
    captured = run(command, stdout=PIPE)
    return captured.stdout.decode()


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

    if unreleased:
        tag_list = get_tags()

        if tag_list:
            last_tag = tag_list[0].name
            command.append(f'{last_tag}..HEAD')

    return _run_command(command)


def add_tag(tag_name):
    name = f'{tag_name}'
    return _run_command(['git', 'tag', '-a', name, '-m', '""'])


def add_commit(message):
    _run_command(['git', 'add', 'HISTORY.rst'])
    _run_command(['git', 'commit', '-m', f'"{message}"'])


def get_tags():

    tags_text = _run_git_tag_command()

    if tags_text == '':
        return []

    if tags_text[-1] == '\n':
        tags_text = tags_text[:-1]

    tag_text_list = tags_text.split('\n')
    tag_list = [Tag(text) for text in tag_text_list]

    return list(reversed(tag_list))


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


def get_commits(unreleased=False):
    git_log_text = _run_git_log_command(unreleased=unreleased)
    commit_text_lst = _extract_commit_texts(git_log_text)

    return [Commit(commit_text) for commit_text in commit_text_lst]


class Git:

    def get_commits(self, unreleased=False):
        return get_commits(unreleased=unreleased)

    def get_tags(self):
        return get_tags()

    def add_commit(self, message):
        add_commit(message)

    def add_tag(self, name):
        add_tag(name)
