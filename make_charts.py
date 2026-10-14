"""Export shareable figures from the SQL output tables."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT=Path(__file__).resolve().parent
CHARTS=ROOT/'charts'; CHARTS.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
 'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#CBD5E1',
 'axes.labelcolor':'#334155','xtick.color':'#475569','ytick.color':'#334155',
 'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})
NAVY='#173D5C'; TEAL='#177E89'; GOLD='#E6A34B'; GREY='#B8C5D0'

def save(fig,name):
    fig.savefig(CHARTS/f'{name}.png',dpi=190,bbox_inches='tight')
    fig.savefig(CHARTS/f'{name}.svg',bbox_inches='tight')
    plt.close(fig)

d=pd.read_csv(ROOT/'outputs'/'delivery_analysis.csv').set_index('period')
v=d.loc[['Q4 2024','Q4 2025']]
fig,ax=plt.subplots(figsize=(7.6,3.5)); fig.subplots_adjust(left=.18,bottom=.35,top=.84,right=.91)
y=[1,0]
ax.barh(y,v.subtotal_less_merchant_fee_usd,color=TEAL,height=.5,label='Subtotal less merchant fee')
ax.barh(y,v.merchant_fee_per_delivery_usd,left=v.subtotal_less_merchant_fee_usd,color=GOLD,height=.5,label='Merchant platform fee')
for j,(_,r) in zip(y,v.iterrows()):
    ax.text(r.subtotal_less_merchant_fee_usd/2,j,f'${r.subtotal_less_merchant_fee_usd:.2f}',ha='center',va='center',color='white',weight='bold')
    ax.text(r.subtotal_less_merchant_fee_usd+r.merchant_fee_per_delivery_usd/2,j,f'${r.merchant_fee_per_delivery_usd:.2f}',ha='center',va='center',color='#172B3A')
    ax.text(r.average_subtotal_usd+.4,j,f'${r.average_subtotal_usd:.2f}',va='center',fontsize=10)
ax.set(yticks=y,yticklabels=v.index,xlim=(0,34),xlabel='Average order subtotal (USD per delivery)')
ax.set_title('After-fee amount per delivery grew 0.8%',loc='left',fontweight='bold',pad=14)
fig.legend(loc='lower center',bbox_to_anchor=(.56,.095),frameon=False,ncol=2,fontsize=9)
fig.text(.02,.015,'DCWP, Q4 2024 vs Q4 2025. Before food, labor, packaging and rent.\nCovered apps include some non-restaurant deliveries.',fontsize=8,color='#475569')
save(fig,'delivery_order_economics')

r=pd.read_csv(ROOT/'outputs'/'rent_comparison.csv')
latest=r[r.period=='H1 2026'].dropna(subset=['median_asking_rent_usd_sqft_year'])
for small in [True,False]:
    labels=['Financial District','Upper West Side (Broadway)','Flatiron (Fifth Avenue)','SoHo','Madison Avenue','Times Square']
    data=(latest[latest.corridor.isin(labels)] if small else latest).sort_values('median_asking_rent_usd_sqft_year')
    fig,ax=plt.subplots(figsize=(7.6,3.25 if small else 6.4)); fig.subplots_adjust(left=.36,bottom=.25 if small else .15,top=.85,right=.91)
    ax.barh(data.corridor,data.median_asking_rent_usd_sqft_year,color=[GOLD if n=='Times Square' else NAVY for n in data.corridor],height=.62)
    for j,x in enumerate(data.median_asking_rent_usd_sqft_year): ax.text(x+max(data.median_asking_rent_usd_sqft_year)*.025,j,f'${x:,.0f}',va='center',fontsize=10)
    ax.invert_yaxis();ax.set_xlim(0,max(data.median_asking_rent_usd_sqft_year)*1.18)
    ax.set_xlabel('Median annual asking rent (USD per ground-floor sq ft)')
    ax.set_title('Asking rents vary sharply across corridors',loc='left',fontweight='bold',pad=16)
    fig.text(.02,.02,'REBNY, H1 2026, p. 24. Retail asking rents; restaurant suitability and executed lease terms are not observed.',fontsize=8,color='#475569')
    save(fig,'rent_selected_corridors' if small else 'rent_all_corridors')

b=pd.read_csv(ROOT/'outputs'/'borough_supply.csv').sort_values('active_permit_records')
fig,ax=plt.subplots(figsize=(8,4.4));fig.subplots_adjust(left=.2,bottom=.22,top=.82,right=.91)
ax.barh(b.borough,b.known_cuisine_records,color=NAVY,label='Known cuisine')
ax.barh(b.borough,b.missing_cuisine_records,left=b.known_cuisine_records,color=GREY,label='Cuisine missing')
for j,(_,row) in enumerate(b.iterrows()): ax.text(row.active_permit_records+130,j,f'{row.active_permit_records:,}',va='center')
ax.set_xlim(0,b.active_permit_records.max()*1.15);ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:,.0f}'))
ax.set_xlabel('Distinct active permit records');ax.set_title('Restaurant supply by borough',loc='left',fontweight='bold',pad=15)
ax.legend(loc='lower right',frameon=False)
fig.text(.02,.04,'DOHMH snapshot: 6 October 2026. Includes permit applicants and college cafeterias.\n95 records without a recognized borough are excluded. Active permit status does not confirm current trading.',fontsize=8,color='#475569')
save(fig,'restaurant_supply_borough')

s=pd.read_csv(ROOT/'outputs'/'sales_analysis.csv')
fig,ax=plt.subplots(figsize=(8,4.6));fig.subplots_adjust(bottom=.27,left=.1,right=.88,top=.82)
ax.plot(s.year_end,s.nominal_sales_million_usd/1000,marker='o',lw=2.5,color=NAVY,label='Nominal sales')
ax.plot(s.year_end,s.real_sales_2019_million_usd/1000,marker='s',lw=2.5,color=TEAL,label='Constant 2019 dollars')
ax.set(ylim=(0,32),xticks=s.year_end,ylabel='Taxable sales (USD billions)',xlabel='Year ending in August')
ax.legend(frameon=False,loc='lower right');ax.grid(axis='y',alpha=.15)
ax.set_title('Price-adjusted restaurant sales remain below 2019',loc='left',fontweight='bold',pad=15)
fig.text(.02,.05,'NYC Comptroller, Annual State of the City Economy and Finances 2025, Table 7.\nRestaurants and other eating places. Each observation covers September through August.',fontsize=8,color='#475569')
save(fig,'restaurant_sales_nominal_real')

v=pd.read_csv(ROOT/'data'/'clean'/'storefront_vacancy.csv').sort_values('vacancy_pct')
fig,ax=plt.subplots(figsize=(8,4.1));fig.subplots_adjust(left=.2,bottom=.23,top=.81,right=.9)
ax.barh(v.borough,v.vacancy_pct,color=TEAL)
for i,n in enumerate(v.vacancy_pct): ax.text(n+.18,i,f'{n:.1f}%',va='center')
ax.set(xlim=(0,15),xlabel='Share of storefronts vacant (%)')
ax.set_title('Storefront vacancy differs across boroughs',loc='left',fontweight='bold',pad=15)
fig.text(.02,.04,'NYC Comptroller / Live XYZ, status at 15 April 2026. All storefronts; this is not a restaurant closure rate.',fontsize=8,color='#475569')
save(fig,'storefront_vacancy')
print('Created six chart pairs (PNG and SVG).')
