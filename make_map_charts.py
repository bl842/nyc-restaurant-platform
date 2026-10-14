"""Export static companion maps from the same display geometry as the HTML."""
from pathlib import Path
import json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Patch
R=Path(__file__).resolve().parent
m=json.loads((R/'outputs/map_data.json').read_text());g=json.loads((R/'data/clean/nta2020_display.geojson').read_text())
areas={a['code']:a for a in m['areas']};cs=math.cos(math.radians(40.7))
def xy(c):return (c[0]*cs,c[1])
def color(v,rent=False):
 cuts=[300,500,800,1500] if rent else [1,5,20,50,100,250]
 cols=['#ffe8c4','#ffc885','#f39b55','#d85a42','#9d243b'] if rent else ['#f3f5f6','#e5f3eb','#bfdfcf','#84c5b1','#48a28f','#237b72','#124f54']
 return '#cbd3da' if v is None else cols[sum(v>=c for c in cuts)]
def base(ax,borough=None):
 for f in g['features']:
  a=areas[f['properties']['nta2020']]
  if borough and a['borough']!=borough:continue
  polys=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
  for poly in polys:
   ax.add_patch(Polygon([xy(c) for c in poly[0]],facecolor='#dbe3e7' if borough else color(a['cuisines'].get('Chinese',0)),edgecolor='white',linewidth=.3))
   for hole in poly[1:]:ax.add_patch(Polygon([xy(c) for c in hole],facecolor='#eaf1f6',edgecolor='white',linewidth=.3))
 ax.autoscale_view();ax.set_aspect('equal');ax.axis('off');ax.set_facecolor('#eaf1f6')
fig,ax=plt.subplots(figsize=(8.5,6));base(ax)
ax.set_title('Chinese cuisine records by NYC neighborhood',loc='left',fontsize=15,pad=16,color='#173d5c')
ax.legend(handles=[Patch(facecolor=color(v),label=t) for v,t in [(0,'0'),(1,'1–4'),(5,'5–19'),(20,'20–49'),(50,'50–99'),(100,'100–249'),(250,'250+')]],loc='lower right',title='Mapped records',frameon=True,facecolor='white',edgecolor='white',fontsize=9)
fig.text(.07,.025,'DOHMH, 6 Oct 2026; NYC DCP 2020 NTA boundaries. Supply counts, not consumer demand.',fontsize=8,color='#546777')
fig.tight_layout(rect=(0,.05,1,1))
for ext in ['png','svg']:fig.savefig(R/'charts'/('cuisine_neighborhood_map.'+ext),dpi=180,bbox_inches='tight')
plt.close(fig)
fig=plt.figure(figsize=(10,6));ax=fig.add_axes([.05,.1,.4,.8]);base(ax,'Manhattan')
for r in m['rents']:
 x,y=xy([r['longitude'],r['latitude']]);ax.scatter([x],[y],s=75,color=color(r['rent'],True),edgecolor='#173d5c',linewidth=.5,zorder=3);ax.annotate(str(r['id']),xy=(x,y),xytext=((-10,8) if r['id']==11 else (10,-8) if r['id']==12 else (0,0)),textcoords='offset points',ha='center',va='center',fontsize=6,zorder=4,arrowprops=dict(arrowstyle='-',lw=.5) if r['id'] in [11,12] else None)
fig.text(.06,.94,'Manhattan retail asking-rent hotspots',fontsize=15,color='#173d5c')
for i,r in enumerate(m['rents']):
 value='n/a' if r['rent'] is None else '${:,.0f}'.format(r['rent'])
 fig.text(.47,.855-i*.043,f"{r['id']:2}. {r['corridor']}",fontsize=9,color='#173d5c');fig.text(.965,.855-i*.043,value,ha='right',fontsize=9,color='#173d5c')
fig.text(.47,.9,'Corridor benchmark                                  USD / sq ft / year',fontsize=9,color='#546777')
fig.text(.06,.045,'REBNY H1 2026, p. 24. Approximate anchors only; grey NTAs have no neighborhood-wide estimate.',fontsize=8,color='#546777')
for ext in ['png','svg']:fig.savefig(R/'charts'/('rent_hotspot_map.'+ext),dpi=180,bbox_inches='tight')
plt.close(fig)
