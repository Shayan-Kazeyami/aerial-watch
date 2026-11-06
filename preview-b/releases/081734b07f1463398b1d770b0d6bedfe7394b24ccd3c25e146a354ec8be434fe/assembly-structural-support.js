/** Retained-stock mechanical carriers, independent of decorative face/rear cover. */
export const STRUCTURAL_SUPPORT_REVISION='retained-stock-carriers-r01';
export const STRUCTURAL_SUPPORT_ASSET='open-front-candidate/open-front-plates.glb';
export const STRUCTURAL_SUPPORT_SHA256='949e7bea145e08842d7c5b478e72811ae6b0bb21e6176d8e03946a1e71b3cb4a';
export function structuralSupportAsset({premiumRequested=false,comparison='restored'}={}){
 return premiumRequested&&comparison!=='source'?STRUCTURAL_SUPPORT_ASSET:'quality-study/open-front-plates.glb';
}
export function structuralSupportVisible({premium=false,comparison='restored',replacementForSourceIndex}={}){
 return !!premium&&comparison!=='source'&&[0,155].includes(replacementForSourceIndex);
}
export function structuralSupportSnapshot(plates,{premium=false,comparison='restored',verifiedSHA256=null}={}){
 return {revision:STRUCTURAL_SUPPORT_REVISION,comparison,asset:structuralSupportAsset({premiumRequested:premium,comparison}),expectedAssetSHA256:premium&&comparison!=='source'?STRUCTURAL_SUPPORT_SHA256:null,verifiedAssetSHA256:verifiedSHA256,auditedAssetSHA256:null,scope:'Candidate structural contact audit pending; not manufacturing certification',visibleCarriers:plates.filter(m=>m.visible).map(m=>m.userData.replacementForSourceIndex)};
}
