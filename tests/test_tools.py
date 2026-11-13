import pytest

from assistant_core.errors import InvalidRequest
from assistant_core.tools import parse_credits, tuition


def test_parse_with_retake():
    assert parse_credits("tuition for 18 credits and 2 retake") == (18, 2)


def test_parse_without_retake():
    assert parse_credits("fee for 15 credits") == (15, 0)


def test_parse_no_numbers_raises():
    with pytest.raises(InvalidRequest, match="How many credits?"):
        parse_credits("tuition for credits")


def test_tuition_value():
    assert tuition(18, 2, 450_000, 1.5, 30) == 9_450_000  # same as the monolith


def test_tuition_no_retake():
    assert tuition(20, 0, 450_000, 1.5, 30) == 9_000_000


@pytest.mark.parametrize("credits", [0, 31, -1, 100])
def test_tuition_out_of_range(credits):
    with pytest.raises(InvalidRequest):
        tuition(credits, 0, 450_000, 1.5, 30)


@pytest.mark.parametrize("credits", [1, 30])
def test_tuition_boundaries(credits):
    res = tuition(credits, 0, 450_000, 1.5, 30)
    assert res == credits * 450_000
