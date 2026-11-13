import asyncio,json,pathlib,hashlib
from playwright.async_api import async_playwright
O=pathlib.Path('mechanism-plates-qa/source-preserving-material-qa');O.mkdir(exist_ok=True)
release='09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29'
base=pathlib.Path('preview-b/releases')/release
URL=f'http://127.0.0.1:8873/{base}/atelier-preview.html?quality=efficient&normalStream=1&plateQA=source-preserving-bevel-v1'
R={'expectedRelease':release,'url':URL,'sourceDigest':hashlib.sha256((base/'assembly-review.js').read_bytes()).hexdigest(),'probeDigest':hashlib.sha256(pathlib.Path('mechanism-plates-qa/source-preserving-probe.js').read_bytes()).hexdigest(),'errors':[],'setup':'Chromium SwiftShader, 900x900 DPR1, current viewer effective metal; AO/bloom disabled equally for matched QA; no device FPS claims'}
async def run():
 async with async_playwright()as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']);page=await b.new_page(viewport={'width':900,'height':900},device_scale_factor=1);page.set_default_timeout(180000)
  async def instrument(route):
   resp=await route.fetch();body=await resp.body();assert hashlib.sha256(body).hexdigest()==R['sourceDigest'];await route.fulfill(response=resp,body=body+b'\n'+pathlib.Path('mechanism-plates-qa/source-preserving-probe.js').read_bytes())
  await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto(URL,wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000);R['init']=await page.evaluate('plateQA.init()');print('INIT',json.dumps(R['init']),flush=True)
   await page.wait_for_function('plateQA.settled()',timeout=300000)
   for pose in ['whole','close','rim']:
    await page.evaluate('(m)=>plateQA.pose(m)',pose);R[pose]={}
    for state in ['baseline','delaunay','bevel','baseline']:
     name=state if state not in R[pose] else state+'-repeat';R[pose][name]=await page.evaluate('(s)=>plateQA.set(s)',state);await page.locator('#assembly-canvas').screenshot(path=str(O/f'{pose}-{name}.png'),timeout=180000);print(pose,name,flush=True)
    assert len({json.dumps(x['camera'],sort_keys=True)for x in R[pose].values()})==1
    assert all(x['materialSame'] for x in R[pose].values()),'Material assignment drift'
    assert len({json.dumps(x['material'],sort_keys=True)for x in R[pose].values()})==1
    from PIL import Image,ImageChops,ImageStat
    a=Image.open(O/f'{pose}-baseline.png').convert('RGB');z=Image.open(O/f'{pose}-baseline-repeat.png').convert('RGB');assert not ImageChops.difference(a,z).getbbox(),'A/B/A baseline pixel drift'
    if pose!='whole':
     x=Image.open(O/f'{pose}-bevel.png').convert('RGB');y=Image.open(O/f'{pose}-delaunay.png').convert('RGB');assert ImageChops.difference(x,y).getbbox(),'Bevel render is a no-op'
   assert R['init']['release']==release;assert not R['errors'];
   expected=json.loads(pathlib.Path('mechanism-plates-qa/source-preserving-front-bevel-invariants.json').read_text());assert R['init']['counts']['bevel']==expected['trianglesCandidate'];
   for pose in ['whole','close','rim']:
    for key in ['position','normal','index']:
     assert R[pose]['bevel']['geometry'][key+'SHA256']==hashlib.sha256(pathlib.Path('mechanism-plates-qa/source-preserving-front-bevel/100/'+key+'.bin').read_bytes()).hexdigest()
   R['passed']=True
  except Exception as e:
   R['passed']=False;R['failure']=repr(e);print('FAIL',repr(e),flush=True)
   try:await page.screenshot(path=str(O/'failure.png'),timeout=15000)
   except Exception:pass
   raise
  finally:
   (O/'report.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(run())
