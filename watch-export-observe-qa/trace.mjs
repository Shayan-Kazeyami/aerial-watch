// Test-only synchronous event ledger. No timers, networking, storage, or telemetry.
export function createExportTrace({now=()=>performance.now(),maxEvents=8192}={}) {
 const events=[];let active=null,lastError=null,dropped=0,sequence=0;
 const emit=(kind,detail={})=>{const event={seq:++sequence,atMs:now(),kind,...detail};if(events.length<maxEvents)events.push(event);else dropped++;return event;};
 return {
  begin(phase,detail={}){if(active)throw Error('Overlapping QA phase');const e=emit('begin',{phase,...detail});active={phase,startMs:e.atMs,...detail};},
  end(phase){if(active?.phase!==phase)throw Error('Mismatched QA phase');emit('end',{phase,elapsedMs:now()-active.startMs});active=null;},
  fail(error){lastError={name:error?.name||'Error',message:String(error?.message||error),phase:active?.phase??null};emit('error',lastError);active=null;},
  note(kind,detail={}){emit(kind,detail);},
  snapshot(status={}){const atMs=now();return {atMs,active:active?{...active,elapsedMs:atMs-active.startMs}:null,lastError,events:events.map(e=>({...e})),dropped,status:{...status},scope:'test-only instrumented timing; not production or hardware performance'};},
 };
}
