-- SQLite 3.25+; input tables are loaded by build_analysis.py.
-- Each source keeps its own grain. No corridor/ZIP or annual/quarterly join is assumed.

DROP VIEW IF EXISTS borough_supply;
CREATE VIEW borough_supply AS
SELECT borough,
       COUNT(*) AS active_permit_records,
       SUM(cuisine <> 'Unknown') AS known_cuisine_records,
       SUM(cuisine = 'Unknown') AS missing_cuisine_records,
       SUM(never_inspected) AS never_inspected_records,
       100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS share_of_located_records_pct
FROM restaurants
WHERE borough <> 'Unknown'
GROUP BY borough;

DROP VIEW IF EXISTS cuisine_borough;
CREATE VIEW cuisine_borough AS
SELECT r.borough, r.cuisine, COUNT(*) AS restaurant_count,
       b.known_cuisine_records AS borough_known_cuisine_total,
       100.0 * COUNT(*) / b.known_cuisine_records AS share_of_known_cuisine_records_pct,
       100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY r.cuisine) AS share_of_cuisine_citywide_pct
FROM restaurants r
JOIN borough_supply b ON r.borough = b.borough
WHERE r.cuisine <> 'Unknown'
GROUP BY r.borough, r.cuisine;

DROP VIEW IF EXISTS zip_cuisine;
CREATE VIEW zip_cuisine AS
SELECT borough, zipcode, cuisine, COUNT(*) AS restaurant_count,
       SUM(never_inspected) AS never_inspected_records
FROM restaurants
WHERE borough <> 'Unknown' AND zipcode IS NOT NULL
GROUP BY borough, zipcode, cuisine;

DROP VIEW IF EXISTS delivery_analysis;
CREATE VIEW delivery_analysis AS
WITH metrics AS (
  SELECT *, average_subtotal_usd - merchant_fee_per_delivery_usd AS subtotal_less_merchant_fee_usd
  FROM delivery_quarterly
), prior AS (
  SELECT *,
    LAG(weekly_deliveries, 4) OVER (ORDER BY year, quarter) AS prior_year_weekly_deliveries,
    LAG(average_subtotal_usd, 4) OVER (ORDER BY year, quarter) AS prior_year_subtotal_usd,
    LAG(merchant_fee_per_delivery_usd, 4) OVER (ORDER BY year, quarter) AS prior_year_fee_usd,
    LAG(subtotal_less_merchant_fee_usd, 4) OVER (ORDER BY year, quarter) AS prior_year_after_fee_usd
  FROM metrics
)
SELECT *,
  100.0 * (weekly_deliveries / NULLIF(prior_year_weekly_deliveries,0) - 1) AS deliveries_yoy_pct,
  100.0 * (average_subtotal_usd / NULLIF(prior_year_subtotal_usd,0) - 1) AS subtotal_yoy_pct,
  100.0 * (merchant_fee_per_delivery_usd / NULLIF(prior_year_fee_usd,0) - 1) AS merchant_fee_yoy_pct,
  100.0 * (subtotal_less_merchant_fee_usd / NULLIF(prior_year_after_fee_usd,0) - 1) AS after_fee_yoy_pct
FROM prior;

DROP VIEW IF EXISTS rent_comparison;
CREATE VIEW rent_comparison AS
SELECT a.corridor, a.year, a.half, a.period,
       a.median_asking_rent_usd_sqft_year,
       b.median_asking_rent_usd_sqft_year AS prior_year_rent,
       100.0 * (a.median_asking_rent_usd_sqft_year / NULLIF(b.median_asking_rent_usd_sqft_year,0)-1) AS yoy_pct
FROM rent_corridor a
LEFT JOIN rent_corridor b ON a.corridor=b.corridor AND a.year=b.year+1 AND a.half=b.half;

DROP VIEW IF EXISTS sales_analysis;
CREATE VIEW sales_analysis AS
SELECT *,
  100.0 * (nominal_sales_million_usd / LAG(nominal_sales_million_usd) OVER (ORDER BY year_end)-1) AS nominal_yoy_pct,
  100.0 * (real_sales_2019_million_usd / LAG(real_sales_2019_million_usd) OVER (ORDER BY year_end)-1) AS real_yoy_pct,
  100.0 * real_sales_2019_million_usd / FIRST_VALUE(real_sales_2019_million_usd) OVER (ORDER BY year_end) AS real_sales_index_2019
FROM citywide_sales;

-- Examples for BI / a later backend. Bind user inputs; do not concatenate SQL.
-- SELECT * FROM cuisine_borough WHERE cuisine = :cuisine ORDER BY restaurant_count DESC;
-- SELECT cuisine, restaurant_count FROM cuisine_borough WHERE borough = :borough ORDER BY restaurant_count DESC;
-- SELECT * FROM zip_cuisine WHERE borough=:borough AND cuisine=:cuisine ORDER BY restaurant_count DESC;
-- SELECT * FROM rent_comparison WHERE year=2026 AND half=1 ORDER BY median_asking_rent_usd_sqft_year;
