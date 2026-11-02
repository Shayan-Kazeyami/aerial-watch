// Inspection variants own only cloned materials, never textures or geometry.
// Restore before the normal finish/selection pipeline replaces its materials.
export function createInspectionMaterials({cloneMaterial}) {
  let disposed=false;
  const entries=[];
  function restore(){
    for(const {mesh,original,variant,castShadow} of entries){
      // A newer async layer may already have supplied its own material.
      if(mesh.material===variant)mesh.material=original;
      mesh.castShadow=castShadow;
      for(const material of Array.isArray(variant)?variant:[variant])material.dispose();
    }
    entries.length=0;
  }
  return {
    restore,
    apply(root,{wireframe=false,transparentBackplate=false}={}){
      restore();if(disposed||!root||(!wireframe&&!transparentBackplate))return;
      root.traverse(mesh=>{
        if(!mesh.isMesh||!mesh.material)return;
        const clear=transparentBackplate&&mesh.userData.assemblyId==='CASEBACK-INSERT';
        if(!wireframe&&!clear)return;
        const original=mesh.material,variant=cloneMaterial(original),castShadow=mesh.castShadow;
        for(const material of Array.isArray(variant)?variant:[variant]){
          if(wireframe){material.wireframe=true;if('transmission'in material)material.transmission=0;}
          if(clear){material.transparent=true;material.opacity=.12;material.depthWrite=false;if('transmission'in material)material.transmission=0;}
          material.needsUpdate=true;
        }
        mesh.material=variant;if(clear)mesh.castShadow=false;
        entries.push({mesh,original,variant,castShadow});
      });
    },
    snapshot(){return {disposed,materialVariants:entries.length};},
    dispose(){if(disposed)return;restore();disposed=true;},
  };
}
