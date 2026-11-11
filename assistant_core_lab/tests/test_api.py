from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from assistant_api.db import Repository, init_db, make_engine
from assistant_api.main import create_app
from assistant_api.weather import WeatherClient
from assistant_core.config import Settings

OK_JSON = {"current": {"time": "2026-10-05T09:00", "temperature_2m": 31.2, "weather_code": 3, "wind_speed_10m": 8.5}}


def weather_with(handler) -> WeatherClient:
    transport = httpx.MockTransport(handler)
    return WeatherClient("https://example.test/forecast", 10.76, 106.68, retries=1, transport=transport)


@pytest.fixture
def client(settings, service):
    settings = settings.model_copy(update={"api_admin_key": "secret-admin", "rate_limit_per_min": 5})
    app = create_app(settings, service, weather_with(lambda req: httpx.Response(200, json=OK_JSON)))
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_chat_fee(client):
    r = client.post("/v1/chat", json={"message": "tuition for 18 credits and 2 retake"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "fee" and "9,450,000" in body["answer"] and body["request_id"]


def test_chat_validation_error(client):
    r = client.post("/v1/chat", json={"message": ""})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


def test_offices_status_200(client):
    r = client.get("/v1/offices")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    names = [o["name"] for o in data]
    assert names == sorted(names)


def test_offices_contains_library(client):
    r = client.get("/v1/offices")
    assert r.status_code == 200
    data = r.json()
    library = next((o for o in data if o["name"] == "Library"), None)
    assert library is not None
    assert library["room"] == "B.201"


def test_rate_limit(client):
    codes = [client.post("/v1/chat", json={"message": "hi"}).status_code for _ in range(6)]
    assert codes[-1] == 429


def test_rate_limit_error_body(client):
    for _ in range(5):
        client.post("/v1/chat", json={"message": "hi"})
    r = client.post("/v1/chat", json={"message": "hi"})
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "too_many_requests"
    assert r.json()["error"]["message"] == "Too many requests"


def test_feedback_roundtrip(client):
    chat_resp = client.post("/v1/chat", json={"message": "hi"})
    assert chat_resp.status_code == 200
    req_id = chat_resp.json()["request_id"]

    r = client.post("/v1/feedback", json={"request_id": req_id, "rating": 1})
    assert r.status_code == 201 and r.json()["id"] == 1
    assert client.get("/v1/feedback").status_code == 401
    listed = client.get("/v1/feedback", headers={"X-API-Key": "secret-admin"})
    assert listed.status_code == 200 and len(listed.json()) == 1
    assert listed.json()[0]["request_id"] == req_id


def test_feedback_valid_ratings(client):
    for r_val in (-1, 0, 1):
        chat_resp = client.post("/v1/chat", json={"message": f"question {r_val}"})
        assert chat_resp.status_code == 200
        req_id = chat_resp.json()["request_id"]

        resp = client.post(
            "/v1/feedback", json={"request_id": req_id, "rating": r_val, "comment": "test feedback"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["rating"] == r_val
        assert data["request_id"] == req_id
        assert "id" in data
        assert "created_at" in data


def test_feedback_rating_out_of_range(client):
    assert client.post("/v1/feedback", json={"request_id": "x", "rating": 5}).status_code == 422
    assert client.post("/v1/feedback", json={"request_id": "x", "rating": -2}).status_code == 422


def test_feedback_unknown_request_id_returns_404(client):
    r = client.post("/v1/feedback", json={"request_id": "unknown-req", "rating": 1})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "interaction_not_found"


def test_feedback_list_newest_first_and_limit(client):
    ids = []
    for i in range(3):
        req_id = client.post("/v1/chat", json={"message": f"msg {i}"}).json()["request_id"]
        fb = client.post("/v1/feedback", json={"request_id": req_id, "rating": 1, "comment": f"c{i}"})
        assert fb.status_code == 201
        ids.append(fb.json()["id"])

    all_fb = client.get("/v1/feedback", headers={"X-API-Key": "secret-admin"})
    assert all_fb.status_code == 200
    assert [item["id"] for item in all_fb.json()] == list(reversed(ids))

    limited = client.get("/v1/feedback?limit=2", headers={"X-API-Key": "secret-admin"})
    assert limited.status_code == 200
    assert [item["id"] for item in limited.json()] == [ids[2], ids[1]]

    invalid_limit = client.get("/v1/feedback?limit=0", headers={"X-API-Key": "secret-admin"})
    assert invalid_limit.status_code == 422
    assert invalid_limit.json()["error"]["code"] == "invalid_request"


def test_feedback_persists_across_app_restart(tmp_path: Path, service):
    db_url = f"sqlite:///{tmp_path / 'feedback_api.db'}"
    settings = Settings(database_url=db_url, session_salt="test-salt", api_admin_key="secret-admin")

    engine1 = make_engine(db_url)
    init_db(engine1)
    app1 = create_app(
        settings,
        service,
        weather_with(lambda req: httpx.Response(200, json=OK_JSON)),
        repo=Repository(engine1, settings.session_salt),
    )
    client1 = TestClient(app1)
    req_id = client1.post("/v1/chat", json={"message": "tuition for 10 credits"}).json()["request_id"]
    post_resp = client1.post("/v1/feedback", json={"request_id": req_id, "rating": -1, "comment": "needs detail"})
    assert post_resp.status_code == 201
    engine1.dispose()

    engine2 = make_engine(db_url)
    app2 = create_app(
        settings,
        service,
        weather_with(lambda req: httpx.Response(200, json=OK_JSON)),
        repo=Repository(engine2, settings.session_salt),
    )
    client2 = TestClient(app2)
    get_resp = client2.get("/v1/feedback", headers={"X-API-Key": "secret-admin"})
    assert get_resp.status_code == 200
    items = get_resp.json()
    assert len(items) == 1
    assert items[0]["request_id"] == req_id
    assert items[0]["rating"] == -1
    assert items[0]["comment"] == "needs detail"
    engine2.dispose()


def test_feedback_auth_missing_or_invalid_key(client):
    assert client.get("/v1/feedback").status_code == 401
    assert client.get("/v1/feedback", headers={"X-API-Key": "wrong-key"}).status_code == 401


def test_weather_ok(client):
    r = client.get("/v1/weather")
    assert r.status_code == 200 and r.json()["description"] == "overcast"


def test_weather_down_returns_503(settings, service):
    def boom(req):
        raise httpx.ConnectTimeout("timeout", request=req)

    app = create_app(settings, service, weather_with(boom))
    r = TestClient(app).get("/v1/weather")
    assert r.status_code == 503 and r.json()["error"]["code"] == "weather_service_unavailable"


def test_weather_stale_cache_when_upstream_fails():
    calls = {"n": 0}

    def flaky(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json=OK_JSON)
        return httpx.Response(500)

    w = weather_with(flaky)
    w.cache_ttl_s = 0  # force a refresh on the second call
    assert not w.current().stale
    assert w.current().stale
