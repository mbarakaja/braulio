import re
from subprocess import run, PIPE


patter = re.compile('^commit (?:.+?(?=commit \w{40})|.+$)', flags=re.M | re.S)
hash_pattern = re.compile('(?<=commit )\w{40}$', re.M)
task_pattern = re.compile('!\w+:\w*')


def _parse_task(text):
    match = re.search(task_pattern, text)

    if match:
        task = match.group(0)
        action, scope = task.split(':')
        scope = None if scope == '' else scope

        return (action[1:], scope)

    return None


class Commit:

    def __init__(self, text):
        # Remove EOL characters from the end of the text
        self.text = text[:-2] if text[-2:] == '\n\n' else text[:-1]
        self._parse_commit_text()

    def _parse_commit_text(self):
        text_lines = self.text.split('\n')

        # Commit hash
        self.hash = text_lines[0][7:]

        # Commit message
        msg_lines = [line[4:] for line in text_lines[4:]]
        self.message = '\n'.join(msg_lines)

        # Commit message header
        self.header = msg_lines[0]

        # Commit message body
        self.body = None
        self.scope = None
        self.action = None

        if len(msg_lines) > 2 and msg_lines[1] == '':
            self.body = '\n'.join(msg_lines[2:])
            task = _parse_task(msg_lines[-1])

            if task:
                self.action, self.scope = task


def _extract_commit_texts(git_log_text):
    return re.findall(patter, git_log_text)


def _get_commits():
    captured = run(['git', 'log'], stdout=PIPE)
    git_log_text = captured.stdout.decode()
    commit_text_lst = _extract_commit_texts(git_log_text)

    return [Commit(commit_text) for commit_text in commit_text_lst]
