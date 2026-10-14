# Neighborhood map definitions and reproducibility

The map release adds an official geographic source S7 to the six market sources. It contains 262 NYC 2020 Neighborhood Tabulation Areas, including 197 residential areas and 65 special areas. NTAs are statistical approximations of neighborhoods; they are not restaurant catchments, ZIP codes or borough-wide markets. The full source GeoJSON and its retrieval hash are retained in data/raw. The restaurant and rent observations remain the prior frozen market snapshots.

## Cuisine heat

The map offers restaurant record count and local known-cuisine share. For a selected cuisine, the numerator is the number of spatially matched distinct CAMIS records of that cuisine in an NTA. The share denominator is all mapped records in that NTA whose cuisine is known. Missing cuisine is excluded from that denominator. All-cuisine and Unknown selections only offer counts. A zero denominator produces an unavailable value. A share based on fewer than 20 known-cuisine records displays a small-base note. The threshold is a display rule, not a statistical significance test.

Counts use fixed bins of 0, 1–4, 5–19, 20–49, 50–99, 100–249 and 250 or more. Shares use fixed breaks at 1%, 5%, 10% and 20%. The same scales apply when a borough is selected. All available area rows, including zero counts, are exported. Areas with no mapped records are not evidence that no operating restaurants exist. Heat is a supply measure; demand, sales and online popularity are unobserved.

Full-resolution point-in-polygon matching assigns 30,655 of 31,469 restaurant records (97.4%). The mutually exclusive exclusions are 95 records with unknown borough, 707 other records with invalid or missing coordinates, 11 outside every NTA and one whose coordinate borough disagrees with its reported borough. Unknown borough is checked first, so 707 differs from the original 802 coordinate-quality flags. Any multiple-boundary match would be quarantined; none occurred. No nearest-neighborhood reassignment is used.

The display geometry is simplified by 0.000035 degrees with topology preservation. This simplification is applied only after assignment. The SVG uses an equirectangular local display projection with longitude scaled by cos(40.7 degrees). It is an orientation map, not a surveying tool. Borough controls fit the view to the selected borough. The selector and ranked table provide text alternatives to polygons.

## Rent heat

Rent hotspots are 16 illustrative Manhattan corridor anchors placed near named streets. They are manually chosen approximate orientation points, not geocoded listings, surveyed endpoints, inferred district centroids or the full geographic reach of a corridor. Anchor coordinates and location descriptions are retained in data/clean/rent_map_anchors.csv and build_geography.py. The entire Financial District, Times Square or any NTA must not be assigned a point's rent value.

Each marker uses the original H1 2026 corridor median from REBNY page 24. Fourteen current values are available; Harlem and West Village Bleecker remain unavailable. Values are USD per ground-floor square foot per year for retail asking rents. Fixed color breaks are $300, $500, $800 and $1,500. Marker size is an interaction aid and does not encode rent, availability or geographic coverage. Grey neighborhoods have no neighborhood-wide estimate. Other boroughs show an empty rent table and disable export because the source has no observations there. Source endpoint text for Times Square is inconsistent, so its center is shown only as an illustrative anchor.

## Tables and files

| File or table | Grain and key | Main fields |
| --- | --- | --- |
| restaurant_nta_assignment.csv | One source CAMIS; unique camis | nta2020, map_status |
| nta_summary.csv | One NTA; unique code | name, borough, type, cdta, total, known |
| nta_cuisine.csv | NTA × source cuisine | nta2020, cuisine, restaurant_count; zero pairs omitted in storage and restored in the UI |
| rent_map_anchors.csv | One corridor anchor; unique id | rent, period, longitude, latitude, source_page, location_method |
| nta2020_display.geojson | One NTA polygon | Simplified geometry and official properties |
| map_data.json | Browser payload | paths, counts, rent anchors and coverage summary |
| geography_queries.sql | SQL examples | Reconcile mapped totals and derive NTA cuisine shares without mixing rent grains |

These four new CSV tables extend the original 13 core analytical CSVs to 17. The SQLite database includes the four corresponding tables. Source GeoJSON and browser JSON are additional geometry/artifact files, not counted as CSV tables.

## Rebuild and verification

Run build_analysis.py first, then build_geography.py, make_charts.py, make_map_charts.py, build_dashboard.py and build_final_handoff.py. Running build_analysis.py recreates the database, so always run build_geography.py afterward to restore the map tables. The new Python dependency is shapely 2.1.2. All steps use bundled inputs and work offline once dependencies are installed.

The original browser pass in qa/ui_checks.json is historical and does not validate the modified HTML. qa/map_checks.json records the new Node calculations and JSDOM behavior checks, including missing denominators, selected areas, entry paths, exports and unchanged non-map metrics. These tests do not verify real browser layout, mobile rendering or SVG pointer panning. An updated Playwright test script is supplied for later browser execution. No new browser pass is claimed.
