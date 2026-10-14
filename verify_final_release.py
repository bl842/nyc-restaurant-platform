"""Check final release data controls and document traceability without a browser."""
from pathlib import Path
import csv,json,sqlite3,re,datetime
R=Path(__file__).resolve().parent
checks=[]
def check(name,v):
 checks.append({'check':name,'passed':bool(v)})
 if not v:raise AssertionError(name)
def rows(p):
 with (R/p).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
c=sqlite3.connect(R/'nyc_restaurants.sqlite')
check('CAMIS total',c.execute('select count(distinct camis) from restaurants').fetchone()[0]==31469)
check('Queens Chinese records',c.execute("select count(*) from restaurants where borough='Queens' and cuisine='Chinese'").fetchone()[0]==757)
check('Manhattan records',c.execute("select count(*) from restaurants where borough='Manhattan'").fetchone()[0]==12565)
check('All build controls pass',all(r['passed']=='True' for r in rows('outputs/validation_checks.csv')))
rs=rows('business_analysis/requirements_traceability.csv')
check('14 unique requirement IDs',len(rs)==len({r['requirement_id'] for r in rs})==14)
check('10 essential requirements traced',len([r for r in rs if r['priority']=='Essential'])==10 and all(r['acceptance_criterion'] and r['verification'] for r in rs))
check('UAT log has no invented observations',len(rows('business_analysis/user_acceptance_log.csv'))==0)
s=json.loads((R/'outputs/summary.json').read_text())
check('Delivery headline',abs(s['delivery_volume_yoy_pct']-18.2797599709519)<1e-8 and abs(s['delivery_after_fee_yoy_pct']-.76328153817955)<1e-8)
h=(R/'NYC_Restaurant_Explorer.html').read_text()
check('HTML has embedded data', '__DATA__' not in h and 'const D=' in h)
check('HTML does not load external scripts',not re.search(r'<script[^>]+src=',h))
check('Review and source dates distinct','Map release 13 October 2026' in h and 'Restaurant snapshot 6 October 2026' in h)
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'final_data_and_structure_checks':checks,'data_build_checks':len(rows('outputs/validation_checks.csv')),'core_csv_table_count':17,'browser_rerun':{'status':'blocked','reason':'Supported browser-control capability unavailable for this map release; prior run also hit socket restrictions','prior_result':'qa/ui_checks.json; retained from 7 October package, not a new pass'},'map_checks':json.loads((R/'qa/map_checks.json').read_text()),'user_acceptance':'Not executed; blank log supplied','document_review':'Eight pages rendered and visually reviewed before packaging'}
(R/'qa'/'final_verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'passed':sum(x['passed'] for x in checks),'executed':len(checks)}))
