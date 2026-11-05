/** Retained-stock mechanical carriers, independent of decorative face/rear cover. */
export const STRUCTURAL_SUPPORT_REVISION='retained-stock-carriers-r01';
export const STRUCTURAL_SUPPORT_ASSET='open-front/open-front-plates.glb';
export const STRUCTURAL_SUPPORT_SHA256='3e3bff2e0b56c4e67633f1ff64e49aa5375ae524ed04ec9e3fff2aaf468d9623';
export function structuralSupportAsset({premiumRequested=false,comparison='restored'}={}){
 return premiumRequested&&comparison!=='source'?STRUCTURAL_SUPPORT_ASSET:'quality-study/open-front-plates.glb';
}
export function structuralSupportVisible({premium=false,comparison='restored',replacementForSourceIndex}={}){
 return !!premium&&comparison!=='source'&&[0,155].includes(replacementForSourceIndex);
}
export function structuralSupportSnapshot(plates,{premium=false,comparison='restored'}={}){
 return {revision:STRUCTURAL_SUPPORT_REVISION,comparison,asset:structuralSupportAsset({premiumRequested:premium,comparison}),auditedAssetSHA256:STRUCTURAL_SUPPORT_SHA256,scope:'Nominal retained-stock geometry; sampled contacts and stock containment, not manufacturing certification',visibleCarriers:plates.filter(m=>m.visible).map(m=>m.userData.replacementForSourceIndex)};
}
