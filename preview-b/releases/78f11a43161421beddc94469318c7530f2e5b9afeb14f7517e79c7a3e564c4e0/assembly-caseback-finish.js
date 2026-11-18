import * as THREE from './vendor/three.module.js';

// CASEBACK has indexed vertices shared between axial caps and walls. Expanding
// private corners is necessary to flatten caps without changing wall normals.
// Original geometry/index/attributes remain untouched and recoverable.
export function createCasebackFinish({mesh}={}) {
  if(mesh?.userData?.assemblyId!=='CASEBACK'||!mesh.geometry?.attributes.position||!mesh.geometry.attributes.normal)throw new Error('Caseback finish requires the actual CASEBACK mesh.');
  let base,owned,audit,disposed=false;
  function release(){if(owned&&mesh.geometry===owned)mesh.geometry=base;owned?.dispose();base=owned=undefined;}
  function build(geometry){
    const clone=geometry.index?geometry.toNonIndexed():geometry.clone(),p=clone.attributes.position,n=clone.attributes.normal;
    const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3(),f=new THREE.Vector3();let triangles=0,areaMM2=0;
    for(let i=0;i<p.count;i+=3){a.fromBufferAttribute(p,i);b.fromBufferAttribute(p,i+1);c.fromBufferAttribute(p,i+2);f.subVectors(b,a).cross(c.sub(a));const area=f.length()/2;if(area<1e-8||Math.abs(f.normalize().y)<.999999)continue;triangles++;areaMM2+=area;for(let j=0;j<3;j++)n.setXYZ(i+j,0,Math.sign(f.y),0);}
    n.needsUpdate=true;return {geometry:clone,audit:{capTriangles:triangles,capAreaMM2:areaMM2,scope:'CASEBACK meaningful axial cap corner normals only; private expanded corners'}};
  }
  return {
    get enabled(){return !!owned&&mesh.geometry===owned;},get audit(){return audit;},
    setEnabled(value){if(disposed)return;if(!value){if(mesh.geometry===owned)mesh.geometry=base;return;}if(mesh.geometry===owned)return;
      if(mesh.geometry!==base){const selected=mesh.geometry;release();const result=build(selected);base=selected;owned=result.geometry;audit=result.audit;}mesh.geometry=owned;
    },
    dispose(){if(disposed)return;release();disposed=true;},
  };
}
