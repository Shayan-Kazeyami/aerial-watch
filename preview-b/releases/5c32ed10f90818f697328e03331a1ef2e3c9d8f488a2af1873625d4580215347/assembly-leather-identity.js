import {AUTHORED_LEATHER_IDENTITY} from './assembly-leather-authoring-identity.js';
export async function verifyLoadedLeatherGeometry(gltf,identity=AUTHORED_LEATHER_IDENTITY,{digest=bytes=>crypto.subtle.digest('SHA-256',bytes)}={}){
 if(typeof gltf?.parser?.getDependency!=='function')throw Error('Authored leather verification unavailable: GLTF parser buffer access required');
 const bytes=await gltf.parser.getDependency('buffer',identity.expectedGeometry.bufferIndex);
 const array=bytes instanceof ArrayBuffer?new Uint8Array(bytes):ArrayBuffer.isView(bytes)?new Uint8Array(bytes.buffer,bytes.byteOffset,bytes.byteLength):null;
 if(!array)throw Error('Authored leather verification requires actual decoded buffer bytes');
 const actualSha256=Array.from(new Uint8Array(await digest(array)),b=>b.toString(16).padStart(2,'0')).join('');
 const proof={status:'verified',id:identity.id,scope:'actual GLTF parser geometry buffer bytes, not pixels or hardware',actualBytes:array.byteLength,actualSha256,expectedBytes:identity.expectedGeometry.bytes,expectedSha256:identity.expectedGeometry.sha256};
 if(proof.actualBytes!==proof.expectedBytes||proof.actualSha256!==proof.expectedSha256)throw Error('Authored leather geometry identity mismatch: expected '+proof.expectedSha256+', loaded '+proof.actualSha256);
 return Object.freeze(proof);
}
export function leatherCandidateDiagnostics(proof=null){return {identity:AUTHORED_LEATHER_IDENTITY,geometryVerification:proof||{status:'not-yet-verified',scope:'expected identity is not runtime evidence'},automaticFallback:false};}
