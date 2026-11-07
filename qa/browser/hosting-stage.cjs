/* Read-only staged-site browser QA. No deployment, Git mutation or request blocking. */
const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');const {execFileSync}=require('node:child_process');
const STAGE='2a8748aeabc70e75f10f63fa644bcad9f315f26f';
const PARENT='f3c983f77ca3099b1061946794f0bf4e711986c5';
const RELEASE='68b516d5945b4b20af8bbf98558381891c5f9b3c81390ec2fc8ecdcfcaf6d45b';
const site=path.resolve(process.env.STAGED_SITE||'staged-site');
const base=process.env.HOSTING_QA_URL||'http://127.0.0.1:8766/aerial-watch/';
const out=path.resolve(process.env.HOSTING_QA_ARTIFACTS||'hosting-stage-artifacts');fs.mkdirSync(out,{recursive:true});
const noticeNames=['aerial-review.html','aerial-v2-index.html','aerial.html','assembly-review.html','atelier-layout-study.html','atelier-preview.html','holder.html','index.html','integrated-preview.html','material-review.html','movement-before-aerial.html','movement.html','tests/browser-embed.html'];
const snapshot=`https://github.com/Shayan-Kazeyami/aerial-watch/tree/${PARENT}/preview-b/releases/${RELEASE}`;
const report={stage:STAGE,environment:'Headless Chromium / ANGLE SwiftShader. Render/control regression only, not hardware performance or visual approval.',notices:[],legacy:[],current:null,passed:false};
function observe(page){
 const evidence={pageErrors:[],consoleErrors:[],consoleWarnings:[],httpErrors:[],requestFailures:[],models:[],metadata:[]};let active=true;
 page.on('pageerror',e=>{if(active)evidence.pageErrors.push(e.message);});
 page.on('console',m=>{if(active&&m.type()==='error')evidence.consoleErrors.push({text:m.text(),url:m.location().url});if(active&&m.type()==='warning')evidence.consoleWarnings.push(m.text());});
 page.on('response',r=>{if(!active)return;const u=new URL(r.url());if(r.status()>=400)evidence.httpErrors.push({url:r.url(),status:r.status()});if(u.pathname.endsWith('.glb'))evidence.models.push({url:r.url(),status:r.status()});if(/\/(automatic|manual-a|manual-b)-parts\.json$/.test(u.pathname))evidence.metadata.push({url:r.url(),status:r.status()});});
 page.on('requestfailed',r=>{if(active)evidence.requestFailures.push({url:r.url(),failure:r.failure()});});
 return {evidence,stop(){active=false;}};
}
function clean(e){for(const k of ['pageErrors','consoleErrors','httpErrors','requestFailures'])assert.deepEqual(e[k].filter(x=>!x?.url||!new URL(x.url).pathname.endsWith('/favicon.ico')),[],k);}
// Optional favicon failures remain recorded, matching the prior route audit's non-product exclusion. No other errors are suppressed.
async function fresh(browser){return browser.newContext({viewport:{width:1280,height:900},deviceScaleFactor:1,acceptDownloads:true});}
(async()=>{
 assert.equal(execFileSync('git',['-C',site,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),STAGE,'wrong checkout');
 assert.equal(execFileSync('git',['-C',site,'status','--porcelain'],{encoding:'utf8'}).trim(),'','staged files modified');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE_PATH||undefined,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  // Each notice is actual staged HTML. No generated replacement pages or denied-route map.
  const snapshotContext=await fresh(browser);
  try{const r=await snapshotContext.request.get(snapshot,{timeout:60000});assert.equal(r.status(),200,'original snapshot unreachable');report.snapshot={url:snapshot,status:r.status()};}finally{await snapshotContext.close();}
  for(const [i,name]of noticeNames.entries()){
   const context=await fresh(browser),page=await context.newPage(),watch=observe(page);const row={name,...watch.evidence};report.notices.push(row);
   try{
    const suffix='?qa=archive%20notice&variant=manual-a#retained-fragment';
    const url=new URL(`preview-b/releases/${RELEASE}/${name}${suffix}`,base).href;
    await page.goto(url,{waitUntil:'networkidle',timeout:60000});
    assert(await page.getByRole('heading',{name:'This preview has been archived'}).isVisible());
    assert(await page.getByText('The snapshot is source code and assets, not an interactive hosted preview.').isVisible());
    const current=page.locator('#current');assert(await current.isVisible());
    const expected=new URL(base);expected.search=new URL(url).search;expected.hash=new URL(url).hash;
    assert.equal(await current.evaluate(a=>a.href),expected.href);
    assert.equal(await page.getByRole('link',{name:'Browse the original source snapshot on GitHub'}).getAttribute('href'),snapshot);
    if(i===0||name.startsWith('tests/'))await page.screenshot({path:path.join(out,`notice-${i}.png`)});
    clean(watch.evidence);
    // Real click reaches the root, including query/hash. Full viewer readiness is tested once below.
    await Promise.all([page.waitForURL(u=>u.href===expected.href,{waitUntil:'domcontentloaded',timeout:60000}),current.click()]);
    row.clickedDestination=page.url();clean(watch.evidence);row.passed=true;
   }finally{watch.stop();await context.close();}
  }
  for(const route of ['movement.html','aerial.html','preview-b/movement.html','preview-b/aerial.html']){
   const context=await fresh(browser),page=await context.newPage(),watch=observe(page);const row={route,...watch.evidence,variants:[]};report.legacy.push(row);
   try{
    await page.goto(new URL(route,base).href,{waitUntil:'domcontentloaded',timeout:120000});
    for(const variant of ['automatic','manual-a','manual-b','automatic']){
     await page.locator('#variant').waitFor({timeout:120000});
     await page.waitForFunction(()=>!document.getElementById('variant').disabled&&document.getElementById('loading').hidden,null,{timeout:120000});
     await page.selectOption('#variant',variant);
     await page.waitForFunction(name=>{const selector=document.getElementById('variant');const s=window.om10Inspect?.()||window.aerialInspect?.();return selector.value===name&&!selector.disabled&&document.getElementById('loading').hidden&&s&&!s.loading&&s.variant===name;},variant,{timeout:120000});
     const state=await page.evaluate(()=>{const s=window.om10Inspect?.()||window.aerialInspect?.();return {variant:s.variant,loading:s.loading,meshCount:s.meshCount??s.sourceMeshes};});
     assert(state.meshCount>0,'no model meshes');row.variants.push(state);
    }
    for(const variant of ['automatic','manual-a','manual-b']){
     assert(watch.evidence.models.some(r=>new URL(r.url).pathname.endsWith(`/releases/${RELEASE}/assets/${variant}.glb`)&&r.status===200),'missing retained GLB '+variant);
     assert(watch.evidence.metadata.some(r=>new URL(r.url).pathname.endsWith(`/assets/${variant}-parts.json`)&&r.status===200),'missing metadata '+variant);
    }
    clean(watch.evidence);await page.screenshot({path:path.join(out,route.replaceAll('/','-')+'.png')});row.passed=true;
   }finally{watch.stop();await context.close();}
  }
  // Exercise the staged root's actual iframe and basic user-visible controls, not a direct substitute URL.
  const context=await fresh(browser),page=await context.newPage(),watch=observe(page);report.current={...watch.evidence,steps:[]};
  try{
   const rootURL=new URL(base);rootURL.searchParams.set('quality','efficient');report.current.requestedURL=rootURL.href;await page.goto(rootURL.href,{waitUntil:'domcontentloaded',timeout:120000});
   await page.locator('#watch-viewer').waitFor({timeout:60000});
   let frame;await page.waitForFunction(()=>document.querySelector('#watch-viewer')?.src,null,{timeout:60000});
   frame=await (await page.locator('#watch-viewer').elementHandle()).contentFrame();assert(frame);
   const settle=()=>frame.waitForFunction(()=>{const s=window.assemblyInspect?.();return s&&!s.loading&&!s.failed&&s.presentation?.phase==='ready'&&s.presentation?.interactive&&!s.presentation?.pending?.length;},null,{timeout:240000});
   await settle();assert(await frame.locator('#assembly-canvas').isVisible());
   report.current.resolvedFrameURL=frame.url();assert(frame.url().includes('/releases/9c055e4777a79c7987dd6cd5ccabf9f189121fd6c64e2f54853aa694827add06/'));
   await frame.locator('#home').click();await settle();report.current.steps.push('home-reset');
   await frame.locator('[data-mode="settings"]').filter({visible:true}).first().click();
   await frame.locator('#atelier-tools [data-camera="lug"]').click();await frame.locator('#close').click();
   await frame.waitForTimeout(1000);await settle();report.current.steps.push('lug-view');
   await page.screenshot({path:path.join(out,'current-root-lug.png')});
   await frame.locator('#home').click();await settle();report.current.steps.push('home-after-lug');
   clean(watch.evidence);report.current.passed=true;
  }finally{watch.stop();await context.close();}
  report.passed=true;
 }catch(error){report.error={message:error.message,stack:error.stack};throw error;}
 finally{fs.writeFileSync(path.join(out,'evidence.json'),JSON.stringify(report,null,2)+'\n');await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
