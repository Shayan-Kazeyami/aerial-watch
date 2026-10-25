const encoder=new TextEncoder();
const sha256=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(value=>value.toString(16).padStart(2,'0')).join('');
const safePath=value=>typeof value==='string'&&!value.startsWith('/')&&!value.includes('..')&&!value.includes('\\')&&/^[a-zA-Z0-9._/-]+$/.test(value);
async function validateRevision(revision){
  if(revision?.schemaVersion!==1||revision.algorithm!=='SHA-256'||!Array.isArray(revision.files)||!revision.files.length||revision.files.length>200)throw new Error('Capture revision metadata is invalid.');
  const paths=new Set();for(const file of revision.files){if(!safePath(file.path)||paths.has(file.path)||!Number.isSafeInteger(file.bytes)||file.bytes<0||!(/^[a-f0-9]{64}$/).test(file.sha256))throw new Error('Capture revision file identity is invalid.');paths.add(file.path);}
  if(await sha256(encoder.encode(JSON.stringify(revision.files)))!==revision.digest)throw new Error('Capture revision digest is invalid.');return revision;
}

// Optional boot metadata is imported in parallel. Nothing here gates the
// original assembly, first interactive frame or ordinary watch controls.
export function createCaptureProvenance({fetcher=fetch,signal,loadBootRevision=()=>import('./quality-study/viewer-revision.js').then(module=>module.default),metadataURL='quality-study/viewer-revision.json'}={}){
  let state={status:'not-yet-verified',scope:'First-party viewer source only',digest:null},pending;
  const boot=Promise.resolve().then(loadBootRevision).then(validateRevision).then(value=>({value}),error=>({error}));
  const snapshot=()=>structuredClone(state);
  return {snapshot,
    resolve(){if(pending)return pending;
      pending=(async()=>{try{
        const pinned=await boot;if(pinned.error)throw pinned.error;
        const response=await fetcher(metadataURL,{cache:'no-store',signal});if(!response.ok)throw new Error('Capture revision metadata is unavailable.');
        const current=await validateRevision(await response.json());
        if(pinned.value.digest!==current.digest){state={status:'viewer-reload-required',digest:pinned.value.digest,currentServedDigest:current.digest,scope:current.scope,reason:'Served source revision changed after this viewer opened. Reload before making revision-verified evidence.'};return snapshot();}
        const mismatches=[];await Promise.all(current.files.map(async file=>{
          const asset=await fetcher(file.path,{cache:'no-store',signal});if(!asset.ok){mismatches.push(file.path);return;}
          const bytes=await asset.arrayBuffer();if(bytes.byteLength!==file.bytes||await sha256(bytes)!==file.sha256)mismatches.push(file.path);
        }));
        state=mismatches.length?{status:'served-source-mismatch',digest:current.digest,scope:current.scope,mismatches:mismatches.sort(),reason:'Source files changed without regenerated capture metadata.'}:
          {status:'verified',digest:current.digest,algorithm:'SHA-256',scope:current.scope,metadataURL,files:current.files,verifiedAt:new Date().toISOString(),limitation:'Identifies the pinned viewer source revision and verifies current served bytes; excludes vendor/model identities, physical behavior and visual acceptance.'};
      }catch(error){state={status:'unavailable',digest:null,scope:'First-party viewer source only',reason:error.message};}return snapshot();})().finally(()=>{pending=null;});return pending;
    },
  };
}

const crc32=bytes=>{let value=0xffffffff;for(const byte of bytes){value^=byte;for(let bit=0;bit<8;bit++)value=(value>>>1)^((value&1)?0xedb88320:0);}return (value^0xffffffff)>>>0;};
// Uncompressed UTF-8 iTXt embeds the exact view/config and source identity in the
// single PNG download. Pixel data and image dimensions are unchanged.
export async function embedPNGConfiguration(blob,configuration){
  const input=new Uint8Array(await blob.arrayBuffer()),signature=[137,80,78,71,13,10,26,10];
  if(signature.some((byte,index)=>input[index]!==byte))throw new Error('Canvas export did not produce a PNG.');
  const payload=encoder.encode('AerialView\0\0\0\0\0'+JSON.stringify(configuration)),type=encoder.encode('iTXt'),chunk=new Uint8Array(payload.length+12),view=new DataView(chunk.buffer);
  view.setUint32(0,payload.length);chunk.set(type,4);chunk.set(payload,8);view.setUint32(payload.length+8,crc32(chunk.subarray(4,payload.length+8)));
  const pieces=[input.subarray(0,8)];let offset=8,found=false;
  while(offset+12<=input.length){const size=new DataView(input.buffer,input.byteOffset+offset,4).getUint32(0),end=offset+size+12;if(end>input.length)throw new Error('Canvas PNG chunks are truncated.');
    const kind=String.fromCharCode(...input.subarray(offset+4,offset+8));
    if(kind==='IEND'){pieces.push(chunk);found=true;}
    const isPriorView=kind==='iTXt'&&new TextDecoder().decode(input.subarray(offset+8,offset+19))==='AerialView\0';if(!isPriorView)pieces.push(input.subarray(offset,end));
    offset=end;if(kind==='IEND')break;
  }
  if(!found)throw new Error('Canvas PNG end chunk is missing.');return new Blob(pieces,{type:'image/png'});
}
