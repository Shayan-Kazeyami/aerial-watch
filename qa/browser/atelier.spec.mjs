import {test,expect} from '@playwright/test';
import {readFile,writeFile} from 'node:fs/promises';
const base=process.env.WATCH_QA_URL||'http://127.0.0.1:8765/atelier-preview.html?quality=efficient';
const expectedDigest=process.env.WATCH_QA_DIGEST;if(!expectedDigest)throw Error('Transformed digest required');
const candidateSHA='f7876b6be8b445a8e72db355fd1dd2705bec13dc19754884ac765c90f8ee7ea2';
test('transformed combined candidate: exact release, hinge, cap and reset smoke',async({page},info)=>{
 const evidence={environment:'GitHub-hosted Chromium headless / requested ANGLE SwiftShader software WebGL. NOT S24, hardware performance, WebGPU parity or visual approval.',requestedURL:base,events:[],console:[],pageErrors:[],httpErrors:[],requestFailures:[],snapshots:[],steps:[]};
 let step='navigation';
 page.on('console',m=>{if(['warning','error'].includes(m.type()))evidence.console.push({step,type:m.type(),text:m.text(),location:m.location()});});
 page.on('pageerror',e=>evidence.pageErrors.push({step,message:e.message,stack:e.stack}));
 page.on('response',r=>{if(r.status()>=400)evidence.httpErrors.push({step,url:r.url(),status:r.status(),resourceType:r.request().resourceType()});});
 page.on('requestfailed',r=>evidence.requestFailures.push({step,url:r.url(),method:r.method(),resourceType:r.resourceType(),failure:r.failure()}));
 await page.addInitScript(()=>{window.__qaPresentation=[];document.addEventListener('atelier:presentation-state',e=>window.__qaPresentation.push({at:performance.now(),detail:e.detail}));});
 const setStep=name=>{step=name;evidence.steps.push({name,at:new Date().toISOString()});};
 const settle=async(expected={})=>{
  await page.waitForFunction(expected=>{
   const s=window.assemblyInspect?.();if(!s||s.loading||s.failed||s.presentation?.phase!=='ready'||s.presentation?.pending?.length||!s.presentation?.interactive)return false;
   const c=s.comparisonLoading;if(c?.loading||c?.failure||(c?.needed&&(!c.formReady||!c.architectureReady)))return false;
   return Object.entries(expected).every(([key,value])=>s[key]===value);
  },expected,{timeout:180000});
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 };
 const panel=async mode=>{await page.locator(`[data-mode="${mode}"]`).filter({visible:true}).first().click();await expect(page.locator('#context')).toBeVisible();};
 const capture=async name=>{await page.screenshot({path:info.outputPath(name+'.png')});};
 async function savedView(name){
  setStep(name);await settle();await panel('capture');
  const pending=page.waitForEvent('download',{timeout:120000});await page.locator('#atelier-tools [data-proxy="export-config"]').click();
  const download=await pending;expect(await download.failure()).toBeNull();const path=info.outputPath(name+'.json');await download.saveAs(path);
  const config=JSON.parse(await readFile(path,'utf8'));evidence.snapshots.push({name,path,cap:config.capRefinement,renderer:config.renderer,GPU:config.GPU,options:config.options,warnings:config.warnings,sourceAtCapture:config.sourceAtCapture});
  expect(config.sourceAtCapture?.status).toBe('verified');expect(config.sourceAtCapture?.digest).toBe(expectedDigest);expect(config.premiumFace?.ready).toBe(true);expect(config.leatherCraft?.candidate?.identity?.id).toBe('strap-hinge-skin-sourcecharts-r16-candidate');expect(config.leatherCraft?.candidate?.geometryVerification?.actualSha256).toBe('d473da297e6dd6565c8c98b3b3e36602f6ed7703c60e51a0205d2ac070825fb0');expect(config.leatherCraft?.candidate?.geometryVerification?.status).toBe('verified');evidence.snapshots.at(-1).leather=config.leatherCraft;
  expect(config.capRefinement?.active).toBe(true);expect(config.capRefinement?.fixedGeometry).toBe(true);expect(config.capRefinement?.candidatePositionSHA256).toBe(candidateSHA);
  expect(config.renderer?.backend).not.toMatch(/webgpu/i);return config;
 }
 try{
  await page.goto(base,{waitUntil:'domcontentloaded',timeout:60000});
  evidence.resolvedURL=page.url();
  await expect(page.locator('#assembly-canvas')).toBeVisible();
  await expect(page.locator('#home')).toBeEnabled({timeout:240000});await settle({openWork:true});
  await expect(page.locator('#assembly-canvas')).toHaveAttribute('aria-busy','false');
  await expect(page.locator('#atelier-retry')).toBeHidden();
  setStep('ready');evidence.readyStatus=await page.locator('#status').innerText();
  if(await page.locator('#motion').getAttribute('aria-pressed')==='true')await page.locator('#motion').click();
  await settle();await capture('whole-watch-ready');await savedView('initial');
  for(let cycle=0;cycle<2;cycle++){
   setStep('comparison-cycle-'+cycle);await panel('settings');await page.locator('#atelier-tools [data-mode="engineering"]').click();
   const face=page.locator('#atelier-tools [data-check="open-work"]');await face.uncheck();await expect(page.locator('#open-work')).not.toBeChecked();await settle({openWork:false});
   const original=await savedView('original-'+cycle);expect(original.options.openWork).toBe(false);
   await panel('settings');await page.locator('#atelier-tools [data-mode="engineering"]').click();await page.locator('#atelier-tools [data-check="open-work"]').check();await settle({openWork:true});
   const premium=await savedView('premium-'+cycle);expect(premium.options.openWork).toBe(true);
  }
  for(const quality of ['balanced','detail','studio','efficient']){
   setStep('quality-'+quality);await panel('quality');await page.locator(`#atelier-tools [data-quality="${quality}"]`).click();await expect(page.locator('#render-quality')).toHaveValue(quality);await settle({renderQuality:quality});
   const config=await savedView('quality-'+quality);expect(config.options.quality).toBe(quality);
  }
  setStep('lug-view');await panel('settings');await page.locator('#atelier-tools [data-camera="lug"]').click();await expect(page.locator('#runtime-bridge [data-view="lug"]')).toHaveAttribute('aria-pressed','true');await page.locator('#close').click();await page.waitForTimeout(1000);await settle();await capture('lug-control-closeup');await savedView('lug-closeup');
  setStep('reset');await page.locator('#home').click();await settle({openWork:true});const reset=await savedView('after-reset');expect(reset.options.openWork).toBe(true);
  await page.locator('#close').click();await page.waitForTimeout(1000);await capture('whole-watch-after-reset');
  // Actual user-visible PNG action; no canvas monkey-patching or synthetic download.
  if(process.env.WATCH_QA_PNG==='1'){
   setStep('png-export');await panel('capture');const pending=page.waitForEvent('download',{timeout:120000});await page.locator('#atelier-tools [data-proxy="capture-scene"]').click();const download=await pending;expect(await download.failure()).toBeNull();const path=info.outputPath('actual-export.png');await download.saveAs(path);const bytes=await readFile(path);expect([...bytes.subarray(0,8)]).toEqual([137,80,78,71,13,10,26,10]);evidence.png={bytes:bytes.length,suggestedFilename:download.suggestedFilename()};
  }
  expect(evidence.pageErrors).toEqual([]);expect(evidence.httpErrors).toEqual([]);expect(evidence.requestFailures).toEqual([]);
  expect(evidence.console.filter(x=>x.type==='error')).toEqual([]);
 }finally{
  evidence.events=await page.evaluate(()=>window.__qaPresentation||[]).catch(()=>[]);
  evidence.finalStatus=await page.locator('#status').textContent().catch(()=>null);
  evidence.finalURL=page.url();await writeFile(info.outputPath('evidence.json'),JSON.stringify(evidence,null,2));await info.attach('software-browser-evidence',{path:info.outputPath('evidence.json'),contentType:'application/json'});
 }
});

