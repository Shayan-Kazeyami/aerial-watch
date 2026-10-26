import * as THREE from './vendor/three.module.js';

/** Authored R05/R07 Boolean replacements; all swaps are private and reversible.
 * targets: Map<number,Mesh> for current displayed plates0/155 and real calendar149.
 * Both scenes must use the same glTF assembly-space mount (not world matrices).
 */
export function createFrontArchitecture({targets,candidateScene,revision}) {
  const candidates=new Map(),revisions=new Set();
  if(revision!==undefined&&!['r05','r07'].includes(revision))throw new Error('Unsupported front architecture revision.');
  candidateScene.traverse(mesh=>{
    const index=mesh.userData?.replacementForSourceIndex;
    if(mesh.isMesh&&[0,155,149].includes(index)) {
      if(candidates.has(index))throw new Error(`Duplicate front architecture source${index}`);
      const expected=index===149?'BLANK-CALENDAR':'FRONT-ARCHITECTURE';
      const match=/^(R05|R07)-(.+)$/.exec(mesh.userData.designPart||'');
      if(!match||match[2]!==expected)throw new Error(`Invalid authored front architecture metadata for source${index}`);
      revisions.add(match[1].toLowerCase());
      candidates.set(index,mesh);
    }
  });
  if(candidates.size!==3)throw new Error('Front architecture requires authored plate0,plate155 and blank calendar149.');
  if(revisions.size!==1)throw new Error('Mixed front architecture revisions.');
  const selectedRevision=[...revisions][0];
  if(revision&&revision!==selectedRevision)throw new Error('Front architecture revision does not match candidate metadata.');
  const rows=[];
  try {
    for(const index of [0,155,149]) {
      const target=targets.get(index),candidate=candidates.get(index);
      if(!target?.isMesh)throw new Error(`Missing front architecture target${index}`);
      target.updateMatrix();candidate.updateMatrix();
      const geometry=candidate.geometry.clone().applyMatrix4(new THREE.Matrix4().copy(target.matrix).invert().multiply(candidate.matrix));
      geometry.clearGroups();geometry.computeBoundingBox();geometry.computeBoundingSphere();
      rows.push({index,target,geometry,original:target.geometry});
    }
  }catch(error){for(const row of rows)row.geometry.dispose();throw error;}
  let enabled=false,disposed=false;
  return {
    audit:{revision:selectedRevision,replacementIndices:rows.map(row=>row.index),calendar:'Actual blank top machined at nativeZ2.099; original gear teeth retained',construction:selectedRevision==='r07'?'Five rounded rim-following windows with extended wheel99 arc and smooth source155 perimeter; original bearing/support reserves retained':'Five small wheel-concentric rounded slots and smooth source155 perimeter; native bearing reserves retained',raisedLip:{innerRadiusMM:9.30,outerRadiusMM:10.80,bottomNativeZMM:2.18,topNativeZMM:2.32,calendarNominalGapMM:.081,correctorNominalGapMM:.020},clearance:{scope:'Static native-pose added-stock sampling only',addedStockSamples:selectedRevision==='r07'?2775:3024,sampledOverlapCount:0,fullMotionValidated:false},physicalValidation:false},
    get enabled(){return enabled;},
    setEnabled(value){if(disposed)return;enabled=!!value;for(const row of rows)row.target.geometry=enabled?row.geometry:row.original;},
    dispose(){if(disposed)return;for(const row of rows){row.target.geometry=row.original;row.geometry.dispose();}disposed=true;enabled=false;},
  };
}



