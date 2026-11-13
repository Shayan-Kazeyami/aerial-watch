import asyncio,json,pathlib,base64,os,hashlib
from playwright.async_api import async_playwright
D=pathlib.Path('isolated-runtime-composition/recovery-2155');O=D/'viewer-evidence';O.mkdir(exist_ok=True)
MODE=os.environ.get('COMPOSE_MODE','current')
F=pathlib.Path('normal-fixture/hardware-normal-qa/e79-rebase')
RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':640,'height':640},device_scale_factor=1);page.set_default_timeout(300000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  async def review(route):
   response=await route.fetch();body=await response.text()
   if MODE=='baked-raw':
    marker="optIn:new URLSearchParams(location.search).get('assets')==='meshopt'";assert marker in body;body=body.replace(marker,'optIn:false')
   await route.fulfill(response=response,body=body+'\n'+(D/'reference-probe.js').read_text())
  async def batch(route):
   response=await route.fetch();s=(D/'composed-canonical-batch.js').read_text().replace("'../hardware-reuse-qa/integration/changes/assembly-hardware-canonical-data.js'","'./assembly-hardware-canonical-data.js'").replace('sourceIndex:e.mesh.userData.sourceIndex','batchUuid:batch.uuid,sourceIndex:e.mesh.userData.sourceIndex').replace('if(!previous||','if(!window.__matrixCacheEnabled||!previous||').replace('batch.setMatrixAt(id,matrix);','window.__matrixWrites=(window.__matrixWrites||0)+1;batch.setMatrixAt(id,matrix);');await route.fulfill(response=response,body=s)
  async def canonical(route):await route.fulfill(status=200,content_type='text/javascript',body=(D/'assembly-hardware-canonical-data.js').read_text())
  await page.route('**/assembly-hardware-canonical-data.js*',canonical)
  await page.route('**/assembly-review.js*',review);await page.route('**/assembly-mechanism-batch.js*',batch)
  requests=[];intercepted=[];page.on('request',lambda r:requests.append(r.url))
  if MODE!='current':
   candidate=F/'assembly-normal-candidate.glb'
   assert hashlib.sha256(candidate.read_bytes()).hexdigest()=='6ac638843c56eb4ae2f3d9ee1135facaac085ae70e2292f2b3d30f9673340039'
   async def raw(r):
    intercepted.append(r.request.url)
    if MODE=='baked-meshopt':raise AssertionError('compressed gate fell back to raw')
    await r.fulfill(path=str(candidate))
   await page.route('**/rebuild/assembly.glb*',raw)
   if MODE=='baked-meshopt':
    gz=F/'optimized-assets/rebuild__assembly.meshopt.glb.gz';assert hashlib.sha256(gz.read_bytes()).hexdigest()=='22877fb671c582361f0613953d1ad065bbf3b2d9e6aa55595e2a6233797587b1'
    async def compressed(r):intercepted.append(r.request.url);await r.fulfill(path=str(gz))
    async def size(r):
     response=await r.fetch();body=await response.body();assert b'const GZIP_DECODED_BYTES=14192960;' in body
     await r.fulfill(response=response,body=body.replace(b'const GZIP_DECODED_BYTES=14192960;',b'const GZIP_DECODED_BYTES=14193252;'))
    await page.route('**/optimized-assets/rebuild__assembly.meshopt.glb.gz*',compressed);await page.route('**/assembly-optimized-loading.js*',size)
  results=[]
  try:
   await page.goto('https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/'+RID+'/atelier-preview.html?normalStream=1'+('&assets=meshopt' if MODE=='baked-meshopt' else '&assets=raw'),wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for();await page.wait_for_function('window.matrixCacheQA && document.querySelector("#stage").dataset.cameraReady==="true"');await page.evaluate('matrixCacheQA.freeze()');await page.wait_for_timeout(1000)
   from PIL import Image
   import numpy as np
   cases=[('movement',dict(view='movement')),('exploded-movement',dict(view='movement',explode=1,pose=4)),('assembled',dict(view='watch'))]+[(f'part-{sid}',dict(sid=sid,view='movement',zoom=1.4))for sid in [12,21,26,39,40,71,125,126,128]]
   diffs=[]
   for name,params in cases:
    pair=[]
    for batched in [False,True]:
     cfg=dict(cache=True,finish=True,pose=0,frames=3,batched=batched);cfg.update(params)
     r=await page.evaluate('(cfg)=>matrixCacheQA.sample(cfg)',cfg);png=r.pop('png');(O/f'{name}-{batched}.png').write_bytes(base64.b64decode(png.split(',')[1]));r['case']=name;pair.append(r);results.append(r);(O/'results.json').write_text(json.dumps(results,indent=2));assert r['normalSourcesUnchanged'];assert r['maxCorrectedMatrixError']<2e-6;assert r['state']['reusedEntries']==57
    a=np.array(Image.open(O/f'{name}-False.png')).astype(float);c=np.array(Image.open(O/f'{name}-True.png')).astype(float);d=np.abs(a-c);diff=dict(case=name,mean=float(d.mean()),pixelsOver8=float(np.mean(d.max(2)>8)));diffs.append(diff);(O/'diffs.json').write_text(json.dumps(diffs,indent=2));print(json.dumps(diff),flush=True)
    assert pair[0]['render']['triangles']==pair[1]['render']['triangles'],pair
    assert diff['mean']<.1 and diff['pixelsOver8']<.001,diff
   if MODE!='current':assert intercepted,'candidate asset route not exercised'
   if MODE=='baked-meshopt':assert not any('/rebuild/assembly.glb' in u for u in requests),'raw fallback masks compressed failure'
   (O/'routes.json').write_text(json.dumps(dict(mode=MODE,intercepted=intercepted,requests=requests),indent=2));(O/'errors.json').write_text(json.dumps(errors));assert not errors,errors
  finally:await b.close()
asyncio.run(run())
