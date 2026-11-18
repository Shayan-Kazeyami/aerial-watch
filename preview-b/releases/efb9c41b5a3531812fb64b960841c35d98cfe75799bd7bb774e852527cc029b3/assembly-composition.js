import * as THREE from './vendor/three.module.js';

// Supported front-only hour hierarchy. Native XY / axial Z, mounted like dial details.
// Eight quiet hour markers complete the existing four cardinal numerals.
export const COMPOSITION_R09 = Object.freeze({radius:15.055,length:.55,width:.16,height:3.55,depth:.006,
  hours:Object.freeze([1,2,4,5,7,8,10,11])});
export function createCompositionIndices(){
  const l=COMPOSITION_R09,positions=[],normals=[];
  for(const hour of l.hours){
    const geometry=new THREE.BoxGeometry(l.width,l.length,l.depth).toNonIndexed();
    geometry.translate(0,l.radius,l.depth/2);geometry.rotateZ(-hour*Math.PI/6);
    positions.push(...geometry.attributes.position.array);normals.push(...geometry.attributes.normal.array);geometry.dispose();
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));
  const material=new THREE.MeshStandardMaterial({color:0xe3dfcf,metalness:.05,roughness:.62});
  const mesh=new THREE.Mesh(geometry,material);mesh.name='Aerial / eight noncardinal hour markers R09';mesh.userData.displayDetail=true;
  const group=new THREE.Group();group.name='Aerial / R09 hour hierarchy candidate';
  group.rotation.x=-Math.PI/2;group.position.y=l.height;group.add(mesh);
  let disposed=false;
  return {group,geometry,dispose(){if(disposed)return;disposed=true;geometry.dispose();material.dispose();group.removeFromParent();}};
}
