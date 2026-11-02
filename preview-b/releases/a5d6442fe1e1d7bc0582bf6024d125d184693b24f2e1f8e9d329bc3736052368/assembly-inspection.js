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

// Explicit display-only suppression. Run after ordinary source/craft visibility.
// Ancestor metadata covers crafted stitching, lining, straps and buckle children.
export function isStrapInspectionPart(object){
 for(let part=object;part;part=part.parent){const d=part.userData||{};if(/^(STRAP(?:-|$)|SPRINGBAR(?:-|$)|KEEPER(?:-|$)|BUCKLE(?:-|$))/.test(d.replacesAssemblyId||d.assemblyId||'')||['QUALITY-STRAP','QUALITY-STITCH'].includes(d.designPart))return true;}
 return false;
}
export function applyStrapInspectionVisibility(root,{hideStrap=false}={}){if(!hideStrap||!root)return;root.traverse(part=>{if(part.isMesh&&isStrapInspectionPart(part))part.visible=false;});}
export function strapInspectionAvailable({view,interior=false,isolated=false,exploded=false}={}){return !interior&&!isolated&&(view==='back'||exploded);}

export function strapInspectionSnapshot(root){const parts=[];root?.traverse(part=>{if(!part.isMesh||!isStrapInspectionPart(part))return;let visible=true;for(let p=part;p;p=p.parent)visible=visible&&p.visible;parts.push({name:part.name,assemblyId:part.userData.assemblyId??part.userData.replacesAssemblyId??null,visible,geometry:part.geometry?.uuid});});return {visibleParts:parts.filter(p=>p.visible).length,hiddenParts:parts.filter(p=>!p.visible).length,parts,scope:'Display-only strap, spring bars, keepers, buckle and authored stitching; no geometry or cover changes'};}

// Physical wire lines can produce non-finite HDR samples. Bloom's blur spreads
// them over the canvas; this display-only view does not need an optical glow.
// Derive the return state from the current profile, never a cached toggle value.
export function inspectionBloomEnabled(studio, {wireframe=false}={}) {
  return !!studio&&!wireframe;
}
