// Render-only batching: source meshes remain authoritative for interaction and animation.
export function createMechanismBatch({THREE,scene,renderer,maxBytes=32*1024*1024}){
 let built=false,disposed=false,enabled=true;const batches=[],hidden=[];
 const audit={supported:!!renderer.extensions?.has('WEBGL_multi_draw'),meshes:0,batches:0,bufferBytes:0,reason:null};
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
   const first=list[0],vertices=list.reduce((n,m)=>n+m.geometry.attributes.position.count,0),indices=list.reduce((n,m)=>n+(m.geometry.index?.count||0),0);
   const batch=new THREE.BatchedMesh(list.length,vertices,indices,first.material);
   batch.name='Mechanism render batch';batch.castShadow=first.castShadow;batch.receiveShadow=first.receiveShadow;batch.renderOrder=first.renderOrder;batch.layers.mask=first.layers.mask;batch.frustumCulled=false;batch.visible=false;
   const entries=list.map(mesh=>({mesh,geometry:mesh.geometry,matrix:null,id:batch.addInstance(batch.addGeometry(mesh.geometry))}));
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

    for(const entry of entries){const {mesh,geometry,id}=entry;let visible=count>0&&mesh.visible&&mesh.geometry===geometry&&mesh.material===batch.material&&!mesh.material.transparent&&!(mesh.material.transmission>0)&&mesh.matrixWorld.determinant()>0;
     for(let p=mesh.parent;p&&visible;p=p.parent)visible=p.visible;
     batch.setVisibleAt(id,visible);
     if(visible){
      // Exact equality only: static instances must not dirty the matrix texture.
      const elements=mesh.matrixWorld.elements,previous=entry.matrix;
      if(!previous||elements.some((value,index)=>value!==previous[index])){
       batch.setMatrixAt(id,mesh.matrixWorld);
       entry.matrix??=new Float64Array(16);entry.matrix.set(elements);
      }
      hidden.push(mesh);mesh.visible=false;any=true;}
    }
    batch.visible=any;
   }
  },afterRender:restore,
  snapshot(){return {...audit,enabled};},
  dispose(){if(disposed)return;restore();disposed=true;for(const {batch} of batches){batch.removeFromParent();batch.dispose();}batches.length=0;}
 };
}
