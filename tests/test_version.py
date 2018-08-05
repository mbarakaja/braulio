import pytest
from braulio.version import validate_version_str, Version, get_next_version


parametrize = pytest.mark.parametrize

version_strings = [
    ("1", True),
    ("1.1", True),
    ("1.1.1", True),
    ("0", True),
    ("0.0", True),
    ("0.0.0", True),
    ("1.0.0", True),
    ("0.1.0", True),
    ("0.0.1", True),
    ("10.10.10", True),
    ("010.010.010", True),
    ("abc", False),
    ("a.b.c", False),
    ("1.1.1.1", False),
    ("1.10.1", True),
]


@parametrize("string, expected", version_strings)
def test_validate_version_str(string, expected):
    assert validate_version_str(string) is expected


class TestVersion:
    def test_constructor_without_arguments(self):
        version = Version()

        assert version.major == 0
        assert version.minor == 0
        assert version.patch == 0
        assert version.string == "0.0.0"

    def test_constructor_with_major_minor_patch_arguments(self):
        version = Version(major=1, minor=2, patch=3)

        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.string == "1.2.3"

    @parametrize(
        "bump_type, major, minor, patch, string",
        [
            ("major", 2, 0, 0, "2.0.0"),
            ("minor", 1, 3, 0, "1.3.0"),
            ("patch", 1, 2, 4, "1.2.4"),
        ],
    )
    def test_bump_method(self, bump_type, major, minor, patch, string):
        version = Version("1.2.3")
        version.bump(bump_type=bump_type)

        assert version.major == major
        assert version.minor == minor
        assert version.patch == patch
        assert version.string == string

    @parametrize(
        "left, right, expected",
        [
            ("4.0.0", "4.0.0", False),
            ("2.0.1", "2.0.0", False),
            ("1.4.0", "1.3.0", False),
            ("3.0.0", "2.23.8", False),
            ("2.0.0", "2.0.1", True),
            ("1.3.0", "1.4.0", True),
            ("2.23.8", "3.0.0", True),
        ],
    )
    def test_less_than_operator(self, left, right, expected):
        assert (Version(left) < Version(right)) is expected

    @parametrize(
        "left, right, expected",
        [
            ("4.0.0", "4.0.0", False),
            ("2.0.1", "2.0.0", True),
            ("1.4.0", "1.3.0", True),
            ("3.0.0", "2.23.8", True),
            ("2.0.0", "2.0.1", False),
            ("1.3.0", "1.4.0", False),
            ("2.23.8", "3.0.0", False),
        ],
    )
    def test_greater_than_operator(self, left, right, expected):
        assert (Version(left) > Version(right)) is expected

    @parametrize(
        "left, right, expected",
        [
            ("2.24.1", "2.24.1", True),
            ("7.4.0", "2.23.8", False),
            ("1.3.0", "1.4.0", False),
            ("2.23.8", "3.0.0", False),
        ],
    )
    def test_equal_to_operator(self, left, right, expected):
        assert (Version(left) == Version(right)) is expected

    @parametrize(
        "left, right, expected",
        [
            ("2.24.1", "2.24.1", False),
            ("7.4.0", "2.23.8", True),
            ("1.3.0", "1.4.0", True),
            ("2.23.8", "3.0.0", True),
        ],
    )
    def test_no_equal_to_operator(self, left, right, expected):
        assert (Version(left) != Version(right)) is expected

    @parametrize(
        "left, right, expected",
        [
            ("2.24.1", "2.24.1", True),
            ("7.4.0", "2.23.8", False),
            ("1.3.0", "1.4.0", True),
            ("2.23.8", "3.0.0", True),
        ],
    )
    def test_less_or_equal_to_operator(self, left, right, expected):
        assert (Version(left) <= Version(right)) is expected

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


@parametrize(
    "bump_version_to, last_version, expected",
    [
        ("0.0.0", Version("0.0.0"), None),
        ("0.0.0", Version("0.0.1"), None),
        ("0.0.2", Version("0.0.1"), Version("0.0.2")),
        ("0.0.0", None, Version("0.0.0")),
        ("7.0.0", None, Version("7.0.0")),
        ("0.8.0", None, Version("0.8.0")),
        ("0.0.12", None, Version("0.0.12")),
        ("major", Version("4.4.7"), Version("5.0.0")),
        ("minor", Version("4.4.7"), Version("4.5.0")),
        ("patch", Version("4.4.7"), Version("4.4.8")),
        ("major", None, Version("1.0.0")),
        ("minor", None, Version("0.1.0")),
        ("patch", None, Version("0.0.1")),
    ],
)
def test_get_next_version(bump_version_to, last_version, expected):
    new_version = get_next_version(
        bump_version_to=bump_version_to, last_version=last_version
    )

    assert new_version == expected
