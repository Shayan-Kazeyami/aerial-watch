// QA candidate: dissolve alternate central axial rows, preserving flute samples.
// Returns private geometry; caller owns assignment/disposal. No production install.
export function createStructuredCrownCandidate(mesh){
 if(mesh.userData?.assemblyId!=='CROWN')throw Error('Expected CROWN');
 const g=mesh.geometry,p=g.attributes.position,ix=g.index.array;
 const rows=new Map();
 for(let i=0;i<p.count;i++){
  const x=p.getX(i),r=Math.hypot(p.getY(i),p.getZ(i));
  if(x>23.13&&x<24.52&&r>2){if(!rows.has(x))rows.set(x,[]);rows.get(x).push(i)}
 }
 const xs=[...rows.keys()].sort((a,b)=>a-b);if(xs.length!==15||xs.some(x=>rows.get(x).length!==384))throw Error('Unexpected crown source grid');
 const kept=xs.filter((x,i)=>i%2===0);const rings=kept.map(x=>rows.get(x).sort((a,b)=>{
  const angle=i=>(Math.atan2(p.getZ(i),p.getY(i))+2*Math.PI)%(2*Math.PI);return angle(a)-angle(b);
 }));
 const selected=i=>p.getX(i)>=xs[0]&&p.getX(i)<=xs.at(-1)&&Math.hypot(p.getY(i),p.getZ(i))>2;
 const result=[];let removed=0;
 for(let k=0;k<ix.length;k+=3){const t=[ix[k],ix[k+1],ix[k+2]];if(t.every(selected))removed++;else result.push(...t)}
 const normal=g.attributes.normal;
 function push(a,b,c){
  const ab=[p.getX(b)-p.getX(a),p.getY(b)-p.getY(a),p.getZ(b)-p.getZ(a)],ac=[p.getX(c)-p.getX(a),p.getY(c)-p.getY(a),p.getZ(c)-p.getZ(a)];
  const face=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]];
  const dot=face[0]*(normal.getX(a)+normal.getX(b)+normal.getX(c))+face[1]*(normal.getY(a)+normal.getY(b)+normal.getY(c))+face[2]*(normal.getZ(a)+normal.getZ(b)+normal.getZ(c));result.push(...(dot>=0?[a,b,c]:[a,c,b]));
 }
 for(let j=0;j<rings.length-1;j++){const a=rings[j],b=rings[j+1];for(let k=0;k<a.length;k++){const next=(k+1)%a.length;push(a[k],a[next],b[next]);push(a[k],b[next],b[k]);}}
 if(removed!==10752||ix.length/3-result.length/3!==5376)throw Error('Unexpected crown patch size');
 const candidate=g.clone();candidate.setIndex(result);candidate.computeBoundingBox();candidate.computeBoundingSphere();return candidate;
}
