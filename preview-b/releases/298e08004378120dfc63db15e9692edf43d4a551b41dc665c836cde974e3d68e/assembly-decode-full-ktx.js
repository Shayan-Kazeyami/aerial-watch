// Private study. Caller must pass the independently hash-verified full KTX bytes.
export async function decodeFullKtx({bytes,renderer,makeLoader,signal,timeoutMs=120000}){
 if(!(bytes instanceof Uint8Array)||bytes.byteLength!==16562348)throw TypeError('Verified full KTX bytes required');
 if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw RangeError('Invalid timeout');signal?.throwIfAborted();
 const ctl=new AbortController(),forward=()=>ctl.abort(signal.reason);signal?.addEventListener('abort',forward,{once:true});
 let timer,loader,ended=false,initStarted=false,initSettled=false,disposed=false;const pending=new Set();
 const stopped=()=>ended||ctl.signal.aborted,reason=()=>ctl.signal.reason||Object.assign(Error('Decode ended'),{name:'AbortError'});
 const dispose=()=>{if(loader&&initStarted&&initSettled&&!disposed){disposed=true;loader.dispose();}};
 const interrupted=new Promise((_,reject)=>{ctl.signal.addEventListener('abort',()=>reject(reason()),{once:true});timer=setTimeout(()=>ctl.abort(Object.assign(Error('Normal decode timeout'),{name:'TimeoutError'})),timeoutMs)});
 const run=async()=>{
  loader=await makeLoader();ctl.signal.throwIfAborted();const post=loader.workerPool.postMessage;
  loader.workerPool.postMessage=function(...args){if(stopped())return Promise.reject(reason());return new Promise((resolve,reject)=>{let settled=false;const finish=(fn,x)=>{if(settled)return;settled=true;pending.delete(stop);ctl.signal.removeEventListener('abort',stop);fn(x)};const stop=()=>finish(reject,reason());pending.add(stop);ctl.signal.addEventListener('abort',stop,{once:true});try{Promise.resolve(post.apply(this,args)).then(x=>stopped()?stop():finish(resolve,x),e=>finish(reject,e))}catch(e){finish(reject,e)}})};
  if(renderer.isWebGPURenderer)await renderer.init();ctl.signal.throwIfAborted();loader.detectSupport(renderer);initStarted=true;
  await Promise.resolve(loader.init()).then(()=>{initSettled=true;if(ended)dispose()},e=>{initSettled=true;if(ended)dispose();throw e});ctl.signal.throwIfAborted();
  return new Promise((resolve,reject)=>{try{loader.parse(bytes.byteOffset===0&&bytes.byteLength===bytes.buffer.byteLength?bytes.buffer:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),texture=>{if(stopped()){texture?.dispose();reject(reason());return;}resolve(texture)},reject)}catch(e){reject(e)}});
 };
 try{return await Promise.race([run(),interrupted]);}
 finally{ended=true;if(!ctl.signal.aborted)ctl.abort(Object.assign(Error('Decode ended'),{name:'AbortError'}));for(const stop of pending)stop();clearTimeout(timer);signal?.removeEventListener('abort',forward);dispose();}
}
