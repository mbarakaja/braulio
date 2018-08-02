import re


VERSION_STRING_REGEXP = re.compile(
    '(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?$')


def validate_version_str(string):
    return bool(re.match(VERSION_STRING_REGEXP, string))


class Version:
    def __init__(self, string=None, major=0, minor=0, patch=0):

        if string:
            self.string = string
            major, minor, patch = string.split('.')

        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)

        self._update_version_string()

    def bump(self, bump_type):
        if bump_type == 'major':
            self.major += 1
            self.minor, self.patch = 0, 0
        elif bump_type == 'minor':
            self.minor += 1
            self.patch = 0
        else:
            self.patch += 1

        self._update_version_string()

    def _update_version_string(self):
        self.string = f'{self.major}.{self.minor}.{self.patch}'

    def _is_comparable(self, value):
        if not isinstance(value, Version):
            raise TypeError(
                f"Comparison not supported"
                f" between instances of '{type(self)}'"
                f" and '{type(value)}'"
            )

    def __eq__(self, v):
        self._is_comparable(v)

        return (
            self.major == v.major and
            self.minor == v.minor and
            self.patch == v.patch
        )

    def __lt__(self, v):
        self._is_comparable(v)

        if self.major < v.major:
            return True

        if self.major > v.major:
            return False

        if self.minor < v.minor:
            return True

        if self.minor > v.minor:
            return False

        return self.patch < v.patch

    def __le__(self, v):
        self._is_comparable(v)

        return self < v or self == v

    def __str__(self):
        return self.string

    def __repr__(self):
        return f"Version('{self.string}')"


def get_next_version(bump_version_to, last_version=None):

    if bump_version_to not in {'major', 'minor', 'patch'}:
        new_version = Version(bump_version_to)

        if last_version and new_version <= last_version:
            return None

        return new_version

    new_version = Version()

    if last_version:
        new_version = Version(
            major=last_version.major,
            minor=last_version.minor,
            patch=last_version.patch,
        )

    new_version.bump(bump_version_to)

    return new_version
