// Explicit, temporary local diagnostic. Render submission/CPU cadence is not GPU time.
const stats=values=>{if(!values.length)return null;const a=[...values].sort((a,b)=>a-b);return {mean:values.reduce((a,b)=>a+b,0)/values.length,p50:a[Math.max(0,Math.ceil(a.length*.5)-1)],p95:a[Math.max(0,Math.ceil(a.length*.95)-1)],max:a.at(-1)};};
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
    if(sample.timestamp-first>=durationMs){const elapsedMs=sample.timestamp-first,intervals=samples.flatMap(s=>s.interval===null?[]:[s.interval]);state={phase:'complete',result:{protocol:'Saved view, frozen mechanism pose, continuous render; 1 s warm-up then at least 10 s measurement',context:snapshot,elapsedMs,renderedFrames:samples.length,sampleWarning:samples.length<30?'Fewer than 30 rendered frames; sparse cadence sample, percentiles are not reliable.':null,percentileMethod:'Nearest rank; intervals exclude the first measured frame.',renderedFPS:elapsedMs>0?(samples.length-1)*1000/elapsedMs:null,renderedIntervalMs:stats(intervals),cpuUpdateAndSubmissionMs:stats(samples.map(s=>s.cpuMs)),drawCallsPerRenderedFrame:stats(samples.map(s=>s.drawCalls).filter(Number.isFinite)),trianglesPerRenderedFrame:stats(samples.map(s=>s.triangles).filter(Number.isFinite)),gpuTimeMs:null,notes:'Frame cadence includes scheduling and renderer submission. CPU duration is not GPU duration. Draw calls and triangles include passes counted by Three.js, not unique model polygons. Browser, quality, view and device affect results. No results are uploaded.'}};publish();return;}}
   if(sample.timestamp-lastPublish>=500){lastPublish=sample.timestamp;publish();}
  },dispose(){cancel('Viewer closed.');samples=[];}
 };
}

