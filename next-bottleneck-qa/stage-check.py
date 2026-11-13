import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('bottleneck-evidence');O.mkdir(exist_ok=True)
RID='3e9e591cbf61eaabb0b8dc9909c157514c9d14144b0dabdaa8543c368d0f4466'
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=1,is_mobile=True,has_touch=True);page.set_default_timeout(300000)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  async def intercept(route):
   response=await route.fetch();await route.fulfill(response=response,body=(await response.text())+'\n'+pathlib.Path('next-bottleneck-qa/probe.js').read_text())
  await page.route('**/assembly-review.js*',intercept)
  try:
   await page.goto('http://127.0.0.1:8765/',wait_until='domcontentloaded')
   await page.wait_for_timeout(10000);f=next(f for f in page.frames if RID in f.url)
   await f.locator('body[data-ready=true]').wait_for();await f.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"')
   await f.evaluate('bottleneckQA.freeze()');await page.wait_for_timeout(3000)
   data=[]
   for profile in ['efficient','studio']:
    for explode,finish in [(0,True),(1,True),(0,False)]:
     for batch in [True,False]:
      cfg=dict(profile=profile,explode=explode,finish=finish,batch=batch)
      result=await f.evaluate('(cfg)=>bottleneckQA.sample(cfg)',cfg);data.append(result);print(json.dumps({**cfg,'render':result['render'],'batchState':result['batch']}),flush=True)
      await f.locator('#assembly-canvas').screenshot(path=str(O/f'{profile}-{explode}-{finish}-{batch}.png'))
      (O/'results.json').write_text(json.dumps(data,indent=2))
   (O/'errors.json').write_text(json.dumps(errors));assert not errors
   from PIL import Image
   import numpy as np
   comparisons=[]
   for profile in ['efficient','studio']:
    for explode,finish in [(0,True),(1,True),(0,False)]:
     a=np.asarray(Image.open(O/f'{profile}-{explode}-{finish}-True.png')).astype('f4');c=np.asarray(Image.open(O/f'{profile}-{explode}-{finish}-False.png')).astype('f4');d=np.abs(a-c)
     comparisons.append(dict(profile=profile,explode=explode,finish=finish,mean=float(d.mean()),max=float(d.max()),pixelsOver8=float(np.mean(d.max(2)>8))))
   (O/'image-diffs.json').write_text(json.dumps(comparisons,indent=2));print(comparisons,flush=True)
   assert all(x['mean']<.1 and x['pixelsOver8']<.001 for x in comparisons),comparisons
   for a,c in zip(data[::2],data[1::2]):
    assert a['render']['triangles']==c['render']['triangles'];assert a['render']['calls']<c['render']['calls']

  finally:
   try:await asyncio.wait_for(b.close(),15)
   except:pass
asyncio.run(run())
