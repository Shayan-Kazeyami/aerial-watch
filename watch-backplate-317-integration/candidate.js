import * as THREE from './vendor/three.module.js';

/** Rear cover proposal, NOT a movement bearing plate. Reuses the actual rear
 * window envelope and its machined caseback seat; never enters the mechanism.
 * Authored glTF space is millimetres with +Y toward the dial. */
export const BACKPLATE_LAYOUT=Object.freeze({diameterMM:31.44,bottomYMM:-3.65,topYMM:-3.35,
  seatRadiusMM:15.75,shoulderRadiusMM:15.40,radialClearanceMM:.03,
  shoulderOverlapMM:.32,minimumMovementYMM:-2.359999895095825,
  minimumAxialClearanceMM:.990000104904175,revision:'rear-cover-r01'});

export function backplateVisible({openWork=false,premium=false,interior=false,movementOnly=false,isolated=false}={}) {
  return openWork&&!interior&&!movementOnly&&!isolated;
}

// Explicit immutable borrow: source root retains geometry disposal ownership.
// Weak keys avoid extending source lifetime; one event listener retires all borrowers.
const borrowedSources=new WeakMap();
function borrowSource(geometry,onRetire){
  let state=borrowedSources.get(geometry);
  if(!state){state={retired:false,borrowers:new Set()};borrowedSources.set(geometry,state);
    geometry.addEventListener('dispose',()=>{state.retired=true;for(const retire of [...state.borrowers])retire();state.borrowers.clear();});}
  if(state.retired)throw new Error('Cannot borrow disposed rear-crystal geometry.');
  state.borrowers.add(onRetire);return ()=>state.borrowers.delete(onRetire);
}

export function createBackplate({rearCrystal,borrowImmutableGeometry=false}={}) {
  if(rearCrystal?.userData?.assemblyId!=='REAR-CRYSTAL'||!rearCrystal.isMesh||!rearCrystal.geometry?.attributes.position)
    throw new Error('Backplate requires the original REAR-CRYSTAL seat geometry.');
  const geometry=borrowImmutableGeometry?rearCrystal.geometry:rearCrystal.geometry.clone();
  const material=new THREE.MeshPhysicalMaterial({color:0xb9bec4,metalness:1,roughness:.38});
  const mesh=new THREE.Mesh(geometry,material);
  mesh.name='Backplate / satin metal rear cover insert';
  mesh.position.copy(rearCrystal.position);mesh.quaternion.copy(rearCrystal.quaternion);mesh.scale.copy(rearCrystal.scale);
  mesh.visible=false;mesh.castShadow=true;mesh.receiveShadow=true;
  mesh.userData={assemblyId:'CASEBACK-INSERT',replacesAssemblyId:'CASEBACK',designPart:'BACKPLATE',
    designRevision:BACKPLATE_LAYOUT.revision,finishKind:'satin',finishZone:'circular',finishFaceAxis:[0,1,0],
    componentRole:'Opaque rear cover in existing exhibition-window seat; not an arbor bearing or bridge',
    replacesRearCrystal:true};
  let disposed=false,pendingCleanupError=null,releaseBorrow=()=>{};
  function dispose(fromSource=false){
    if(disposed){if(!fromSource&&pendingCleanupError){const error=pendingCleanupError;pendingCleanupError=null;throw error;}return;}
    disposed=true;const failures=[],attempt=fn=>{try{fn();}catch(error){failures.push(error);}};
    attempt(releaseBorrow);attempt(()=>mesh.removeFromParent());
    if(!borrowImmutableGeometry)attempt(()=>geometry.dispose());
    attempt(()=>material.dispose());
    if(failures.length){const error=new AggregateError(failures,'Backplate cleanup failed: '+failures.map(e=>e.message).join('; '));if(fromSource)pendingCleanupError=error;else throw error;}
  }
  if(borrowImmutableGeometry){try{releaseBorrow=borrowSource(geometry,()=>dispose(true));}catch(error){material.dispose();throw error;}}
  return {mesh,meshes:[mesh],audit:{...BACKPLATE_LAYOUT,
    construction:borrowImmutableGeometry?'Immutable borrowed rear-window solid; source root owns geometry disposal':'Exact private copy of rear-window solid; original glass hidden only while cover is shown',
    geometryOwnership:borrowImmutableGeometry?'borrowed-source-root':'private',
    scope:'Nominal source-pose axial envelope clearance; existing ring/shoulder retained',
    physicalValidation:false,sealAndRetentionValidated:false},
    // Call after ordinary visibility() resets the original exterior visibility.
    // Disabling does not force glass visible in interior/isolated/crystals-off views.
    syncVisibility(state){if(disposed)return;mesh.visible=backplateVisible(state);if(mesh.visible)rearCrystal.visible=false;},
    dispose,
  };
}
