import asyncio,json,pathlib,hashlib
from playwright.async_api import async_playwright
O=pathlib.Path('mechanism-plates-qa/material-qa');O.mkdir(exist_ok=True)
release='f0148dab28e427621143d47b157bc7802ebab4f661d2d530e2162c4508b4b485'
base=pathlib.Path('preview-b/releases')/release
URL=f'http://127.0.0.1:8873/{base}/atelier-preview.html?quality=efficient&normalStream=1&plateQA=bevel-v1'
R={'expectedRelease':release,'url':URL,'sourceDigest':hashlib.sha256((base/'assembly-review.js').read_bytes()).hexdigest(),'probeDigest':hashlib.sha256(pathlib.Path('mechanism-plates-qa/bevel-probe.js').read_bytes()).hexdigest(),'errors':[],'setup':'Chromium SwiftShader, 900x900 DPR1, current viewer effective metal; AO/bloom disabled equally for matched QA; no device FPS claims'}
async def run():
 async with async_playwright()as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']);page=await b.new_page(viewport={'width':900,'height':900},device_scale_factor=1);page.set_default_timeout(180000)
  async def instrument(route):
   resp=await route.fetch();body=await resp.body();assert hashlib.sha256(body).hexdigest()==R['sourceDigest'];await route.fulfill(response=resp,body=body+b'\n'+pathlib.Path('mechanism-plates-qa/bevel-probe.js').read_bytes())
  await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto(URL,wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000);R['init']=await page.evaluate('plateQA.init()');print('INIT',json.dumps(R['init']),flush=True)
   await page.wait_for_function('plateQA.settled()',timeout=300000)
   for pose in ['whole','close','rim']:
    await page.evaluate('(m)=>plateQA.pose(m)',pose);R[pose]={}
    for state in ['baseline','delaunay','bevel','baseline']:
     name=state if state not in R[pose] else state+'-repeat';R[pose][name]=await page.evaluate('(s)=>plateQA.set(s)',state);await page.locator('#assembly-canvas').screenshot(path=str(O/f'{pose}-{name}.png'),timeout=180000);print(pose,name,flush=True)
    assert len({json.dumps(x['camera'],sort_keys=True)for x in R[pose].values()})==1
   assert R['init']['release']==release;assert not R['errors'];R['passed']=True
  except Exception as e:
   R['passed']=False;R['failure']=repr(e);print('FAIL',repr(e),flush=True)
   try:await page.screenshot(path=str(O/'failure.png'),timeout=15000)
   except Exception:pass
   raise
  finally:
   (O/'report.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(run())
