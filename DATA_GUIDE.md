# Data guide and initial findings

Market captures prepared 7 October 2026; geography extension added 13 October 2026. Use the source catalog and download manifest for exact URLs and source versions. All monetary amounts are USD. Missing numerical values are blank in CSV and null in SQLite. Preserve identifiers such as CAMIS and ZIP as text.

## The evidence and its meaning

The current DOHMH extract has 296,270 inspection/violation rows but 31,469 unique CAMIS establishments. Of these, 31,374 have a recognized borough. Manhattan has 12,565, Brooklyn 7,998, Queens 7,046, the Bronx 2,642 and Staten Island 1,123. The source identifies supply recorded under active permits, including uninspected applicants and college cafeterias. It does not establish current trading, sales or demand. Of all establishments, 3,860 lack cuisine, 494 lack a five-digit ZIP, and 3,858 are marked as never inspected. [S1]

Across covered delivery apps, Q4 2025 weekly delivery volume was 18.3% above Q4 2024. Average subtotal rose from $29.71 to $30.66 per delivery; merchant platform fees rose from $5.63 to $6.40. The difference rose from $24.08 to $24.26, or 0.8%. Merchant fee growth accounts arithmetically for about 80.6% of the subtotal increase per delivery. This is before food, labor, packaging, rent and other costs. Some covered deliveries involve non-restaurant items, and the merchant/order mix can change. [S2]

H1 2026 median asking rents range from $200 in the Financial District to $2,500 on Upper Fifth Avenue among the reported corridors. Times Square is $1,328, 6.64 times the Financial District figure. These are annual asking rents per ground-floor square foot for retail space. They are not signed restaurant leases. The changing available-space sample prevents a same-property interpretation of the time series. [S3]

For September 2024–August 2025, restaurant and other eating-place taxable sales were $28.544 billion nominally and $22.182 billion in constant 2019 dollars. The latter was 3.6% below September 2018–August 2019. This is useful macro context; it cannot be divided into cuisine or restaurant-price-tier performance. [S4]

Storefront vacancy was 11.0% citywide on 15 April 2026. Borough figures were 12.9% in Manhattan, 12.3% in Brooklyn, 9.5% in Queens, 8.0% in the Bronx and 7.5% on Staten Island. These describe all storefronts, so the platform should label them as commercial context rather than restaurant closures. [S5]

The Times Square Alliance reported 240,257 average daily pedestrians in August 2026, with a rounded 2% increase over August 2025. This is a single-district context indicator and does not measure restaurant transactions. [S6]

These findings suggest that the first platform should help users compare evidence, with cost and coverage visible beside supply. A defensible opportunity ranking needs a compatible demand measure and user preferences. Low competition alone is insufficient.

## Data model and joins

| Table or view | Grain | Key and intended use |
| --- | --- | --- |
| restaurants | One CAMIS in the current source snapshot | Unique `camis`; filter by `borough`, `cuisine`, `zipcode` |
| borough_supply | One borough | `borough`; totals include unknown cuisine |
| cuisine_borough | Borough × known cuisine | `borough`, `cuisine`; denominators exclude unknown cuisine |
| zip_cuisine | Borough × ZIP × cuisine | Three-key aggregate; missing ZIP and borough excluded |
| citywide_cuisine CSV | One known cuisine | Counts across all source records, excluding missing cuisine |
| delivery_quarterly / delivery_analysis | One citywide quarter | `year`, `quarter`; do not join to restaurant rows |
| rent_corridor / rent_comparison | Corridor × half year | `corridor`, `year`, `half`; no assumed ZIP mapping |
| citywide_sales / sales_analysis | September–August year | `year_end`; `period_start`, `period_end` make the coverage explicit |
| storefront_vacancy | Borough snapshot | `borough`, `as_of`; label as a separate commercial context measure |
| pedestrian_context | Times Square monthly indicator | `area`, `month`; not a general NYC demand table |

Keep the source fact tables separate. Joining a citywide quarterly amount to every restaurant and summing would multiply it by the number of restaurants. Joining a REBNY corridor to a ZIP by similar names would create unverified geography. Borough vacancy may be displayed beside a borough supply total, but the different dates and populations must remain visible.

## Cleaning and calculation rules

The DOHMH query groups by CAMIS and the current profile fields, keeping the maximum inspection date and record date. This removes repeated violation rows at the source. The build checks the distinct count against a separate source count query and aborts on duplicate CAMIS profiles. It trims text, preserves the publisher's cuisine categories, replaces missing cuisine or unrecognized borough with `Unknown`, and keeps only five-digit formatted ZIPs. This is a formatting check, not geographic validation. The 1900 inspection placeholder becomes a missing date plus `never_inspected=1`. Coordinates are retained with a broad NYC plausibility flag; the flag is not a point-in-boundary check and coordinates are used for NTA assignment after additional boundary and borough checks; they are not used for success recommendations.

DCWP sheet labels are trimmed and quarter columns are reshaped to one row per quarter. Weekly totals remain weekly averages. Per-delivery values are the agency's reported values, so they need not exactly equal the ratio of two published aggregate averages. The derived after-fee amount is `average_subtotal_usd - merchant_fee_per_delivery_usd`. Year-over-year calculations compare matching quarters using SQL `LAG(...,4)` and guard the denominator.

REBNY medians are parsed from PDF page 24 into long format. The published percentage-change columns are not used. The build recomputes comparisons from the underlying medians and preserves N/A for Harlem and Bleecker Street in H1 2026. The Times Square boundary text and some narrative change statements appear inconsistent in the source, so no exact polygon or narrative-derived change is assigned.

Comptroller sales are extracted from HTML Table 7 and stored in USD millions. The report's constant-dollar series is used directly; the pipeline does not apply another inflation adjustment. Storefront borough percentages are small narrative captures validated against the source passage. Times Square's pedestrian value is extracted from PDF page 2; the reported rounded YoY value is retained separately.

## Field dictionary

`camis` is the establishment identifier; `restaurant_name` is the source DBA. `borough`, `cuisine` and `zipcode` are categorical filters. `latest_inspection_date` is the latest recorded inspection for that establishment, not an opening date. `record_date` is the source snapshot day. `never_inspected` and `coordinate_plausible` are integer flags. `source_id` points to the source catalog.

Counts ending in `_records` or `_count` count establishments, unless a source measure explicitly says deliveries. `share_of_located_records_pct` uses only the five recognized boroughs. `share_of_known_cuisine_records_pct` divides the selected cuisine count by known-cuisine records in that borough. `share_of_cuisine_citywide_pct` divides the borough's cuisine count by that cuisine's count across the five boroughs. All `_pct` fields use 0–100 percentage units; `merchant_fee_share` alone is stored as a 0–1 proportion.

Delivery `weekly_*` fields are average weekly totals within the quarter. `average_*_usd`, `merchant_fee_per_delivery_usd` and `subtotal_less_merchant_fee_usd` are USD per delivery. `prior_year_*` fields are the corresponding values four quarters earlier. All delivery YoY fields are percentage changes from that matching quarter.

`median_asking_rent_usd_sqft_year` and `prior_year_rent` are USD per ground-floor square foot per year. `half` is 1 or 2. Rent `yoy_pct` compares the same half of the previous year and stays missing if either observation is unavailable. The dashboard's monthly illustration is annual asking rate multiplied by entered area and divided by 12.

`nominal_sales_million_usd` is current-dollar taxable sales; `real_sales_2019_million_usd` is the publisher's constant-2019-dollar series. `real_sales_index_2019` sets the year ending August 2019 to 100. `vacancy_pct` is vacant storefronts as a percentage of all storefronts. `average_daily_pedestrians` is the district's published daily average in a month; `reported_yoy_pct_rounded` is a rounded source value, not reconstructed prior-year traffic.

## Source links

[S1] [NYC DOHMH: Restaurant Inspection Results](https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j/about_data). Record date 2026-10-06.

[S2] [NYC DCWP: Restaurant Delivery App Data](https://www.nyc.gov/assets/dca/downloads/xlsx/Restaurant-Delivery-App-Data-Quarterly.xlsx). Q1 2022–Q4 2025.

[S3] [REBNY: Manhattan Retail Report H1 2026](https://www.rebny.com/reports/manhattan-retail-report-first-half-2026/). H1 2023–H1 2026.

[S4] [NYC Comptroller: Annual State of the City Economy and Finances 2025](https://comptroller.nyc.gov/reports/annual-state-of-the-citys-economy-and-finances-2025/). Years ending August 2019–2025.

[S5] [NYC Comptroller / Live XYZ: Who Is Minding the Storefronts](https://comptroller.nyc.gov/reports/whos-minding-the-storefronts/). Status at 2026-04-15; report 2026-06-04.

[S6] [Times Square Alliance: August 2026 Monthly Economic Indicator Report](https://www.timessquarenyc.org/business-community/market-research-data). August 2026.


## Geographic extension

Source S7 is the official NYC DCP 2020 NTA boundary dataset, retrieved 13 October 2026 in New York time (14 October UTC). Its 262 areas support a new cuisine choropleth. Full-precision spatial matching assigns 30,655 records and excludes 814 with recorded reasons. The map denominator differs from borough totals because records without usable geographic assignments remain in the original supply table.

MAP_GUIDE.md gives the new field dictionary, thresholds and file grains. Rent points are illustrative anchors only. No rent is allocated to an NTA, borough or restaurant. The core dataset now contains 17 analytical CSV tables.

[S7] [NYC DCP 2020 Neighborhood Tabulation Areas](https://data.cityofnewyork.us/City-Government/2020-Neighborhood-Tabulation-Areas-NTAs-/9nt8-h7nd). Original geometry and retrieval hash are in data/raw.
