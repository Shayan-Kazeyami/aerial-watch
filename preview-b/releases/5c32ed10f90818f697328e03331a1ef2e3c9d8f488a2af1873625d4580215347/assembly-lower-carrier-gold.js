import {BufferAttribute} from './vendor/three.module.js';
export const LOWER_CARRIER_GOLD=Object.freeze({revision:'lower-carrier-gold-zone-r01',assetSHA256:'3e3bff2e0b56c4e67633f1ff64e49aa5375ae524ed04ec9e3fff2aaf468d9623',replacementForSourceIndex:0,watchYBoundaryMM:-4.9,materials:Object.freeze(['satin','brass'])});
/** Default only on the selected premium design with SHA-audited restored stock.
 * Explicit off/unknown modes are fail-closed; legacy/source comparisons unchanged.
 */
export function lowerCarrierGoldRequested({premiumRequested=false,comparison='restored',mode=null}={}){
 return !!premiumRequested&&comparison==='restored'&&(mode===null||mode==='lower');
}
/** Finish-zone subdivision only. Does not move source vertices or change source
 * geometry; crossing triangles are linearly subdivided on their same plane.
 * Caller owns returned geometry; original must remain available for rollback.
 * Apply only to the SHA-verified retained-stock carrier, NOT original source0.
 */
export function lowerCarrierGoldGeometry(mesh){
 const g=mesh.geometry,p=g?.attributes?.position;
 if(mesh.userData?.replacementForSourceIndex!==0||mesh.userData?.designPart!=='OPEN-MAINPLATE')throw Error('Lower gold requires retained OPEN-MAINPLATE carrier0');
 if(!g.index||!p||g.morphAttributes&&Object.keys(g.morphAttributes).length)throw Error('Unsupported carrier geometry');
 mesh.updateMatrix();const m=mesh.matrix.elements;
 // Existing glTF carrier is translation only; parent rotates +pi/2 about X.
 for(let i=0;i<16;i++)if(![12,13,14].includes(i)&&Math.abs(m[i]-(i%5===0?1:0))>1e-9)throw Error('Carrier coordinate frame changed');
 const boundary=-LOWER_CARRIER_GOLD.watchYBoundaryMM-m[14];
 const attrs=Object.entries(g.attributes),values=new Map();
 for(const [name,a]of attrs){if(a.isInterleavedBufferAttribute||a.normalized||a.count!==p.count)throw Error('Unsupported carrier attribute '+name);values.set(name,Array.from(a.array));}
 const positions=values.get('position'),distance=i=>positions[i*3+2]-boundary;
 const cuts=new Map(),indices=[[],[]];let crossed=0;
 function cut(a,b){
  const key=a<b?`${a}:${b}`:`${b}:${a}`;if(cuts.has(key))return cuts.get(key);
  const da=distance(a),db=distance(b),t=da/(da-db),id=positions.length/3;
  for(const[name,attribute]of attrs){const array=values.get(name),size=attribute.itemSize;for(let k=0;k<size;k++)array.push(array[a*size+k]+t*(array[b*size+k]-array[a*size+k]));}
  cuts.set(key,id);return id;
 }
 function clip(tri,gold){const out=[];for(let k=0;k<3;k++){const a=tri[k],b=tri[(k+1)%3],ain=gold?distance(a)>=0:distance(a)<=0,bin=gold?distance(b)>=0:distance(b)<=0;if(ain)out.push(a);if(ain!==bin)out.push(cut(a,b));}return out;}
 for(let i=0;i<g.index.count;i+=3){const tri=[g.index.getX(i),g.index.getX(i+1),g.index.getX(i+2)],d=tri.map(distance);if(d.every(x=>x>=0)){indices[1].push(...tri);continue;}if(d.every(x=>x<=0)){indices[0].push(...tri);continue;}crossed++;for(let side=0;side<2;side++){const polygon=clip(tri,!!side);for(let k=1;k+1<polygon.length;k++)indices[side].push(polygon[0],polygon[k],polygon[k+1]);}}
 const out=g.clone();
 for(const[name,a]of attrs)out.setAttribute(name,new BufferAttribute(new a.array.constructor(values.get(name)),a.itemSize,false));
 out.setIndex(new BufferAttribute(new Uint32Array([...indices[0],...indices[1]]),1));out.clearGroups();out.addGroup(0,indices[0].length,0);out.addGroup(indices[0].length,indices[1].length,1);out.computeBoundingBox();out.computeBoundingSphere();
 out.userData={...g.userData,lowerCarrierGold:{...LOWER_CARRIER_GOLD,sourceVertices:p.count,sourceTriangles:g.index.count/3,splitTriangles:crossed,addedVertices:positions.length/3-p.count,goldTriangles:indices[1].length/3,silverTriangles:indices[0].length/3}};
 return out;
}
/** Own derived geometry only; material library retains ownership of materials.
 * Register disposal after proposal ownership so reverse teardown restores source.
 */
export function createLowerCarrierGoldZone(mesh,goldMaterial,{requestMode='lower'}={}){
 const original=mesh.geometry,derived=lowerCarrierGoldGeometry(mesh);let disposed=false,active=false;
 return {mesh,original,derived,
  get snapshot(){return {requested:true,requestMode,policy:'lower-gold-default-premium-r01',active,disposed,...derived.userData.lowerCarrierGold};},
  apply(base,{enabled=false}={}){
   if(disposed)return base;
   const compatible=mesh.geometry===original||mesh.geometry===derived;
   active=!!enabled&&compatible;
   if(active){mesh.geometry=derived;return [base,goldMaterial];}
   if(mesh.geometry===derived)mesh.geometry=original;
   return base;
  },
  dispose(){if(disposed)return;disposed=true;active=false;if(mesh.geometry===derived)mesh.geometry=original;derived.dispose();},
 };
}
