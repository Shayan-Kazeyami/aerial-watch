// Opt-in CPU wall-time observations, not GPU execution or physical-device claims.
export function createStartupDiagnostics({enabled=false,now=()=>performance.now(),capacity=256}={}){
 const start=enabled?now():0,events=[],shader={compileCalls:0,compileSubmitMs:0,linkCalls:0,linkSubmitMs:0,supported:false};let restore=()=>{};
 const mark=phase=>{if(enabled&&events.length<capacity)events.push({phase,elapsedMs:now()-start});};
 const measure=(phase,work)=>{if(!enabled)return work();mark(phase+':start');try{return work();}finally{mark(phase+':end');}};
 const observeWebGL=gl=>{
  if(!enabled||!gl)return;restore();const restorers=[];
  for(const [method,calls,duration] of [['compileShader','compileCalls','compileSubmitMs'],['linkProgram','linkCalls','linkSubmitMs']]){
   const original=gl[method];if(typeof original!=='function')continue;
   const wrapped=function(...args){const begin=now();try{return original.apply(this,args);}finally{shader[calls]++;shader[duration]+=now()-begin;}};
   try{gl[method]=wrapped;if(gl[method]===wrapped)restorers.push(()=>{if(gl[method]===wrapped)gl[method]=original;});}catch{/* Unsupported observation is not a rendering failure. */}
  }
  shader.supported=restorers.length===2;restore=()=>{for(const undo of restorers)try{undo();}catch{};restorers.length=0;};
 };
 return {mark,measure,observeWebGL,stop:()=>restore(),snapshot:()=>({enabled,events:events.map(e=>({...e})),shader:{...shader},notes:'CPU phase wall times; shader compile/link API submission only, excluding asynchronous driver/GPU work. Fetch and parsing may overlap. First selected frame means render returned, not presentation scanout. No phone/network speed inference.'})};
}
