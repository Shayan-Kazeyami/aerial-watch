import {loadGLTFAsset} from './assembly-loading.js';
export const COMPAT_LEATHER_URL='leather-compat-r12/leather.gltf';
export const COMPAT_LEATHER_WARNING='Reduced leather detail · outer normal detail unavailable. Current R12 geometry, stitching and color retained.';
export const COMPAT_LEATHER_IDENTITY=Object.freeze({geometryRevision:'R12',geometrySha256:'0a604095b96b3fc3b52db734d91861803391fa796e6039d13f25941d053e6040',omittedMap:'R12 outer-normal-4k.ktx2',deliveryFormat:'PNG RGBA decode of current R12 KTX color/roughness; original lining PNG/JPEG',outerColorSha256:'402da467baa9000edb54f6e8d1f67933b54018f0d763db5c99310bbf0f0e9e3d',outerRoughnessSha256:'3364286c7869d202131dfd14a477017742d144c83e24b4ac7f36c0e03a058955',quality:'reduced-outer-normal-detail',automaticFallback:false});
export async function loadCompatLeather(options={}, {optIn=false,loadAsset=loadGLTFAsset}={}){
 if(optIn!==true)throw new Error('Explicit reduced-detail leather opt-in required.');
 const result=await loadAsset(COMPAT_LEATHER_URL,options);
 return {...result,compatibility:COMPAT_LEATHER_IDENTITY,warning:COMPAT_LEATHER_WARNING,metrics:{...result.metrics,assetDelivery:{requested:'compat12',used:'r12-png-no-outer-normal',automaticFallback:false}}};
}
