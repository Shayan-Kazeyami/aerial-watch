import {test,expect} from '@playwright/test';
import {readFile,writeFile} from 'node:fs/promises';
const url=process.env.WATCH_QA_URL||'http://127.0.0.1:8765/atelier-preview.html?quality=efficient';
test('studio-quality real viewer material contact sheet sources',async({page},info)=>{
 test.setTimeout(600000);
 const report={scope:'Actual candidate viewer captures, hosted software WebGL. Human visual review required; no automated aesthetic approval, no physical phone or WebGPU parity.',url,shots:[],errors:[],warnings:[]};
 let shot='startup';page.on('pageerror',e=>report.errors.push({shot,type:'pageerror',message:e.message,stack:e.stack}));page.on('console',m=>{if(m.type()==='error'||m.type()==='warning')report[m.type()==='error'?'errors':'warnings'].push({shot,type:m.type(),message:m.text(),location:m.location()});});page.on('response',r=>{if(r.status()>=400)report.errors.push({shot,type:'http',url:r.url(),status:r.status()});});page.on('requestfailed',r=>report.errors.push({shot,type:'requestfailed',url:r.url(),failure:r.failure()}));
 const panel=async name=>{await page.locator(`[data-mode="${name}"]:visible`).first().click();};
 const ready=async view=>{await page.waitForFunction(view=>{const s=window.assemblyInspect?.(),c=s?.comparisonLoading;return s&&!s.loading&&!s.failed&&s.presentation?.phase==='ready'&&!s.presentation.pending.length&&!c?.loading&&!c?.failure&&(!view||s.view===view);},view,{timeout:240000});};
 async function stableCamera(){
  let previous=null,count=0;
  await expect.poll(async()=>{const state=await page.evaluate(()=>{const s=window.assemblyInspect();return JSON.stringify({camera:s.camera,target:s.target,view:s.view});});count=state===previous?count+1:0;previous=state;return count;},{timeout:30000,intervals:[250]}).toBeGreaterThanOrEqual(3);
  await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
 }
 let pose;
 async function save(name,view,notes){
  shot=name;await ready(view);if(await page.locator('#context').isVisible())await page.locator('#close').click();await stableCamera();
  const actual=await page.evaluate(()=>window.assemblyInspect());expect(actual.renderQuality).toBe('studio');expect(actual.animation).toBe(false);expect(actual.interiorAnimation).toBe(false);expect(actual.mechanismElapsed).toBe(pose.mechanismElapsed);expect(actual.illustrativeElapsed).toBe(pose.illustrativeElapsed);
  const canvasPath=info.outputPath(name+'-canvas.png');await page.locator('#assembly-canvas').screenshot({path:canvasPath});await page.screenshot({path:info.outputPath(name+'-ui.png')});
  await panel('capture');const wait=page.waitForEvent('download',{timeout:120000});await page.locator('#atelier-tools [data-proxy="export-config"]').click();const file=await wait;expect(await file.failure()).toBeNull();const path=info.outputPath(name+'.json');await file.saveAs(path);const config=JSON.parse(await readFile(path,'utf8'));
  expect(config.capRefinement?.active).toBe(true);expect(config.capRefinement?.candidatePositionSHA256).toBe('f7876b6be8b445a8e72db355fd1dd2705bec13dc19754884ac765c90f8ee7ea2');expect(config.options.quality).toBe('studio');expect(config.options.finishes).toBe(true);
  report.shots.push({name,notes,canvasPath,configPath:path,view:config.view,renderer:config.renderer,GPU:config.GPU,lightRig:config.lightRig,cap:config.capRefinement,options:config.options,source:config.sourceAtCapture,clock:config.clock,inspect:actual});await page.locator('#close').click();
 }
 try{
  await page.goto(url,{waitUntil:'domcontentloaded'});await ready();
  report.adapter=await page.evaluate(()=>{
   const canvas=document.getElementById('assembly-canvas'),gl=canvas.getContext('webgl2')||canvas.getContext('webgl');
   if(!gl)return {userAgent:navigator.userAgent,context:'no existing WebGL context'};
   const ext=gl.getExtension('WEBGL_debug_renderer_info');return {userAgent:navigator.userAgent,version:gl.getParameter(gl.VERSION),shadingLanguageVersion:gl.getParameter(gl.SHADING_LANGUAGE_VERSION),vendor:gl.getParameter(gl.VENDOR),renderer:gl.getParameter(gl.RENDERER),debugRendererInfoAvailable:!!ext,unmaskedVendor:ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):null,unmaskedRenderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):null};
  });
  await page.locator('#home').click();await ready();
  // Home resets real hand/mechanism pose and pauses playback before every shot series.
  await panel('quality');await page.locator('#atelier-tools [data-quality="studio"]').click();await expect(page.locator('#render-quality')).toHaveValue('studio');pose=await page.evaluate(()=>window.assemblyInspect());
  await panel('explore');await save('01-face','face','Actual Explore camera; front-facing face/glass, not a fabricated front-camera control.');
  for(const [name,view,notes] of [
   ['02-portrait','three-quarter','Hero/portrait: glass highlights, overall metal and leather balance.'],
   ['03-reverse','back','Rear case and leather; existing Reverse view.'],
   ['04-profile','side','Case thickness, glass edge and metal reflections.'],
   ['05-lugs','lug','Lug/cap region and leather connection; existing camera, not guaranteed isolated macro.'],
   ['06-buckle','buckle','Leather grain/stitching and buckle finish.']]){
   await panel('settings');await page.locator(`#atelier-tools [data-camera="${view}"]`).click();await save(name,view,notes);
  }
  await panel('time');await save('07-crown','crown','Existing Set time panel focuses crown without pulling or turning it.');
  await panel('inside');await save('08-interior','interior','Existing Inside overview, intended geometry visibility differs from exterior views.');
  for(const [name,view,notes] of [['09-balance','balance','Balance and jewel close view.'],['10-gears','train','Gear/train metal and contrast.'],['11-winding','winding','Winding components close view.']]){
   await panel('inside');await page.locator(`#atelier-tools [data-camera="${view}"]`).click();await save(name,view,notes);
  }
  expect(report.errors).toEqual([]);
 }finally{report.finalURL=page.url();await writeFile(info.outputPath('material-review-index.json'),JSON.stringify(report,null,2));}
});
