import {hardwareCanonicalReuse} from '/hardware-reuse-qa/canonical-data.js';
// Render-only batching: source meshes remain authoritative for interaction and animation.
export function createMechanismBatch({THREE,scene,renderer,maxBytes=32*1024*1024}){
 let built=false,disposed=false,enabled=true;const batches=[],hidden=[];
 // BatchedMesh copies source buffers. Attribute identity is part of invalidation,
 // because replacing an attribute may restart its version at zero.
 const geometryState=g=>({index:g.index,attributes:Object.entries(g.attributes).map(([name,a])=>[name,a,a.version]),indexVersion:g.index?.version,groups:JSON.stringify(g.groups),drawStart:g.drawRange.start,drawCount:g.drawRange.count});
 const geometryMatches=(g,s)=>g.index===s.index&&g.index?.version===s.indexVersion&&Object.keys(g.attributes).length===s.attributes.length&&s.attributes.every(([name,a,v])=>g.attributes[name]===a&&a.version===v)&&JSON.stringify(g.groups)===s.groups&&g.drawRange.start===s.drawStart&&g.drawRange.count===s.drawCount;
 const corrections=new Map(hardwareCanonicalReuse.map(r=>[r.sourceIndex,r]));
 const audit={reusedEntries:0,rejectedReuse:0,canonicalGeometryCount:0,allocatedGeometryBufferBytes:0,originalGeometryBufferBytes:0,supported:!!renderer.extensions?.has('WEBGL_multi_draw'),meshes:0,batches:0,bufferBytes:0,reason:null};
 function build(source){
  if(built||disposed||!source.length)return;built=true;
  if(!audit.supported){audit.reason='WEBGL_multi_draw unavailable';return;}
  const groups=new Map();
  for(const mesh of source){const g=mesh.geometry,m=mesh.material;
   if(!g?.attributes.position||Array.isArray(m)||m.transparent||m.transmission>0||mesh.isSkinnedMesh||mesh.isInstancedMesh||g.morphAttributes.position?.length||g.groups.length||g.drawRange.start!==0||Number.isFinite(g.drawRange.count))continue;
   if(Object.values(g.attributes).some(a=>a.isInterleavedBufferAttribute))continue;
   const signature=JSON.stringify([m.uuid,!!g.index,mesh.castShadow,mesh.receiveShadow,mesh.renderOrder,mesh.layers.mask,Object.entries(g.attributes).map(([n,a])=>[n,a.itemSize,a.normalized,a.array.constructor.name])]);
   if(!groups.has(signature))groups.set(signature,[]);groups.get(signature).push(mesh);
  }
  for(const list of groups.values()){
   if(list.length<8)continue;
   const bytes=list.reduce((n,m)=>n+Object.values(m.geometry.attributes).reduce((s,a)=>s+a.array.byteLength,0)+(m.geometry.index?.array.byteLength||0),0);
   if(audit.bufferBytes+bytes>maxBytes)continue;
   const bySource=new Map(list.map(mesh=>[mesh.userData.sourceIndex,mesh]));
   const plan=list.map(mesh=>{
    const row=corrections.get(mesh.userData.sourceIndex),canonical=row&&bySource.get(row.canonical);
    if(!canonical)return {mesh,geometry:mesh.geometry,renderGeometry:mesh.geometry,correction:null};
    const a=canonical.geometry,b=mesh.geometry,pa=a.attributes.position,pb=b.attributes.position,na=a.attributes.normal,nb=b.attributes.normal;
    const keys=Object.keys(a.attributes).sort().join(',');
    let valid=keys===Object.keys(b.attributes).sort().join(',')&&keys==='normal,position'&&pa.count===pb.count&&na?.count===nb?.count&&a.index?.count===b.index?.count;
    if(valid)for(let i=0;i<a.index.count;i++)if(a.index.getX(i)!==b.index.getX(i)){valid=false;break;}
    const correction=new THREE.Matrix4().fromArray(row.matrix),p=new THREE.Vector3(),n=new THREE.Vector3(),normalMatrix=new THREE.Matrix3().getNormalMatrix(correction),other=new THREE.Vector3();
    let maxPosition=0,maxNormal=0;
    if(valid)for(let i=0;i<pa.count;i++){
     p.fromBufferAttribute(pa,i).applyMatrix4(correction);maxPosition=Math.max(maxPosition,p.distanceTo(other.fromBufferAttribute(pb,i)));
     n.fromBufferAttribute(na,i).applyMatrix3(normalMatrix);maxNormal=Math.max(maxNormal,n.distanceTo(other.fromBufferAttribute(nb,i)));
    }
    valid=valid&&maxPosition<=2e-6&&maxNormal<=.001;
    if(!valid){audit.rejectedReuse++;return {mesh,geometry:mesh.geometry,renderGeometry:mesh.geometry,correction:null};}
    audit.reusedEntries++;return {mesh,geometry:mesh.geometry,renderGeometry:a,canonical,correction,maxPosition,maxNormal,
     originalVersions:[pa.version,na.version,a.index.version,pb.version,nb.version,b.index.version]};
   });
   const unique=[...new Set(plan.map(e=>e.renderGeometry))];
   const first=list[0],vertices=unique.reduce((n,g)=>n+g.attributes.position.count,0),indices=unique.reduce((n,g)=>n+(g.index?.count||0),0);
   audit.canonicalGeometryCount+=unique.length;
   const oldVertices=list.reduce((n,m)=>n+m.geometry.attributes.position.count,0),oldIndices=list.reduce((n,m)=>n+(m.geometry.index?.count||0),0);
   audit.originalGeometryBufferBytes+=oldVertices*24+oldIndices*(oldVertices>65535?4:2);
   const batch=new THREE.BatchedMesh(list.length,vertices,indices,first.material);
   batch.name='Mechanism render batch';batch.castShadow=first.castShadow;batch.receiveShadow=first.receiveShadow;batch.renderOrder=first.renderOrder;batch.layers.mask=first.layers.mask;batch.frustumCulled=false;batch.visible=false;
   const ids=new Map();for(const g of unique)ids.set(g,batch.addGeometry(g));
     const entries=plan.map(e=>({...e,sourceState:geometryState(e.geometry),canonicalState:e.canonical?geometryState(e.renderGeometry):null,renderMatrix:new THREE.Matrix4(),versions:[...Object.values(e.geometry.attributes).map(a=>a.version),e.geometry.index?.version],id:batch.addInstance(ids.get(e.renderGeometry))}));
   audit.allocatedGeometryBufferBytes+=Object.values(batch.geometry.attributes).reduce((n,a)=>n+a.array.byteLength,0)+(batch.geometry.index?.array.byteLength||0);
   scene.add(batch);batches.push({batch,entries});audit.meshes+=list.length;audit.bufferBytes+=bytes;
  }
  audit.batches=batches.length;
 }
 function restore(){for(const mesh of hidden)mesh.visible=true;hidden.length=0;for(const {batch} of batches)batch.visible=false;}
 return {
  build,setEnabled(value){enabled=!!value;},
  beforeRender(){
   if(disposed||!enabled||!batches.length)return;
   scene.updateMatrixWorld(true);
   for(const {batch,entries} of batches){let any=false;
    // Finish/inspection modes may replace materials without changing geometry.
    // Reuse the existing buffers for the largest compatible material cohort;
    // exceptions stay on their original meshes and retain their exact material.
    const cohorts=new Map();
    for(const {mesh,geometry} of entries){const m=mesh.material;
     if(mesh.geometry!==geometry||Array.isArray(m)||!m||m.transparent||m.transmission>0)continue;
     cohorts.set(m,(cohorts.get(m)||0)+1);
    }
    let count=0;for(const [material,n] of cohorts)if(n>count){batch.material=material;count=n;}

    for(const entry of entries){const {mesh,geometry,id,canonical,renderGeometry,correction,originalVersions,renderMatrix,sourceState,canonicalState,versions:sourceVersions}=entry;let visible=count>0&&mesh.visible&&mesh.geometry===geometry&&mesh.material===batch.material&&!mesh.material.transparent&&!(mesh.material.transmission>0)&&mesh.matrixWorld.determinant()>0;
     for(let p=mesh.parent;p&&visible;p=p.parent)visible=p.visible;
     if(visible)visible=geometryMatches(geometry,sourceState);
     if(visible&&correction){
      const a=canonical.geometry,b=mesh.geometry;
      const versions=[a.attributes.position?.version,a.attributes.normal?.version,a.index?.version,b.attributes.position?.version,b.attributes.normal?.version,b.index?.version];
      visible=a===renderGeometry&&geometryMatches(a,canonicalState)&&versions.every((v,i)=>v===originalVersions[i]);
     }
     batch.setVisibleAt(id,visible);
     if(visible){batch.setMatrixAt(id,correction?renderMatrix.multiplyMatrices(mesh.matrixWorld,correction):mesh.matrixWorld);hidden.push(mesh);mesh.visible=false;any=true;}
    }
    batch.visible=any;
   }
  },afterRender:restore,
  snapshot(){return {...audit,enabled,entries:batches.flatMap(({batch,entries})=>entries.filter(e=>e.correction).map(e=>({sourceIndex:e.mesh.userData.sourceIndex,canonical:e.canonical.userData.sourceIndex,instanceId:e.id,maxPositionErrorMM:e.maxPosition,maxNormalError:e.maxNormal,lastInstanceVisible:batch.getVisibleAt(e.id)}))) };},
  dispose(){if(disposed)return;restore();disposed=true;for(const {batch} of batches){batch.removeFromParent();batch.dispose();}batches.length=0;}
 };
}
