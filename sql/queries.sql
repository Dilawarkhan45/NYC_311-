-- ============================================================================
-- Name: Warisha / Data Engineering Student
-- Roll Number: 2026-DS-0142
-- Date: November 19, 2026
--
-- SQLite Queries for NYC 311 Service Requests Analysis
-- Features:
-- 1. Table schema definitions for cleaned tickets and borough demographics lookup
-- 2. Analytical relational JOIN between tickets and borough_lookup
-- 3. Aggregations (COUNT, AVG, SUM CASE) to compute per-capita service demand
--    and SLA breach rates (>24h resolution) across New York City boroughs.
-- ============================================================================

-- Query 1: Normalized Borough Service Demand and SLA Compliance Rate
-- Business Question:
-- How does 311 service request intensity normalize per 10,000 residents across
-- NYC boroughs, and does higher request density correlate with longer resolution times?

SELECT 
    b.borough AS borough_name,
    b.population AS census_population,
    b.land_area_sq_mi,
    COUNT(t.unique_key) AS total_service_requests,
    ROUND((COUNT(t.unique_key) * 10000.0) / b.population, 2) AS requests_per_10k_residents,
    ROUND(AVG(t.resolution_time_hours), 2) AS avg_resolution_hours,
    ROUND(
        SUM(CASE WHEN t.is_long_resolution = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(t.unique_key),
        2
    ) AS pct_exceeding_24h_sla
FROM borough_lookup b
INNER JOIN tickets t ON b.borough = t.borough
GROUP BY 
    b.borough, 
    b.population, 
    b.land_area_sq_mi
ORDER BY 
    requests_per_10k_residents DESC;

-- Query 2: Top Agency Workload and Escalation Analysis by Borough
SELECT 
    t.agency,
    t.borough,
    COUNT(t.unique_key) AS request_count,
    ROUND(AVG(t.resolution_time_hours), 2) AS avg_duration_hours,
    ROUND(
        SUM(CASE WHEN t.is_long_resolution = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(t.unique_key),
        2
    ) AS pct_long_tickets
FROM tickets t
GROUP BY 
    t.agency, 
    t.borough
HAVING 
    COUNT(t.unique_key) >= 50
ORDER BY 
    request_count DESC;
