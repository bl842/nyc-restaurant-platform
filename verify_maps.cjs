/* Node calculation and DOM tests. This does not validate browser layout or drag behavior. */
const fs=require('fs'),path=require('path'),assert=require('assert'),vm=require('vm');
const {JSDOM,VirtualConsole}=require(process.env.NYC_JSDOM_MODULE||'jsdom');
const Core=require('./map_core.js'),R=__dirname,M=JSON.parse(fs.readFileSync(path.join(R,'outputs/map_data.json'),'utf8'));
const checks=[];function check(n,b){assert(b,n);checks.push({check:n,passed:true})}
(async()=>{
check('262 unique NTA polygons',M.areas.length===262&&new Set(M.areas.map(a=>a.code)).size===262);
check('Mapped totals reconcile',M.areas.reduce((n,a)=>n+a.total,0)===30655&&M.summary.mapped_records+M.summary.excluded_records===31469);
const flushing=M.areas.find(a=>a.name==='Flushing-Willets Point');
check('Chinese count and denominator',Core.value(flushing,'Chinese','count')===266&&flushing.known===509);
check('Share uses known-cuisine denominator',Math.abs(Core.value(flushing,'Chinese','share')-266/509*100)<1e-10);
check('Missing denominator stays unavailable',Core.value({...flushing,known:0},'Chinese','share')===null);
check('Absent cuisine is zero',Core.value(flushing,'Nonexistent cuisine','count')===0);
check('Count zero and missing use different colors',Core.color(0,'count')!==Core.color(null,'count'));
check('Borough filter matches polygons',Core.rows(M.areas,'Queens','Chinese','count').every(r=>r.borough==='Queens'));
check('Rent values retain original source',M.rents.length===16&&M.rents.filter(r=>r.rent===null).length===2&&M.rents.find(r=>r.corridor==='Financial District').rent===200);
check('Rent anchors limited to Manhattan',M.rents.every(r=>r.borough==='Manhattan'));
const html=fs.readFileSync(path.join(R,'NYC_Restaurant_Explorer.html'),'utf8');
const errors=[];const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));let exported=[],blobs=[];
const dom=new JSDOM(html,{runScripts:'dangerously',virtualConsole:vc,beforeParse(w){w.URL.createObjectURL=b=>{blobs.push(b);return 'blob:map-test'};w.URL.revokeObjectURL=()=>{};w.HTMLAnchorElement.prototype.click=function(){exported.push(this.download)};w.HTMLElement.prototype.scrollIntoView=function(){};}});
const w=dom.window,d=w.document,$=id=>d.getElementById(id);function set(id,v){$(id).value=v;$(id).dispatchEvent(new w.Event('change',{bubbles:true}))}function click(id){$(id).click()}
check('No initialization errors',errors.length===0);
check('Map initially visible with all NTAs',!$('maps').hidden&&d.querySelectorAll('.map-area-path').length===262);
set('map-cuisine','Chinese');set('map-borough','Queens');set('map-area',flushing.code);
check('Selected neighborhood count renders',$('map-detail').textContent.includes('266')&&$('map-detail').textContent.includes('509'));
set('map-metric','share');check('Share display rounds correctly',$('map-detail').textContent.includes('52.3%'));
set('map-cuisine','');check('All-cuisine share is disabled',$('map-metric').value==='count'&&$('map-metric').options[1].disabled);
set('map-cuisine','Unknown');check('Unknown cuisine cannot use known-cuisine share',$('map-metric').options[1].disabled);
set('map-cuisine','Chinese');const before=$('neighborhood-map').getAttribute('viewBox');click('map-in');check('Zoom changes viewBox',before!==$('neighborhood-map').getAttribute('viewBox'));click('map-home');check('Fit restores viewBox',before===$('neighborhood-map').getAttribute('viewBox'));
click('export-map');check('Cuisine export triggered',exported.at(-1)==='neighborhood_cuisine_heat.csv');
set('map-layer','rent');check('Rent defaults to Manhattan with 16 markers',$('map-borough').value==='Manhattan'&&d.querySelectorAll('.map-rent-point').length===16);
const rentButton=d.querySelector('[data-select="R16"]');rentButton.click();check('Rent selection has correct value and scope',$('map-detail').textContent.includes('$200')&&$('map-detail').textContent.includes('not an NTA-wide'));
set('map-borough','Queens');check('Uncovered borough has no imputed rent',d.querySelectorAll('.map-rent-point').length===0&&$('map-rank-body').textContent.includes('No published rent observations')&&$('export-map').disabled);
set('map-borough','Manhattan');click('export-map');check('Rent export triggered',exported.at(-1)==='rent_hotspots.csv');
d.querySelector('[data-flow="cuisine"]').click();check('Cuisine entry links to map',!$('maps').hidden&&$('map-cuisine').value==='Chinese'&&$('map-layer').value==='cuisine');
d.querySelector('[data-flow="location"]').click();check('Location entry links to map',!$('maps').hidden&&$('map-borough').value==='Manhattan');
d.querySelector('[data-flow="explore"]').click();check('Exploration resets map filters',$('map-borough').value===''&&$('map-cuisine').value==='');
click('tab-supply');check('Original supply total retained',$('supply-stats').textContent.includes('31,374'));
click('tab-delivery');check('Original delivery metrics retained',$('delivery-stats').textContent.includes('+18.3%')&&$('delivery-stats').textContent.includes('+0.8%'));
click('tab-rent');check('Original rent table retained',$('rent-body').querySelectorAll('tr').length===16);
const text=await new Promise(resolve=>{const f=new w.FileReader();f.onload=()=>resolve(f.result);f.readAsText(blobs[0])});
check('Cuisine export retains geography and definition',text.includes('nta2020')&&text.includes('not consumer demand')&&text.includes('Flushing-Willets Point'));
check('No DOM runtime errors',errors.length===0);
check('HTML has no external script dependency',!d.querySelector('script[src]')&&html.indexOf('__MAP_')===-1);
dom.window.close();
const out={tested_at_utc:new Date().toISOString(),test_type:'Node calculation and JSDOM behavior tests; not browser layout QA',passed:checks.length,checks,limitations:['Real browser rendering and responsiveness not executed','SVG pointer pan not exercised in JSDOM','Keyboard focus appearance requires browser review']};fs.writeFileSync(path.join(R,'qa/map_checks.json'),JSON.stringify(out,null,2));console.log(JSON.stringify({passed:checks.length}));
})().catch(e=>{console.error(e);process.exit(1)});
