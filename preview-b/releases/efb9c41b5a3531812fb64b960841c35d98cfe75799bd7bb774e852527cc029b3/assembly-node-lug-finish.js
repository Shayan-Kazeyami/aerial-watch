import * as T from './vendor/three.tsl.js';
export const NODE_LUG_FINISH_REVISION='lug-longitudinal-tsl-r01';
const {Fn,float,vec2,vec3,vec4,fract,floor,mix,smoothstep,fwidth,varying,positionGeometry,normalGeometry,modelViewMatrix,materialRoughness,materialNormal,positionView,dFdx,dFdy,cross,dot,sign,abs,max,min,length,normalize,clamp,If,anisotropyT,anisotropyB,normalView}=T;
// Arithmetic and ordering match the accepted native lugHash/lugNoise exactly.
export const lugHashNode=Fn(([input])=>{const x=fract(input.mul(.1031)).toVar();x.mulAssign(x.add(33.33));x.mulAssign(x.add(x));return fract(x).mul(2).sub(1);});
export const lugNoiseNode=Fn(([x])=>{const c=floor(x),raw=fract(x),f=raw.mul(raw).mul(float(3).sub(raw.mul(2)));return mix(lugHashNode(c),lugHashNode(c.add(1)),f).mul(float(1).sub(smoothstep(.18,.65,fwidth(x))));});
export const lugProfileNode=q=>lugNoiseNode(q.div(.047).add(17.31)).mul(.65).add(lugNoiseNode(q.div(.083).sub(9.73)).mul(.25)).add(lugNoiseNode(q.div(.137).add(3.17)).mul(.10));
export const lugFieldNode=(p,n)=>{const raw=n.xy.mul(n.xy),w=raw.div(max(raw.x.add(raw.y),1e-8));return w.y.mul(lugProfileNode(p.x)).add(w.x.mul(lugProfileNode(p.y)));};
export const lugPerturbedNormalNode=(field,n,p)=>{const q0=dFdx(p),q1=dFdy(p),r0=cross(q1,n),r1=cross(n,q0),det=dot(q0,r0),height=field.mul(.0003);const slope=sign(det).mul(dFdx(height).mul(r0).add(dFdy(height).mul(r1))).div(max(abs(det),1e-10));return normalize(n.sub(slope.mul(min(1,float(.025).div(max(length(slope),1e-8))))));};
export const lugAcrossNode=Fn(([n,travel,fallback])=>{const along=travel.sub(n.mul(dot(travel,n))).toVar();If(dot(along,along).lessThan(.01),()=>{along.assign(fallback.sub(n.mul(dot(fallback,n))));});along.assign(normalize(along));return normalize(cross(along,n));});
const applied=new WeakSet();
export function applyNodeLugFinish(node,source){
 const spec=source.userData?.lugFinish;if(!spec)return node;
 if(spec.revision!=='lug-longitudinal-physical-r01'||spec.physicalHeightPeakToPeakMM!==.0006||spec.spacingMM?.join(',')!=='0.047,0.083,0.137'||spec.travelLocal?.join(',')!=='0,0,-1')throw Error('Unsupported source lug finish descriptor');
 if(applied.has(node))return node;
 if(!node.isMeshPhysicalNodeMaterial||typeof node.setupVariants!=='function')throw Error('Lug finish requires physical node material');
 const p=varying(positionGeometry,'v_lugPosition'),n=varying(normalGeometry,'v_lugNormal');
 const travel=varying(modelViewMatrix.mul(vec4(0,0,-1,0)).xyz,'v_lugTravel'),fallback=varying(modelViewMatrix.mul(vec4(1,0,0,0)).xyz,'v_lugFallback');
 const field=lugFieldNode(p,n);
 node.roughnessNode=clamp(materialRoughness.add(field.mul(.008)),.065,1);
 node.normalNode=lugPerturbedNormalNode(field,materialNormal,positionView);
 node.anisotropyNode=vec2(.18,0);
 // r187's standard anisotropy setup uses imported TBN. Keep its scalar alphaT
 // calculation, then overwrite only this material's BRDF axes using its FINAL
 // perturbed view normal. Never mutate geometry tangent or global TSL nodes.
 const setup=node.setupVariants;
 node.setupVariants=function(builder){setup.call(this,builder);const across=lugAcrossNode(normalView,travel,fallback);anisotropyT.assign(across);anisotropyB.assign(normalize(cross(normalView,across)));};
 node.userData={...node.userData,lugFinishNode:{revision:NODE_LUG_FINISH_REVISION,sourceRevision:spec.revision,frame:'analytic view-space; rebuilt after physical normal',extraTextures:0,renderedParity:'pending actual matched node captures',hardwareWebGPUValidated:false}};
 const key=node.customProgramCacheKey;node.customProgramCacheKey=function(){return key.call(this)+'|'+NODE_LUG_FINISH_REVISION;};
 applied.add(node);return node;
}
