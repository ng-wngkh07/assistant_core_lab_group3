# Lab 4 — API contract worksheet

Fill in one row per endpoint **before** you code it.

| Method | Path | Request body / params | Success (code + body) | Errors (code + error.code) | Who calls it |
|---|---|---|---|---|---|
| GET | /health | — | 200 `{"status": "ok", "version": "1.0.0"}` | — | ops, UI |
| POST | /v1/chat | JSON `{"message": str, "session_id": str}` | 200 `ChatResponse(answer, intent, sources, degraded, request_id)` | 422 `invalid_request`, 429 `too_many_requests` | UI, tests |
| GET | /v1/offices | — | 200 `list[OfficeOut(name, room, hours)]` | — | UI, tests |
| POST | /v1/feedback | JSON `{"request_id": str, "rating": int (-1, 0, 1), "comment": str?}` | 201 `FeedbackOut(id, created_at, request_id, rating, comment)` | 404 `interaction_not_found`, 422 `invalid_request` | UI |
| GET | /v1/feedback | Header `X-API-Key: str`, query `limit?: int (1–1000)` | 200 `list[FeedbackOut]` | 401 `missing_or_invalid_api_key`, 422 `invalid_request` | staff dashboard |
| GET | /v1/weather | — | 200 `Weather(temperature_c, wind_kmh, description, observed_at, stale)` | 503 `weather_service_unavailable` | UI |

Questions:
1. Which fields are required, and what are their limits?
   - `ChatRequest`: `message` (required, 1-2000 chars), `session_id` (optional, default "anonymous", max 64 chars).
   - `FeedbackIn`: `request_id` (required, 1-64 chars), `rating` (required int, -1 to 1: -1 = thumbs down, 0 = neutral, 1 = thumbs up), `comment` (optional, max 500 chars).
   - `Header`: `X-API-Key` required on `GET /v1/feedback` to match configured `API_ADMIN_KEY`.
2. What does the UI show for each error code?
   - 401: "Missing or invalid API key" - prompts admin to authenticate or re-enter key.
   - 404: "Interaction not found" - feedback references an unknown or unrecorded `request_id`.
   - 422: Form validation message indicating field-level errors (e.g. "rating: Input should be less than or equal to 1").
   - 429: "Too many requests. Please wait a moment before asking again."
   - 503: "Weather service unavailable" - indicates downstream service failure, fallback shown if cached data exists.
3. What changes would force a `/v2`?
   - Breaking change to request body fields (e.g., changing `rating` to a 5-star scale 1-5 without backwards compatibility, renaming `message` to `query`).
   - Breaking change to response structure (e.g., returning feedback as nested objects or altering error response schema format).
