import asyncio,json,pathlib,traceback,os,hashlib,math,base64
from playwright.async_api import async_playwright
Q=pathlib.Path('strap-combined-qa');MODE=os.environ.get('QA_ASSETS','meshopt');assert MODE in ('raw','meshopt');CAND=(Q/'release-id.txt').read_text().strip();SOURCE='75756356ca7b944a5143c519b75d3cac2f8aa62cfcf40302b249f7eefda85f69';O=pathlib.Path('strap-combined-evidence-'+MODE);O.mkdir(exist_ok=True);BUILD=json.loads((Q/'build-report.json').read_text());R={'sourceRelease':SOURCE,'candidateRelease':CAND,'assetMode':MODE,'setup':'Actual sealed assets; instrumentation only, no geometry route overlays. Chromium SwiftShader, not hardware FPS. Matched AO off; seeded randomness.','variants':{}}
def compare_rows(a,b,tolerance=False):
 assert len(a)==len(b)
 mp=mn=0
 for x,y in zip(a,b):
  assert x['name']==y['name'] and x['triangles']==y['triangles'] and x['indexHash']==y['indexHash']
  assert x['attrs']['uv']==y['attrs']['uv']
  assert len(x['worldPositions'])==len(y['worldPositions'])
  for i in range(0,len(x['worldPositions']),3):
   pa=x['worldPositions'][i:i+3];pb=y['worldPositions'][i:i+3];na=x['worldNormals'][i:i+3];nb=y['worldNormals'][i:i+3]
   mp=max(mp,math.sqrt(sum((v-w)**2 for v,w in zip(pa,pb))));den=math.sqrt(sum(v*v for v in na)*sum(v*v for v in nb));mn=max(mn,math.degrees(math.acos(max(-1,min(1,sum(v*w for v,w in zip(na,nb))/den)))))
  if not tolerance:assert x==y
 assert mp<.0001 and mn<.05,(mp,mn)
 return {'maxWorldPositionErrorMm':mp,'maxWorldNormalErrorDegrees':mn}
async def run():
 async with async_playwright()as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for variant,rid in [('source',SOURCE),('candidate',CAND)]:
   context=await browser.new_context(viewport={'width':1100,'height':800},device_scale_factor=1);page=await context.new_page();cdp=await context.new_cdp_session(page);await cdp.send('Network.enable',{'maxTotalBufferSize':134217728,'maxResourceBufferSize':67108864});page.set_default_timeout(300000);errors=[];requests=[];tasks=[];r={'pageErrors':errors,'transport':[]};R['variants'][variant]=r;page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda q:requests.append(q.url))
   await page.add_init_script('Math.random=(()=>{let s=192837465;return ()=>((s=(1664525*s+1013904223)>>>0)/4294967296)})();')
   async def instrument(route):
    response=await route.fetch();text=await response.text();needle='function initializeBaseline(result,metadata){';assert text.count(needle)==1;text=text.replace(needle,needle+'window.springQAAssetDelivery=result.metrics?.assetDelivery;window.combinedParserJSON=(result.gltf||result).parser.json;')+'\n'+(Q/'probe.js').read_text();await route.fulfill(response=response,body=text)
   await page.route('**/assembly-review.js*',instrument)
   # Read on the CDP session whose retention limits we configure, not Playwright's
   # separate internal inspector session. No transport routes or asset substitutions.
   asset_ids=set()
   def asset_received(event):
    name=event['response']['url'].split('?')[0]
    if name.endswith('/rebuild/assembly.glb') or name.endswith('/optimized-assets/rebuild__assembly.meshopt.glb.gz'):
     asset_ids.add(event['requestId'])
   async def asset_finished(event):
    if event['requestId']not in asset_ids:return
    payload=await cdp.send('Network.getResponseBody',{'requestId':event['requestId']})
    body=base64.b64decode(payload['body'])if payload.get('base64Encoded')else payload['body'].encode()
    r['transport'].append({'requestId':event['requestId'],'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'capture':'passive same-session CDP'})
   cdp.on('Network.responseReceived',asset_received)
   cdp.on('Network.loadingFinished',lambda event:tasks.append(asyncio.create_task(asset_finished(event))))
   try:
    await page.goto('http://127.0.0.1:8765/preview-b/releases/'+rid+'/atelier-preview.html?quality=efficient&normalStream=1&ao=off&assets='+MODE,wait_until='domcontentloaded',timeout=120000)
    await page.locator('body[data-ready=true]').wait_for(timeout=300000);await asyncio.gather(*tasks);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"');await page.wait_for_function('leatherQASnapshot().proof?.status==="verified"');await page.evaluate('leatherQAFrames(6)');r['initialLeather']=await page.evaluate('leatherQASnapshot()');expected='f7e7a7638b7ac58a3d3f568cbbcc0baa989d840d9b989e10b0c72485298ed0d5'if variant=='candidate'else'97377092fcfc6f5a7e934e083f71a1d5e99c9d2007a1b5c3ba38a2b6a6dc61e3';assert r['initialLeather']['proof']['actualSha256']==expected;assert not r['initialLeather']['failed']
    await page.wait_for_function('''()=>{document.getElementById('refresh-diagnostics').click();return JSON.parse(document.getElementById('diagnostics-report').textContent).progressiveNormal==='full'}''');r['config']=await page.evaluate('''()=>{document.getElementById('refresh-diagnostics').click();return JSON.parse(document.getElementById('diagnostics-report').textContent)}''');assert r['config']['leatherCraft']['candidate']['detail']['activeNormalIdentity']['width']==4096
    r['initialKeepers']=await page.evaluate('springQASnapshot()');r['initialSpringbars']=await page.evaluate('springQASnapshot("^SPRINGBAR")');assert r['initialKeepers']['assetDelivery']['used']==MODE;assert not r['initialKeepers']['assetDelivery']['fallbackReason'];assert r['initialSpringbars']['sharedPositionAttribute'] and r['initialSpringbars']['sharedNormalAttribute'] and r['initialSpringbars']['distinctUVAttribute'];assert r['initialSpringbars']['uploadedPositionNormalBytes']==54384
    if variant=='candidate':
     assert r['initialKeepers']['sharedGeometry'] and r['initialKeepers']['uploadedPositionNormalBytes']==18432
     assert await page.evaluate('combinedParserJSON.meshes[146].primitives[0].attributes.POSITION===451&&combinedParserJSON.meshes[146].primitives[0].attributes.NORMAL===452&&combinedParserJSON.nodes[146].matrix.length===16')
    else:assert not r['initialKeepers']['sharedGeometry'] and r['initialKeepers']['uploadedPositionNormalBytes']==36864
    assert len(r['initialKeepers']['rows'])==2;assert all(row['attrs']['uv']is None for row in r['initialKeepers']['rows'])
    start=len(requests);r['poses']=[]
    for amount,pulled in[(0,False),(.25,False),(.5,True),(.75,True),(1,False),(0,False)]:
     await page.evaluate('([a,p])=>leatherQAPose(a,p)',[amount,pulled]);await page.evaluate('leatherQAFrames(8)');s=await page.evaluate('leatherQASnapshot()');assert s['canvas']==r['initialLeather']['canvas'] and s['timeOrigin']==r['initialLeather']['timeOrigin'];assert [x['matrix']for x in s['rows']]==[x['matrix']for x in r['initialLeather']['rows']];r['poses'].append({'amount':amount,'pulled':pulled,'keepers':await page.evaluate('springQASnapshot()'),'springbars':await page.evaluate('springQASnapshot("^SPRINGBAR")')})
    r['assetRefetches']=[u for u in requests[start:]if any(u.split('?')[0].endswith(x)for x in['.glb','.gltf','.bin','.glb.gz'])];assert not r['assetRefetches'];await page.screenshot(path=str(O/(variant+'-assembled.png')))
    await asyncio.gather(*tasks);transport=r['transport'];assert len(transport)==1,transport
    manifest=json.loads(pathlib.Path('preview-b/releases',rid,'deployment-manifest.json').read_text());logical='rebuild/assembly.glb'if MODE=='raw'else'optimized-assets/rebuild__assembly.meshopt.glb.gz';spec=next(x for x in manifest['localFiles']if x['path']==logical);assert transport[0]['sha256']==spec['sha256'] and transport[0]['bytes']==spec['sizeBytes'],transport
    r['visuals']=[]
    for view in['strap-whole','strap-macro','strap-macro-wire','keeper-whole','keeper-wire']:
     r['visuals'].append(await page.evaluate('combinedVisual',view));await page.evaluate('leatherQAFrames(8)');await page.locator('#assembly-canvas').screenshot(path=str(O/(variant+'-'+view+'.png')))
    r['disposalArmed']=await page.evaluate('combinedArmDisposal()');r['disposal']=await page.evaluate('combinedTeardown()');assert r['disposal']['lifecycleDisposed'];assert all(x==1 for x in r['disposal']['geometryEvents']);assert all(x==1 for x in r['disposal']['bufferDeletes']);assert not errors;r['passed']=True
   except Exception as e:
    r.update(passed=False,error=repr(e),traceback=traceback.format_exc());
    try:await asyncio.wait_for(page.screenshot(path=str(O/(variant+'-failure.png'))),15)
    except Exception:pass
    raise
   finally:
    (O/'report.json').write_text(json.dumps(R,indent=2));await context.close()
  a=R['variants']['source'];b=R['variants']['candidate'];R['keeperFidelity']=[compare_rows(a['initialKeepers']['rows'],b['initialKeepers']['rows'],True)]+[compare_rows(x['keepers']['rows'],y['keepers']['rows'],True)for x,y in zip(a['poses'],b['poses'])];R['springbarsUnchanged']=[compare_rows(a['initialSpringbars']['rows'],b['initialSpringbars']['rows'])]+[compare_rows(x['springbars']['rows'],y['springbars']['rows'])for x,y in zip(a['poses'],b['poses'])];R['verifiedKeeperUploadSavingsBytes']=18432;R['passed']=True;(O/'report.json').write_text(json.dumps(R,indent=2));await browser.close()
asyncio.run(asyncio.wait_for(run(),1800))
