import * as THREE from './vendor/three.module.js';

/** Authored R05 Boolean replacements; all swaps are private and reversible.
 * targets: Map<number,Mesh> for current displayed plates0/155 and real calendar149.
 * Both scenes must use the same glTF assembly-space mount (not world matrices).
 */
export function createFrontArchitecture({targets,candidateScene}) {
  const candidates=new Map();
  candidateScene.traverse(mesh=>{
    const index=mesh.userData?.replacementForSourceIndex;
    if(mesh.isMesh&&[0,155,149].includes(index)) {
      if(candidates.has(index))throw new Error(`Duplicate R05 source${index}`);
      candidates.set(index,mesh);
    }
  });
  if(candidates.size!==3)throw new Error('R05 requires authored plate0,plate155 and blank calendar149.');
  const rows=[];
  try {
    for(const index of [0,155,149]) {
      const target=targets.get(index),candidate=candidates.get(index);
      if(!target?.isMesh)throw new Error(`Missing R05 target${index}`);
      target.updateMatrix();candidate.updateMatrix();
      const geometry=candidate.geometry.clone().applyMatrix4(new THREE.Matrix4().copy(target.matrix).invert().multiply(candidate.matrix));
      geometry.clearGroups();geometry.computeBoundingBox();geometry.computeBoundingSphere();
      rows.push({index,target,geometry,original:target.geometry});
    }
  }catch(error){for(const row of rows)row.geometry.dispose();throw error;}
  let enabled=false,disposed=false;
  return {
    audit:{replacementIndices:rows.map(row=>row.index),calendar:'Actual blank top machined at nativeZ2.099; original gear teeth retained',construction:'Five small wheel-concentric rounded slots and smooth source155 perimeter; native bearing reserves retained',raisedLip:{innerRadiusMM:9.30,outerRadiusMM:10.80,bottomNativeZMM:2.18,topNativeZMM:2.32,calendarNominalGapMM:.081,correctorNominalGapMM:.020},clearance:{scope:'Static native-pose added-stock sampling only',addedStockSamples:3024,sampledOverlapCount:0,fullMotionValidated:false},physicalValidation:false},
    get enabled(){return enabled;},
    setEnabled(value){if(disposed)return;enabled=!!value;for(const row of rows)row.target.geometry=enabled?row.geometry:row.original;},
    dispose(){if(disposed)return;for(const row of rows){row.target.geometry=row.original;row.geometry.dispose();}disposed=true;enabled=false;},
  };
}



