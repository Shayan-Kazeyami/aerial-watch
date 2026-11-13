import asyncio,gzip,hashlib,json,pathlib
from playwright.async_api import async_playwright
from PIL import Image,ImageChops
ROOT=pathlib.Path('mechanism-plates-qa');O=ROOT/'integration-09e3';O.mkdir(exist_ok=True)
RELEASE='09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29'
BASE=pathlib.Path('preview-b/releases')/RELEASE
URL=f'http://127.0.0.1:8873/{BASE}/atelier-preview.html?quality=efficient&normalStream=1&plateQA=integrated-09e3-v1&paused=1'
R={'expectedRelease':RELEASE,'sourceDigest':hashlib.sha256((BASE/'assembly-review.js').read_bytes()).hexdigest(),'probeDigest':hashlib.sha256((ROOT/'integration-probe.js').read_bytes()).hexdigest(),'errors':[],'poses':{},'scope':'Private runtime swaps of all five plate fixtures on current sealed production viewer. AO/bloom off equally. SwiftShader WebGL2, not phone FPS or continuous contact certification.'}
async def run():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']);page=await browser.new_page(viewport={'width':1100,'height':1000},device_scale_factor=1);page.set_default_timeout(240000)
  async def instrument(route):
   response=await route.fetch();body=await response.body();assert hashlib.sha256(body).hexdigest()==R['sourceDigest'];await route.fulfill(response=response,body=body+b'\n'+(ROOT/'integration-probe.js').read_bytes())
  await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto(URL,wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('plateIntegrationQA.ready()',timeout=300000)
   print('INIT START',flush=True);R['init']=await page.evaluate('plateIntegrationQA.init()');assert R['init']['release']==RELEASE
   gate=json.loads((ROOT/'current-raw-hash-gate.json').read_text())
   for target in R['init']['source']['targets']:
    expected=next(x for x in gate['rows']if x['sourceIndex']==target['sid'])['attrs'];assert target['positionHash']==expected['POSITION'];assert target['normalHash']==expected['NORMAL']
   for spec in [{'name':'assembled','view':'showcase'},{'name':'front','view':'face'},{'name':'exploded','view':'showcase','explode':1},{'name':'moving-7','view':'interior','time':7},{'name':'moving-23','view':'interior','time':23},{'name':'crown-pulled','view':'showcase','pulled':True},{'name':'reset','view':'showcase'}]:
    name=spec.pop('name');print('POSE',name,flush=True);await page.evaluate('(s)=>plateIntegrationQA.pose(s)',spec);row={};R['poses'][name]=row
    for label,mode in [('baseline','baseline'),('candidate','candidate'),('bevel','bevel'),('baseline-repeat','baseline')]:
     print('SET',name,label,flush=True);data=await asyncio.wait_for(page.evaluate('(m)=>plateIntegrationQA.set(m)',mode),timeout=120);row[label]=data
     await page.locator('#assembly-canvas').screenshot(path=str(O/f'{name}-{label}.png'));print(name,label,flush=True)
     if label!='baseline-repeat':
      print('CONTACTS',name,label,flush=True);contacts=await asyncio.wait_for(page.evaluate('plateIntegrationQA.contacts()'),timeout=120);(O/f'{name}-{label}-contacts.json.gz').write_bytes(gzip.compress(json.dumps(contacts,separators=(',',':')).encode()))
     assert not data['loading']and not data['failed'];assert all(x['materialSame']for x in data['targets']);assert not data['AO']and not data['bloom']
     if mode!='baseline':
      for target in data['targets']:
       directory='front-bevel-trial'if mode=='bevel'and target['sid']==100 else'exact-seams';d=ROOT/directory/str(target['sid'])
       for k in ['position','normal','index']:assert target[k+'Hash']==hashlib.sha256((d/f'{k}.bin').read_bytes()).hexdigest()
    assert len({json.dumps(x['camera'],sort_keys=True)for x in row.values()})==1
    assert len({json.dumps([(t['sid'],t['matrix'],t['visible'],t['material'])for t in x['targets']],sort_keys=True)for x in row.values()})==1
    a=Image.open(O/f'{name}-baseline.png').convert('RGB');b=Image.open(O/f'{name}-baseline-repeat.png').convert('RGB');assert not ImageChops.difference(a,b).getbbox(),'A/B/A drift'
    row['baselineRepeatPixelExact']=True
   assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);R['pageText']=await page.locator('body').inner_text();print('FAIL',repr(e),flush=True);raise
  finally:(O/'report.json').write_text(json.dumps(R,indent=2));await browser.close()
asyncio.run(run())
