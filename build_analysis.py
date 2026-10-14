"""Clean six public sources, execute SQL, and export analysis-ready CSVs.

Use the frozen raw folder for reproducibility. Refresh deliberately with fetch_sources.py.
No API key, server, or paid data is required for this first version.
"""
from pathlib import Path
import datetime, hashlib, html, io, json, re, sqlite3
import pandas as pd
import numpy as np
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'data'/'raw'
CLEAN=ROOT/'data'/'clean'
OUT=ROOT/'outputs'
for p in [CLEAN,OUT]: p.mkdir(parents=True,exist_ok=True)
DB=ROOT/'nyc_restaurants.sqlite'
checks=[]

def check(name,passed,details):
    checks.append({'check':name,'passed':bool(passed),'details':details})
    if not passed: raise ValueError(f'{name}: {details}')

def write(df,name):
    df.to_csv(CLEAN/f'{name}.csv',index=False)
    return df

def records(df):
    return json.loads(df.to_json(orient='records'))

def numerical_capture(name):
    """Use the checked numerical capture when a full linked report is absent.

    Report prose and complete third-party PDFs are not redistributed in the package.
    Run fetch_sources.py to repeat the extraction from the publishers' documents.
    """
    path=ROOT/'data'/'source_extracts'/f'{name}.csv'
    manifest=json.loads((path.parent/'capture_manifest.json').read_text())
    expected=manifest['captures'][path.name]['sha256']
    check(f'capture integrity {name}',hashlib.sha256(path.read_bytes()).hexdigest()==expected,'Numerical capture SHA256 matches the reviewed snapshot')
    return write(pd.read_csv(path,float_precision='round_trip'),name)

def clean_restaurants():
    d=pd.read_csv(RAW/'dohmh_restaurants.csv',dtype=str)
    source_counts=json.loads((RAW/'dohmh_counts.json').read_text())[0]
    check('DOHMH query completeness',len(d)<50000 and d.camis.nunique()==int(source_counts['distinct_camis']),
          f'{len(d)} downloaded profiles; {source_counts["distinct_camis"]} source CAMIS IDs')
    check('one row per CAMIS after source aggregation',d.camis.notna().all() and not d.camis.duplicated().any(),
          'Source GROUP BY removes repeated violation rows; a conflict aborts this build')
    for col in d.columns: d[col]=d[col].str.strip().replace('',pd.NA)
    d=d.rename(columns={'dba':'restaurant_name','boro':'borough','cuisine_description':'cuisine'})
    d['cuisine']=d.cuisine.fillna('Unknown')
    known_boros=['Manhattan','Brooklyn','Queens','Bronx','Staten Island']
    d['borough']=d.borough.where(d.borough.isin(known_boros),'Unknown')
    d['zipcode']=d.zipcode.where(d.zipcode.str.fullmatch(r'\d{5}',na=False))
    d['never_inspected']=(d.latest_inspection_date.str[:10]=='1900-01-01').astype(int)
    d['latest_inspection_date']=pd.to_datetime(d.latest_inspection_date,errors='coerce').dt.strftime('%Y-%m-%d')
    d.loc[d.never_inspected==1,'latest_inspection_date']=pd.NA
    d['record_date']=pd.to_datetime(d.record_date,errors='raise').dt.strftime('%Y-%m-%d')
    check('single source snapshot day',d.record_date.nunique()==1,d.record_date.unique().tolist())
    check('reviewed DOHMH snapshot date',d.record_date.iloc[0]=='2026-10-06',
          'A newer snapshot requires review of the frozen narrative and dashboard labels before updating this guard')
    for col in ['latitude','longitude']: d[col]=pd.to_numeric(d[col],errors='coerce')
    # Broad NYC plausibility box is a quality flag, not boundary assignment or geocoding.
    d['coordinate_plausible']=(d.latitude.between(40.4,41.0)&d.longitude.between(-74.3,-73.65)).astype(int)
    d['source_id']='S1'
    quality={'source_violation_rows':int(source_counts['inspection_rows']),
             'restaurant_records':len(d),'missing_borough':int((d.borough=='Unknown').sum()),
             'missing_cuisine':int((d.cuisine=='Unknown').sum()),
             'missing_zipcode':int(d.zipcode.isna().sum()),
             'never_inspected':int(d.never_inspected.sum()),
             'implausible_or_missing_coordinates':int((d.coordinate_plausible==0).sum()),
             'record_date':d.record_date.iloc[0]}
    return write(d,'restaurants'),quality

def clean_delivery():
    if not (RAW/'dcwp_delivery.xlsx').exists(): return numerical_capture('delivery_quarterly')
    workbook=pd.ExcelFile(RAW/'dcwp_delivery.xlsx')
    sheets={s:pd.read_excel(workbook,sheet_name=s) for s in ['Workers','Consumers','Merchants']}
    for s in sheets.values(): s.iloc[:,0]=s.iloc[:,0].astype(str).str.strip()
    mapping={
        'weekly_deliveries':('Workers','Total deliveries'),
        'weekly_consumer_spending_usd':('Consumers','Total consumer spending'),
        'weekly_order_subtotals_usd':('Consumers','Order subtotals'),
        'average_total_order_cost_usd':('Consumers','Average total order cost'),
        'average_subtotal_usd':('Consumers','Average subtotal'),
        'average_consumer_fees_usd':('Consumers','Average consumer fees'),
        'weekly_merchant_fees_usd':('Merchants','Total merchant fees*'),
        'merchant_fee_share':('Merchants','Merchant fees, as a percentage of order subtotals'),
        'merchant_fee_per_delivery_usd':('Merchants','Merchant fees per delivery'),
    }
    quarters=[c for c in sheets['Consumers'].columns if re.fullmatch(r'Q[1-4] \d{4}',str(c))]
    rows=[]
    for label in quarters:
        q,y=label.split(); row={'period':label,'year':int(y),'quarter':int(q[1]),'source_id':'S2'}
        for name,(sheet,metric) in mapping.items():
            df=sheets[sheet]; match=df[df.iloc[:,0]==metric]
            # Workbook heading may mark aggregate measures with a footnote asterisk.
            if len(match)==0: match=df[df.iloc[:,0].str.rstrip('*')==metric.rstrip('*')]
            check(f'DCWP field {metric} {label}',len(match)==1,f'{len(match)} matches')
            row[name]=float(match.iloc[0][label])
        rows.append(row)
    d=pd.DataFrame(rows).sort_values(['year','quarter'])
    check('DCWP contiguous quarters',len(d)==16 and d.period.iloc[0]=='Q1 2022' and d.period.iloc[-1]=='Q4 2025',
          'Frozen source covers 2022 Q1 through 2025 Q4; review schema if refreshed')
    check('DCWP positive denominators',(d.weekly_deliveries>0).all() and (d.average_subtotal_usd>d.merchant_fee_per_delivery_usd).all(),
          'Per-delivery measures retain the agency reported averages')
    return write(d,'delivery_quarterly')

def clean_rent():
    if not (RAW/'rebny_manhattan_h1_2026.pdf').exists(): return numerical_capture('rent_corridor')
    text=PdfReader(RAW/'rebny_manhattan_h1_2026.pdf').pages[23].extract_text()
    anchors=[('Harlem','Harlem (125th)'),('Upper West Side','Upper West Side (Broadway)'),
      ('Columbus Avenue','Columbus Avenue'),('Upper East Side','Upper East Side (86th Street)'),
      ('Madison Avenue','Madison Avenue'),('Third Avenue','Third Avenue'),
      ('Lower Fifth Avenue','Lower Fifth Avenue'),('Upper Fifth Avenue','Upper Fifth Avenue'),
      ('Times Square','Times Square'),('Herald Square','Herald Square'),
      ('Flatiron (Fifth','Flatiron (Fifth Avenue)'),('Flatiron (Broadway','Flatiron (Broadway)'),
      ('Meatpacking','Meatpacking'),('West Village','West Village (Bleecker)'),
      ('Soho','SoHo'),('Financial District','Financial District')]
    periods=[(2026,1),(2025,2),(2025,1),(2024,2),(2024,1),(2023,2),(2023,1)]
    rows=[]
    for i,(anchor,name) in enumerate(anchors):
        start=text.index(anchor)
        end=text.index(anchors[i+1][0],start+len(anchor)) if i+1<len(anchors) else text.index('Median Asking Rent',start)
        values=re.findall(r'\$[\d,]+|N/A',text[start:end])[:7]
        check(f'REBNY seven periods {name}',len(values)==7,str(values))
        for (year,half),v in zip(periods,values):
            rows.append({'corridor':name,'year':year,'half':half,'period':f'H{half} {year}',
                'median_asking_rent_usd_sqft_year':None if v=='N/A' else float(v.replace('$','').replace(',','')),
                'source_id':'S3','source_page':24})
    d=pd.DataFrame(rows)
    check('REBNY missing values retained',d.loc[(d.period=='H1 2026') & d.corridor.isin(['Harlem (125th)','West Village (Bleecker)']),'median_asking_rent_usd_sqft_year'].isna().all(),
          'Published N/A is not zero; printed change columns are not used')
    return write(d,'rent_corridor')

def clean_sales():
    if not (RAW/'comptroller_economy_2025.html').exists(): return numerical_capture('citywide_sales')
    tables=pd.read_html(io.StringIO((RAW/'comptroller_economy_2025.html').read_text()))
    matches=[t for t in tables if 'Taxable Sales at restaurants & other eating places (current dollars in millions)' in t.to_string()]
    check('Comptroller restaurant table found',len(matches)==1,'Table 7')
    t=matches[0]; rows=[]
    for i,col in enumerate(t.columns[1:]):
        rows.append({'year_end':2019+i,'period_start':f'{2018+i}-09-01','period_end':f'{2019+i}-08-31',
           'nominal_sales_million_usd':float(t.iloc[0,i+1]),'real_sales_2019_million_usd':float(t.iloc[3,i+1]),
           'source_id':'S4','source_table':'Table 7'})
    return write(pd.DataFrame(rows),'citywide_sales')

def clean_context():
    if not (RAW/'comptroller_storefronts_2026.html').exists() and not (RAW/'times_square_aug_2026.pdf').exists():
        return numerical_capture('storefront_vacancy'),numerical_capture('pedestrian_context')
    raw=(RAW/'comptroller_storefronts_2026.html').read_text()
    text=html.unescape(re.sub('<[^>]+>',' ',raw)); text=re.sub(r'\s+',' ',text)
    # Small narrative capture. Validate each value remains in the matching passage.
    boroughs=[('Manhattan',12.9),('Brooklyn',12.3),('Queens',9.5),('Bronx',8.0),('Staten Island',7.5)]
    start=text.index('12.9%'); passage=text[start-500:start+1100]
    for name,value in boroughs: check(f'vacancy passage {name}',f'{value:.1f}%' in passage and name in passage,str(value))
    vacancy=pd.DataFrame([{'borough':b,'vacancy_pct':v,'as_of':'2026-04-15','source_id':'S5'} for b,v in boroughs])
    write(vacancy,'storefront_vacancy')
    t=PdfReader(RAW/'times_square_aug_2026.pdf').pages[1].extract_text()
    t=re.sub(r'\s+',' ',t)
    match=re.search(r'([\d,]+) August 2026 Average Daily Pedestrians',t)
    check('Times Square pedestrian capture',match is not None,'PDF page 2')
    foot=pd.DataFrame([{'area':'Times Square','month':'2026-08','average_daily_pedestrians':int(match.group(1).replace(',','')),
                        'reported_yoy_pct_rounded':2.0,'source_id':'S6','source_page':2}])
    check('Times Square rounded YoY',re.search(r'Change from 2025.*?2%',t) is not None,'Published rounded comparison')
    return vacancy,write(foot,'pedestrian_context')

def build():
    restaurants,quality=clean_restaurants()
    delivery=clean_delivery(); rent=clean_rent(); sales=clean_sales(); vacancy,foot=clean_context()
    tables={'restaurants':restaurants,'delivery_quarterly':delivery,'rent_corridor':rent,'citywide_sales':sales,
            'storefront_vacancy':vacancy,'pedestrian_context':foot}
    with sqlite3.connect(DB) as conn:
        for name,df in tables.items(): df.to_sql(name,conn,if_exists='replace',index=False)
        conn.executescript('CREATE UNIQUE INDEX IF NOT EXISTS restaurant_camis ON restaurants(camis); CREATE INDEX IF NOT EXISTS restaurant_filters ON restaurants(borough,cuisine,zipcode);')
        conn.executescript((ROOT/'analysis.sql').read_text())
        views={name:pd.read_sql_query(f'SELECT * FROM {name}',conn) for name in ['borough_supply','cuisine_borough','zip_cuisine','delivery_analysis','rent_comparison','sales_analysis']}
        for name,df in views.items(): df.to_csv(OUT/f'{name}.csv',index=False)
        by_cuisine=pd.read_sql_query("SELECT cuisine,COUNT(*) restaurant_count FROM restaurants WHERE cuisine <> 'Unknown' GROUP BY cuisine ORDER BY restaurant_count DESC",conn)
        by_cuisine.to_csv(OUT/'citywide_cuisine.csv',index=False)
        check('borough totals reconcile',int(views['borough_supply'].active_permit_records.sum())+quality['missing_borough']==len(restaurants),'Located plus unknown borough equals all records')
        check('known cuisine totals reconcile',int(views['cuisine_borough'].restaurant_count.sum())==int(((restaurants.cuisine!='Unknown')&(restaurants.borough!='Unknown')).sum()),'All cuisine and borough aggregates reconcile')
        latest=views['delivery_analysis'].sort_values(['year','quarter']).iloc[-1]
        base=views['delivery_analysis'].query('year==2024 and quarter==4').iloc[0]
        check('headline delivery independent arithmetic',abs(latest.after_fee_yoy_pct - ((latest.average_subtotal_usd-latest.merchant_fee_per_delivery_usd)/(base.average_subtotal_usd-base.merchant_fee_per_delivery_usd)-1)*100)<1e-9,'SQL compared with independent raw-field calculation')
        stats={**quality,'delivery_volume_yoy_pct':float(latest.deliveries_yoy_pct),
          'delivery_after_fee_yoy_pct':float(latest.after_fee_yoy_pct),
          'delivery_after_fee_2024q4':float(base.subtotal_less_merchant_fee_usd),
          'delivery_after_fee_2025q4':float(latest.subtotal_less_merchant_fee_usd),
          'fee_increment_share_pct':float((latest.merchant_fee_per_delivery_usd-base.merchant_fee_per_delivery_usd)/(latest.average_subtotal_usd-base.average_subtotal_usd)*100),
          'real_sales_vs_2019_pct':float(views['sales_analysis'].iloc[-1].real_sales_index_2019-100)}
    pd.DataFrame(checks).to_csv(OUT/'validation_checks.csv',index=False)
    (OUT/'summary.json').write_text(json.dumps(stats,indent=2))
    payload={'summary':stats,'boroughs':records(views['borough_supply']),'cuisines':records(views['cuisine_borough']),
       'zipCuisines':records(views['zip_cuisine']),'citywideCuisines':records(by_cuisine),
       'delivery':records(views['delivery_analysis']),'rents':records(views['rent_comparison']),
       'sales':records(views['sales_analysis']),'vacancy':records(vacancy),'footfall':records(foot)}
    (OUT/'dashboard_data.json').write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')))
    print(json.dumps({'summary':stats,'checks_passed':len(checks),'output_tables':len(tables)+len(views)+1},indent=2))

if __name__=='__main__': build()
