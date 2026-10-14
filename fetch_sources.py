"""Download public evidence with retrieval dates and SHA256 checksums."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, urllib.request, urllib.parse

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data' / 'raw'
RAW.mkdir(parents=True, exist_ok=True)
SOURCE_URLS = {
    'nyc_nta2020.geojson': 'https://data.cityofnewyork.us/resource/9nt8-h7nd.geojson?$limit=1000',
    'dcwp_delivery.xlsx': 'https://www.nyc.gov/assets/dca/downloads/xlsx/Restaurant-Delivery-App-Data-Quarterly.xlsx',
    'comptroller_economy_2025.html': 'https://comptroller.nyc.gov/reports/annual-state-of-the-citys-economy-and-finances-2025/',
    'comptroller_storefronts_2026.html': 'https://comptroller.nyc.gov/reports/whos-minding-the-storefronts/',
    'rebny_manhattan_h1_2026.pdf': 'https://downloads.ctfassets.net/6zi14rd5umxw/3Vr3b2g2AgkuFQBWAqLB9t/67f0279be062efb9eef66e3308d38cdb/Manhattan_Retail_Report_H1_2026__1_.pdf',
    'times_square_aug_2026.pdf': 'https://cdn.prod.website-files.com/66164ec19113caaa1f66178a/6a99adcee6d25387709e7a2f_August%20%2726%20Monthly%20Economic%20Indicator%20Report.pdf',
    'dohmh_metadata.json': 'https://data.cityofnewyork.us/api/views/43nn-pn8j.json',
    'dohmh_counts.json': 'https://data.cityofnewyork.us/resource/43nn-pn8j.json?' + urllib.parse.urlencode({'$select':'count(*) as inspection_rows,count(distinct camis) as distinct_camis'}),
    'dohmh_restaurants.csv': 'https://data.cityofnewyork.us/resource/43nn-pn8j.csv?' + urllib.parse.urlencode({
        '$select':'camis,dba,boro,cuisine_description,zipcode,latitude,longitude,max(inspection_date) as latest_inspection_date,max(record_date) as record_date',
        '$group':'camis,dba,boro,cuisine_description,zipcode,latitude,longitude',
        '$order':'camis', '$limit':50000}),
}

def fetch(item):
    filename,url = item
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (public data research)'})
        with urllib.request.urlopen(req, timeout=45) as response:
            data = response.read()
            content_type = response.headers.get('Content-Type','')
            final_url = response.url
        (RAW/filename).write_bytes(data)
        entry = {'file':filename,'url':url,'resolved_url':final_url,
                 'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'content_type':content_type,'status':'ok'}
    except Exception as error:
        entry = {'file':filename,'url':url,'status':'error','error':str(error)}
    print(json.dumps({k:v for k,v in entry.items() if k in ['file','bytes','status','error']}), flush=True)
    return entry

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(fetch,SOURCE_URLS.items()))
    (RAW/'download_manifest.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    geography=next(item for item in results if item['file']=='nyc_nta2020.geojson')
    if geography['status']=='ok':
        (RAW/'geography_download_manifest.json').write_text(json.dumps({**geography,'source_id':'S7'},indent=2))
    if any(item['status']!='ok' for item in results):
        raise SystemExit('Some sources failed. Review the manifest before rebuilding; do not mix stale and fresh sources.')
