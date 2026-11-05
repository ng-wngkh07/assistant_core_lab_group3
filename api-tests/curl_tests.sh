#!/usr/bin/env bash
# Integration curl tests for Study Assistant API (Lab 4)
# Usage: ./api-tests/curl_tests.sh [BASE_URL]

set -u

BASE_URL="${1:-${BASE_URL:-http://127.0.0.1:8000}}"
echo "Running API integration tests against ${BASE_URL}..."
echo "----------------------------------------------------"

echo "[1/5] Testing GET /health..."
curl -s -f -X GET "${BASE_URL}/health" | grep -q '"status":"ok"' && echo "PASS: /health returned ok" || echo "FAIL: /health"

echo "[2/5] Testing POST /v1/chat..."
CHAT_RESP=$(curl -s -X POST "${BASE_URL}/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "tuition for 18 credits and 2 retake"}')
echo "${CHAT_RESP}" | grep -q "9,450,000" && echo "PASS: /v1/chat fee calculated correctly" || echo "FAIL: /v1/chat response: ${CHAT_RESP}"

echo "[3/5] Testing GET /v1/offices..."
OFFICES_RESP=$(curl -s -X GET "${BASE_URL}/v1/offices")
echo "${OFFICES_RESP}" | grep -q "Library" && echo "PASS: /v1/offices contains Library" || echo "FAIL: /v1/offices response: ${OFFICES_RESP}"

echo "[4/5] Testing GET /docs..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs")
if [ "${HTTP_CODE}" = "200" ]; then
  echo "PASS: /docs returned HTTP 200"
else
  echo "FAIL: /docs returned HTTP ${HTTP_CODE}"
fi

echo "[5/5] Testing GET /v1/weather..."
WEATHER_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "${BASE_URL}/v1/weather")
if [ "${WEATHER_CODE}" = "200" ] || [ "${WEATHER_CODE}" = "503" ]; then
  echo "PASS: /v1/weather returned HTTP ${WEATHER_CODE}"
else
  echo "FAIL: /v1/weather returned HTTP ${WEATHER_CODE}"
fi

echo "----------------------------------------------------"
echo "All integration curl tests completed."
