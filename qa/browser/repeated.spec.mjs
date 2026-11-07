import {test,expect} from '@playwright/test';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const digest='947d891f95f7be19219ca3c7f7f2ca78aeae52fef8d41d0a7d42e48421a48063',cap='f7876b6be8b445a8e72db355fd1dd2705bec13dc19754884ac765c90f8ee7ea2';
async function ready(p){await p.waitForFunction(()=>{const s=window.assemblyInspect?.(),c=s?.comparisonLoading;return s&&!s.loading&&!s.failed&&s.presentation?.phase==='ready'&&!s.presentation.pending.length&&!c?.loading&&!c?.failure&&(!c?.needed||(c.formReady&&c.architectureReady));},null,{timeout:240000});}
async function panel(p){await p.locator('.task-dock [data-mode="capture"]').click();await expect(p.locator('#context')).toBeVisible();}
function identity(c){expect(c.sourceAtCapture.status).toBe('verified');expect(c.sourceAtCapture.digest).toBe(digest);expect(c.capRefinement.active).toBe(true);expect(c.capRefinement.candidatePositionSHA256).toBe(cap);expect(c.options.quality).toBe('efficient');}
function png(b){expect([...b.subarray(0,8)]).toEqual([137,80,78,71,13,10,26,10]);let view;for(let n=8;n+12<=b.length;){const len=b.readUInt32BE(n),kind=b.toString('ascii',n+4,n+8),payload=b.subarray(n+8,n+8+len);if(kind==='iTXt'&&payload.subarray(0,15).toString()==='AerialView\0\0\0\0\0')view=JSON.parse(payload.subarray(15).toString());n+=len+12;}expect(view).toBeTruthy();return {width:b.readUInt32BE(16),height:b.readUInt32BE(20),view};}
test('three real PNG JSON restore cycles with owned URL cleanup',async({page},info)=>{
 test.setTimeout(720000);const evidence={scope:'Actual combined source, software SwiftShader desktop only; no hardware or visual quality acceptance.',cycles:[],errors:[]};
 await page.addInitScript(()=>{const originalCreate=URL.createObjectURL,originalRevoke=URL.revokeObjectURL;window.__urls=[];URL.createObjectURL=function(b){const url=originalCreate.call(this,b);window.__urls.push({url,type:b.type,size:b.size,created:performance.now(),revoked:null});return url;};URL.revokeObjectURL=function(url){const item=window.__urls.find(x=>x.url===url);if(item)item.revoked=performance.now();return originalRevoke.call(this,url);};});
 page.on('pageerror',e=>evidence.errors.push(e.message));page.on('console',m=>{if(m.type()==='error')evidence.errors.push(m.text());});page.on('response',r=>{if(r.status()>=400)evidence.errors.push(r.status()+' '+r.url());});
 async function download(proxy,name){const pending=page.waitForEvent('download',{timeout:120000});await page.locator(`#atelier-tools [data-proxy="${proxy}"]`).click();const d=await pending;expect(await d.failure()).toBeNull();const path=info.outputPath(name);await d.saveAs(path);return {path,bytes:await readFile(path)};}
 try{
 await page.goto('http://127.0.0.1:8765/atelier-preview.html?quality=efficient',{waitUntil:'domcontentloaded'});await ready(page);if(await page.locator('#motion').getAttribute('aria-pressed')==='true')await page.locator('#motion').click();
 evidence.adapter=await page.evaluate(()=>{const g=document.querySelector('canvas').getContext('webgl2'),x=g.getExtension('WEBGL_debug_renderer_info');return {renderer:x?g.getParameter(x.UNMASKED_RENDERER_WEBGL):null,ua:navigator.userAgent};});
 for(let i=0;i<3;i++){
  await page.setViewportSize({width:1440-i*100,height:1000-i*40});await ready(page);await panel(page);await page.locator('#close').click();await expect(page.locator('#context')).toBeHidden();await panel(page);
  const saved=await download('export-config',`saved-${i}.json`),c=JSON.parse(saved.bytes);identity(c);
  const picture=await download('capture-scene',`actual-${i}.png`),p=png(picture.bytes);identity(p.view);
  const dimensions=await page.locator('#assembly-canvas').evaluate(c=>({width:c.width,height:c.height}));expect({width:p.width,height:p.height}).toEqual(dimensions);expect(p.width).toBe(1440-i*100);
  await page.locator('#home').click();await ready(page);await panel(page);const chooser=page.waitForEvent('filechooser');await page.locator('#atelier-import').click();await(await chooser).setFiles(saved.path);await expect(page.locator('#viewer-status')).toContainText('Saved camera, crown, options');await ready(page);
  const resaved=await download('export-config',`restored-${i}.json`),r=JSON.parse(resaved.bytes);identity(r);for(const k of ['camera','options','crown','explosion'])expect(r[k]).toEqual(c[k]);
  evidence.cycles.push({cycle:i,dimensions,bytes:picture.bytes.length,pngSHA256:createHash('sha256').update(picture.bytes).digest('hex'),embeddedDigest:p.view.sourceAtCapture.digest,activeCap:p.view.capRefinement.active,roundtrip:true});
  await expect(page.locator('#atelier-tools [data-proxy="capture-scene"]')).toBeEnabled();await page.locator('#close').click();
 }
 expect(new Set(evidence.cycles.map(c=>c.pngSHA256)).size).toBe(3);
 // Actual manager retains download URLs for 60 seconds; observe natural cleanup, not synthetic pagehide/dispose.
 await expect.poll(()=>page.evaluate(()=>window.__urls.filter(x=>['image/png','application/json'].some(t=>x.type.startsWith(t))&&x.revoked===null).length),{timeout:75000,intervals:[1000]}).toBe(0);
 evidence.urls=await page.evaluate(()=>window.__urls);const exports=evidence.urls.filter(x=>['image/png','application/json'].some(t=>x.type.startsWith(t)));expect(exports.filter(x=>x.type==='image/png')).toHaveLength(3);expect(exports.filter(x=>x.type.startsWith('application/json'))).toHaveLength(6);expect(exports.every(x=>x.revoked!==null)).toBe(true);expect(await page.locator('a[download]').count()).toBe(0);expect(evidence.errors).toEqual([]);evidence.passed=true;
 }finally{evidence.finalURLs=await page.evaluate(()=>window.__urls).catch(()=>null);await writeFile(info.outputPath('repeated-export-evidence.json'),JSON.stringify(evidence,null,2));}
});
