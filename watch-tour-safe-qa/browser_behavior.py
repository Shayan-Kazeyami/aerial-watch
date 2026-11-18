import asyncio,hashlib,json,pathlib,os,time,re
from playwright.async_api import async_playwright
HERE=pathlib.Path(__file__).resolve().parent
OUT=pathlib.Path(os.environ.get('ART13_OUT',HERE/'output'));OUT.mkdir(exist_ok=True,parents=True)
RID='a9b5db9042cf25036cd74c1471cbb87c48b966b8c68cbf2992d134b45b9f9ac7'
URL=f'http://127.0.0.1:8765/preview-b/releases/{RID}/'
N=('assembly-review.js','atelier-preview.js')
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
  resp=await pg.request.get(URL+name);data=await resp.body()
  assert resp.ok and h(data)==row['sha256'] and len(data)==row['sizeBytes'],name
  report['exact_modules'][name]=h(data)
 await pg.goto(URL+'atelier-preview.html?quality=efficient',wait_until='domcontentloaded')
 await pg.locator('body[data-ready=true]').wait_for(timeout=300000)
 await pg.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=80000)

 rects="""() => {const rect=(s)=>{const r=document.querySelector(s).getBoundingClientRect();return {l:r.left,t:r.top,r:r.right,b:r.bottom,w:r.width,h:r.height};};return {stage:rect('#assembly-canvas'),panel:rect('#context'),dock:rect('.task-dock'),controls:rect('.bottom-zone'),host:rect('#atelier-stage-host')};}"""
 original=(await pg.evaluate(rects))['stage']
 await pg.locator('button.atelier-more').click()
 await pg.locator('#context [data-mode=tour]').click()
 await pg.wait_for_function("document.body.style.getPropertyValue('--tour-stage-end')!==''")
 state=pg.locator('#atelier-tour-state')
 nextb=pg.locator('#context [data-proxy=tour-next]')
 shots=(('showcase','Complete watch'),('face','Dial and hands'),('interior','Movement overview'),('balance','Balance and hairspring'),('train','Gear train'),('lug','Lugs and strap'))
 button=pg.locator('#context [data-proxy=tour]')
 previous=pg.locator('#context [data-proxy=tour-previous]')
 await nextb.click();await nextb.click()
 await pg.wait_for_function("()=>assemblyInspect().view==='face'&&document.querySelector('#stage').dataset.cameraReady==='true'")
 report['cases'][label]={'stageBeforeTour':original}
 if motion=='no-preference':
  trace=await button.evaluate("""b=>{b.click();const a=assemblyInspect();b.click();const z=assemblyInspect();return [[a.view,a.studioTour],[z.view,z.studioTour]];}""")
  assert trace==[['face',True],['face',False]],trace
  current=await pg.evaluate("()=>{const a=assemblyInspect();return [a.view,a.camera,a.target];}")
  await pg.wait_for_timeout(7500)
  assert current==await pg.evaluate("()=>{const a=assemblyInspect();return [a.view,a.camera,a.target];}")
  await button.click()
  await pg.wait_for_function("assemblyInspect().view==='interior'&&assemblyInspect().studioTour",timeout=120000)
  await button.click()
  assert await button.get_attribute('aria-pressed')=='false'
  await previous.click()
  await pg.wait_for_function("assemblyInspect().view==='face'&&document.querySelector('#stage').dataset.cameraReady==='true'")
  report['cases'][label].update({'sameShotResume':trace,'pausedPoseStable':True,'elapsedDwellContinues':True,'previousGoesBack':True})
 else:
  assert await button.get_attribute('aria-pressed')=='false'
  await pg.wait_for_timeout(7500)
  assert await pg.evaluate("assemblyInspect().view==='face'&&!assemblyInspect().studioTour")
  await pg.set_viewport_size({'width':932,'height':430})
  await pg.wait_for_function("document.querySelector('#assembly-canvas').getBoundingClientRect().right<=document.querySelector('#context').getBoundingClientRect().left-11")
  rs=await pg.evaluate(rects)
  assert rs['controls']['t']-rs['stage']['b']>=11
  assert await pg.evaluate("assemblyInspect().view==='face'&&!assemblyInspect().studioTour")
  await previous.click()
  await pg.wait_for_function("assemblyInspect().view==='showcase'&&document.querySelector('#stage').dataset.cameraReady==='true'")
  await pg.screenshot(path=str(OUT/'rotated-reduced-motion.png'))
  await pg.set_viewport_size({'width':width,'height':height})
  await pg.wait_for_function("document.querySelector('#assembly-canvas').getBoundingClientRect().bottom<=document.querySelector('#context').getBoundingClientRect().top-11")
  report['cases'][label].update({'stillDidNotAdvance':True,'rotationPreservedShotAndReflowed':True,'previousGoesBack':True})
 await pg.locator('#close').click()
 await pg.wait_for_function("document.body.style.getPropertyValue('--tour-stage-end')===''")
 after=(await pg.evaluate(rects))['stage']
 assert after==original,(after,original)
 assert await pg.locator('.atelier-more').evaluate('(b)=>document.activeElement===b')
 report['cases'][label]['stageAndFocusRestored']=True
 await pg.close()
async def main():
 width,height=map(int,os.environ.get('VIEW','820x600').split('x'))
 motion=os.environ.get('MOTION','reduce')
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'])
  try:
   await check(b,width,height,motion)
   assert set(report['exact_modules'])==set(N) and not report['errors'],report
   report['passed']=True
  finally:
   (OUT/'REPORT.json').write_text(json.dumps(report,indent=2))
   await b.close()
if __name__=='__main__':asyncio.run(main())
