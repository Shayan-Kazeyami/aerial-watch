import {applyNodeCarrierFinish,NODE_CARRIER_FINISH_REVISION} from './assembly-node-carrier-microfinish.js';
import {applyNodeLugFinish,NODE_LUG_FINISH_REVISION} from './assembly-node-lug-finish.js';
import {applyNodeLeatherMicrodetail} from './assembly-node-leather-microdetail.js';
import {applyNodeRefraction} from './assembly-node-refraction.js';
// TSL port of the authored baseline surface field, not a replacement noise look.
import * as T from './vendor/three.tsl.js';
const {Fn,vec3,float,fract,dot,floor,mix,smoothstep,length,fwidth,sin,normalize,cross,abs,pow,max,clamp,varying,positionGeometry,normalGeometry,materialRoughness,dFdx,dFdy,positionView,materialNormal,materialColor,step}=T;
const hash=Fn(([input])=>{const p=fract(input.mul(.1031)).toVar();p.addAssign(dot(p,p.yzx.add(33.33)));return fract(p.x.add(p.y).mul(p.z));});
const noise=Fn(([p])=>{const q=floor(p),raw=fract(p),f=raw.mul(raw).mul(float(3).sub(raw.mul(2)));const h=(x,y,z)=>hash(q.add(vec3(x,y,z)));return mix(mix(mix(h(0,0,0),h(1,0,0),f.x),mix(h(0,1,0),h(1,1,0),f.x),f.y),mix(mix(h(0,0,1),h(1,0,1),f.x),mix(h(0,1,1),h(1,1,1),f.x),f.y),f.z);});
const filtered=p=>mix(.5,noise(p),float(1).sub(smoothstep(.35,1.3,length(fwidth(p)))));
const wave=p=>sin(p).mul(float(1).sub(smoothstep(.45,2.5,fwidth(p))));
export function applyNodeFinish(node,source){
 const spec=source.userData.aerialSurface;
 if(spec){
  const {type,strength,axis,kind,faceAxis}=spec,p=varying(positionGeometry),n=normalize(varying(normalGeometry));
  const raw=pow(abs(n),vec3(6)),w=raw.div(max(dot(raw,vec3(1)),.001));
  function linear(plane){
   // Projection basis is constant for these three fixed planes, just as GLSL.
   let travel=[...axis],d=travel.reduce((s,v,i)=>s+v*plane[i],0),t=travel.map((v,i)=>v-plane[i]*d);
   if(t.reduce((s,v)=>s+v*v,0)<.01){travel=Math.abs(plane[2])<.8?[0,0,1]:[0,1,0];d=travel.reduce((s,v,i)=>s+v*plane[i],0);t=travel.map((v,i)=>v-plane[i]*d);}
   const tangent=normalize(vec3(...t)),pn=vec3(...plane),across=normalize(cross(pn,tangent));
   let scratch=filtered(vec3(dot(p,across).mul(145),dot(p,tangent).mul(.8),dot(p,pn).mul(2)));
   if(type==='cross')scratch=scratch.mul(.65).add(filtered(vec3(dot(p,tangent).mul(120),dot(p,across).mul(.8),dot(p,pn).mul(2))).mul(.35));
   return float(.5).add(scratch.sub(.5).mul(.22)).add(filtered(p.mul(45)).sub(.5).mul(.06));
  }
  let height;
  if(type==='leather')height=filtered(p.mul(4.8)).mul(.65).add(filtered(p.mul(28)).mul(.35));
  else if(type==='circular')height=float(.5).add(w.x.mul(wave(length(p.yz).mul(205))).add(w.y.mul(wave(length(p.xz).mul(205)))).add(w.z.mul(wave(length(p.xy).mul(205)))).mul(.12)).add(filtered(p.mul(40)).sub(.5).mul(.08));
  else height=w.x.mul(linear([1,0,0])).add(w.y.mul(linear([0,1,0]))).add(w.z.mul(linear([0,0,1])));
  let rough=clamp(materialRoughness.add(height.sub(.5).mul(strength)),.065,1);
  if(kind==='satin')rough=mix(rough,.20,smoothstep(.12,.65,float(1).sub(abs(dot(n,vec3(...faceAxis))))));
  node.roughnessNode=rough;
  if(type==='leather'){
   node.colorNode=materialColor.mul(float(.91).add(height.mul(.16)));
   const normal=materialNormal,q0=dFdx(positionView),q1=dFdy(positionView),r0=cross(q1,normal),r1=cross(normal,q0),det=dot(q0,r0);
   const grad=T.sign(det).mul(dFdx(height).mul(r0).add(dFdy(height).mul(r1)));
   node.normalNode=normalize(abs(det).mul(normal).sub(grad.mul(.025)));
  }
 }
 const cap=source.userData.aerialCrownCap;
 if(cap){
  const n=normalize(varying(normalGeometry));let mask;
  if(cap.eligibilityAttribute){
   // Same authored per-triangle scope as native GLSL; no interpolated absolute
   // X or derivative-plane test when the exact eligibility replaces them.
   mask=step(.5,varying(T.attribute(cap.eligibilityAttribute,'float'))).mul(step(cap.normalThreshold,n.x));
   if(cap.positionGate!==false){const p=varying(positionGeometry);mask=mask.mul(step(abs(p.x.sub(cap.maxX)),cap.positionTolerance));}
  }else{const p=varying(positionGeometry),face=cross(dFdx(p),dFdy(p));mask=step(abs(p.x.sub(cap.maxX)),cap.positionTolerance).mul(step(cap.normalThreshold,n.x)).mul(step(cap.normalThreshold,abs(face.x).div(max(length(face),1e-20))));}
  node.roughnessNode=mix(node.roughnessNode||materialRoughness,cap.roughness,mask);
 }
 applyNodeLugFinish(node,source);
 applyNodeCarrierFinish(node,source);
 applyNodeLeatherMicrodetail(node,source);
 return applyNodeRefraction(node,source);
}
export function installNodeFinishLibrary(renderer,identity){
 const from=renderer.library.fromMaterial.bind(renderer.library);
 renderer.library.fromMaterial=material=>{const node=from(material);if(node&&!material.isNodeMaterial)applyNodeFinish(node,material);return node;};
 renderer.aerialNodeLugFinish=Object.freeze({installed:true,revision:NODE_LUG_FINISH_REVISION,sourceRevision:'lug-longitudinal-physical-r01',renderedParity:'pending matched node/native captures',hardwareWebGPUValidated:false});
 renderer.aerialNodeCarrierFinish=Object.freeze({installed:true,revision:NODE_CARRIER_FINISH_REVISION,sourceRevision:'carrier-circular-physical-r01',renderedParity:'pending actual matched node captures',hardwareWebGPUValidated:false});
 identity.nodeFinishes={carrierMicrofinish:renderer.aerialNodeCarrierFinish,lugFinish:renderer.aerialNodeLugFinish,revision:'baseline-field-tsl-r2-exact-crown',ported:['linear','circular','cross','procedural leather','satin cut walls','crown planar cap','dual-scale leather RNM/roughness','R5 longitudinal lug field and analytic anisotropy frame','DIAL-CARRIER circular physical normal and radial anisotropy frame'],pending:['studio4 analytic anisotropy microfinish','node/WebGPU rendered parity verification']};
}
