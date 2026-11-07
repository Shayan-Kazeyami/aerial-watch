// Playwright helper. Read-only DOM/assemblyInspect observations, no app state mutation.
export async function installCaptureLayoutProbe(page){
 await page.addInitScript(()=>{
  window.__qaCaptureLayout=[];
  document.addEventListener('click',event=>{
   const button=event.target.closest?.('[data-proxy]');if(!['capture-scene','record-scene'].includes(button?.dataset.proxy))return;
   const probe={action:button.dataset.proxy,start:performance.now(),samples:[],frames:[],ended:null};window.__qaCaptureLayout.push(probe);
   let active=true,raf=0,timer=0;
   const sample=()=>{const stage=document.getElementById('stage'),canvas=document.getElementById('assembly-canvas'),context=document.getElementById('context');if(!stage||!canvas)return;const r=stage.getBoundingClientRect(),state=window.assemblyInspect?.();probe.samples.push({at:performance.now()-probe.start,width:r.width,height:r.height,canvasWidth:canvas.width,canvasHeight:canvas.height,aspectError:Math.abs(canvas.width*r.height-canvas.height*r.width),aspectTolerance:r.width+r.height,contextHidden:context?.hidden,panelOpen:document.body.dataset.panelOpen,panelMedia:matchMedia('(max-width:680px)').matches,status:document.getElementById('status')?.textContent,exportNotice:document.getElementById('atelier-export-notice')?.textContent,recordButton:document.getElementById('record-scene')?.textContent,animation:state?.animation,interiorAnimation:state?.interiorAnimation,quality:state?.renderQuality});};
   const stop=()=>{if(!active)return;active=false;clearInterval(timer);cancelAnimationFrame(raf);sample();probe.ended=performance.now()-probe.start;};
   const frame=at=>{if(!active)return;probe.frames.push(at-probe.start);if(probe.frames.length>120)probe.frames.shift();raf=requestAnimationFrame(frame);};
   sample();timer=setInterval(sample,200);raf=requestAnimationFrame(frame);setTimeout(stop,20000);window.addEventListener('pagehide',stop,{once:true});
  },true);
 });
}
export async function readCaptureLayoutProbe(page){return page.evaluate(()=>window.__qaCaptureLayout||[]);}
