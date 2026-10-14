-- Run after build_analysis.py and build_geography.py.
-- Map total must be 30655 and all status counts must sum to 31469.
SELECT map_status, COUNT(*) AS records
FROM restaurant_nta_assignment GROUP BY map_status;

-- Cuisine shares at NTA grain. No rent facts participate in this join.
WITH known AS (
 SELECT a.nta2020, COUNT(*) AS known_cuisine_records
 FROM restaurant_nta_assignment a JOIN restaurants r USING(camis)
 WHERE a.map_status='assigned' AND r.cuisine<>'Unknown'
 GROUP BY a.nta2020
)
SELECT c.nta2020, n.name, n.borough, c.cuisine, c.restaurant_count,
       k.known_cuisine_records,
       CASE WHEN c.cuisine='Unknown' THEN NULL
            ELSE 100.0*c.restaurant_count/NULLIF(k.known_cuisine_records,0) END
         AS share_of_local_known_cuisine_pct
FROM nta_cuisine c JOIN nta_summary n ON n.code=c.nta2020
LEFT JOIN known k ON k.nta2020=c.nta2020
ORDER BY c.restaurant_count DESC;
