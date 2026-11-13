import {BufferAttribute,Vector3} from './vendor/three.module.js';
import {createCrownCapFinish,CROWN_CAP_FINISH,crownCapMask} from './assembly-crown-finish.js';
export const CROWN_CAP_ELIGIBILITY_REVISION='crown-cap-exact-eligibility-r01';
// Exact authored cap only. Split shared attribute vertices, never change a
// coordinate, normal, UV, triangle order, group, material value or transform.
export function createCrownCapEligibility(mesh,baseMaterial,{positionGate=false}={}){
 if(Array.isArray(baseMaterial)||!baseMaterial?.isMeshPhysicalMaterial)throw new TypeError('Crown cap requires one MeshPhysicalMaterial');
 if(mesh?.userData?.assemblyId!=='CROWN')throw new Error('Actual CROWN required');
 const source=mesh.geometry,p=source?.attributes.position,n=source?.attributes.normal,idx=source?.index;
 if(!p||!n||!idx||p.isInterleavedBufferAttribute||n.isInterleavedBufferAttribute)throw new Error('Indexed crown positions and normals required');
 let maxX=-Infinity;for(let i=0;i<p.count;i++)maxX=Math.max(maxX,p.getX(i));
 const capTriangles=[],vertices=new Set(),a=new Vector3(),b=new Vector3(),c=new Vector3(),f=new Vector3();let area=0;
 for(let k=0;k<idx.count;k+=3){
  const ids=[idx.getX(k),idx.getX(k+1),idx.getX(k+2)];a.fromBufferAttribute(p,ids[0]);b.fromBufferAttribute(p,ids[1]);c.fromBufferAttribute(p,ids[2]);f.subVectors(b,a).cross(c.clone().sub(a));const twiceArea=f.length();if(!(twiceArea>0))throw new Error('Degenerate source crown triangle');f.divideScalar(twiceArea);
  if(ids.every(i=>crownCapMask({x:p.getX(i),normalX:n.getX(i)/Math.hypot(n.getX(i),n.getY(i),n.getZ(i)),faceNormalX:f.x,maxX}))){
   if(f.x<0)throw new Error('Inward cap face');capTriangles.push(k);ids.forEach(i=>vertices.add(i));area+=twiceArea/2;
  }
 }
 if(p.count!==13352||idx.count!==77748||capTriangles.length!==190||vertices.size!==192||Math.abs(maxX-25.399999618530273)>1e-7||Math.abs(area-11.279485)>1e-4)throw new Error('Authored crown cap fixture mismatch');
 for(const attribute of Object.values(source.attributes))if(attribute.isInterleavedBufferAttribute||attribute.count!==p.count)throw new Error('Unsupported crown attribute layout');
 const geometry=source.clone(),copies=[...vertices],lookup=new Map(copies.map((old,i)=>[old,p.count+i]));
 for(const [name,attribute] of Object.entries(source.attributes)){
  if(attribute.isInterleavedBufferAttribute||attribute.count!==p.count)throw new Error('Unsupported crown attribute layout');
  const array=new attribute.array.constructor((p.count+copies.length)*attribute.itemSize);array.set(attribute.array);
  copies.forEach((old,i)=>array.set(attribute.array.subarray(old*attribute.itemSize,(old+1)*attribute.itemSize),(p.count+i)*attribute.itemSize));
  const copy=attribute.clone();copy.array=array;copy.count=p.count+copies.length;geometry.setAttribute(name,copy);
 }
 const eligibility=new Float32Array(p.count+copies.length);eligibility.fill(1,p.count);geometry.setAttribute('aerialCrownCapEligible',new BufferAttribute(eligibility,1));
 const index=idx.array.slice();for(const k of capTriangles)for(let j=0;j<3;j++)index[k+j]=lookup.get(index[k+j]);geometry.setIndex(new BufferAttribute(index,1));
 const finish=createCrownCapFinish(mesh,baseMaterial),material=finish.material,compile=material.onBeforeCompile,key=material.customProgramCacheKey;
 material.userData.aerialCrownCap={...material.userData.aerialCrownCap,eligibilityAttribute:'aerialCrownCapEligible',positionGate,revision:CROWN_CAP_ELIGIBILITY_REVISION};
 material.name=baseMaterial.name+' / satin exact face / position gate '+(positionGate?'ON':'OFF');
 material.onBeforeCompile=function(shader,renderer){
  compile.call(this,shader,renderer);
  const declarations='\nvarying float vAerialCrownCapEligible;\n';
  shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nattribute float aerialCrownCapEligible;'+declarations).replace('#include <begin_vertex>','#include <begin_vertex>\nvAerialCrownCapEligible=aerialCrownCapEligible;');
  shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>'+declarations);
  const old=`*step(${CROWN_CAP_FINISH.normalThreshold},abs(aerialCrownCapFace.x)/max(aerialCrownCapFaceLength,1.e-20))`;
  if(!shader.fragmentShader.includes(old))throw new Error('Crown derivative gate layout mismatch');
  shader.fragmentShader=shader.fragmentShader.replace(old,'*step(0.5,vAerialCrownCapEligible)')
   .replace('vec3 aerialCrownCapFace=cross(dFdx(vAerialCrownCapLocalPosition),dFdy(vAerialCrownCapLocalPosition));','')
   .replace('float aerialCrownCapFaceLength=length(aerialCrownCapFace);','');
  if(!positionGate){const proximity=`step(abs(vAerialCrownCapLocalPosition.x-uAerialCrownCapMaxX),${CROWN_CAP_FINISH.positionTolerance.toFixed(8)})`;if(!shader.fragmentShader.includes(proximity))throw new Error('Crown proximity gate layout mismatch');shader.fragmentShader=shader.fragmentShader.replace(proximity,'1.0');}

 };
 material.customProgramCacheKey=function(){return key.call(material)+'|'+CROWN_CAP_ELIGIBILITY_REVISION+'|position:'+positionGate;};
 let disposed=false;
 return {geometry,material,originalGeometry:source,audit:{revision:CROWN_CAP_ELIGIBILITY_REVISION,positionGate,capTriangles:capTriangles.length,duplicatedAttributeVertices:copies.length,sourceVertices:p.count,candidateVertices:p.count+copies.length,triangleCount:idx.count/3,capArea:area,maxX,positionsNormalsUVs:'exact per triangle corner copies',bevelEligibility:0,changedGate:'exact face and local-normal gates retained; only redundant local-position gate toggled',roughness:finish.audit.roughness,backendScope:'Native GLSL gate visually verified; equivalent TSL graph tested, node/WebGPU rendered parity unverified'},dispose(){if(disposed)return;disposed=true;if(mesh.geometry===geometry)mesh.geometry=source;geometry.dispose();finish.dispose();}};
}
