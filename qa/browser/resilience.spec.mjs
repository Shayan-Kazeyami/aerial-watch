import {test,expect} from '@playwright/test';
import {readFile,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
const target=process.env.WATCH_QA_URL||'http://127.0.0.1:8765/atelier-preview.html?quality=efficient';
test.setTimeout(600000);
const sha='f7876b6be8b445a8e72db355fd1dd2705bec13dc19754884ac765c90f8ee7ea2';
function recorder(page,info){
 const data={scope:'Simulated hosted desktop Chromium software WebGL. Fault injection is local to this test. Not physical S24, hardware performance or WebGPU acceptance.',events:[],downloads:[]};let step='boot';
 for(const event of ['console','pageerror','requestfailed','response'])page.on(event,value=>{if(event==='console'&&!['warning','error'].includes(value.type()))return;if(event==='response'&&value.status()<400)return;data.events.push({step,event,...event==='console'?{type:value.type(),text:value.text(),location:value.location()}:event==='pageerror'?{message:value.message,stack:value.stack}:event==='response'?{url:value.url(),status:value.status()}:{url:value.url(),failure:value.failure()}});});
 return {data,step:s=>{step=s;},save:async()=>{data.finalURL=page.url();data.lastInspect=await page.evaluate(()=>window.assemblyInspect?.()).catch(()=>null);await writeFile(info.outputPath('resilience-evidence.json'),JSON.stringify(data,null,2));}};
}
async function ready(page,expected={}){await page.waitForFunction(expected=>{const s=window.assemblyInspect?.(),c=s?.comparisonLoading;return s&&!s.loading&&!s.failed&&s.presentation?.phase==='ready'&&!s.presentation.pending.length&&!c?.loading&&!c?.failure&&(!c?.needed||(c.formReady&&c.architectureReady))&&Object.entries(expected).every(([k,v])=>s[k]===v);},expected,{timeout:240000});}
async function panel(page,mode){await page.locator(`[data-mode="${mode}"]:visible`).first().click();await expect(page.locator('#context')).toBeVisible();}
async function download(page,info,proxy,name){const wait=page.waitForEvent('download',{timeout:120000});await page.locator(`#atelier-tools [data-proxy="${proxy}"]`).click();const file=await wait;expect(await file.failure()).toBeNull();const path=info.outputPath(name);await file.saveAs(path);return path;}
async function config(page,info,name){await ready(page);await panel(page,'capture');const path=await download(page,info,'export-config',name+'.json');const data=JSON.parse(await readFile(path,'utf8'));expect(data.sourceAtCapture.status).toBe('verified');expect(data.sourceAtCapture.digest).toBe('947d891f95f7be19219ca3c7f7f2ca78aeae52fef8d41d0a7d42e48421a48063');expect(data.leatherCraft.candidate.identity.id).toBe('strap-hinge-skin-sourcecharts-r16-candidate');expect(data.leatherCraft.candidate.geometryVerification.actualSha256).toBe('d473da297e6dd6565c8c98b3b3e36602f6ed7703c60e51a0205d2ac070825fb0');expect(data.leatherCraft.candidate.geometryVerification.status).toBe('verified');expect(data.capRefinement.active).toBe(true);expect(data.capRefinement.candidatePositionSHA256).toBe(sha);return {path,data};}
async function boot(page){await page.goto(target,{waitUntil:'domcontentloaded'});await ready(page,{openWork:true});if(await page.locator('#motion').getAttribute('aria-pressed')==='true')await page.locator('#motion').click();}

test('controlled missing and aborted raw model: visible reload retry recovers',async({page},info)=>{
 const log=recorder(page,info);const url=new URL(target);url.searchParams.set('assets','raw');
 try{for(const fault of ['404','abort']){
  log.step('injected-'+fault);let intercepted=0;
  const route=async r=>{intercepted++;if(fault==='404')await r.fulfill({status:404,contentType:'text/plain',body:'QA intentionally missing model'});else await r.abort('failed');};
  await page.route('**/rebuild/assembly.glb',route);await page.goto(url.href,{waitUntil:'domcontentloaded'});
  await expect(page.locator('#atelier-retry')).toBeVisible({timeout:180000});expect(intercepted).toBeGreaterThan(0);await expect(page.locator('#home')).toBeDisabled();await page.screenshot({path:info.outputPath('fault-'+fault+'.png')});
  log.data.events.push({step:'fault-count',fault,intercepted});await page.unroute('**/rebuild/assembly.glb',route);
  log.step('recovery-'+fault);await page.locator('#atelier-retry').click();await ready(page,{openWork:true});await expect(page.locator('#atelier-retry')).toBeHidden();await config(page,info,'recovered-'+fault);
 }}finally{await log.save();}
});

test('rapid final option consistency and actual saved-view roundtrip',async({page},info)=>{
 const log=recorder(page,info);
 try{
  await boot(page);log.step('rapid-design-options');await panel(page,'settings');await page.locator('#atelier-tools [data-mode="engineering"]').click();
  const toggle=page.locator('#atelier-tools [data-check="open-work"]');for(const state of [false,true,false,true])await toggle.setChecked(state);await ready(page,{openWork:true});
  log.step('rapid-quality-options');await panel(page,'quality');for(const quality of ['balanced','detail','efficient'])await page.locator(`#atelier-tools [data-quality="${quality}"]`).click();await ready(page,{renderQuality:'efficient'});
  await panel(page,'settings');await page.locator('#atelier-tools [data-camera="lug"]').click();await ready(page,{view:'lug'});await page.waitForTimeout(1200);
  log.step('saved-view-export');const saved=await config(page,info,'before-roundtrip');await page.locator('#home').click();await ready(page);
  log.step('saved-view-import');await panel(page,'capture');const chooser=page.waitForEvent('filechooser');await page.locator('#atelier-import').click();await (await chooser).setFiles(saved.path);
  await expect(page.locator('#viewer-status')).toContainText('Saved camera, crown, options',{timeout:60000});await ready(page,{view:saved.data.view,renderQuality:saved.data.options.quality});
  const restored=await config(page,info,'after-roundtrip');expect(restored.data.options).toEqual(saved.data.options);expect(restored.data.camera).toEqual(saved.data.camera);expect(restored.data.crown).toEqual(saved.data.crown);expect(restored.data.explosion).toBe(saved.data.explosion);
  expect(log.data.events.filter(x=>x.event==='pageerror'||x.event==='requestfailed'||x.event==='response'||(x.event==='console'&&x.type==='error'))).toEqual([]);
 }finally{await log.save();}
});

test('actual WebGL context loss requires documented reload recovery',async({page},info)=>{
 const log=recorder(page,info);
 try{await boot(page);log.step('context-loss');const supported=await page.evaluate(()=>{const c=document.getElementById('assembly-canvas'),gl=c.getContext('webgl2')||c.getContext('webgl');const ext=gl?.getExtension('WEBGL_lose_context');if(!ext)return false;ext.loseContext();return true;});
  test.skip(!supported,'WEBGL_lose_context unavailable; not a passed recovery check');
  await expect(page.locator('#atelier-retry')).toBeVisible();await expect(page.locator('#load-message')).toContainText('graphics context was lost');await expect(page.locator('#home')).toBeDisabled();await page.screenshot({path:info.outputPath('context-lost.png')});
  log.step('reload-recovery');await page.locator('#atelier-retry').click();await ready(page,{openWork:true});await config(page,info,'after-context-reload');await page.screenshot({path:info.outputPath('context-recovered.png')});
 }finally{await log.save();}
});
