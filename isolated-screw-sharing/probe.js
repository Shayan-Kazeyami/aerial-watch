window.screwQa={
 setup(){
  const m=exterior.filter(x=>/^BACK-SCREW-[0-5]$/.test(x.userData.assemblyId||'')).sort((a,b)=>a.userData.assemblyId.localeCompare(b.userData.assemblyId));if(m.length!==6)throw Error('expected six exterior screw meshes, got '+m.length);this.meshes=m;this.original=m.map(x=>({p:x.geometry.attributes.position,n:x.geometry.attributes.normal,u:x.geometry.attributes.uv,g:x.geometry,id:x.userData.assemblyId,name:x.name,mat:x.material}));
  for(const x of m){for(const a of ['position','normal','uv'])if(!x.geometry.attributes[a])throw Error('missing '+a);}
  for(const k of ['p','n'])for(const x of this.original){const a=x[k].array,b=this.original[0][k].array;if(a.length!==b.length||!a.every((v,i)=>Object.is(v,b[i])))throw Error(k+' mismatch');}
  if(new Set(this.original.map(x=>x.u)).size!==6)throw Error('UV references not distinct');
  for(const id of ['animate','animate-movement']){const e=$(id);if(e){e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}}stopTour();cameraTween=null;return {ids:m.map(x=>x.userData.assemblyId),beforeObjects:{position:new Set(this.original.map(x=>x.p)).size,normal:new Set(this.original.map(x=>x.n)).size,uv:new Set(this.original.map(x=>x.u)).size},byteLength:this.original[0].p.array.byteLength+this.original[0].n.array.byteLength};
 },
 setShared(on){for(let i=0;i<6;i++){let x=this.original[i],g=x.g;g.setAttribute('position',on?this.original[0].p:x.p);g.setAttribute('normal',on?this.original[0].n:x.n);if(g.attributes.uv!==x.u||this.meshes[i].geometry!==g||this.meshes[i].userData.assemblyId!==x.id)throw Error('identity changed');}dirty=true;},
 async capture({shared,explode,dispose}){
  this.setShared(shared);$('finish').checked=true;updateMaterials();visibility();registerExplosionParts();explosion.setAmount(explode,{instant:true});scene.updateMatrixWorld(true);
  const center=new THREE.Vector3();for(const m of this.meshes){const p=new THREE.Vector3();m.getWorldPosition(p);center.add(p)}center.multiplyScalar(1/6);controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(0,-80,0));camera.up.set(0,0,-1);camera.lookAt(center);camera.updateProjectionMatrix();controls.update();
  if(dispose)this.meshes[1].geometry.dispose();renderer.info.reset();for(let i=0;i<3;i++){mechanismBatch.build(source);try{mechanismBatch.beforeRender();composer.render()}finally{mechanismBatch.afterRender()}};
  let refs={position:new Set(this.meshes.map(m=>m.geometry.attributes.position)).size,normal:new Set(this.meshes.map(m=>m.geometry.attributes.normal)).size,uv:new Set(this.meshes.map(m=>m.geometry.attributes.uv)).size};let rows=this.meshes.map(m=>({id:m.userData.assemblyId,name:m.name,world:m.matrixWorld.elements.slice(),uv:m.geometry.attributes.uv.array.length,visible:m.visible}));return {refs,rows,render:{...renderer.info.render},memory:{...renderer.info.memory},png:renderer.domElement.toDataURL('image/png')};
 }
};
