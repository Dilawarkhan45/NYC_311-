-- ============================================================================
-- Name: Dilawar khan
-- Roll Number: TRN-2026-000961
-- Date: 17 Nov 2026
--
-- SQLite Relational Queries for NYC 311 Service Requests (Part A)
-- Evaluates per-capita service demand and resolution duration across boroughs
-- by joining cleaned tickets with Census demographic lookup tables.
-- ============================================================================

-- Query 1: Normalized Borough Civic Demand and Resolution Performance
-- Relational JOIN between tickets and borough_lookup
SELECT 
    b.borough AS borough_name,
    b.population AS census_population,
    b.land_area_sq_mi,
    COUNT(t.unique_key) AS total_service_requests,
    ROUND((COUNT(t.unique_key) * 10000.0) / b.population, 2) AS requests_per_10k_residents,
    ROUND(AVG(t.resolution_hours), 2) AS avg_resolution_hours,
    ROUND(
        SUM(CASE WHEN t.is_zero_duration = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(t.unique_key),
        2
    ) AS pct_zero_duration_tickets
FROM borough_lookup b
INNER JOIN tickets t ON b.borough = t.borough
GROUP BY 
    b.borough, 
    b.population, 
    b.land_area_sq_mi
ORDER BY 
    requests_per_10k_residents DESC;

-- Query 2: Workload Breakdown by Responding Municipal Agency
SELECT 
    t.agency,
    COUNT(t.unique_key) AS total_tickets,
    ROUND(AVG(t.resolution_hours), 2) AS avg_resolution_hours,
    COUNT(DISTINCT t.complaint_type) AS distinct_complaint_types
FROM tickets t
GROUP BY 
    t.agency
HAVING 
    COUNT(t.unique_key) >= 100
ORDER BY 
    total_tickets DESC;
