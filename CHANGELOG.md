# Map release changes

The map extension adds S7 official 2020 NTA geometry, full-resolution restaurant spatial assignment, a cuisine choropleth, and rent corridor hotspots. The default screen is now Neighborhood maps. Three entry paths open corresponding map filters, while original analytical modules remain available.

The release contains seven sources, 17 core CSV tables, eight chart pairs, 14 requirements and 10 essential requirements. Report text, user workflow, source catalog, field dictionary, BI build guide, acceptance evidence and Chinese instructions have been synchronized. New map tests are calculation and DOM checks; actual browser layout remains unverified.

Rent points are approximate orientation anchors for existing Manhattan corridor values. No area-wide rent estimate or other-borough rent has been inferred. Market observations retain their original dates.

## Prior final handoff


The 13 October 2026 release adds a seven-page business analysis report, a branching user workflow, 12 prioritized and traceable requirements, user stories, KPI definitions, a risk and decision register, and a user acceptance procedure with a blank recording sheet. It preserves the six reviewed data sources and the original analytical scope.

The prototype release label now separates the review date from the frozen data date. Supply counts, rents, delivery metrics and their source coverage are unchanged. The Python/SQL pipeline was rerun, and final technical evidence is recorded in qa/final_verification.json. No user-test outcome or stakeholder approval was inferred from technical tests.

The initial brief and Chinese meeting notes are retained in archive for reference. README now points to the final report and distinguishes delivered analysis and prototype work from native BI, hosting and future ranking work. The original material-generation script remains available for provenance but is excluded from final rebuild instructions because it would regenerate the preliminary README.
