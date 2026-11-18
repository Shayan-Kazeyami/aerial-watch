import {RGFormat,RED_GREEN_RGTC2_Format,RG11_EAC_Format,TangentSpaceNormalMap} from './vendor/three.module.js';
import * as T from './vendor/three.tsl.js';
import {getLeatherMicrodetailBinding} from './assembly-leather-microdetail.js';
const {Fn,vec2,vec3,float,texture,normalMap,materialReference,materialRoughness,normalize,dot,max,length,dFdx,dFdy,smoothstep,clamp,unpackNormal,negateOnBackSide}=T;
export const NODE_LEATHER_MICRODETAIL_REVISION='leather-dual-scale-tsl-r2-sign';
// Exactly the GLSL RNM formula, before native normalMap's tangent-to-view step.
export const leatherRNMNode=Fn(([baseN,detailN])=>{
 const t=normalize(baseN).add(vec3(0,0,1));
 const u=normalize(detailN).mul(vec3(-1,-1,1));
 return normalize(t.mul(dot(t,u)).div(max(t.z,.0001)).sub(u));
});
export function applyNodeLeatherMicrodetail(node,source,binding=getLeatherMicrodetailBinding(source)){
 if(!source.userData?.leatherMicrodetail)return node;
 // An adapted material must never silently lose an installed authored layer.
 if(!binding?.normalMap?.isTexture||!binding?.roughnessMap?.isTexture)throw Error('Node leather microdetail: missing owned texture binding; copyLeatherMicrodetailBinding is required for material clones');
 if(!source.normalMap?.isTexture||source.normalMapType!==TangentSpaceNormalMap)throw Error('Node leather microdetail requires the authored tangent-space macro normal map');
 const {normalMap:microNormal,roughnessMap:microRough,settings:s}=binding;
 const macroSample=texture(source.normalMap);
 // TextureNode uses the original channel and animated texture.matrix. Detail
 // intentionally reuses transformed MACRO UVs × repeat, like vNormalMapUv GLSL.
 const macroUv=macroSample.getTransformedUV(macroSample.getDefaultUV());
 const detailUv=macroUv.mul(s.repeat);
 const texelSize=vec2(microNormal.image?.width||2048,microNormal.image?.height||2048);
 const footprint=max(length(dFdx(detailUv).mul(texelSize)),length(dFdy(detailUv).mul(texelSize)));
 const weight=float(1).sub(smoothstep(s.fadeStartTexels,s.fadeEndTexels,footprint));
 let base=macroSample.xyz.mul(2).sub(1);
 // Same compressed RG normal reconstruction used by r187 materialNormal.
 if([RGFormat,RED_GREEN_RGTC2_Format,RG11_EAC_Format].includes(source.normalMap.format))base=unpackNormal(base.xy);
 const rawScale=materialReference('normalScale','vec2',source);
 // Sign only, including zero→+1. Derive BEFORE the independent flat-face
 // correction so a backside never negates the fine layer twice.
 const handedness=vec2(rawScale.x.lessThan(0).select(-1,1),rawScale.y.lessThan(0).select(-1,1));
 let scale=rawScale;
 if(source.flatShading)scale=negateOnBackSide(scale);
 base=vec3(base.xy.mul(scale),base.z);
 let rawDetail=texture(microNormal,detailUv).xyz.mul(2).sub(1);
 if([RGFormat,RED_GREEN_RGTC2_Format,RG11_EAC_Format].includes(microNormal.format))rawDetail=unpackNormal(rawDetail.xy);
 let detailScale=float(s.normalStrength).mul(weight);
 if(source.flatShading)detailScale=negateOnBackSide(detailScale);
 const detail=vec3(rawDetail.xy.mul(handedness).mul(detailScale),rawDetail.z);
 const combined=leatherRNMNode(base,detail);
 // normalMap(..., null) keeps all native TBN/face behavior without applying
 // macro normalScale twice. No view-space mixing or invalid transpose inverse.
 node.normalNode=normalMap(combined.mul(.5).add(.5));
 const fineRoughness=texture(microRough,detailUv).g;
 node.roughnessNode=clamp((node.roughnessNode||materialRoughness).add(fineRoughness.sub(s.roughnessMean).mul(s.roughnessStrength).mul(weight)),.04,1);
 node.userData={...node.userData,leatherMicrodetailNode:{revision:NODE_LEATHER_MICRODETAIL_REVISION,sourceRevision:s.revision,repeat:s.repeat,normalStrength:s.normalStrength,roughnessStrength:s.roughnessStrength,extraTextureAllocations:0}};
 return node;
}
