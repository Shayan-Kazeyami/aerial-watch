import asyncio,json,pathlib,hashlib,os,traceback
from playwright.async_api import async_playwright
Q=pathlib.Path('movement-retopo-qa/current-pack');CAND=(Q/'release-id.txt').read_text().strip();SOURCE='09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29';MODE=os.environ.get('QA_ASSETS','raw');O=Q/('evidence-'+MODE);O.mkdir(exist_ok=True);R={'sourceRelease':SOURCE,'candidateRelease':CAND,'assetMode':MODE,'setup':'Exact sealed local assets, no geometry overlays; production lights/materials, AO off, seeded randomness; Chromium SwiftShader, not hardware FPS','variants':{}}
async def run():
 async with async_playwright()as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for variant,rid in [('source',SOURCE),('candidate',CAND)]:
   c=await browser.new_context(viewport={'width':1100,'height':1000},device_scale_factor=1);pg=await c.new_page();pg.set_default_timeout(300000);r={'errors':[],'transport':[]};R['variants'][variant]=r;pg.on('pageerror',lambda e:r['errors'].append(str(e)));tasks=[]
   await pg.add_init_script('Math.random=(()=>{let s=192837465;return ()=>((s=(1664525*s+1013904223)>>>0)/4294967296)})();')
   async def instrument(route):
    response=await route.fetch();s=await response.text();needle='function initializeBaseline(result,metadata){';assert s.count(needle)==1;s=s.replace(needle,needle+'window.wheelQAAssetDelivery=result.metrics?.assetDelivery;window.wheelQAParserJSON=(result.gltf||result).parser.json;')+'\n'+(Q/'probe.js').read_text();await route.fulfill(response=response,body=s)
   await pg.route('**/assembly-review.js*',instrument)
   async def response(resp):
    if resp.url.split('?')[0].endswith(('/rebuild/assembly.glb','/optimized-assets/rebuild__assembly.meshopt.glb.gz')):
     b=await resp.body();r['transport'].append({'url':resp.url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
   pg.on('response',lambda resp:tasks.append(asyncio.create_task(response(resp))))
   try:
    await pg.goto(f'http://127.0.0.1:8767/preview-b/releases/{rid}/atelier-preview.html?quality=efficient&normalStream=1&ao=off&paused=1&assets={MODE}',wait_until='domcontentloaded');await pg.locator('body[data-ready=true]').wait_for();await pg.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"');await pg.evaluate('wheelQA.init()');await pg.wait_for_function('wheelQA.settled()');await pg.evaluate('wheelQA.frames(8)');r['initial']=await pg.evaluate('wheelQA.snapshot()');assert r['initial']['triangles']==(21944 if variant=='source'else 17812);assert r['initial']['delivery']['used']==MODE and not r['initial']['delivery']['fallbackReason'];assert r['initial']['proof']['status']=='verified';r['poses']=[]
    for amount,pulled in[(0,False),(.25,False),(.5,True),(.75,True),(1,False),(0,False)]:
     await pg.evaluate('([a,p])=>wheelQA.pose(a,p)',[amount,pulled]);await pg.evaluate('wheelQA.frames(5)');r['poses'].append({'amount':amount,'pulled':pulled,'snapshot':await pg.evaluate('wheelQA.snapshot()')})
    start=await pg.evaluate('wheelQA.motion().mechanism');await pg.locator('#play-motion').evaluate('e=>e.click()');await pg.wait_for_function('(s)=>wheelQA.motion().mechanism>s+.1',arg=start);await pg.evaluate('wheelQA.freeze()');r['motionAdvanced']=True
    r['visuals']=[]
    for v in['assembled','exploded','wheel-whole','wheel-whole-wire','wheel-macro','wheel-macro-wire']:
     r['visuals'].append(await pg.evaluate('(v)=>wheelQA.visual(v)',v));await pg.wait_for_function('wheelQA.settled()');await pg.evaluate('wheelQA.frames(5)');await pg.locator('#assembly-canvas').screenshot(path=str(O/f'{variant}-{v}.png'))
    await asyncio.gather(*tasks);manifest=json.loads((Q/'serve/preview-b/releases'/rid/'deployment-manifest.json').read_text());logical='rebuild/assembly.glb'if MODE=='raw'else'optimized-assets/rebuild__assembly.meshopt.glb.gz';spec=next(x for x in manifest['localFiles']if x['path']==logical);assert len(r['transport'])==1 and r['transport'][0]['sha256']==spec['sha256'] and r['transport'][0]['bytes']==spec['sizeBytes'];assert not r['errors'];r['passed']=True
   except Exception as e:
    r.update(passed=False,error=repr(e),traceback=traceback.format_exc());await pg.screenshot(path=str(O/(variant+'-failure.png')));raise
   finally:(O/'report.json').write_text(json.dumps(R,indent=2));await c.close()
  a=R['variants']['source'];b=R['variants']['candidate'];assert a['visuals']==b['visuals'];R['matchedVisualCameras']=True
  for x,y in zip(a['poses'],b['poses']):
   assert x['amount']==y['amount'] and x['pulled']==y['pulled'];assert x['snapshot']['matrix']==y['snapshot']['matrix'];assert x['snapshot']['contactNodeMatrices']==y['snapshot']['contactNodeMatrices']
  R['allSixMechanicalPoseMatricesExact']=True;R['passed']=True;(O/'report.json').write_text(json.dumps(R,indent=2));await browser.close()
asyncio.run(asyncio.wait_for(run(),1800))
