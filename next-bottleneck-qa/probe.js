window.bottleneckQA={
 freeze(){for(const id of ['animate','animate-movement']){const e=$(id);if(e){e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}}stopTour();dirty=true;},
 async sample({batch=true,profile='efficient',explode=0,finish=true}={}){
  $('finish').checked=finish;updateMaterials();visibility();renderingQuality(profile);explosion.setAmount(explode,{instant:true});mechanismBatch?.setEnabled(batch);
  const previous=renderer.info.render.frame;dirty=true;await new Promise(resolve=>{const wait=()=>renderer.info.render.frame>previous?resolve():requestAnimationFrame(wait);requestAnimationFrame(wait)});
  const rows=source.map(m=>({name:m.name,triangles:(m.geometry.index?.count??m.geometry.attributes.position.count)/3,visible:m.visible,material:m.material.uuid,materialType:m.material.type,transparent:m.material.transparent}));
  return {batch:mechanismBatch?.snapshot(),profile,explode,finish,render:{...renderer.info.render},memory:{...renderer.info.memory},rows};
 }
};
