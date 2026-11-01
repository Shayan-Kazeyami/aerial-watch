/** Review-only: lossless file reassembly, not texture compression.
 * manager MUST be dedicated to this one asset parse. No global manager changes.
 * deadline is one absolute performance.now() deadline shared with the caller.
 * Callback must use supplied signal/remainingMs for the existing asset loader.
 */
const activeManagers = new WeakSet();
const timeoutError = () => Object.assign(new Error('Chunked texture deadline exceeded.'), {name:'TimeoutError'});
const fail = message => { throw new Error(message); };
const integer = n => Number.isSafeInteger(n) && n > 0;
const hashPattern = /^[a-f0-9]{64}$/;
function relativeURL(path, base) {
  if (typeof path !== 'string' || !path || /[\\:%?#]/.test(path) || path.startsWith('/') || path.split('/').some(p=>!p || p==='.' || p==='..')) fail('Unsafe relative resource path.');
  const url=new URL(path,base);
  if(url.origin!==base.origin || !['https:','http:'].includes(url.protocol)) fail('Cross-origin resource refused.');
  return url.href;
}
async function readBounded(response, limit, signal) {
  if(!response?.ok) fail(`Resource request failed (${response?.status ?? 'unknown'}).`);
  const declared=response.headers?.get('content-length');
  if(declared!==null && declared!==undefined && (!/^\d+$/.test(declared) || Number(declared)>limit)) fail('Resource exceeds byte limit.');
  if(!response.body?.getReader) fail('A bounded readable response body is required.');
  const reader=response.body.getReader(), parts=[];let bytes=0,complete=false;
  const cancel=()=>{reader.cancel(signal.reason).catch(()=>{});};
  signal.addEventListener('abort',cancel,{once:true});
  try {
    for(;;){signal.throwIfAborted();const {done,value}=await reader.read();signal.throwIfAborted();if(done){complete=true;break;}bytes+=value.byteLength;if(bytes>limit)fail('Resource exceeds byte limit.');parts.push(value);}
    const result=new Uint8Array(bytes);let offset=0;for(const part of parts){result.set(part,offset);offset+=part.byteLength;}return result;
  } finally {signal.removeEventListener('abort',cancel);if(!complete)cancel();reader.releaseLock();}
}
export async function withChunkedTexture(options, parseAsset) {
  const {manager,manifestURL,baseURL=globalThis.location?.href,signal,deadline,maxBytes,
    expectedBytes,expectedSha256,disposeLateResult=()=>{},
    fetchImpl=globalThis.fetch,cryptoImpl=globalThis.crypto,urlAPI=globalThis.URL,
    locationHref=globalThis.location?.href,
    now=()=>performance.now()}=options;
  if(!manager || typeof manager.resolveURL!=='function' || typeof parseAsset!=='function') throw new TypeError('A dedicated manager and parse callback are required.');
  if(activeManagers.has(manager)) fail('Manager already has an active chunked asset.');
  if(!Number.isFinite(deadline) || !integer(maxBytes) || !integer(expectedBytes) || expectedBytes>maxBytes || !hashPattern.test(expectedSha256)) throw new TypeError('Audited hash/bytes, maxBytes and absolute deadline are required.');
  if(!cryptoImpl?.subtle?.digest) fail('SHA-256 verification is unavailable.');
  const base=new URL(baseURL);if(!['https:','http:'].includes(base.protocol))fail('HTTP(S) base URL required.');
  if(locationHref && base.origin!==new URL(locationHref).origin)fail('Base URL must match the browser origin.');
  const manifestAddress=relativeURL(manifestURL,base);
  signal?.throwIfAborted();if(deadline<=now())throw timeoutError();
  if(deadline-now()>2147483647)throw new RangeError('Deadline window exceeds timer range.');
  activeManagers.add(manager);
  const controller=new AbortController();let timer, blobURL, installed=false, ended=false;
  const previousResolve=manager.resolveURL;let wrappedResolve;
  const abort=()=>controller.abort(signal.reason);
  signal?.addEventListener('abort',abort,{once:true});
  const checkpoint=()=>{controller.signal.throwIfAborted();const remaining=deadline-now();if(remaining<=0){controller.abort(timeoutError());controller.signal.throwIfAborted();}return remaining;};
  const interrupted=new Promise((_,reject)=>{
    controller.signal.addEventListener('abort',()=>reject(controller.signal.reason),{once:true});
    timer=setTimeout(()=>controller.abort(timeoutError()),Math.min(2147483647,deadline-now()));
  });
  const request=async (url,limit)=>{
    checkpoint();const response=await fetchImpl(url,{signal:controller.signal,redirect:'error',credentials:'same-origin'});checkpoint();
    if(response.redirected || (response.url && response.url!==url))fail('Redirected resource refused.');
    try{return await readBounded(response,limit,controller.signal);}
    catch(error){if(response.body && !response.body.locked)await response.body.cancel().catch(()=>{});throw error;}
  };
  const run=async()=>{
    const encoded=await request(manifestAddress,65536);checkpoint();
    const manifest=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(encoded));
    if(manifest.version!==1 || manifest.bytes!==expectedBytes || manifest.sha256!==expectedSha256 || !Array.isArray(manifest.chunks) || !manifest.chunks.length || manifest.chunks.length>32)fail('Manifest does not match audited texture.');
    const directory=new URL('.',manifestAddress),canonical=relativeURL(manifest.texture,directory);
    let total=0;const paths=new Set();
    const chunks=manifest.chunks.map(c=>{
      if(!integer(c.bytes) || c.bytes>8*1024*1024)fail('Invalid chunk size.');
      const address=relativeURL(c.uri,directory);if(paths.has(address))fail('Duplicate chunk path.');paths.add(address);total+=c.bytes;
      if(total>maxBytes || total>expectedBytes)fail('Manifest exceeds byte limit.');return {...c,address};
    });
    if(total!==expectedBytes)fail('Chunk lengths do not match audited total.');
    const bytes=new Uint8Array(total);let offset=0;
    for(const chunk of chunks){const part=await request(chunk.address,chunk.bytes);checkpoint();if(part.byteLength!==chunk.bytes)fail('Chunk byte length mismatch.');bytes.set(part,offset);offset+=part.byteLength;}
    const digest=await cryptoImpl.subtle.digest('SHA-256',bytes);checkpoint();
    const actual=[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');
    if(actual!==expectedSha256)fail('Texture SHA-256 mismatch.');
    // Verify KTX2 signature, preventing accidental wrong asset publication.
    const magic=[171,75,84,88,32,50,48,187,13,10,26,10];
    if(!magic.every((v,i)=>bytes[i]===v))fail('Verified file is not KTX2.');
    blobURL=urlAPI.createObjectURL(new Blob([bytes],{type:'image/ktx2'}));checkpoint();
    wrappedResolve=function(url){let resolved;try{resolved=new URL(url,base).href;}catch{}return resolved===canonical?blobURL:previousResolve.call(this,url);};
    manager.resolveURL=wrappedResolve;installed=true;
    const result=await parseAsset({signal:controller.signal,remainingMs:checkpoint,canonicalTextureURL:canonical,textureBytes:total,sha256:actual});
    if(ended || controller.signal.aborted){disposeLateResult(result);controller.signal.throwIfAborted();throw new Error('Asset parse completed after scope ended.');}
    try{checkpoint();}catch(error){disposeLateResult(result);throw error;}return result;
  };
  try{return await Promise.race([run(),interrupted]);}
  finally {
    ended=true;clearTimeout(timer);signal?.removeEventListener('abort',abort);
    if(installed && manager.resolveURL===wrappedResolve)manager.resolveURL=previousResolve;
    if(blobURL)urlAPI.revokeObjectURL(blobURL);
    activeManagers.delete(manager);
  }
}
