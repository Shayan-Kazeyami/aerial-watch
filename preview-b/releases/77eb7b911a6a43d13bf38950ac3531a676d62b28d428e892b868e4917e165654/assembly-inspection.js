import {Mesh,MeshBasicMaterial} from './vendor/three.module.js';
// Inspection variants own only cloned materials, never textures or geometry.
// Restore before the normal finish/selection pipeline replaces its materials.
export function createInspectionMaterials({cloneMaterial}) {
  let disposed=false;
  const entries=[],overlays=[];
  function restore(){
    for(const overlay of overlays){overlay.removeFromParent();overlay.material.dispose();}
    overlays.length=0;
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
    apply(root,{wireframe=false,solidWireframe=false,transparent=false,transparentBackplate=false}={}){
      restore();if(disposed||!root||(!wireframe&&!solidWireframe&&!transparent&&!transparentBackplate))return;
      const meshes=[];root.traverse(mesh=>{if(mesh.isMesh&&!mesh.userData.inspectionOverlay)meshes.push(mesh);});
      for(const mesh of meshes){
        if(!mesh.material)continue;
        const opticalShell=['FRONT-CRYSTAL','REAR-CRYSTAL'].includes(mesh.userData.assemblyId);
        const clearCover=transparentBackplate&&mesh.userData.assemblyId==='CASEBACK-INSERT';
        const clear=transparent||clearCover||(solidWireframe&&opticalShell);
        if(!wireframe&&!solidWireframe&&!clear)continue;
        const original=mesh.material,variant=cloneMaterial(original),castShadow=mesh.castShadow;
        for(const material of Array.isArray(variant)?variant:[variant]){
          if(wireframe){material.wireframe=true;if('transmission'in material)material.transmission=0;}
          if(clear){material.transparent=true;material.opacity=opticalShell&&(solidWireframe||transparent)?0:clearCover?.12:.22;material.depthWrite=false;if('transmission'in material)material.transmission=0;}
          if(transparent){if('metalness'in material)material.metalness=0;if('roughness'in material)material.roughness=1;if('clearcoat'in material)material.clearcoat=0;if('envMapIntensity'in material)material.envMapIntensity=.15;}
          if(solidWireframe){material.polygonOffset=true;material.polygonOffsetFactor=1;material.polygonOffsetUnits=1;}
          material.needsUpdate=true;
        }
        mesh.material=variant;if(clear)mesh.castShadow=false;
        entries.push({mesh,original,variant,castShadow});
        if(solidWireframe&&!opticalShell){
          const edgeMaterial=new MeshBasicMaterial({color:0x6c9098,wireframe:true,transparent:true,opacity:.55,depthWrite:false,toneMapped:false});
          const overlay=new Mesh(mesh.geometry,edgeMaterial);
          overlay.name='Inspection triangle overlay';overlay.userData.inspectionOverlay=true;
          overlay.raycast=()=>{};overlay.renderOrder=mesh.renderOrder+1;
          mesh.add(overlay);overlays.push(overlay);
        }
      }
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
export function inspectionBloomEnabled(studio, {wireframe=false,solidWireframe=false,transparent=false}={}) {
  return !!studio&&!wireframe&&!solidWireframe&&!transparent;
}
