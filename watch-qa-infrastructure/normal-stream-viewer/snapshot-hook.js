// QA copy only: read existing state, do not trigger render/retry/adoption or change scene.
window.__normalStreamViewerQA=()=>({
 detail:currentCaptureDetail(),configuration:captureConfiguration(),inspect:window.assemblyInspect(),
 bindings:(leatherDetails?.meshes??[]).filter(mesh=>{
  const m=finishMaterials.get(mesh);return m&&/^leather \/ /i.test(m.name)&&/R14/.test(m.name)
 }).map(mesh=>({name:mesh.name,visible:mesh.visible,effectiveVisible:(()=>{for(let p=mesh;p;p=p.parent)if(!p.visible)return false;return true})(),materials:(Array.isArray(mesh.material)?mesh.material:[mesh.material]).map(m=>({name:m.name,normalUUID:m.normalMap?.uuid??null,width:m.normalMap?.image?.width??null,height:m.normalMap?.image?.height??null,mipLevels:m.normalMap?.mipmaps?.length??null,normalScale:m.normalScale?.toArray?.()??null}))}))
});
