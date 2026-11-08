#!/usr/bin/env bash
# Integration curl tests for Study Assistant API (Lab 5 Persistence & Database)
# Usage: ./api-tests/curl_tests.sh [BASE_URL]

set -u

BASE_URL="${1:-${BASE_URL:-http://127.0.0.1:8000}}"
API_ADMIN_KEY="${API_ADMIN_KEY:-change-me}"

echo "Running API integration tests against ${BASE_URL}..."
echo "----------------------------------------------------"

echo "[1/10] Testing GET /health..."
curl -s -f -X GET "${BASE_URL}/health" | grep -q '"status":"ok"' && echo "PASS: /health returned ok" || echo "FAIL: /health"

echo "[2/10] Testing POST /v1/chat and extracting request_id..."
CHAT_RESP=$(curl -s -X POST "${BASE_URL}/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "tuition for 18 credits and 2 retake", "session_id": "test-user-session"}')
echo "${CHAT_RESP}" | grep -q "9,450,000" && echo "PASS: /v1/chat fee calculated correctly" || echo "FAIL: /v1/chat response: ${CHAT_RESP}"

# Extract request_id from JSON response
REQ_ID=$(echo "${CHAT_RESP}" | grep -o '"request_id":"[^"]*' | cut -d'"' -f4)
if [ -n "${REQ_ID}" ]; then
  echo "PASS: Received request_id: ${REQ_ID}"
else
  echo "FAIL: Could not extract request_id"
  REQ_ID="fallback-id"
fi

echo "[3/10] Testing GET /v1/offices..."
OFFICES_RESP=$(curl -s -X GET "${BASE_URL}/v1/offices")
echo "${OFFICES_RESP}" | grep -q "Library" && echo "PASS: /v1/offices contains Library" || echo "FAIL: /v1/offices response: ${OFFICES_RESP}"

echo "[4/10] Testing GET /docs..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs")
if [ "${HTTP_CODE}" = "200" ]; then
  echo "PASS: /docs returned HTTP 200"
else
  echo "FAIL: /docs returned HTTP ${HTTP_CODE}"
fi

echo "[5/10] Testing GET /v1/weather..."
WEATHER_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "${BASE_URL}/v1/weather")
if [ "${WEATHER_CODE}" = "200" ] || [ "${WEATHER_CODE}" = "503" ]; then
  echo "PASS: /v1/weather returned HTTP ${WEATHER_CODE}"
else
  echo "FAIL: /v1/weather returned HTTP ${WEATHER_CODE}"
fi

echo "[6/10] Testing POST /v1/feedback with valid request_id -> 201..."
FB_RESP=$(curl -s -X POST "${BASE_URL}/v1/feedback" \
  -H "Content-Type: application/json" \
  -d "{\"request_id\": \"${REQ_ID}\", \"rating\": 1, \"comment\": \"Great answer!\"}")
echo "${FB_RESP}" | grep -q '"id":' && echo "PASS: /v1/feedback submitted successfully" || echo "FAIL: /v1/feedback response: ${FB_RESP}"

echo "[7/10] Testing POST /v1/feedback with non-existent request_id 'nope' -> 404..."
FB_NOPE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "nope", "rating": 1, "comment": "test"}')
if [ "${FB_NOPE_CODE}" = "404" ]; then
  echo "PASS: /v1/feedback with 'nope' returned HTTP 404"
else
  echo "FAIL: /v1/feedback with 'nope' returned HTTP ${FB_NOPE_CODE}"
fi

echo "[8/10] Testing POST /v1/feedback with invalid rating 7 -> 422..."
FB_INVALID_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/v1/feedback" \
  -H "Content-Type: application/json" \
  -d "{\"request_id\": \"${REQ_ID}\", \"rating\": 7}")
if [ "${FB_INVALID_CODE}" = "422" ]; then
  echo "PASS: /v1/feedback invalid rating returned HTTP 422"
else
  echo "FAIL: /v1/feedback invalid rating returned HTTP ${FB_INVALID_CODE}"
fi

echo "[9/10] Testing GET /v1/feedback without API key (expect 401)..."
FB_UNAUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/v1/feedback")
if [ "${FB_UNAUTH_CODE}" = "401" ]; then
  echo "PASS: /v1/feedback without key returned HTTP 401"
else
  echo "FAIL: /v1/feedback without key returned HTTP ${FB_UNAUTH_CODE}"
fi

echo "[10/10] Testing GET /v1/feedback with valid admin key (expect 200)..."
FB_LIST_RESP=$(curl -s -X GET "${BASE_URL}/v1/feedback" -H "X-API-Key: ${API_ADMIN_KEY}")
echo "${FB_LIST_RESP}" | grep -q "\"request_id\":\"${REQ_ID}\"" && echo "PASS: /v1/feedback retrieved persisted feedback list" || echo "FAIL: /v1/feedback response: ${FB_LIST_RESP}"

echo "----------------------------------------------------"
echo "All integration curl tests completed."
