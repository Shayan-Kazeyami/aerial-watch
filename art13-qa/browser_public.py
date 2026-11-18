import asyncio,hashlib,json,pathlib,os,time,re
from playwright.async_api import async_playwright
HERE=pathlib.Path(__file__).resolve().parent
OUT=pathlib.Path(os.environ.get('ART13_OUT',HERE/'output'));OUT.mkdir(exist_ok=True,parents=True)
RID='78f11a43161421beddc94469318c7530f2e5b9afeb14f7517e79c7a3e564c4e0'
ROOT='https://shayan-kazeyami.github.io/aerial-watch/'
URL=ROOT+f'preview-b/releases/{RID}/'
N=('assembly-story.js','assembly-review.js','atelier-preview.js')
h=lambda b:hashlib.sha256(b).hexdigest()
report={'immutable_base':RID,'exact_modules':{},'module_overlays':False,'cases':{},'errors':[],'software_rendering_only':True}
async def check(b,width,height,motion):
 label=f'{width}x{height}-{motion}'; pg=await b.new_page(viewport={'width':width,'height':height},reduced_motion=motion,device_scale_factor=1)
 pg.set_default_timeout(180000)
 pg.on('pageerror',lambda e:report['errors'].append(str(e)))
 pg.on('response',lambda r:report['errors'].append('HTTP '+str(r.status)+' '+r.url) if r.status>=400 and '/preview-b/releases/' in r.url else None)
 m=await (await pg.request.get(URL+'deployment-manifest.json')).json();assert m['releaseId']==RID
 expected={x['path']:x for x in m['localFiles']if x['path'] in N};assert set(expected)==set(N)
 for name,row in expected.items():
  response=await pg.request.get(URL+name);data=await response.body()
  assert response.ok and h(data)==row['sha256'] and len(data)==row['sizeBytes'],name
  report['exact_modules'][name]=h(data)
 top=pg
 await top.goto(ROOT+'?art13-watch='+RID[:12],wait_until='domcontentloaded')
 await top.wait_for_function('(release)=>document.querySelector("#watch-viewer")?.src.includes(release)',arg=RID,timeout=90000)
 await top.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000)
 pg=next(f for f in top.frames if RID in f.url)
 report['public_loader']=top.url
 report['public_iframe']=pg.url
 await pg.locator('body[data-ready=true]').wait_for(timeout=300000)
 await pg.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=80000)
 stage=pg.locator('#assembly-canvas');dims=await stage.evaluate('(c)=>[c.width,c.height]')
 await pg.locator('button.atelier-more').click()
 await pg.locator('#context [data-mode=tour]').click()
 state=pg.locator('#atelier-tour-state');button=pg.locator('#context [data-proxy=tour]')
 nextb=pg.locator('#context [data-proxy=tour-next]');prev=pg.locator('#context [data-proxy=tour-previous]')
 async def shown(v): await pg.wait_for_function('(v)=>document.querySelector("#atelier-tour-state").textContent.includes(v)',arg=v)
 if motion=='reduce':
  assert await button.inner_text()=='Open still tour'
  await button.click();await shown('Complete watch')
  assert await button.get_attribute('aria-pressed')=='false'
  await nextb.click();await shown('Dial and hands')
  assert await pg.locator('#stage').get_attribute('data-camera-ready')=='true'
  await pg.wait_for_timeout(7300);assert 'Dial and hands' in await state.inner_text()
  await prev.click();await shown('Complete watch')
  await prev.click();await shown('Lugs and strap')
 else:
  assert await button.inner_text()=='Start studio tour'
  await nextb.click();await shown('Complete watch')
  await nextb.click();await shown('Dial and hands')
  assert await button.inner_text()=='Resume studio tour'
  await pg.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"')
  # Test the key regression: resume from a manually selected nonfirst shot.
  # Inspect the actual 3D viewer state between two genuine UI button activations,
  # avoiding extra frame scheduling delay on a software browser.
  trace=await button.evaluate('''b=>{b.click();let first=assemblyInspect();b.click();let second=assemblyInspect();return [[first.view,first.studioTour],[second.view,second.studioTour]];}''')
  assert trace==[['face',True],['face',False]],trace
  await shown('Dial and hands')
  paused=await pg.evaluate('''() => {const s=assemblyInspect();return {view:s.view,camera:s.camera,target:s.target};}''')
  await pg.wait_for_timeout(7500);assert 'Dial and hands' in await state.inner_text()
  same=await pg.evaluate('''() => {const s=assemblyInspect();return {view:s.view,camera:s.camera,target:s.target};}''')
  assert same['view']==paused['view'] and all(abs(x-y)<1e-7 for k in ('camera','target') for x,y in zip(same[k],paused[k]))
  await nextb.click();await shown('Movement overview')
  await nextb.click();await shown('Balance and hairspring')
  assert await button.get_attribute('aria-pressed')=='false'
  await pg.locator('#close').click();await pg.locator('#assembly-canvas').focus()
  await top.keyboard.press('Home')
  await pg.locator('button.atelier-more').click()
  await pg.locator('#context [data-mode=tour]').click()
  assert await button.inner_text()=='Start studio tour'
 # Compatibility: close the tour before entering exploded mode, reassemble,
 # then open and cancel the exact current video chooser without starting a render.
 await pg.locator('#close').click()
 await pg.locator('.task-dock [data-mode=explode]').click()
 await pg.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
 await pg.locator('#atelier-layer-focus').select_option('balance')
 await pg.wait_for_function('assemblyInspect().layerFocus.selected==="balance"')
 await pg.locator('#atelier-layer-overview').click()
 await pg.locator('#home').click()
 await pg.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating')
 await pg.locator('.task-dock [data-mode=capture]').click()
 await pg.wait_for_function('!document.querySelector("#context [data-proxy=record-scene]").disabled',timeout=180000)
 await pg.locator('#context [data-proxy=record-scene]').click()
 await pg.get_by_role('group',name='Video resolution').wait_for()
 await top.keyboard.press('Escape')
 await pg.get_by_role('dialog').wait_for(state='hidden')
 assert not await pg.evaluate('assemblyInspect().videoExport.active')
 await pg.locator('button.atelier-more').click()
 await pg.locator('#context [data-mode=tour]').click()
 assert await stage.evaluate('(c)=>[c.width,c.height]')==dims
 assert await state.get_attribute('role')=='status'
 report['cases'][label]={'passed':True,'canvas':dims,'state':await state.inner_text()}
 await top.close()
async def main():
 async with async_playwright() as p:
  kw={'args':['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox']}
  if os.environ.get('SYSTEM_CHROME'):kw['executable_path']=os.environ['SYSTEM_CHROME']
  b=await p.chromium.launch(**kw)
  try:
   await check(b,820,600,'no-preference')
   await check(b,430,932,'reduce')
   assert set(report['exact_modules'])==set(N) and not report['errors'],report
   report['passed']=True
  finally:
   (OUT/'REPORT.json').write_text(json.dumps(report,indent=2))
   await b.close()
if __name__=='__main__':asyncio.run(main())
