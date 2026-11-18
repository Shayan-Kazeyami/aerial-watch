import asyncio,json,pathlib,time
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).parent;O=P/'output';O.mkdir(exist_ok=True);RID='87a8607a738ba192c68f266db3f241e148f48f34216e7976c73cc062adb1f3e2'
R={'release':RID,'scope':'Live Chromium SwiftShader bounded same-state resource cycles, not hardware FPS/VRAM/heap measurement','errors':[],'requests':[],'navigations':[],'cycles':[]};phase='load'
async def main():
 global phase
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':430,'height':932},is_mobile=True,has_touch=True,reduced_motion='reduce');page.set_default_timeout(180000)
  page.on('pageerror',lambda e:R['errors'].append(str(e)))
  page.on('framenavigated',lambda f:R['navigations'].append({'phase':phase,'url':f.url}))
  page.on('request',lambda q:R['requests'].append({'phase':phase,'url':q.url,'type':q.resource_type}))
  try:
   await page.goto('https://shayan-kazeyami.github.io/aerial-watch/?quality=efficient&resource-cycle-proof=1',wait_until='domcontentloaded');await page.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=360000);f=next(x for x in page.frames if RID in x.url)
   await f.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'")
   await f.evaluate("()=>{window.__qaContextLosses=0;document.querySelector('canvas').addEventListener('webglcontextlost',()=>window.__qaContextLosses++);}")
   sample="""()=>{const s=assemblyInspect(),r=assemblyResourceInspect(),c=document.querySelector('#assembly-canvas'),b=c.getBoundingClientRect();return {memory:r.rendererReportedMemory.values,totals:r.totals,targetSizes:r.renderTargets.map(t=>({name:t.name,width:t.width,height:t.height})),textureIds:r.textures.map(t=>t.uuid).sort(),canvas:[b.x,b.y,b.width,b.height,c.width,c.height],state:{quality:s.renderQuality,explosion:s.explosion.amount,view:s.view,inspection:s.inspectionDisplay,sourceMeshes:s.sourceMeshes},contextLosses:window.__qaContextLosses}}"""
   async def settle():
    last=None
    for _ in range(30):
     await page.wait_for_timeout(150);s=await f.evaluate(sample);key=json.dumps([s['memory'],s['totals'],s['canvas']],sort_keys=True)
     if key==last:return s
     last=key
    raise AssertionError('same-state inventory did not settle')
   async def close():
    metrics=await f.evaluate("()=>{const box=()=>{const r=document.querySelector('#assembly-canvas').getBoundingClientRect();return [r.x,r.y,r.width,r.height]};const before=box();document.querySelector('#close').click();return {before,after:box()}}")
    assert metrics['before']==metrics['after'],metrics
   for i in range(11):
    phase='warmup' if i<3 else 'measured'
    for quality in ['balanced','efficient']:
     await f.locator('.masthead .quality').tap();await f.locator('[data-quality='+quality+']').tap();await f.wait_for_function('(q)=>assemblyInspect().renderQuality===q',arg=quality);await close()
    await f.locator('.atelier-more').tap();await f.locator('[data-camera=back]').tap();await f.wait_for_function("assemblyInspect().view==='back'")
    await f.locator('[data-inspection=hideStrap]').tap();await f.wait_for_function('assemblyInspect().inspectionDisplay.hideStrap===true')
    await f.locator('[data-inspection=wireframe]').tap();await f.wait_for_function('assemblyInspect().inspectionDisplay.wireframe===true')
    await f.locator('#atelier-inspection-reset').tap();await f.wait_for_function('!assemblyInspect().inspectionDisplay.hideStrap&&!assemblyInspect().inspectionDisplay.wireframe');await close()
    await f.locator('.task-dock [data-mode=explode]').tap();await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
    await f.locator('#atelier-reassemble').tap();await f.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating');await close()
    await f.locator('.atelier-more').tap();await f.locator('[data-camera=three-quarter]').tap();await f.wait_for_function("assemblyInspect().view==='three-quarter'");await close();await f.locator('#home').tap()
    s=await settle();R['cycles'].append({'iteration':i,'phase':phase,'snapshot':s});print(json.dumps({'iteration':i,'memory':s['memory'],'totals':s['totals']}),flush=True)
    if i==2:await page.screenshot(path=str(O/'warm.png'))
   await page.screenshot(path=str(O/'final.png'));rows=[x['snapshot']for x in R['cycles']if x['phase']=='measured'];baseline=R['cycles'][2]['snapshot']
   R['sameStateCountersStable']=all(x['memory']==baseline['memory']and x['totals']==baseline['totals']and x['targetSizes']==baseline['targetSizes']for x in rows)
   R['sameTextureIdentities']=all(x['textureIds']==baseline['textureIds']for x in rows)
   R['assetRequestsAfterWarmup']=[q for q in R['requests']if q['phase']=='measured'and any(e in q['url'].split('?')[0].lower()for e in ['.glb','.gltf','.bin','.ktx2','.webp','.png'])]
   assert not R['errors']and all(x['contextLosses']==0 for x in rows)
   assert not [x for x in R['navigations']if x['phase']=='measured']
   assert all(x['canvas']==baseline['canvas']for x in rows)
   assert R['sameStateCountersStable']and R['sameTextureIdentities'], 'Resource identities/counters changed after warmup; investigate before labeling leak'
   assert not R['assetRequestsAfterWarmup'];R['passed']=True
  finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(main())
