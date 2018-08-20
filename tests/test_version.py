import pytest
from unittest.mock import patch as mock_patch
from collections import OrderedDict
from braulio.version import (
    validate_version_str,
    Version,
    get_next_version,
    parse_version_string_parts,
    Stage,
)


parametrize = pytest.mark.parametrize


@pytest.fixture
def stages():
    return OrderedDict(
        dev=Stage("dev", "{major}.{minor}.{patch}.dev{n}"),
        beta=Stage("beta", "{major}.{minor}.{patch}beta{n}"),
        final=Stage("final", "{major}.{minor}.{patch}"),
    )


version_strings = [
    # ---- invalids -----
    ("abc", None),
    ("a.b.c", None),
    ("1.1.1.1", None),
    ("1.", None),
    ("1.1.", None),
    ("1.1.1.", None),
    ("1.2.3.dev", None),
    ("1.2.3a", None),
    ("1.2.3alpha", None),
    ("1.2.3beta", None),
    ("1.2.3b3ta0", None),
    ("1.2.3rc", None),
    # ---- valids -----
    ("1", {"major": 1, "minor": 0, "patch": 0, "stage": None, "n": 0}),
    ("1.1", {"major": 1, "minor": 1, "patch": 0, "stage": None, "n": 0}),
    ("1.1.1", {"major": 1, "minor": 1, "patch": 1, "stage": None, "n": 0}),
    ("0", {"major": 0, "minor": 0, "patch": 0, "stage": None, "n": 0}),
    ("0.0", {"major": 0, "minor": 0, "patch": 0, "stage": None, "n": 0}),
    ("0.0.0", {"major": 0, "minor": 0, "patch": 0, "stage": None, "n": 0}),
    ("7.10.3", {"major": 7, "minor": 10, "patch": 3, "stage": None, "n": 0}),
    ("30.1.11", {"major": 30, "minor": 1, "patch": 11, "stage": None, "n": 0}),
    ("010.05.04", {"major": 10, "minor": 5, "patch": 4, "stage": None, "n": 0}),
    ("1.2.3.dev1", {"major": 1, "minor": 2, "patch": 3, "stage": "dev", "n": 1}),
    ("1.2.3a3", {"major": 1, "minor": 2, "patch": 3, "stage": "a", "n": 3}),
    ("1.2.3alpha5", {"major": 1, "minor": 2, "patch": 3, "stage": "alpha", "n": 5}),
]


@parametrize("string, expected", version_strings)
def test_validate_version_str(string, expected):
    assert validate_version_str(string) is bool(expected)


@parametrize("string, parts", version_strings)
def test_parse_version_string_parts(string, parts):
    result = parse_version_string_parts(string)
    assert result == parts


class TestVersion:
    def test_default(self):
        version = Version()

        assert version.major == 0
        assert version.minor == 0
        assert version.patch == 0
        assert version.string == "0.0.0"
        assert version.stage == "final"
        assert version.n is 0

    def test_invalid_version_string_argument(self):
        with pytest.raises(ValueError):
            Version("invalid")

    @parametrize(
        "string, major, minor, patch, stage, n",
        [
            ("1.2.3", 1, 2, 3, "final", 0),
            ("1", 1, 0, 0, "final", 0),
            ("2.1a2", 2, 1, 0, "a", 2),
            ("3.1.4.dev0", 3, 1, 4, "dev", 0),
        ],
    )
    def test_deserializing(self, string, minor, major, patch, stage, n):
        stages = OrderedDict(
            dev=Stage("dev", "{major}.{minor}.{patch}dev{n}"),
            a=Stage("alpha", "{major}.{minor}.{patch}a{n}"),
            final=Stage("final", "{major}.{minor}.{patch}"),
        )

        with mock_patch.object(Version, "stages", stages):
            version = Version(string)

            assert version.major == major
            assert version.minor == minor
            assert version.patch == patch
            assert version.stage == stage
            assert version.n == n

    @parametrize(
        "major, minor, patch, expected", [(1, 2, 3, "1.2.3"), (1, 0, 0, "1.0.0")]
    )
    def test_default_serializers(self, major, minor, patch, expected):
        version = Version(major=major, minor=minor, patch=patch)

        assert version.string == expected

    @parametrize(
        "major, minor, patch, stage, n, expected",
        [
            (1, 2, 3, None, 0, "1.2.3"),
            (2, 1, 0, "dev", 2, "2.1.0.dev2"),
            (2, 1, 0, "beta", 1, "2.1.0beta1"),
        ],
    )
    def test_custom_serializers(self, major, minor, patch, stage, n, expected, stages):
        with mock_patch.object(Version, "stages", stages):
            version = Version(major=major, minor=minor, patch=patch, stage=stage, n=n)

            assert version.string == expected

    def test_unknown_stage(self):
        error = "gama is an unknown stage"

        with pytest.raises(ValueError, match=error):
            Version("2.0.7gama0")

    def test_set_stages(self, stages):
        _stages = [
            ("dev", "{major}.{minor}.{patch}.dev{n}"),
            ("beta", "{major}.{minor}.{patch}beta{n}"),
            ("final", "{major}.{minor}.{patch}"),
        ]

        with mock_patch.object(Version, "stages", {}):
            Version.set_stages(_stages)

            assert Version.stages == stages

    def test_set_stages_with_invalid_serializer(self):
        stages = [
            ("alpha", "{major}.{minor}.{patch}a{n}"),
            ("beta", "{major}.{patch}beta{n}"),
            ("final", "{major}.{minor}.{patch}"),
        ]

        message = "{major}.{patch}beta{n} is an invalid serializer"

        with pytest.raises(ValueError, match=message):
            Version.set_stages(stages)

    @parametrize(
        "current, bump_part, expected",
        [
            ("1.2.3", "major", "2.0.0"),
            ("1.2.3", "minor", "1.3.0"),
            ("1.2.3", "patch", "1.2.4"),
            ("1.2.3.dev0", "dev", "1.2.3.dev1"),
            ("1.2.3.dev5", "beta", "1.2.3beta0"),
            ("1.2.3.dev5", "final", "1.2.3"),
            ("1.2.3beta0", "final", "1.2.3"),
        ],
        ids=[
            "major",
            "minor",
            "patch",
            "stage numerical component",
            "to next stage",
            "from pre-release stage to final stage",
            "from first stage to final stage",
        ],
    )
    def test_bump(self, current, bump_part, expected, stages):
        with mock_patch.object(Version, "stages", stages):
            version = Version(current)
            new_version = version.bump(bump_part)

            assert new_version == Version(expected)
            assert new_version is not version

    @parametrize(
        "current, bump_part, message",
        [
            ("1.2.3beta0", "dev", "dev stage is previous to 1.2.3beta0"),
            ("1.2.3beta0", "major", "Can't do a major version bump"),
            ("1.2.3beta0", "minor", "Can't do a minor version bump"),
            ("1.2.3beta0", "patch", "Can't do a patch version bump"),
            ("1.2.3", "final", "1.2.3 is already in final stage"),
            ("1.2.3", "unknown", "Unknown unknown stage"),
        ],
        ids=[
            "to previous stage",
            "major part in pre-release stage",
            "minor part in pre-release stage",
            "patch part in pre-release stage",
            "from final to final stage",
            "unknown stage",
        ],
    )
    def test_invalid_bump(self, current, bump_part, message, stages):
        with mock_patch.object(Version, "stages", stages):
            with pytest.raises(ValueError, match=message):
                version = Version(current)
                version.bump(bump_part)

    @parametrize(
        "left, right",
        [
            (Version(), 1),
            (Version(), "2.23.8"),
            (Version(), None),
            (Version(), True),
            (1, Version()),
            ("2.23.8", Version()),
            (None, Version()),
            (True, Version()),
        ],
    )
    def test_comparators_with_invalid_values(self, left, right):
        error_message = "not supported"

        with pytest.raises(TypeError, match=error_message):
            left > right

        with pytest.raises(TypeError, match=error_message):
            left < right

        with pytest.raises(TypeError, match=error_message):
            left <= right

        with pytest.raises(TypeError, match=error_message):
            left >= right

        with pytest.raises(TypeError, match=error_message):
            left == right

        with pytest.raises(TypeError, match=error_message):
            left != right

    def test_repr(self):
        assert repr(Version("3.2.1")) == "Version('3.2.1')"

    def test_str(self):
        assert str(Version("3.2.1")) == "3.2.1"


# This tuple defines the expected result of comparing
# two Version instances using <, >, ==, <= operators.
version_strings_to_compare = (
    ("4.0.0", "4.0.0", False, False, True),
    ("2.0.1", "2.0.0", False, True, False),
    ("1.4.0", "1.3.0", False, True, False),
    ("3.0.0", "2.23.8", False, True, False),
    ("2.0.0", "2.0.1", True, False, False),
    ("1.3.0", "1.4.0", True, False, False),
    ("2.23.8", "3.0.0", True, False, False),
    ("1.0.0.dev1", "1.0.0.dev0", False, True, False),
    ("0.1.0.dev1", "0.1.0.dev0", False, True, False),
    ("0.0.1.dev1", "0.0.1.dev0", False, True, False),
    ("2.0.0.dev0", "2.0.0.dev0", False, False, True),
    ("0.2.0.dev0", "0.2.0.dev0", False, False, True),
    ("0.0.2.dev0", "0.0.2.dev0", False, False, True),
    ("3.0.0beta0", "3.0.0.dev7", False, True, False),
    ("0.3.0beta0", "0.3.0.dev7", False, True, False),
    ("0.0.3beta0", "0.0.3.dev7", False, True, False),
    ("5.0.0.dev0", "4.0.0beta1", False, True, False),
    ("0.5.0.dev0", "0.4.0beta1", False, True, False),
    ("0.0.5.dev0", "0.0.4beta1", False, True, False),
    ("6.0.0", "6.0.0beta1", False, True, False),
    ("0.6.0", "0.6.0beta1", False, True, False),
    ("0.0.6", "0.0.6beta1", False, True, False),
    ("1.0.0.dev0", "1.0.0.dev1", True, False, False),
    ("0.1.0.dev0", "0.1.0.dev1", True, False, False),
    ("0.0.1.dev0", "0.0.1.dev1", True, False, False),
    ("3.0.0dev3", "3.0.0beta0", True, False, False),
    ("0.3.0dev3", "0.3.0beta0", True, False, False),
    ("0.0.3dev3", "0.0.3beta0", True, False, False),
    ("6.0.0beta5", "6.0.0", True, False, False),
    ("0.6.0beta5", "0.6.0", True, False, False),
    ("0.0.6beta5", "0.0.6", True, False, False),
)


@parametrize("left, right, is_less, is_greater, is_equal", version_strings_to_compare)
def test_comparison_operators(left, right, is_less, is_greater, is_equal, stages):
    with mock_patch.object(Version, "stages", stages):
        assert (Version(left) < Version(right)) is is_less
        assert (Version(left) > Version(right)) is is_greater
        assert (Version(left) == Version(right)) is is_equal
        assert (Version(left) <= Version(right)) is (is_less or is_equal)
        assert (Version(left) >= Version(right)) is (is_greater or is_equal)
        assert (Version(left) != Version(right)) is not is_equal


@parametrize(
    "current, bump_to, stage, expected",
    [
        ("0.0.0", "major", None, "1.0.0"),
        ("0.0.0", "minor", None, "0.1.0"),
        ("0.0.0", "patch", None, "0.0.1"),
        ("0.0.0", "0.0.0", None, None),
        ("0.0.1", "0.0.0", None, None),
        ("0.0.1", "0.0.2", None, "0.0.2"),
        ("4.4.7", "major", None, "5.0.0"),
        ("4.4.7", "minor", None, "4.5.0"),
        ("4.4.7", "patch", None, "4.4.8"),
        ("4.4.7", "major", "dev", "5.0.0.dev0"),
        ("4.4.7", "minor", "dev", "4.5.0.dev0"),
        ("4.4.7", "patch", "dev", "4.4.8.dev0"),
        ("3.0.0.dev2", None, "beta", "3.0.0beta0"),
        ("3.0.0beta3", None, "beta", "3.0.0beta4"),
        ("4.4.7beta3", None, None, "4.4.7"),
        ("4.4.7", None, None, None),
    ],
)
def test_get_next_version(current, bump_to, stage, expected, stages):
    with mock_patch.object(Version, "stages", stages):
        current = Version(current)
        expected = Version(expected) if expected else None

        new_version = get_next_version(current, bump_to, stage)

        assert new_version == expected
