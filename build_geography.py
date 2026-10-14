"""Spatially assign frozen restaurant records to official 2020 NTAs.
Requires shapely. No nearest-neighborhood imputation and no inferred rent surface.
"""
from pathlib import Path
import json,hashlib,math,sqlite3
import pandas as pd
from shapely.geometry import shape,Point,mapping
from shapely.strtree import STRtree
R=Path(__file__).resolve().parent
raw=R/'data/raw/nyc_nta2020.geojson'
manifest=json.loads((raw.parent/'geography_download_manifest.json').read_text())
assert hashlib.sha256(raw.read_bytes()).hexdigest()==manifest['sha256']
geo=json.loads(raw.read_text());features=sorted(geo['features'],key=lambda f:f['properties']['nta2020'])
assert len(features)==262 and len({f['properties']['nta2020'] for f in features})==262
geoms=[shape(f['geometry']) for f in features];assert all(g.is_valid for g in geoms)
tree=STRtree(geoms)
d=pd.read_csv(R/'data/clean/restaurants.csv',dtype={'camis':str,'zipcode':str})
assign=[]
for r in d.itertuples():
 status='assigned';idx=None
 if r.borough not in ['Manhattan','Brooklyn','Queens','Bronx','Staten Island']:status='unknown_borough'
 elif not r.coordinate_plausible:status='invalid_or_missing_coordinates'
 else:
  matches=list(tree.query(Point(r.longitude,r.latitude),predicate='intersects'))
  if not matches:status='outside_nta_boundaries'
  elif len(matches)>1:status='ambiguous_boundary'
  elif features[matches[0]]['properties']['boroname']!=r.borough:status='borough_mismatch'
  else:idx=int(matches[0])
 assign.append({'camis':r.camis,'nta2020':features[idx]['properties']['nta2020'] if idx is not None else None,'map_status':status})
a=pd.DataFrame(assign);a.to_csv(R/'data/clean/restaurant_nta_assignment.csv',index=False)
e=d.merge(a,on='camis',validate='one_to_one');matched=e[e.map_status=='assigned']
counts=matched.groupby(['nta2020','cuisine']).size().rename('restaurant_count').reset_index()
counts.to_csv(R/'outputs/nta_cuisine.csv',index=False)
cs={code:dict(zip(g.cuisine,g.restaurant_count.astype(int))) for code,g in counts.groupby('nta2020')}
# Compact display geometry: assignment uses full precision source, display only is simplified.
cos=math.cos(math.radians(40.7))
def project(c):return [(c[0]+74.3)*cos*1600,(41.0-c[1])*1600]
def path(g):
 polygons=g.geoms if g.geom_type=='MultiPolygon' else [g]
 pieces=[]
 for poly in polygons:
  for ring in [poly.exterior,*poly.interiors]:
   xy=[project(c) for c in ring.coords]
   pieces.append('M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in xy)+'Z')
 return ''.join(pieces)
areas=[];simplified=[]
for f,g in zip(features,geoms):
 p=f['properties'];code=p['nta2020'];c=cs.get(code,{})
 sg=g.simplify(.000035,preserve_topology=True)
 x0,y0=project([g.bounds[0],g.bounds[3]]);x1,y1=project([g.bounds[2],g.bounds[1]])
 center=project(list(g.representative_point().coords)[0])
 row={'code':code,'name':p['ntaname'],'borough':p['boroname'],'type':p['ntatype'],'cdta':p['cdta2020'],'total':sum(c.values()),'known':sum(v for k,v in c.items() if k!='Unknown'),'cuisines':c,'path':path(sg),'bounds':[round(v,3) for v in [x0,y0,x1,y1]],'center':[round(v,3) for v in center]}
 areas.append(row);simplified.append({'type':'Feature','properties':{k:p[k] for k in ['nta2020','ntaname','boroname','ntatype','cdta2020']},'geometry':mapping(sg)})
(R/'data/clean/nta2020_display.geojson').write_text(json.dumps({'type':'FeatureCollection','features':simplified},separators=(',',':')))
pd.DataFrame([{k:v for k,v in ar.items() if k in ['code','name','borough','type','cdta','total','known']} for ar in areas]).to_csv(R/'outputs/nta_summary.csv',index=False)
# Illustrative anchors aid orientation only. They are neither corridor endpoints nor an NTA rent crosswalk.
anchors=[
('Harlem (125th)',-73.9485,40.8089,'125th Street near Lenox Avenue'),
('Upper West Side (Broadway)',-73.9820,40.7788,'Broadway near West 72nd Street'),
('Columbus Avenue',-73.9775,40.7776,'Columbus Avenue near West 72nd Street'),
('Upper East Side (86th Street)',-73.9543,40.7786,'East 86th Street near Third Avenue'),
('Madison Avenue',-73.9690,40.7673,'Madison Avenue near East 65th Street'),
('Third Avenue',-73.9620,40.7650,'Third Avenue near East 66th Street'),
('Lower Fifth Avenue',-73.9785,40.7558,'Fifth Avenue near West 45th Street'),
('Upper Fifth Avenue',-73.9745,40.7605,'Fifth Avenue near West 53rd Street'),
('Times Square',-73.9851,40.7580,'Times Square center; source endpoint text is inconsistent'),
('Herald Square',-73.9878,40.7498,'Herald Square near West 34th Street'),
('Flatiron (Fifth Avenue)',-73.9920,40.7390,'Fifth Avenue near West 19th Street'),
('Flatiron (Broadway)',-73.9900,40.7385,'Broadway near East 20th Street'),
('Meatpacking',-74.0060,40.7416,'West 14th Street between Ninth and Tenth Avenues'),
('West Village (Bleecker)',-74.0030,40.7340,'Bleecker Street near Christopher Street'),
('SoHo',-73.9985,40.7240,'Broadway near Prince Street'),
('Financial District',-74.0060,40.7105,'Broadway near Fulton Street')]
rents=pd.read_csv(R/'outputs/rent_comparison.csv');current=rents[(rents.year==2026)&(rents.half==1)].set_index('corridor')
assert set(x[0] for x in anchors)==set(current.index)
markers=[]
for i,(name,lon,lat,desc) in enumerate(anchors,1):
 val=current.loc[name,'median_asking_rent_usd_sqft_year'];pos=project([lon,lat]);cands=tree.query(Point(lon,lat),predicate='intersects')
 assert len(cands)>=1 and all(features[int(j)]['properties']['boroname']=='Manhattan' for j in cands)
 markers.append({'id':i,'corridor':name,'borough':'Manhattan','longitude':lon,'latitude':lat,'x':round(pos[0],3),'y':round(pos[1],3),'rent':float(val) if pd.notna(val) else None,'period':'H1 2026','source_id':'S3','source_page':24,'anchor_description':desc,'location_method':'Illustrative manually placed anchor; not a surveyed corridor footprint or an NTA rent estimate'})
pd.DataFrame(markers).to_csv(R/'data/clean/rent_map_anchors.csv',index=False)
summary={'source_records':len(d),'mapped_records':len(matched),'mapped_pct':len(matched)/len(d)*100,'excluded_records':len(d)-len(matched),'exclusion_reasons':{str(k):int(v) for k,v in a[a.map_status!='assigned'].map_status.value_counts().items()},'nta_count':262,'residential_nta_count':sum(ar['type']=='0' for ar in areas),'boundary_source':'S7','boundary_download':manifest['retrieved_utc'],'restaurant_record_date':'2026-10-06','rent_marker_count':len(markers),'rent_with_value':sum(m['rent'] is not None for m in markers),'rent_missing_value':sum(m['rent'] is None for m in markers)}
assert sum(ar['total'] for ar in areas)==len(matched)
assert a.camis.is_unique and len(a)==31469 and summary['rent_with_value']==14
out={'areas':areas,'rents':markers,'summary':summary,'cuisines':sorted(set(matched.cuisine)-{'Unknown'})}
(R/'outputs/map_data.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
(R/'outputs/geography_summary.json').write_text(json.dumps(summary,indent=2))
with sqlite3.connect(R/'nyc_restaurants.sqlite') as db:
 a.to_sql('restaurant_nta_assignment',db,if_exists='replace',index=False)
 pd.read_csv(R/'outputs/nta_summary.csv').to_sql('nta_summary',db,if_exists='replace',index=False)
 counts.to_sql('nta_cuisine',db,if_exists='replace',index=False)
 pd.DataFrame(markers).to_sql('rent_map_anchors',db,if_exists='replace',index=False)
print(json.dumps(summary,indent=2))
