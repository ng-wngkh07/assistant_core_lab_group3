from assistant_core.models import Intent
from assistant_core.router import route

OFFICE_NAMES = {"library", "student affairs", "finance"}


def test_route_greeting():
    assert route("Hello!", OFFICE_NAMES) == Intent.GREETING
    assert route("xin chao?", OFFICE_NAMES) == Intent.GREETING


def test_route_fee():
    assert route("tuition for 18 credits and 2 retake", OFFICE_NAMES) == Intent.FEE
    assert route("How much is the fee?", OFFICE_NAMES) == Intent.FEE


def test_route_office():
    assert route("Where is the library?", OFFICE_NAMES) == Intent.OFFICE
    assert route("contact student affairs office", OFFICE_NAMES) == Intent.OFFICE


def test_route_rule():
    assert route("thesis registration credits", OFFICE_NAMES) == Intent.RULE
    assert route("exam absence regulations", OFFICE_NAMES) == Intent.RULE
