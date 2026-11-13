// This policy never verifies texture bytes or installs a texture. The caller must
// pass evidence from the verified loader and the *currently installed* binding,
// updating it only after successful adoption. URL/quality choices are not proof.
export const FULL_LEATHER_NORMAL=Object.freeze({bytes:16562348,sha256:'bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585',width:4096,height:4096,mipLevels:13});
export const LOW_LEATHER_NORMAL=Object.freeze({bytes:4389472,sha256:'5d8aa10702589424c1157d9a58a7f75aca265569d7c8fac09525a00af19455bc',width:2048,height:2048,mipLevels:12});
const matches=(actual,expected)=>actual?.verified===true&&['bytes','sha256','width','height','mipLevels'].every(k=>actual[k]===expected[k]);
const copyEvidence=actual=>actual?Object.freeze({bytes:actual.bytes??null,sha256:actual.sha256??null,width:actual.width??null,height:actual.height??null,mipLevels:actual.mipLevels??null,verified:actual.verified===true}):null;
export function captureDetailPolicy({required=true,phase='disabled',activeNormal=null}={}){
 const activeNormalIdentity=copyEvidence(activeNormal),requestedNormalIdentity=required?FULL_LEATHER_NORMAL:null;
 const fullInstalled=matches(activeNormalIdentity,FULL_LEATHER_NORMAL),lowInstalled=matches(activeNormalIdentity,LOW_LEATHER_NORMAL);
 let ready=false,reason,message;
 if(!required){ready=true;reason='not-required';message='';}
 else if(phase==='failed'){reason='upgrade-failed';message='Full leather detail could not load. Use Retry detail in Capture before saving an image or video.';}
 else if(phase==='waiting-for-first-frame'||phase==='upgrading'){reason='upgrade-pending';message='Full leather detail is still loading. Wait before saving an image or video.';}
 else if((phase==='disabled'||phase==='direct'||phase==='full')&&fullInstalled){ready=true;reason='full-detail-ready';message='';}
 else {reason='detail-not-verified';message='Full leather detail is not verified yet. Wait before saving an image or video.';}
 return Object.freeze({required,phase,ready,reason,message,activeNormalIdentity,requestedNormalIdentity,installedDetail:fullInstalled?'full':lowInstalled?'initial':'unverified'});
}
// Call on a fresh policy snapshot before either video path, and again immediately
// before PNG rendering after any asynchronous preparation/provenance resolution.
export function assertCaptureDetailReady(policy){
 if(policy?.ready!==true){const error=new Error(policy?.message||'Full leather detail is not ready for capture.');error.name='CaptureDetailNotReadyError';error.code=policy?.reason||'detail-not-verified';throw error;}
 return policy;
}
