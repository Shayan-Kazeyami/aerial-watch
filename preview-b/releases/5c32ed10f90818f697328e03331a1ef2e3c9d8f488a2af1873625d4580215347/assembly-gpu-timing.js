// Opt-in, local-only WebGL2 GPU timing. Call poll() on a later animation frame,
// then begin()/end() around composer.render(), with end() in a finally block.
// No gl.finish(), synchronous result waits, quality changes or network activity.
// https://registry.khronos.org/webgl/extensions/EXT_disjoint_timer_query_webgl2/
export function createGPUTiming(gl,{enabled=false,now=()=>performance.now(),intervalMs=1000,timeoutMs=10000,capacity=120}={}) {
  intervalMs=Math.max(1000,Number.isFinite(intervalMs)?intervalMs:1000);
  timeoutMs=Math.max(intervalMs,Number.isFinite(timeoutMs)?timeoutMs:10000);
  capacity=Math.max(1,Math.min(600,Math.floor(capacity)||120));
  let ext=null,status=enabled?'unsupported':'disabled',active=null,pending=null,lastStart=-Infinity,disposed=false,disjointSeen=false;
  const samples=[];let disjointEvents=0,discarded=0,timeouts=0,collisions=0,errors=0,totalSamples=0;
  const lost=()=>!!gl?.isContextLost?.();
  function remove(query){if(query&&!lost())gl.deleteQuery(query);}
  function clear(){
    if(active&&!lost()&&gl.getQuery(ext.TIME_ELAPSED_EXT,gl.CURRENT_QUERY)===active.query)gl.endQuery(ext.TIME_ELAPSED_EXT);
    remove(active?.query);remove(pending?.query);active=pending=null;
  }
  function fail(){errors++;try{clear();}catch{}status='error';}
  function init(){
    if(disposed||!enabled)return;
    try{
      if(lost()){status='context-lost';return;}
      ext=typeof gl?.createQuery==='function'?gl.getExtension('EXT_disjoint_timer_query_webgl2'):null;
      status=ext?'ready':'unsupported';
    }catch{fail();}
  }
  function onLost(){active=pending=null;ext=null;samples.length=0;status='context-lost';}
  function onRestored(){lastStart=-Infinity;disjointSeen=false;init();}
  function usable(){if(disposed||status!=='ready')return false;if(lost()){onLost();return false;}return true;}
  function disjoint(){
    const value=!!gl.getParameter(ext.GPU_DISJOINT_EXT);
    if(value){if(!disjointSeen)disjointEvents++;discarded+=Number(!!active)+Number(!!pending);clear();}
    disjointSeen=value;return value;
  }
  init();
  if(enabled){gl?.canvas?.addEventListener('webglcontextlost',onLost);gl?.canvas?.addEventListener('webglcontextrestored',onRestored);}
  return {
    begin(){
      if(!usable())return false;
      try{
        const time=now();if(active||pending||time-lastStart<intervalMs||disjoint())return false;
        if(gl.getQuery(ext.TIME_ELAPSED_EXT,gl.CURRENT_QUERY)!==null){collisions++;return false;}
        const query=gl.createQuery();if(!query)return false;
        active={query,start:time};gl.beginQuery(ext.TIME_ELAPSED_EXT,query);lastStart=time;return true;
      }catch{fail();return false;}
    },
    end(){
      if(!usable()||!active)return;
      try{
        if(gl.getQuery(ext.TIME_ELAPSED_EXT,gl.CURRENT_QUERY)!==active.query){collisions++;discarded++;remove(active.query);active=null;return;}
        gl.endQuery(ext.TIME_ELAPSED_EXT);pending={...active,ended:now()};active=null;
      }catch{fail();}
    },
    poll(){
      if(!usable())return;
      try{
        if(disjoint())return;
        const time=now();
        if(active&&time-active.start>=timeoutMs){timeouts++;discarded++;clear();return;}
        if(!pending||time<=pending.ended)return;
        if(time-pending.start>=timeoutMs){timeouts++;discarded++;clear();return;}
        if(!gl.getQueryParameter(pending.query,gl.QUERY_RESULT_AVAILABLE))return;
        const ns=gl.getQueryParameter(pending.query,gl.QUERY_RESULT);
        remove(pending.query);pending=null;
        if(Number.isFinite(ns)&&ns>0){samples.push(ns/1e6);totalSamples++;if(samples.length>capacity)samples.shift();}
        else discarded++;
      }catch{fail();}
    },
    reset(){
      if(disposed)return;
      try{clear();}catch{fail();return;}
      samples.length=0;totalSamples=disjointEvents=discarded=timeouts=collisions=errors=0;
      // Retain lastStart so resetting diagnostics cannot exceed one query/sec.
    },
    snapshot(){
      const sorted=[...samples].sort((a,b)=>a-b),percentile=q=>sorted.length?sorted[Math.min(sorted.length-1,Math.floor(sorted.length*q))]:null;
      return {enabled,status,supported:ext!==null,sampleCount:samples.length,totalSamples,gpuFrameMs:{median:percentile(.5),p95:percentile(.95)},
        pendingQueries:Number(!!active)+Number(!!pending),disjointEvents,discarded,timeouts,collisions,errors,intervalMs,
        note:'Opt-in GPU elapsed time for sampled composed frames; excludes CPU work. Unsupported, invalid and absent measurements are unknown, never zero. No device FPS inferred.'};
    },
    dispose(){if(disposed)return;try{clear();}catch{errors++;}disposed=true;status='disposed';
      if(enabled){gl?.canvas?.removeEventListener('webglcontextlost',onLost);gl?.canvas?.removeEventListener('webglcontextrestored',onRestored);}
    },
  };
}
