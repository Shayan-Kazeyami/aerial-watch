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

export function createBackplate({rearCrystal}={}) {
  if(rearCrystal?.userData?.assemblyId!=='REAR-CRYSTAL'||!rearCrystal.isMesh||!rearCrystal.geometry?.attributes.position)
    throw new Error('Backplate requires the original REAR-CRYSTAL seat geometry.');
  const geometry=rearCrystal.geometry.clone();
  const material=new THREE.MeshPhysicalMaterial({color:0xb9bec4,metalness:1,roughness:.38});
  const mesh=new THREE.Mesh(geometry,material);
  mesh.name='Backplate / satin metal rear cover insert';
  mesh.position.copy(rearCrystal.position);mesh.quaternion.copy(rearCrystal.quaternion);mesh.scale.copy(rearCrystal.scale);
  mesh.visible=false;mesh.castShadow=true;mesh.receiveShadow=true;
  mesh.userData={assemblyId:'CASEBACK-INSERT',replacesAssemblyId:'CASEBACK',designPart:'BACKPLATE',
    designRevision:BACKPLATE_LAYOUT.revision,finishKind:'satin',finishZone:'circular',finishFaceAxis:[0,1,0],
    componentRole:'Opaque rear cover in existing exhibition-window seat; not an arbor bearing or bridge',
    replacesRearCrystal:true};
  let disposed=false;
  return {mesh,meshes:[mesh],audit:{...BACKPLATE_LAYOUT,
    construction:'Exact private copy of rear-window solid; original glass hidden only while cover is shown',
    scope:'Nominal source-pose axial envelope clearance; existing ring/shoulder retained',
    physicalValidation:false,sealAndRetentionValidated:false},
    // Call after ordinary visibility() resets the original exterior visibility.
    // Disabling does not force glass visible in interior/isolated/crystals-off views.
    syncVisibility(state){if(disposed)return;mesh.visible=backplateVisible(state);if(mesh.visible)rearCrystal.visible=false;},
    dispose(){if(disposed)return;disposed=true;mesh.removeFromParent();geometry.dispose();material.dispose();},
  };
}
