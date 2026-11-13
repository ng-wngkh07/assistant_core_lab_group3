# Lab 4 homework — design for an external service that goes down

Service chosen (weather / maps / news / other approved): Open-Meteo Weather  Base URL: https://api.open-meteo.com/v1/forecast

| Failure | How you simulate it | What your API returns | What the user sees |
|---|---|---|---|
| timeout | transport raises ConnectTimeout | HTTP 503 `{"error": {"code": "weather_service_unavailable", "message": "Weather service unavailable"}}` | Weather service temporarily unavailable |
| 500 from upstream | MockTransport returns 500 | HTTP 503 `{"error": {"code": "weather_service_unavailable", "message": "Weather service unavailable"}}` (or stale cached weather if cached earlier with `stale: true`) | Stale weather notice or unavailable warning |
| malformed JSON | MockTransport returns `{}` | HTTP 503 `{"error": {"code": "weather_service_unavailable", "message": "Weather service unavailable"}}` | Weather service temporarily unavailable |
| rate limited (429) | MockTransport returns 429 | HTTP 503 `{"error": {"code": "weather_service_unavailable", "message": "Weather service unavailable"}}` | Weather service temporarily unavailable |

Timeout value and why: 3.0s — Prevents API requests from blocking too long when external provider is slow.
Retries and why: 1 retry with 0.2s backoff — Recovers from transient connection glitches without worsening upstream congestion.
Cache TTL and why: 600s (10 min) — Weather data updates infrequently; caching provides snappy responses and serves as fallback if upstream fails.
Tests added (file + names):
- `tests/test_api.py`: `test_weather_ok`, `test_weather_down_returns_503`, `test_weather_stale_cache_when_upstream_fails`, `test_rate_limit`, `test_rate_limit_error_body`
