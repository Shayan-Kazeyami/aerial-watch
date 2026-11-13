// Explicit, temporary local diagnostic. Render submission/CPU cadence is not GPU time.
const stats=values=>{if(!values.length)return null;const a=[...values].sort((a,b)=>a-b);return {mean:values.reduce((a,b)=>a+b,0)/values.length,p50:a[Math.floor((a.length-1)*.5)],p95:a[Math.floor((a.length-1)*.95)],max:a.at(-1)};};
export function createDebugBenchmark({context=()=>({}),emit=()=>{},warmupMs=1000,durationMs=10000}={}){
 let state={phase:'idle'},start=null,first=null,last=null,samples=[],snapshot=null,signature=null,lastPublish=-Infinity;
 const publish=()=>emit({...state});
 const cancel=reason=>{if(!['warming','running'].includes(state.phase))return;state={phase:'cancelled',reason};samples=[];publish();};
 return {
  get active(){return ['warming','running'].includes(state.phase);},get state(){return {...state};},
  start(){if(this.active)return;start=first=last=null;samples=[];snapshot=context();signature=JSON.stringify(snapshot.stability);lastPublish=-Infinity;state={phase:'warming',secondsRemaining:(warmupMs+durationMs)/1000};publish();},
  cancel,
  frame(sample){
   if(!this.active)return;if(!Number.isFinite(sample.timestamp)||!Number.isFinite(sample.cpuMs))return;
   if(JSON.stringify(context().stability)!==signature){cancel('Quality, viewport, assets or renderer changed. Run again with stable settings.');return;}
   start??=sample.timestamp;const elapsed=sample.timestamp-start;
   if(elapsed<warmupMs){state={phase:'warming',secondsRemaining:Math.ceil((warmupMs+durationMs-elapsed)/1000)};}
   else{first??=sample.timestamp;const interval=last===null?null:sample.timestamp-last;last=sample.timestamp;samples.push({...sample,interval});state={phase:'running',secondsRemaining:Math.max(0,Math.ceil((durationMs-(sample.timestamp-first))/1000))};
    if(sample.timestamp-first>=durationMs){const elapsedMs=sample.timestamp-first,intervals=samples.flatMap(s=>s.interval===null?[]:[s.interval]);state={phase:'complete',result:{protocol:'Current view, continuous render; 1 s warm-up then 10 s measurement; motion and camera are not reset',context:snapshot,elapsedMs,renderedFrames:samples.length,renderedFPS:elapsedMs>0?(samples.length-1)*1000/elapsedMs:null,renderedIntervalMs:stats(intervals),cpuUpdateAndSubmissionMs:stats(samples.map(s=>s.cpuMs)),drawCallsPerRenderedFrame:stats(samples.map(s=>s.drawCalls).filter(Number.isFinite)),trianglesPerRenderedFrame:stats(samples.map(s=>s.triangles).filter(Number.isFinite)),gpuTimeMs:null,notes:'Frame cadence includes scheduling and renderer submission. CPU duration is not GPU duration. Draw calls and triangles include passes counted by Three.js, not unique model polygons. Browser, quality, view and device affect results. No results are uploaded.'}};publish();return;}}
   if(sample.timestamp-lastPublish>=500){lastPublish=sample.timestamp;publish();}
  },dispose(){cancel('Viewer closed.');samples=[];}
 };
}

export function createBenchmarkSuite({context,applyQuality,emit=()=>{},presets=['efficient','balanced','detail','studio'],now=()=>Date.now(),warmupMs=1000,durationMs=10000}={}){
 let running=false,index=0,original=null,initial=null,startedAt=null,rows=[],trial=null,state={phase:'idle'};
 const publish=()=>emit({...state});
 function finish(status,reason,restore=true){running=false;trial=null;let restoreError=null;if(restore)try{applyQuality(original);}catch(e){restoreError=String(e.message||e);}state={phase:status==='complete'?'complete':'cancelled',reason,result:{schemaVersion:1,status,reason:reason||null,startedAt:new Date(startedAt).toISOString(),finishedAt:new Date(now()).toISOString(),method:{warmupMs,measurementMs:durationMs,presets,scene:'Current camera and motion state; continuous render forced only during tests',gpuTiming:'unavailable; not measured',transfer:'Local only. Copy/download explicitly to share.'},context:initial,originalQuality:original,restoredQuality:restore&&!restoreError?original:null,restoreError,presets:rows}};publish();}
 function advance(){if(!running)return;if(index>=presets.length){finish('complete');return;}const preset=presets[index];try{applyQuality(preset);if(context().quality!==preset)throw new Error('Preset was not applied');}catch(error){rows.push({preset,status:'unsupported',reason:String(error.message||error)});index++;advance();return;}
  trial=createDebugBenchmark({context,warmupMs,durationMs,emit:detail=>{if(!running)return;state={...detail,preset,index:index+1,total:presets.length};if(detail.phase!=='complete'&&detail.phase!=='cancelled')publish();}});trial.start();
 }
 return {get active(){return running;},get state(){return {...state};},start(){if(running)return;initial=context();original=initial.quality;startedAt=now();rows=[];index=0;running=true;advance();},frame(sample){if(!running||!trial)return;trial.frame(sample);if(trial.state.phase==='complete'){rows.push({preset:presets[index],status:'complete',...trial.state.result});index++;advance();}else if(trial.state.phase==='cancelled'){rows.push({preset:presets[index],status:'interrupted',reason:trial.state.reason});finish('interrupted',trial.state.reason);}},cancel(reason='Cancelled by user.',{restore=true}={}){if(!running)return;rows.push({preset:presets[index],status:'interrupted',reason});finish('interrupted',reason,restore);},dispose(){this.cancel('Viewer closed.');}};
}
