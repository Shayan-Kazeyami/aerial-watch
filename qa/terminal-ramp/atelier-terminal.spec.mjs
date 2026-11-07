import {test,expect} from '@playwright/test';
import {readFile,writeFile} from 'node:fs/promises';

// Read-only QA supplement: no browser monkey-patching, no source changes.
// `normalStream=1` is the product's opt-in progressive path, NOT a UI normal toggle.
const initial=new URL(process.env.WATCH_QA_URL||'http://127.0.0.1:8765/atelier-preview.html?quality=efficient');
initial.searchParams.set('leather','craft14');initial.searchParams.set('normalStream','1');
const expectedDigest='56baa829316fa357b0adfe9ff251758f87389a8f1f74d82cce91b8e7cb8afb34';
const expectedGeometry='c97e6e5e2f23acb65ccf0c10d0a844924fb161bb38d7966e72db43c7ced1bf29';
const expectedNormal='bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585';
const expectedSegments=['normal-4k-header.bin','normal-4k-high.part0','normal-4k-high.part1'];

test('terminal upper and lower views with progressive full normal and reset',async({page},info)=>{
 const evidence={environment:'GitHub-hosted Chromium headless / ANGLE SwiftShader software WebGL; not hardware or mobile parity.',requestedURL:initial.href,cameraMethod:'Upper Lugs uses visible preset. Upper/lower closeups use camera-only JSON authored from that exported view and loaded through public Load view; not claims of lower preset or manual camera operation.',normalLimitation:'No user-facing normal toggle or normal-scale control found. Fixed effective values and progressive full upgrade are verified; no toggle comparison claimed.',snapshots:[],segmentResponses:[],pageErrors:[],httpErrors:[],requestFailures:[],consoleErrors:[]};
 let step='navigation';
 page.on('pageerror',e=>evidence.pageErrors.push({step,message:e.message}));
 page.on('console',m=>{if(m.type()==='error')evidence.consoleErrors.push({step,text:m.text()});});
 page.on('requestfailed',r=>evidence.requestFailures.push({step,url:r.url(),failure:r.failure()}));
 page.on('response',r=>{if(r.status()>=400)evidence.httpErrors.push({step,url:r.url(),status:r.status()});const name=new URL(r.url()).pathname.split('/').pop();if(expectedSegments.includes(name))evidence.segmentResponses.push({name,status:r.status(),url:r.url()});});
 const settle=async()=>{await page.waitForFunction(()=>{const s=window.assemblyInspect?.();if(!s||s.loading||s.failed||s.presentation?.phase!=='ready'||s.presentation?.pending?.length||!s.presentation?.interactive)return false;const c=s.comparisonLoading;return !(c?.loading||c?.failure||(c?.needed&&(!c.formReady||!c.architectureReady)));},null,{timeout:180000});await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));};
 const panel=async mode=>{await page.locator(`[data-mode="${mode}"]`).filter({visible:true}).first().click();await expect(page.locator('#context')).toBeVisible();};
 async function save(name,{mustBeFull=false}={}){
  step=name;await settle();await panel('capture');const pending=page.waitForEvent('download',{timeout:120000});await page.locator('#atelier-tools [data-proxy="export-config"]').click();const dl=await pending;expect(await dl.failure()).toBeNull();const file=info.outputPath(name+'.json');await dl.saveAs(file);const c=JSON.parse(await readFile(file,'utf8'));
  expect(c.sourceAtCapture?.status).toBe('verified');expect(c.sourceAtCapture?.digest).toBe(expectedDigest);expect(c.leatherCraft?.candidate?.identity?.id).toBe('strap-hinge-terminal-ramp-r17-candidate');expect(c.leatherCraft?.candidate?.geometryVerification?.status).toBe('verified');expect(c.leatherCraft?.candidate?.geometryVerification?.actualSha256).toBe(expectedGeometry);expect(c.leatherCraft?.candidate?.normalIdentity?.sha256).toBe(expectedNormal);
  const outer=c.leatherCraft?.effectiveOuterMaterials||[];expect(outer.length).toBeGreaterThanOrEqual(2);for(const m of outer){expect(m.normalScale).toEqual([0.25,-0.25]);expect(m.maps?.normalMap).toBeTruthy();}if(mustBeFull)expect(c.progressiveNormal).toBe('full');
  evidence.snapshots.push({name,file,digest:c.sourceAtCapture.digest,geometry:c.leatherCraft.candidate.geometryVerification,progressiveNormal:c.progressiveNormal,normalIdentity:c.leatherCraft.candidate.normalIdentity,normalScale:outer.map(m=>({mesh:m.mesh,normalScale:m.normalScale,normalMap:m.maps.normalMap})),options:c.options,view:c.view,camera:c.camera});return c;
 }
 async function screenshot(name){if(await page.locator('#close').isVisible())await page.locator('#close').click();await page.waitForTimeout(1000);await settle();await page.screenshot({path:info.outputPath(name+'.png')});}
 async function loadCameraFromView(base,name,target){
  const config=structuredClone(base),from=base.camera.position.map((v,i)=>v-base.camera.target[i]),length=Math.hypot(...from),distance=20;config.camera.target=target;config.camera.position=target.map((v,i)=>v+from[i]/length*distance);config.camera.zoom=1;
  const file=info.outputPath(name+'-view-input.json');await writeFile(file,JSON.stringify(config,null,2));step='import-'+name;await panel('capture');await expect(page.locator('#atelier-import')).toBeEnabled();await page.locator('#atelier-import').click();await page.locator('#import-config').setInputFiles(file);
  await page.waitForFunction(target=>{const a=window.assemblyInspect?.();return a&&a.target?.every((v,i)=>Math.abs(v-target[i])<1e-4);},target,{timeout:30000});await settle();return config;
 }
 try{
  await page.goto(initial.href,{waitUntil:'domcontentloaded',timeout:60000});await expect(page.locator('#assembly-canvas')).toBeVisible();await expect(page.locator('#home')).toBeEnabled({timeout:240000});await settle();if(await page.locator('#motion').getAttribute('aria-pressed')==='true')await page.locator('#motion').click();await settle();
  // Full upgrade is exposed in exported config, not in the read-only assemblyInspect API.
  let full;const until=Date.now()+180000;for(let i=0;Date.now()<until;i++){const c=await save('normal-upgrade-poll-'+i);if(c.progressiveNormal==='full'){full=c;break;}expect(c.progressiveNormal).not.toBe('failed');await page.waitForTimeout(3000);}expect(full,'progressive full normal upgrade did not complete').toBeTruthy();
  for(const name of expectedSegments)expect(evidence.segmentResponses.some(x=>x.name===name&&x.status>=200&&x.status<300),`missing successful ${name}`).toBeTruthy();
  await panel('settings');await page.locator('#atelier-tools [data-camera="lug"]').click();await expect(page.locator('#runtime-bridge [data-view="lug"]')).toHaveAttribute('aria-pressed','true');await page.waitForTimeout(1000);await settle();await screenshot('upper-visible-lugs-preset');const lug=await save('upper-visible-lugs-preset',{mustBeFull:true});expect(lug.view).toBe('lug');expect(lug.camera.target[1]).toBeCloseTo(22.4,2);const options=lug.options;
  // Local glTF +π/2 X rotation: upper local z=-22.4 → world y=+22.4; lower local z=+22.4 → world y=-22.4.
  for(const [name,target]of [['upper-imported-closeup',[8.5,22.4,-0.95]],['lower-imported-closeup',[8.5,-22.4,-0.95]]]){
   const authored=await loadCameraFromView(lug,name,target);await screenshot(name);const actual=await save(name,{mustBeFull:true});expect(actual.options).toEqual(options);for(let i=0;i<3;i++){expect(actual.camera.target[i]).toBeCloseTo(authored.camera.target[i],3);expect(actual.camera.position[i]).toBeCloseTo(authored.camera.position[i],3);}expect(actual.view).toBe('lug');
  }
  step='reset';await page.locator('#home').click();await settle();await screenshot('after-reset');const reset=await save('after-reset',{mustBeFull:true});expect(reset.options.openWork).toBe(true);expect(reset.camera.target).not.toEqual([8.5,-22.4,-0.95]);
  expect(evidence.pageErrors).toEqual([]);expect(evidence.httpErrors).toEqual([]);expect(evidence.requestFailures).toEqual([]);expect(evidence.consoleErrors).toEqual([]);
 }finally{await writeFile(info.outputPath('terminal-evidence.json'),JSON.stringify(evidence,null,2));await info.attach('terminal-evidence',{path:info.outputPath('terminal-evidence.json'),contentType:'application/json'});}
});
