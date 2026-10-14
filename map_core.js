/* Pure map calculations shared by the HTML and Node regression checks. */
const MapCore = {
 value(area,cuisine,metric){
  const count=cuisine?(area.cuisines[cuisine]||0):area.total;
  if(metric==='share')return cuisine&&cuisine!=='Unknown'&&area.known>0?count/area.known*100:null;
  return count;
 },
 color(value,kind){
  if(value===null||!Number.isFinite(value))return '#cbd3da';
  const cuts=kind==='rent'?[300,500,800,1500]:kind==='share'?[1,5,10,20]:[1,5,20,50,100,250];
  const colors=kind==='rent'?['#ffe8c4','#ffc885','#f39b55','#d85a42','#9d243b']:kind==='share'?['#e4f2ed','#bddfd3','#76bdae','#369686','#126356']:['#f3f5f6','#e5f3eb','#bfdfcf','#84c5b1','#48a28f','#237b72','#124f54'];
  return colors[cuts.filter(c=>value>=c).length];
 },
 rows(areas,borough,cuisine,metric){return areas.filter(a=>!borough||a.borough===borough).map(a=>({code:a.code,name:a.name,borough:a.borough,type:a.type,count:cuisine?(a.cuisines[cuisine]||0):a.total,total:a.total,known:a.known,value:this.value(a,cuisine,metric)})).sort((a,b)=>(b.value??-1)-(a.value??-1)||b.count-a.count||a.name.localeCompare(b.name));},
 extent(areas){const bs=areas.map(a=>a.bounds);let x0=Math.min(...bs.map(b=>b[0])),y0=Math.min(...bs.map(b=>b[1])),x1=Math.max(...bs.map(b=>b[2])),y1=Math.max(...bs.map(b=>b[3]));let w=x1-x0,h=y1-y0;const p=Math.max(w,h)*.055;return [x0-p,y0-p,w+2*p,h+2*p]},
 zoom(box,factor){const [x,y,w,h]=box;const nw=Math.max(10,Math.min(1300,w*factor)),nh=h*nw/w;return [x+(w-nw)/2,y+(h-nh)/2,nw,nh];}
};
if(typeof module!=='undefined')module.exports=MapCore;
