import asyncio,json,pathlib,hashlib
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
O=pathlib.Path('mechanism-plates-qa/other-material-qa');O.mkdir(exist_ok=True)
release='f0148dab28e427621143d47b157bc7802ebab4f661d2d530e2162c4508b4b485';base=pathlib.Path('preview-b/releases')/release
URL=f'http://127.0.0.1:8873/{base}/atelier-preview.html?quality=efficient&normalStream=1&plateQA=other-exact-v1'
R={'expectedRelease':release,'url':URL,'sourceDigest':hashlib.sha256((base/'assembly-review.js').read_bytes()).hexdigest(),'probeDigest':hashlib.sha256(pathlib.Path('mechanism-plates-qa/other-plates-probe.js').read_bytes()).hexdigest(),'errors':[],'sources':{},'setup':'Chromium SwiftShader WebGL2; 900x900 viewport DPR1; exact-seam geometry; actual post-override material; AO/bloom disabled equally; isolated parts only, not device FPS or whole-watch/contact acceptance'}
async def run():
 async with async_playwright()as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']);page=await browser.new_page(viewport={'width':900,'height':900},device_scale_factor=1);page.set_default_timeout(180000)
  async def instrument(route):
   response=await route.fetch();body=await response.body();assert hashlib.sha256(body).hexdigest()==R['sourceDigest'];await route.fulfill(response=response,body=body+b'\n'+pathlib.Path('mechanism-plates-qa/other-plates-probe.js').read_bytes())
  await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto(URL,wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000)
   for sid in [41,70,116,141]:
    out=O/str(sid);out.mkdir(exist_ok=True);d=pathlib.Path(f'mechanism-plates-qa/exact-seams/{sid}');expected={k+'SHA256':hashlib.sha256((d/f'{k}.bin').read_bytes()).hexdigest() for k in ['position','normal','index']}
    row={'init':await page.evaluate('(sid)=>plateQA.init(sid)',sid),'states':{}};R['sources'][str(sid)]=row;await page.wait_for_function('plateQA.settled()',timeout=300000)
    for pose in ['whole','close','rim']:
     await page.evaluate('(m)=>plateQA.pose(m)',pose);data={}
     for label,state in [('baseline','baseline'),('candidate','delaunay'),('baseline-repeat','baseline')]:
      data[label]=await page.evaluate('(s)=>plateQA.set(s)',state);await page.locator('#assembly-canvas').screenshot(path=str(out/f'{pose}-{label}.png'),timeout=180000);print(sid,pose,label,flush=True)
     assert len({json.dumps(x['camera'],sort_keys=True)for x in data.values()})==1;assert all(x['materialSame']for x in data.values());assert len({json.dumps(x['material'],sort_keys=True)for x in data.values()})==1
     for k,v in expected.items():assert data['candidate']['geometry'][k]==v,(sid,pose,k)
     a=Image.open(out/f'{pose}-baseline.png').convert('RGB');repeat=Image.open(out/f'{pose}-baseline-repeat.png').convert('RGB');assert not ImageChops.difference(a,repeat).getbbox(),'A/B/A baseline pixel drift';b=Image.open(out/f'{pose}-candidate.png').convert('RGB');diff=ImageChops.difference(a,b);data['metrics']={'baselineRepeatPixelExact':True,'meanAbsoluteDifference255':sum(ImageStat.Stat(diff).mean)/3,'differenceBBox':diff.getbbox()};row['states'][pose]=data
    (out/'report.json').write_text(json.dumps(row,indent=2))
   assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);print('FAIL',repr(e),flush=True);raise
  finally:(O/'report.json').write_text(json.dumps(R,indent=2));await browser.close()
asyncio.run(run())
