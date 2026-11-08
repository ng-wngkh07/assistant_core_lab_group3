-- sql/my_queries.sql: Analytical queries on assistant.db

-- F1: How many questions per intent?
-- Group interactions by intent and sort by descending request count.
SELECT intent, COUNT(*) AS requests
FROM interaction
GROUP BY intent
ORDER BY requests DESC;

-- Sample output for F1:
-- intent    requests
-- --------  --------
-- rule      140
-- fee       61
-- office    47
-- greeting  26
-- unknown   26


-- F2: Average time taken per intent?
-- Compute average latency in milliseconds for each intent, rounded to 1 decimal place.
SELECT intent, ROUND(AVG(latency_ms), 1) AS avg_latency_ms
FROM interaction
GROUP BY intent
ORDER BY avg_latency_ms DESC;

-- Sample output for F2:
-- intent    avg_latency_ms
-- --------  --------------
-- unknown   45.3
-- rule      34.5
-- fee       21.7
-- office    18.8
-- greeting  12.3


-- F3: Which topics got the most thumbs-down?
-- Join interaction with feedback where rating = -1, grouped by topic, sorted by thumbs-down count.
SELECT i.topic, COUNT(*) AS thumbs_down
FROM interaction i
JOIN feedback f ON f.request_id = i.request_id
WHERE f.rating = -1 AND i.topic IS NOT NULL
GROUP BY i.topic
ORDER BY thumbs_down DESC;

-- Sample output for F3:
-- topic          thumbs_down
-- -------------  -----------
-- health_center  4
-- retake-rules   3
-- goodbye        3
-- H26-2.1        3
-- library        2
-- graduation-req 2
-- H26-5.3        2


-- H2: What share of answers used a backup path (degraded responses)?
-- Compute total interactions, count of degraded interactions, and percentage.
SELECT 
    COUNT(*) AS total_interactions,
    SUM(CASE WHEN degraded THEN 1 ELSE 0 END) AS degraded_count,
    ROUND(100.0 * SUM(CASE WHEN degraded THEN 1 ELSE 0 END) / COUNT(*), 2) AS degraded_percentage
FROM interaction;

-- Sample output for H2:
-- total_interactions  degraded_count  degraded_percentage
-- ------------------  --------------  -------------------
-- 300                 6               2.0
