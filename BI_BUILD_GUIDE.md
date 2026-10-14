# Build the next version in Tableau or Power BI

Choose one BI tool for the next iteration. Use the already validated CSV tables to focus on visual design and user decisions. The local HTML prototype demonstrates the intended interactions; native Tableau and Power BI workbooks have not been produced or tested in this package.

## Minimum dashboard

| View | Prepared input | Visual and field mapping | Interaction |
| --- | --- | --- | --- |
| Restaurant supply | `data/clean/restaurants.csv` | Horizontal bars: borough; distinct count of CAMIS | Borough and cuisine filters; optional ZIP |
| Cuisine mix | Same restaurant table | Horizontal bars: cuisine; distinct count of CAMIS | Use the selected borough; show Unknown separately |
| Delivery | `outputs/delivery_analysis.csv` | Quarter on the horizontal axis; subtotal and merchant fee amounts in USD per delivery | Select a quarter or compare the same quarter a year earlier |
| Rent | `outputs/rent_comparison.csv` | Corridor on the vertical axis; median annual asking rent on the horizontal axis | Filter to H1 2026; preserve two unavailable medians |

Restaurant, delivery and rent sources should remain separate. The current geography and time grains do not justify a single fact-table join. Borough/cuisine filters apply only to the supply module. Label delivery as citywide and rents as selected Manhattan corridors.

## Tableau path

Use the Text File connector for each CSV. Confirm that CAMIS and ZIP are strings and numerical measures are numeric. Use separate data sources for the modules above. In the supply source, create a `COUNTD([camis])` measure and put borough or cuisine on Rows. Exclude the Unknown borough from a five-borough chart, while retaining its count in a coverage note. Use a cuisine filter to explore a chosen concept.

For the first version, use counts instead of introducing a calculated cuisine-share measure with an ambiguous filter denominator. The prepared `outputs/cuisine_borough.csv` already contains `share_of_known_cuisine_records_pct`. If you use that table for a separate share view, display one row per borough and cuisine and treat the percentage as a value at that grain, not as a sum across cuisines or boroughs.

For delivery, sort the period labels by year and quarter. Display the published per-delivery measures; do not sum averages across quarters. The prepared YoY fields already compare matching quarters. For rent, filter `year=2026` and `half=1`, then place corridor against its one median. A missing value should remain missing.

Official reference: [Tableau Text File connector](https://help.tableau.com/current/pro/desktop/en-us/examples_text.htm).

## Power BI path

Use Get Data and the Text/CSV connector, then Transform Data to review types. Import restaurant identifiers and ZIP as Text. Use Whole Number for counts and Decimal Number for prices and percentages. Load each source as a separate table; review and remove automatic relationships that would join unrelated grains.

For a restaurant count measure, the following DAX is sufficient after naming the imported table `restaurants`:

```dax
Restaurant records = DISTINCTCOUNT(restaurants[camis])
```

Use borough and cuisine slicers for supply visuals, and a bar chart with cuisine on the category axis. Keep the delivery and rent pages independent of these slicers. For rent, filter to the single period before plotting the numerical median. For delivery averages, use a single-period card or a line chart with one row per quarter, and verify that the visual does not sum multiple quarters into a meaningless per-delivery number.

Fields ending in `_pct` are already in 0–100 units. Format them as ordinary decimal numbers with a percent suffix or divide by 100 in a new measure before applying percentage formatting. `merchant_fee_share` is already a 0–1 proportion and can use percentage formatting directly. Missing prior-year values in the first four delivery quarters should remain blank.

Official reference: [Microsoft Power Query Text/CSV connector](https://learn.microsoft.com/en-us/power-query/connectors/text-csv).

## Acceptance checks

With no cuisine filter and only the five recognized boroughs, the restaurant count is 31,374. Including Unknown borough gives 31,469. Manhattan is 12,565. Chinese cuisine across the five boroughs is 2,274; selecting Queens gives 757. These are establishment records, not inspection rows.

For Q4 2025 versus Q4 2024, delivery volume YoY is 18.2798% and subtotal less merchant fees per delivery YoY is 0.7633%. An identical-quarter comparison should show zero change. For H1 2026, Financial District rent is $200/sq ft/year, Times Square is $1,328 and Upper Fifth Avenue is $2,500. Harlem and West Village Bleecker have unavailable current medians.

Every visual should show a source name, observation period, unit and relevant coverage limit. Review each of the three user starting points with a colleague and record whether the comparison helped them identify a concrete next research question.

## Suggested five-day plan

| Day | Work | Completion condition |
| --- | --- | --- |
| 1 | Confirm scope and choose the BI tool | Agreed user scenarios and indicator definitions |
| 2 | Build supply and cuisine views | Counts match the SQL controls and missing categories remain visible |
| 3 | Add delivery or rent comparison | Correct periods, units and non-additive measures |
| 4 | Test the three entry paths | Filters, empty results and source notes work consistently |
| 5 | Review feedback and document progress | Updated dashboard, short written progress update and one next data priority |

After that review, add one demand-side source at a compatible geographic scale. Test geographic matching before promising a score or recommendation engine.

## Neighborhood map extension

Use data/clean/nta2020_display.geojson as the spatial reference and outputs/nta_summary.csv as the area dimension. The stable key is nta2020 in GeoJSON and code in the summary. A compatible BI spatial connector or conversion may be required by the chosen desktop version. Keep the geometry separate from rent observations.

For cuisine, relate outputs/nta_cuisine.csv to the area dimension by nta2020. It is one row per observed NTA/cuisine pair, so absent pairs must be shown as zero when the NTA has mapped records. Preserve the full 262-area dimension. Count is restaurant_count. Share is the selected cuisine count divided by the summary's known field, multiplied by 100; do not let the cuisine filter change the denominator. Disable share for All cuisines and Unknown, and leave zero denominators blank. Use the fixed bins defined in MAP_GUIDE.md.

For rent, use data/clean/rent_map_anchors.csv as an independent point layer. Latitude and longitude are approximate corridor orientation anchors; use rent for color and retain nulls. Do not join point values into NTA-wide filled rent polygons. Restrict the layer to Manhattan and show other boroughs as uncovered.

Controls: 262 NTAs; 30,655 mapped records; Flushing-Willets Point Chinese count 266, known base 509 and share 52.3%; 16 rent markers, 14 values and two missing. These are implementation specifications; no native BI workbook has been created.
