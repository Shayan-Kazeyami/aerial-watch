// Private bounded candidate: original OM00-00114 source #12 upper spherical cap.
// Coordinates fitted separately to authoring and rotated/recentered delivery
// tessellations: max sampled radial residual < 2e-9 / 4.7e-8 mm respectively.
// No positions, indices, bounds, hard-edge side/fillet normals or transforms change.
// Exact decoded-buffer fixtures, independently SHA-256 verified by delivery tests.
// FNV checks are inexpensive runtime drift guards, not cryptographic integrity.
export const FRONT_CAP_NORMAL_REVISION='front-cap-sphere-two-frames-r02';
export const FRONT_CAP_NORMAL_FIXTURES=Object.freeze([
 Object.freeze({id:'authoring-aerial',center:Object.freeze([.000037476722233088946,-2.8300000777108076,-.00012824618492631522]),radius:2.9000000764766902,position:'5d224624',normal:'c676364f',index:'a448b771'}),
 Object.freeze({id:'rebuild-delivery',center:Object.freeze([.0001281499862512017,-2.8299941850594315,.00003815311405599219]),radius:2.8999940825687185,position:'b9db03d8',normal:'4bbb942d',index:'0b848819'}),
]);
function fingerprint(array){let hash=2166136261;for(const value of new Uint8Array(array.buffer,array.byteOffset,array.byteLength))hash=Math.imul(hash^value,16777619)>>>0;return hash.toString(16).padStart(8,'0');}
export function repairFrontCapNormals(mesh){
 if(mesh?.userData?.sourceIndex!==12||mesh.userData.partNumber!=='OM00-00114')return {applied:false,reason:'identity'};
 const g=mesh.geometry,p=g?.getAttribute('position'),n=g?.getAttribute('normal'),idx=g?.index;
 if(!p||!n||!idx||p.isInterleavedBufferAttribute||n.isInterleavedBufferAttribute||p.count!==4076||n.count!==4076||idx.count!==22503)return {applied:false,reason:'fixture'};
 const buffers={position:fingerprint(p.array),normal:fingerprint(n.array),index:fingerprint(idx.array)};
 const fixture=FRONT_CAP_NORMAL_FIXTURES.find(f=>f.position===buffers.position&&f.normal===buffers.normal&&f.index===buffers.index);
 if(!fixture)return {applied:false,reason:'buffer-fixture',buffers,revision:FRONT_CAP_NORMAL_REVISION};
 const CENTER=fixture.center,RADIUS=fixture.radius;
 const onSphere=i=>Math.abs(Math.hypot(p.getX(i)-CENTER[0],p.getY(i)-CENTER[1],p.getZ(i)-CENTER[2])-RADIUS)<1e-6;
 const vertices=new Set();let faces=0;
 for(let k=0;k<idx.count;k+=3){
  const ids=[idx.getX(k),idx.getX(k+1),idx.getX(k+2)];if(!ids.every(onSphere))continue;
  const a=ids.map(i=>[p.getX(i),p.getY(i),p.getZ(i)]),u=a[1].map((v,i)=>v-a[0][i]),v=a[2].map((v,i)=>v-a[0][i]);
  if(Math.hypot(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])<1e-12)continue;
  faces++;ids.forEach(i=>vertices.add(i));
 }
 if(faces!==170||vertices.size!==125)return {applied:false,reason:'surface-fixture',faces,vertices:vertices.size};
 const copy=g.clone(),normals=copy.getAttribute('normal');
 for(const i of vertices){const a=[p.getX(i)-CENTER[0],p.getY(i)-CENTER[1],p.getZ(i)-CENTER[2]],d=Math.hypot(...a);normals.setXYZ(i,...a.map(v=>v/d));}
 normals.needsUpdate=true;mesh.geometry=copy;
 return {applied:true,revision:FRONT_CAP_NORMAL_REVISION,fixture:fixture.id,buffers,faces,vertices:vertices.size,originalGeometry:g,geometry:copy};
}
