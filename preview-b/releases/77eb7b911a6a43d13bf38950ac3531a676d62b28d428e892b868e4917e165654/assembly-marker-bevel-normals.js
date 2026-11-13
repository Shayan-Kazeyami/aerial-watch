import {BufferAttribute,Vector3} from './vendor/three.module.js';

// The seven authored hour markers already have a three-step rounded bevel.
// Repair only its split per-face normals. Never move/weld vertices or alter
// the cap, vertical flats, indices, chamfer width, or approved silhouette.
export function createMarkerBevelNormals(mesh){
 if(!/^SVG[ _]hour-\d{2}$/.test(mesh?.name)||!mesh.geometry?.attributes.normal)
  throw new TypeError('Expected authored SVG hour marker');
 const geometry=mesh.geometry,p=geometry.attributes.position,original=geometry.attributes.normal,index=geometry.index;
 const groups=new Map(),normal=new Vector3(),a=new Vector3(),b=new Vector3(),c=new Vector3();
 for(let i=0;i<p.count;i++){
  const key=[p.getX(i),p.getY(i),p.getZ(i)].map(v=>Math.round(v*1e6)).join(',');
  if(!groups.has(key))groups.set(key,[]);groups.get(key).push(i);
 }
 const sums=Array.from({length:p.count},()=>new Vector3()),count=index?.count??p.count;
 for(let i=0;i<count;i+=3){
  const ids=[0,1,2].map(k=>index?index.getX(i+k):i+k);
  for(let corner=0;corner<3;corner++){
   const id=ids[corner];a.fromBufferAttribute(p,id);b.fromBufferAttribute(p,ids[(corner+1)%3]).sub(a);c.fromBufferAttribute(p,ids[(corner+2)%3]).sub(a);
   const angle=b.angleTo(c);normal.fromBufferAttribute(original,id);sums[id].addScaledVector(normal,angle);
  }
 }
 const repaired=original.array.slice();let changed=0;
 for(const ids of groups.values())for(const id of ids){
  const y=original.getY(id);if(Math.abs(y)<1e-5||Math.abs(y)>.99999)continue;
  const sameHemisphere=ids.filter(other=>original.getY(other)*y>=-1e-5);
  const caps=sameHemisphere.filter(other=>Math.abs(original.getY(other))>.99999);
  const sides=sameHemisphere.filter(other=>Math.abs(original.getY(other))<1e-5);
  // Exact cap/side tangent at the terminal ring; interpolate interior rings
  // with corner-angle weighting, independent of triangulation fan density.
  const neighbors=caps.length?caps:sides.length?sides:sameHemisphere;
  normal.set(0,0,0);for(const other of neighbors)normal.add(sums[other]);normal.normalize();
  if(!Number.isFinite(normal.x)||normal.lengthSq()<.99)throw new Error('Invalid marker bevel normal');
  repaired.set(normal.toArray(),id*3);changed++;
 }
 const smooth=new BufferAttribute(repaired,3),audit={name:mesh.name,changedVertices:changed,vertexCount:p.count,scope:'bevel normals only; caps/sides/positions/indices unchanged'};
 return {audit,setEnabled(enabled){geometry.setAttribute('normal',enabled?smooth:original);},original,smooth};
}
