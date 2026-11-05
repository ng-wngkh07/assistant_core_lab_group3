import pytest
from pydantic import ValidationError

from assistant_core.models import Intent, Message
from assistant_core.responder import StubLLMResponder


def test_service_greeting(service):
    r = service.handle(Message(text="hello"))
    assert r.intent == Intent.GREETING
    assert "Hello! I can help" in r.answer
    assert not r.degraded


def test_service_fee_valid(service):
    r = service.handle(Message(text="tuition for 18 credits and 2 retake"))
    assert r.intent == Intent.FEE
    assert "9,450,000" in r.answer
    assert not r.degraded


def test_service_fee_invalid(service):
    r = service.handle(Message(text="fee for 35 credits"))
    assert r.intent == Intent.FEE
    assert r.degraded
    assert "Credits must be between 1 and 30" in r.answer


def test_service_office(service):
    r = service.handle(Message(text="where is the library?"))
    assert r.intent == Intent.OFFICE
    assert "Library" in r.answer
    assert "room B.201" in r.answer
    assert "Mon-Sat 07:00-20:00" in r.answer


def test_service_rule(service):
    r = service.handle(Message(text="thesis registration credits"))
    assert r.intent == Intent.RULE
    assert len(r.sources) == 1
    assert r.sources[0].id == "H26-5.3"
    assert "100 credits" in r.answer
    assert not r.degraded


def test_service_rule_unknown(service):
    r = service.handle(Message(text="how to build a spaceship"))
    assert r.intent == Intent.UNKNOWN
    assert "Sorry, I don't know that yet." in r.answer
    assert r.sources == []


def test_fallback_when_provider_fails(service):
    service.responder = StubLLMResponder(fail=True)
    r = service.handle(Message(text="thesis registration credits"))
    assert r.degraded and r.sources
    assert r.sources[0].id == "H26-5.3"
    assert "Graduation Thesis Registration: Undergraduate students" in r.answer


def test_empty_message_validation_error():
    with pytest.raises(ValidationError):
        Message(text="")


def test_office_directory_all(offices):
    all_offices = offices.all()
    assert len(all_offices) == 5
    names = [o.name for o in all_offices]
    assert names == sorted(names)
    assert any(o.name == "Library" for o in all_offices)
