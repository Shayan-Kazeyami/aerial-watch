import asyncio,json,pathlib,base64
from playwright.async_api import async_playwright
D=pathlib.Path('isolated-runtime-composition/recovery-2155');O=D/'viewer-evidence';O.mkdir(exist_ok=True)
RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':640,'height':640},device_scale_factor=1);page.set_default_timeout(300000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  async def review(route):
   response=await route.fetch();await route.fulfill(response=response,body=(await response.text())+'\n'+(D/'viewer-probe.js').read_text())
  async def batch(route):
   response=await route.fetch();s=(D/'composed-canonical-batch.js').read_text().replace("'../hardware-reuse-qa/integration/changes/assembly-hardware-canonical-data.js'","'./assembly-hardware-canonical-data.js'").replace('if(!previous||','if(!window.__matrixCacheEnabled||!previous||').replace('batch.setMatrixAt(id,matrix);','window.__matrixWrites=(window.__matrixWrites||0)+1;batch.setMatrixAt(id,matrix);');await route.fulfill(response=response,body=s)
  async def canonical(route):await route.fulfill(status=200,content_type='text/javascript',body=(D/'assembly-hardware-canonical-data.js').read_text())
  await page.route('**/assembly-hardware-canonical-data.js*',canonical)
  await page.route('**/assembly-review.js*',review);await page.route('**/assembly-mechanism-batch.js*',batch)
  results=[]
  try:
   await page.goto('https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/'+RID+'/atelier-preview.html?normalStream=1',wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for();await page.wait_for_function('window.matrixCacheQA && document.querySelector("#stage").dataset.cameraReady==="true"');await page.evaluate('matrixCacheQA.freeze()');await page.wait_for_timeout(1000)
   for explode,finish,pose in [(0,True,0),(1,True,1),(1,False,4),(0,True,17),(.45,True,3),(.7,False,9),(0,False,0),(1,True,17)]:
    for cache in [True,False]:
     cfg=dict(cache=cache,explode=explode,finish=finish,pose=pose,frames=3);r=await page.evaluate('(cfg)=>matrixCacheQA.sample(cfg)',cfg);(O/'latest-diagnostic.json').write_text(json.dumps({k:v for k,v in r.items() if k!='png'},indent=2));assert r['state']['reusedEntries']==57,r['state'];assert r['normalSourcesUnchanged'];assert r['maxCorrectedMatrixError']<2e-6;png=r.pop('png');(O/f'{explode}-{finish}-{pose}-{cache}.png').write_bytes(base64.b64decode(png.split(',')[1]));results.append(r);print(json.dumps({k:r[k] for k in ['cache','explode','finish','pose','writes','render','cpuSubmissionMs']}),flush=True);(O/'results.json').write_text(json.dumps(results,indent=2))
   (O/'dynamic.json').write_text(json.dumps(await page.evaluate('matrixCacheQA.dynamic()'),indent=2))
   (O/'errors.json').write_text(json.dumps(errors));assert not errors,errors
   from PIL import Image
   import numpy as np
   diffs=[]
   for c,a in zip(results[::2],results[1::2]):
    assert a['render']['triangles']==c['render']['triangles'];assert a['render']['calls']==c['render']['calls']
    key=f"{a['explode']}-{a['finish']}-{a['pose']}"
    imageA=np.array(Image.open(O/f'{key}-False.png')).astype(float);imageB=np.array(Image.open(O/f'{key}-True.png')).astype(float);d=np.abs(imageA-imageB)
    diff=dict(case=key,mean=float(d.mean()),pixelsOver8=float(np.mean(d.max(2)>8)));diffs.append(diff)
    assert diff['mean']<.1 and diff['pixelsOver8']<.001,diff
    assert c['writes']<a['writes'],[a['writes'],c['writes']]
   # A/B/A exact repeat after state transitions must match, not merely look nonblank.
   repeat=[]
   for cfg in [dict(cache=True,explode=0,finish=True,pose=0,frames=3),dict(cache=True,explode=1,finish=False,pose=6,frames=3),dict(cache=True,explode=0,finish=True,pose=0,frames=3)]:
    r=await page.evaluate('(cfg)=>matrixCacheQA.sample(cfg)',cfg);repeat.append(r.pop('png'))
   assert repeat[0]==repeat[2], 'A/B/A repeat mismatch'
   (O/'repeat.json').write_text(json.dumps(dict(exactRepeat=True)))
   (O/'diffs.json').write_text(json.dumps(diffs,indent=2))
  finally:await b.close()
asyncio.run(run())
