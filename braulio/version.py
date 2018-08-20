import re
from collections import OrderedDict, namedtuple
from string import Formatter


VERSION_STRING_PATTERN = (
    "(?P<major>\d+)"  # Major part
    "(?:\.(?P<minor>\d+))?"  # Minor part (optional)
    "(?:\.(?P<patch>\d+))?"  # Patch part (optional)
    "(?:\.?(?P<stage>[a-z]+)(?P<n>\d+))?"  # Pre-release (optional)
)

VERSION_STRING_REGEXP = re.compile(f"^{VERSION_STRING_PATTERN}$")


def validate_version_str(string):
    return bool(re.match(VERSION_STRING_REGEXP, string))


def parse_version_string_parts(string):
    match = VERSION_STRING_REGEXP.match(string)

    if not match:
        return None

    parts = match.groupdict(default=0)

    return OrderedDict(
        major=int(parts["major"]),
        minor=int(parts["minor"]),
        patch=int(parts["patch"]),
        stage=parts["stage"] or None,
        n=int(parts["n"]),
    )


stage_pattern = re.compile(
    "^(?:{major}\.{minor}\.{patch})"  # Required parts
    "(?:\.?(?P<stage>[a-z]+)?\{n\})?$"  # Optional parts
)


Stage = namedtuple("Stage", ["label", "serializer"])


class Version:

    pattern = VERSION_STRING_PATTERN

    stages = {"final": Stage("final", "{major}.{minor}.{patch}")}

    def __init__(self, string=None, major=0, minor=0, patch=0, stage=None, n=0):

        self.tag = None

        if string:
            parts = parse_version_string_parts(string)

            if not parts:
                raise ValueError(f"Invalid version string: {string}")

            major, minor, patch, stage, n = parts.values()

        stage = stage or "final"
        n = 0 if stage == "final" else n

        try:
            self.serializer = self.stages[stage].serializer
            index = tuple(self.stages).index(stage)
        except KeyError:
            raise ValueError(f"{stage} is an unknown stage")

        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)
        self.stage = stage or None
        self.n = int(n)

        args = major, minor, patch, index, n
        self._number = int("{:0>3}{:0>3}{:0>3}{:0>3}{:0>3}".format(*args))

        parts = {}
        serializer = self.serializer

        for p in Formatter().parse(serializer):
            part = p[1]
            if part:
                parts[p[1]] = getattr(self, p[1])

        self._string = serializer.format(**parts)
        self._stage_number = index

    @classmethod
    def set_stages(cls, stages):
        _stages = OrderedDict()

        for label, serializer in stages:
            match = stage_pattern.match(serializer)

            if not match:
                raise ValueError(f"{serializer} is an invalid serializer")

            key = match.groupdict(default="final")["stage"]
            _stages[key] = Stage(label, serializer)

        cls.stages = _stages

    def bump(self, bump_part):
        """Return a new bumped version instance."""

        major, minor, patch, stage, n = tuple(self)

        # stage bump
        if bump_part not in {"major", "minor", "patch"}:

            if bump_part not in self.stages:
                raise ValueError(f"Unknown {bump_part} stage")

            # We can not bump from final stage to final again.
            if self.stage == "final" and bump_part == "final":
                raise ValueError(f"{self} is already in final stage.")

            # bump in the same stage (numeric part)
            if bump_part == self.stage:
                n += 1
            else:
                new_stage_number = tuple(self.stages).index(bump_part)

                # We can not bump to a previous stage
                if new_stage_number < self._stage_number:
                    raise ValueError(f"{bump_part} stage is previous to {self}")

                stage = bump_part
                n = 0
        else:
            # major, minor, or patch bump

            # Only version in final stage can do a major, minor or patch
            # bump
            if self.stage != "final":
                raise ValueError(
                    f"{self} is a pre-release version."
                    f" Can't do a {bump_part} version bump"
                )

            if bump_part == "major":
                major += 1
                minor, patch = 0, 0
            elif bump_part == "minor":
                minor += 1
                patch = 0
            else:
                patch += 1

        return Version(major=major, minor=minor, patch=patch, stage=stage, n=n)

    @property
    def string(self):
        return self._string

    def _is_comparable(self, value):
        if not isinstance(value, Version):
            raise TypeError(
                f"Comparison not supported"
                f" between instances of '{type(self)}'"
                f" and '{type(value)}'"
            )

    def __eq__(self, v):
        self._is_comparable(v)

        return self._number == v._number

    def __lt__(self, v):
        self._is_comparable(v)
        return self._number < v._number

    def __le__(self, v):
        self._is_comparable(v)

        return self._number <= v._number

    def __iter__(self):
        yield self.major
        yield self.minor
        yield self.patch
        yield self.stage
        yield self.n

    def __str__(self):
        return self.string

    def __repr__(self):
        return f"Version('{self.string}')"


def get_next_version(current, bump_to=None, stage=None):

    if current.stage != "final":
        stage = stage or "final"
        return current.bump(stage)

    if bump_to:
        parts = {"major", "minor", "patch"}
        _version = current.bump(bump_to) if bump_to in parts else Version(bump_to)
    else:
        _version = current

    if stage:
        args = list(_version)
        args[-2] = stage
        _version = Version(None, *args)

    if _version <= current:
        return None

    return _version
