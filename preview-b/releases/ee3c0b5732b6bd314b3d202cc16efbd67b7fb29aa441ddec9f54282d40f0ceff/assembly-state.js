// Source references, derived design visibility and owned GPU resources are
// separate boundaries. Visibility never changes a native transform or geometry.
export function partVisible(part,{isolated=false,selected=false,movementOnly=false,interior=false,
  openWork=false,replacedSources=new Set(),crystals=true}={}) {
  if(isolated)return selected;
  if(part.sourceIndex!==undefined)return !(openWork&&replacedSources.has(part.sourceIndex));
  return !movementOnly&&!(openWork&&part.assemblyId==='DIAL')&&
    (!interior||!/^(CASEBACK|BACK-SCREW|REAR-CRYSTAL|STRAP|SPRINGBAR|KEEPER|BUCKLE)/.test(part.assemblyId||''))&&
    (!part.inspectionTransparent||crystals);
}

export function createVariantManifest(source,derived=[]) {
  const ids=source.map(mesh=>mesh.userData.sourceIndex);
  if(source.length!==166||new Set(ids).size!==166||ids.some(id=>!Number.isInteger(id)||id<0||id>165))
    throw new Error('Expected all 166 immutable OM10 source IDs.');
  if(derived.some(mesh=>mesh.userData.sourceIndex!==undefined))throw new Error('Derived design must not impersonate an original source mesh.');
  return {units:'mm',CADToGLTF:'[-z,y,x]',sceneMount:'rotationX(+pi/2)',baseline:'rebuild/assembly.glb',
    originalSources:source.map(mesh=>({id:mesh.userData.sourceIndex,partNumber:mesh.userData.partNumber,name:mesh.name})).sort((a,b)=>a.id-b.id),
    derived:derived.map(mesh=>({id:mesh.userData.assemblyId||mesh.name,name:mesh.name,replacesSource:mesh.userData.replacementForSourceIndex??null}))};
}

export function createResourceScope() {
  const entries=[];let disposed=false;
  return {
    own(label,dispose){if(disposed)throw new Error('Resource scope is closed.');if(typeof dispose!=='function')throw new TypeError('Resource disposal callback required.');
      const entry={label,dispose,active:true};entries.push(entry);return ()=>{if(entry.active){entry.active=false;entry.dispose();}};},
    snapshot(){return {disposed,active:entries.filter(entry=>entry.active).map(entry=>entry.label)};},
    dispose(){if(disposed)return;disposed=true;const failures=[];
      for(const entry of entries.toReversed())if(entry.active){entry.active=false;try{entry.dispose();}catch(error){failures.push(error);}}
      if(failures.length)throw new AggregateError(failures,'Some scene resources could not be disposed.');},
  };
}

export function createObjectTreeDisposer(root) {
  const geometries=new Set(),materials=new Set(),textures=new Set();
  root.traverse(object=>{if(!object.isMesh)return;geometries.add(object.geometry);
    for(const material of Array.isArray(object.material)?object.material:[object.material])if(material){materials.add(material);for(const value of Object.values(material))if(value?.isTexture)textures.add(value);}});
  let disposed=false;
  return ()=>{
    if(disposed)return;disposed=true;
    const failures=[],attempt=dispose=>{try{dispose();}catch(error){failures.push(error);}};
    for(const value of [...geometries,...materials,...textures])attempt(()=>value.dispose());
    attempt(()=>root.removeFromParent());
    if(failures.length)throw new AggregateError(failures,'Some object resources could not be disposed.');
  };
}
export function disposeObjectTree(root) {createObjectTreeDisposer(root)();}
