import * as T from './vendor/three.tsl.js';
import {lugNoiseNode} from './assembly-node-lug-finish.js';
export const NODE_CARRIER_FINISH_REVISION='carrier-circular-tsl-r02';
const {Fn,float,vec2,vec3,vec4,length,varying,positionGeometry,modelViewMatrix,materialNormal,positionView,dFdx,dFdy,cross,dot,sign,abs,max,min,normalize,If,anisotropyT,anisotropyB,normalView,anisotropy,alphaT,roughness}=T;
// Same filtered scalar noise as accepted native carrierHash/carrierNoise.
export const carrierHeightNode=p=>{const r=length(p.xz);return float(.00035).mul(lugNoiseNode(r.div(.03).add(17.31)).mul(.78).add(lugNoiseNode(r.div(.07).sub(9.73)).mul(.22)));};
export const carrierNormalNode=(height,n,p)=>{const q0=dFdx(p),q1=dFdy(p),r0=cross(q1,n),r1=cross(n,q0),det=dot(q0,r0);const slope=sign(det).mul(dFdx(height).mul(r0).add(dFdy(height).mul(r1))).div(max(abs(det),1e-10));return normalize(n.sub(slope.mul(min(1,float(.012).div(max(length(slope),1e-8))))));};
export const carrierRadialNode=Fn(([p,n,viewX,viewZ])=>{const radial=normalize(p.xz),t=viewX.mul(radial.x).add(viewZ.mul(radial.y)).toVar();t.subAssign(n.mul(dot(t,n)));If(dot(t,t).lessThan(1e-6),()=>{t.assign(viewX.negate().mul(radial.y).add(viewZ.mul(radial.x)));});return normalize(t);});
const applied=new WeakSet();
export function applyNodeCarrierFinish(node,source){
 const spec=source.userData?.carrierMicrofinish;if(!spec)return node;
 if(spec.revision!=='carrier-circular-physical-r01'||spec.heightMm!==.00035||spec.maxSlope!==.012||spec.correlationMm?.join(',')!=='0.03,0.07'||spec.anisotropy!==.18||spec.axis!=='source local Y'||spec.membership!=='DIAL-CARRIER / Dial carrier · stepped support seat / CASE')throw Error('Unsupported carrier microfinish descriptor');
 if(applied.has(node))return node;
 if(!node.isMeshPhysicalNodeMaterial||typeof node.setupVariants!=='function')throw Error('Carrier microfinish requires physical node material');
 const p=varying(positionGeometry,'v_carrierPosition'),viewX=varying(modelViewMatrix.mul(vec4(1,0,0,0)).xyz,'v_carrierViewX'),viewZ=varying(modelViewMatrix.mul(vec4(0,0,1,0)).xyz,'v_carrierViewZ');
 // Keep existing satin roughness/color nodes; append only the accepted physical normal.
 node.normalNode=carrierNormalNode(carrierHeightNode(p),node.normalNode||materialNormal,positionView);node.anisotropyNode=vec2(.18,0);
 const diagnostic={revision:NODE_CARRIER_FINISH_REVISION,sourceRevision:spec.revision,graphBuildCount:0,graphInstalled:true,scope:'TSL graph construction count, not driver compile count',renderedParity:'pending actual matched node captures',hardwareWebGPUValidated:false};
 source.userData.carrierNodeFinish=diagnostic;node.userData={...node.userData,carrierNodeFinish:diagnostic};
 // r187 stock anisotropy requests mesh TBN/UV even when its axes are overwritten.
 // This actual carrier has neither UV nor tangent. Suppress ONLY that instance's
 // stock anisotropy variant while retaining every other physical-material variant;
 // then reproduce its scalar alphaT and assign the analytic frame directly.
 let skipStockAnisotropy=false;
 Object.defineProperty(node,'useAnisotropy',{configurable:true,get(){return !skipStockAnisotropy&&(this.anisotropy>0||this.anisotropyNode!==null);}});
 const setup=node.setupVariants;node.setupVariants=function(builder){
  skipStockAnisotropy=true;try{setup.call(this,builder);}finally{skipStockAnisotropy=false;}
  anisotropy.assign(.18);alphaT.assign(anisotropy.pow2().mix(roughness.pow2(),1.0));
  const radial=carrierRadialNode(p,normalView,viewX,viewZ);anisotropyT.assign(radial);anisotropyB.assign(normalize(cross(normalView,radial)));diagnostic.graphBuildCount++;
 };
 const key=node.customProgramCacheKey;node.customProgramCacheKey=function(){return key.call(this)+'|'+NODE_CARRIER_FINISH_REVISION;};applied.add(node);return node;
}
