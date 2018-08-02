import re
from pathlib import Path
from typing import NamedTuple
from subprocess import run, PIPE, CalledProcessError

hash_pattern = re.compile('(?<=commit )\w{40}$', re.M)


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
        self.name = text[10:].strip()

    def __str__(self):
        return f'Tag({self.version})'

    def __repr__(self):
        return f'Tag({self.version})'


class Commit:

    def __init__(self, text):
        self.text = text
        lines = text.strip().split('\n')

        # Commit hash
        self.hash = lines[0][7:]

        # Commit message
        msg_lines = [line[4:] for line in lines[4:]]
        self.message = '\n'.join(msg_lines)

        # Commit message header
        self.header = msg_lines[0]
        self.footer = msg_lines[-1]

        # Commit message body
        self.body = None

        if len(msg_lines) > 2 and msg_lines[1] == '':
            self.body = '\n'.join(msg_lines[2:])

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


class SemanticCommit(NamedTuple):
    subject: str
    message: str
    action: str
    scope: str


def commit_analyzer(commits, label_pattern, label_position='footer'):
    """Analyzes a list of :class:`~braulio.git.Commit` objects searching for
    messages that match a given message convention and extract metadata from
    them.

    A message convention is determined by ``label_pattern``, which is not a
    regular expression pattern. Instead it must be a string literals with
    placeholders that indicates metadata information in a given position of
    the commit message. The possible placeholders are ``{action}``, ``{scope}``
    and ``{subject}``.

    The ``label_position`` argument dictates where (header|footer) to look in
    the commit message for the pattern passed in ```label_pattern``.

    ``{subject}`` must be included in ``label_pattern`` just if the metadata is
    in the header, otherwise must be omitted.

    Examples.

    If ``label_position`` is equal to **header**, in order to match the next
    commit message::

        fix(cli): Ensure --help option doesn't hang

    The pattern must be ``{action}({scope}): {subject}``, where the metadata
    information extracted will be::

        {
            'action': 'fix',
            'scope': 'cli',
            'subject': 'Ensure --help option doesn't hang'
        }
    """

    # Internally, a real regular expression pattern is used
    pattern_string = re.escape(label_pattern)

    # Capturing group patterns
    action_cgp = r'(?P<action>\w+)'
    scope_cgp = r'(?P<scope>\w*)'
    subject_cgp = r'(?P<subject>.+)'

    pattern_string = pattern_string \
        .replace(r'\{action\}', action_cgp) \
        .replace(r'\{scope\}', scope_cgp) \

    if label_position == 'header':
        pattern_string = pattern_string \
            .replace(r'\{subject\}', subject_cgp)

    regexp_pattern = re.compile(pattern_string)

    semantic_commits = []

    for commit in commits:
        text = commit.header if label_position == 'header' else commit.footer
        match = regexp_pattern.search(text)

        if not match:
            continue

        metadata = match.groupdict()

        if label_position == 'footer':
            metadata['subject'] = commit.header

        sc = SemanticCommit(
            subject=metadata['subject'].strip(),
            action=metadata['action'],
            scope=metadata.get('scope') or None,
            message=commit.message,
        )

        semantic_commits.append(sc)

    return semantic_commits
