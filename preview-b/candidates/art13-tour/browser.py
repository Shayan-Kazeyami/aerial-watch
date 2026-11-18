import asyncio,hashlib,json,pathlib,os,time,re
from playwright.async_api import async_playwright
HERE=pathlib.Path(__file__).resolve().parent
OUT=pathlib.Path(os.environ.get('ART13_OUT',HERE/'output'));OUT.mkdir(exist_ok=True,parents=True)
RID='e1d6f75a57a44d0ceba1ff3be1d92e7205fdc0e95b256a576a305bea27ad4f9b'
URL=f'https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/{RID}/'
N=('assembly-story.js','assembly-review.js','atelier-preview.js')
h=lambda b:hashlib.sha256(b).hexdigest()
report={'immutable_base':RID,'overlay':{},'cases':{},'errors':[],'software_rendering_only':True}
async def check(b,width,height,motion):
 label=f'{width}x{height}-{motion}'; pg=await b.new_page(viewport={'width':width,'height':height},reduced_motion=motion,device_scale_factor=1)
 pg.set_default_timeout(180000)
 pg.on('pageerror',lambda e:report['errors'].append(str(e)))
 pg.on('response',lambda r:report['errors'].append('HTTP '+str(r.status)+' '+r.url) if r.status>=400 and '/preview-b/releases/' in r.url else None)
 m=await (await pg.request.get(URL+'deployment-manifest.json')).json();assert m['releaseId']==RID
 expected={x['path']:x for x in m['localFiles']if x['path'] in N};assert set(expected)==set(N)
 async def overlay(route):
  name=route.request.url.split('?')[0].split('/')[-1];orig=await route.fetch();data=await orig.body()
  assert orig.ok and h(data)==expected[name]['sha256'] and len(data)==expected[name]['sizeBytes']
  v=(HERE/name).read_bytes();report['overlay'][name]={'base':h(data),'candidate':h(v)}
  await route.fulfill(response=orig,body=v)
 for n in N:await pg.route(URL+n+'*',overlay)
 await pg.goto(URL+'atelier-preview.html?quality=efficient',wait_until='domcontentloaded')
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
  await button.click();await shown('Complete watch')
  assert await button.get_attribute('aria-pressed')=='true'
  await shown('Dial and hands')
  await button.click();await shown('Dial and hands')
  assert await button.inner_text()=='Resume studio tour'
  await pg.wait_for_timeout(7300);assert 'Dial and hands' in await state.inner_text()
  await button.click();assert 'Dial and hands' in await state.inner_text()
  await shown('Movement overview')
  await nextb.click();await shown('Balance and hairspring')
  assert await button.get_attribute('aria-pressed')=='false'
  await pg.locator('#close').click();await pg.locator('#assembly-canvas').focus()
  await pg.keyboard.press('Home')
  await pg.locator('button.atelier-more').click()
  await pg.locator('#context [data-mode=tour]').click()
  assert await button.inner_text()=='Start studio tour'
 assert await stage.evaluate('(c)=>[c.width,c.height]')==dims
 assert await state.get_attribute('role')=='status'
 await pg.screenshot(path=str(OUT/(label+'.png')))
 report['cases'][label]={'passed':True,'canvas':dims,'state':await state.inner_text()}
 await pg.close()
async def main():
 async with async_playwright() as p:
  kw={'args':['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox']}
  if os.environ.get('SYSTEM_CHROME'):kw['executable_path']=os.environ['SYSTEM_CHROME']
  b=await p.chromium.launch(**kw)
  try:
   await check(b,1100,760,'no-preference')
   await check(b,430,932,'reduce')
   assert set(report['overlay'])==set(N) and not report['errors'],report
   report['passed']=True
  finally:
   (OUT/'REPORT.json').write_text(json.dumps(report,indent=2))
   await b.close()
if __name__=='__main__':asyncio.run(main())
