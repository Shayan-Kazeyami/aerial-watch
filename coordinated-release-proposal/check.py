import asyncio,json,os,pathlib,traceback,hashlib
from playwright.async_api import async_playwright
P=pathlib.Path('coordinated-release-proposal');OUT=P/('evidence-'+os.environ['QA_ASSETS']+'-'+os.environ['QA_VIEWPORT']);OUT.mkdir(exist_ok=True)
RID=(P/'release-id.txt').read_text().strip();W,H=map(int,os.environ.get('QA_VIEWPORT','430x932').split('x'))
MODE=os.environ['QA_ASSETS'];REQUEST_MODE='meshopt'if MODE in ['fallback','default']else MODE;Q=P;source=P.joinpath('staging/preview-b/releases',RID,'assembly-review.js').read_bytes().decode();needle='function initializeBaseline(result,metadata){';assert source.count(needle)==1;wrapper=(source.replace(needle,needle+'window.casebackLoadedAssetDelivery=result.metrics?.assetDelivery;').replace('if(mesh.userData.sourceIndex!==undefined)source.push(mesh);else exterior.push(mesh);',"if(mesh.userData.sourceIndex!==undefined){source.push(mesh);const a=mesh.geometry.attributes.normal.array,bytes=new Uint8Array(a.buffer,a.byteOffset,a.byteLength).slice();(window.__releaseSerializedNormalHashes??=[]).push(crypto.subtle.digest('SHA-256',bytes).then(h=>({sourceIndex:mesh.userData.sourceIndex,normalSHA256:[...new Uint8Array(h)].map(x=>x.toString(16).padStart(2,'0')).join('')})));}else exterior.push(mesh);")+'\n'+(P/'crown-probe.js').read_bytes().decode()+'\n'+(Q/'caseback-proof.js').read_bytes().decode()+'\n'+(Q/'full-probe.js').read_bytes().decode()).encode();EXPECTED_WRAPPER=hashlib.sha256(wrapper).hexdigest()
R={'assetMode':MODE,'expectedQAWrapperSHA256':EXPECTED_WRAPPER,'release':RID,'viewport':[W,H],'errors':[],'setup':'Chromium SwiftShader touch emulation, not physical-device FPS'}
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await browser.new_page(viewport={'width':W,'height':H},device_scale_factor=1,is_mobile=True,has_touch=True);page.set_default_timeout(180000)
  host=page;served={}
  async def executed(res):
   name=res.url.split('?')[0].split('/')[-1]
   if name in ['assembly-mechanism-batch.js','assembly-hardware-canonical-data.js','assembly-optimized-loading.js','assembly-leather-authoring-identity.js','viewer-revision.js']:served[res.url.split('?')[0]]=hashlib.sha256(await res.body()).hexdigest()
  page.on('response',executed)
  requests=[];R['requests']=requests;R['fallbackRetryPolicy']='Unchanged e79 fetchAsset retries a503 once; require2 deliberate failures per compressed owned asset before raw fallback';page.on('request',lambda q:requests.append(q.url));page.on('pageerror',lambda e:R['errors'].append(str(e)))
  async def instrument(route):
   await route.fulfill(status=200,content_type='text/javascript',body=wrapper)
  async def atelier(route):
   res=await route.fetch();text=await res.text();assert text.count("import('./assembly-review.js?v=atelier-local-1')")==1;await route.fulfill(response=res,body=text.replace("import('./assembly-review.js?v=atelier-local-1')","import('./assembly-review-caseback-integrated-private-qa.js')"))
  await page.route('**/atelier-preview.js',atelier);await page.route('**/assembly-review-caseback-integrated-private-qa.js',instrument)
  async def response(res):
   if 'assembly-review-caseback-integrated-private-qa.js' in res.url:R['executedQAWrapperSHA256']=hashlib.sha256(await res.body()).hexdigest()
  page.on('response',response)
  if MODE=='fallback':
   async def failCompressed(route):R['forcedCompressedFailures']=R.get('forcedCompressedFailures',0)+1;await route.fulfill(status=503,body='Deliberate QA failure to test canonical raw fallback')
   await page.route('**/optimized-assets/rebuild__assembly.meshopt.glb.gz*',failCompressed)
  if MODE=='fallback':
   async def failFace(route):R['forcedFaceFailures']=R.get('forcedFaceFailures',0)+1;await route.fulfill(status=503,body='Deliberate QA face failure to test raw fallback')
   await page.route('**/optimized-assets/premium-face__face-svg04.meshopt.glb*',failFace)
  try:
   await page.goto('http://127.0.0.1:8765/?quality=efficient'+(''if MODE=='default'else'&assets='+REQUEST_MODE),wait_until='domcontentloaded',timeout=120000)
   await host.wait_for_function('document.querySelector("#watch-viewer")?.contentWindow?.location.pathname.includes("'+RID+'")')
   page=next(f for f in host.frames if RID in f.url)
   R['entryURL']=host.url;R['iframeURL']=page.url
   await page.locator('body[data-ready=true]').wait_for(timeout=300000)
   await page.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"',timeout=300000)
   inventory=await page.evaluate('watchGeometryInventory()')
   expected={'SVG_broad_sloped_champagne_wall':21172,'SVG_champagne_aperture_rim':6080,'SVG_lower_champagne_rim_lip':5888}
   R['faceGeometry']={r['name']:r['triangles'] for r in inventory['rows'] if r['name'] in expected}
   assert R['faceGeometry']==expected,R['faceGeometry']
   expectedParts={'CASE':239896,'CROWN':20540,'CROWN-TUBE':1536,'CASEBACK':16728}
   R['integratedGeometry']={r['userData'].get('assemblyId'):r['triangles'] for r in inventory['rows'] if r['userData'].get('assemblyId') in expectedParts}
   assert R['integratedGeometry']==expectedParts,R['integratedGeometry']
   assert R['executedQAWrapperSHA256']==EXPECTED_WRAPPER
   proof=await page.evaluate('casebackIntegratedProof()');R['sealedAssetProof']=proof
   expectedHashes={'position':'dcb0f019a5115a1355305b4b3a65a10258b57f4b69843cf08a892e308baa3c86','normal':'8daa2f12cfe7837c4a5e66ff27988eecb5a4a5c5b6cae25c08223da6717116d0','uv':'038513f0103424dca92c9be6adf8c17b1d4fbb216e9ea8f6d96aa30aa5d9e723','index':'a38f85bc8389d37d1294f1e28bc1d0fd9db700007e309d44fc6e11c91d48e680'}
   assert proof['caseback']['hashes']==expectedHashes
   assert proof['caseback']['canonicalTriangles']==proof['caseback']['displayTriangles']==16728
   assert proof['caseback']['cap']['capTriangles']==2160 and abs(proof['caseback']['cap']['capAreaMM2']-777.1554592858047)<1e-9
   assert proof['keeper']=={'count':2,'sharedGeometry':True,'sharedPosition':True,'sharedNormal':True,'positionNormalBytes':18432}
   assert proof['springbar']=={'count':2,'sharedPosition':True,'sharedNormal':True,'distinctUV':True}
   assert proof['leatherProof']['status']=='verified' and proof['leatherProof']['actualSha256']=='f7e7a7638b7ac58a3d3f568cbbcc0baa989d840d9b989e10b0c72485298ed0d5'
   assert proof['delivery']['used']==('raw'if MODE=='fallback'else 'meshopt'if MODE=='default'else MODE),proof['delivery']
   if MODE=='fallback':assert proof['delivery']['fallbackReason'] and R['forcedCompressedFailures']==2,proof['delivery']
   else:assert not proof['delivery']['fallbackReason'],proof['delivery']
   full=await page.evaluate('releaseFullProof()');R['fullReleaseProof']=full
   expected=json.loads((P/'expected-normal-hashes.json').read_text());assert sorted(full['serializedSources'],key=lambda x:x['sourceIndex'])==expected,'Serialized normal/source parity lost'
   build=json.loads((P/'build-report.json').read_text());assert full['revision']['digest']==build['viewerRevisionDigest'];assert full['three']=='187'
   assert full['ring']['vertices']==3088 and full['ring']['indices']==9216;assert full['ring']['userData']['premiumFacePart'] and full['ring']['userData']['designRevision']=='B-SVG-04'
   assert full['batch']['reusedEntries']==57 and full['batch']['rejectedReuse']==0
   assert full['batch']['originalGeometryBufferBytes']-full['batch']['allocatedGeometryBufferBytes']==5037456
   R['normalComparisonScope']='All166 decoded serialized normal hashes captured before existing e79 crown/winding/setting/spring private display derivation; runtime normals separately checked immutable across composed renders';R['runtimeCacheGuards']=await page.evaluate('releaseRuntimeCheck()');assert R['runtimeCacheGuards']['sourceNormalsUnchangedAcrossRender']
   manifest=json.loads(P.joinpath('staging/preview-b/releases',RID,'deployment-manifest.json').read_text());byname={f['path']:f for f in manifest['localFiles']}
   for url,h in served.items():
    if '/'+RID+'/' in url:
     name=url.split('/'+RID+'/',1)[1];assert name in byname and h==byname[name]['sha256'],('Executed runtime hash drift',url,h)
   assert any('/'+RID+'/assembly-mechanism-batch.js' in u for u in served);assert any('/'+RID+'/assembly-hardware-canonical-data.js' in u for u in served);R['executedModuleHashes']=served
   for i,cfg in enumerate([dict(pose=0),dict(pose=1,explode=1),dict(pose=4,explode=.45,finish=False),dict(pose=17,explode=0,viewName='movement')]):
    snap=await page.evaluate('(cfg)=>releaseCapture(cfg)',cfg);raw=__import__('base64').b64decode(snap.pop('png').split(',')[1]);(OUT/f'combined-{i}.png').write_bytes(raw);from PIL import Image,ImageStat
    im=Image.open(__import__('io').BytesIO(raw)).convert('RGB');assert max(ImageStat.Stat(im).stddev)>5,'Blank combined canvas';R.setdefault('combinedStates',[]).append(snap)
   await page.evaluate('releaseCapture({pose:0,explode:0,finish:true,viewName:"watch"})')
   await page.evaluate('prepareCrownMeshTouch()');await page.evaluate('mobileAuditFrames(4)')
   point=await page.evaluate('crownMeshPoint()');assert point,'No ray-confirmed mesh point outside hotspot';R['meshPoint']=point
   cdp=await host.context.new_cdp_session(host)
   async def touch(t,x=None,y=None):await cdp.send('Input.dispatchTouchEvent',{'type':t,'touchPoints':[] if x is None else [{'x':x,'y':y}]})
   initial=await page.evaluate('mobileAuditSnapshot()');startrequests=len(requests)
   for surface in ['mesh','dot']:
    previous=None;stable=0
    for settleAttempt in range(40):
     snap=await page.evaluate('mobileAuditFrames(2)')
     stable=stable+1 if previous==snap['camera'] else 0
     previous=snap['camera']
     if stable>=2:break
    assert stable>=2,'Pre-gesture camera never settled'
    if surface=='mesh':point=await page.evaluate('crownMeshPoint()')
    else:
     bb=await page.locator('.crown-hotspot').bounding_box();point={'x':bb['x']+bb['width']/2,'y':bb['y']+bb['height']/2}
    x,y=point['x'],point['y'];before=await page.evaluate('mobileAuditSnapshot()');await touch('touchStart',x,y);await touch('touchMove',x,y-22)
    a=await page.evaluate('mobileAuditFrames(4)');b=await page.evaluate('mobileAuditFrames(4)');assert b['state']['degrees']>a['state']['degrees']+.1,(surface,a,b)
    await touch('touchMove',x,y);a=await page.evaluate('mobileAuditFrames(4)');b=await page.evaluate('mobileAuditFrames(4)');assert a['state']['degrees']==b['state']['degrees']
    await touch('touchMove',x,y+22);c=await page.evaluate('mobileAuditFrames(4)');assert c['state']['degrees']<b['state']['degrees']-.1
    await touch('touchEnd');a=await page.evaluate('mobileAuditFrames(4)');b=await page.evaluate('mobileAuditFrames(4)');assert a['state']['degrees']==b['state']['degrees']
    assert a['camera']==before['camera'] and b['camera']==before['camera'],('Crown gesture moved camera',surface,before['camera'],a['camera'],b['camera'])
    assert b['orbitEnabled']==before['orbitEnabled'],'Orbit ownership not restored'
    assert not await page.locator('#context[data-tool="time"]').is_visible(),'Unsolicited Time panel'
    R[surface]={'continued':True,'neutralStops':True,'reversal':True,'releaseStops':True}
    # Reset while an actual held touch remains down must stop either input owner.
    await touch('touchStart',x,y);await touch('touchMove',x,y-22);await page.evaluate('mobileAuditFrames(3)');await page.evaluate('crownQAReset()')
    a=await page.evaluate('mobileAuditFrames(4)');b=await page.evaluate('mobileAuditFrames(4)');assert a['state']['degrees']==b['state']['degrees'],(surface,'reset continued')
    await touch('touchEnd');await page.evaluate('prepareCrownMeshTouch()');await page.evaluate('mobileAuditFrames(3)')
    # Both entry surfaces use the same tap and time-setting behavior.
    if surface=='mesh':point=await page.evaluate('crownMeshPoint()')
    else:
     bb=await page.locator('.crown-hotspot').bounding_box();point={'x':bb['x']+bb['width']/2,'y':bb['y']+bb['height']/2}
    x,y=point['x'],point['y'];before=await page.evaluate('mobileAuditSnapshot()')
    await touch('touchStart',x,y);await touch('touchEnd');after=await page.evaluate('mobileAuditFrames(4)')
    assert after['state']['pulled']!=before['state']['pulled'];assert after['settingSeconds']==before['settingSeconds']
    await page.wait_for_function('!mobileAuditSnapshot().crown')
    if surface=='mesh':point=await page.evaluate('crownMeshPoint()')
    else:
     bb=await page.locator('.crown-hotspot').bounding_box();point={'x':bb['x']+bb['width']/2,'y':bb['y']+bb['height']/2}
    x,y=point['x'],point['y'];await touch('touchStart',x,y);await touch('touchMove',x,y-22)
    setting=await page.evaluate('mobileAuditFrames(4)');assert setting['settingSeconds']!=after['settingSeconds']
    await touch('touchCancel');a=await page.evaluate('mobileAuditFrames(4)');b=await page.evaluate('mobileAuditFrames(4)');assert a['settingSeconds']==b['settingSeconds']
    R[surface].update(tapOnce=True,settingHold=True,cancelStops=True)
    await page.evaluate('prepareCrownMeshTouch()');await page.evaluate('mobileAuditFrames(3)')

   await page.locator('.crown-hotspot').focus();before=await page.evaluate('mobileAuditSnapshot()');await host.keyboard.press('ArrowUp');after=await page.evaluate('mobileAuditFrames(4)');assert after['state']['degrees']>before['state']['degrees'];R['keyboardTurns']=True
   await page.locator('.task-dock [data-mode="time"]').tap();assert await page.locator('#context[data-tool="time"]').is_visible();R['explicitTimePanel']=True
   await page.locator('.task-dock [data-mode="explore"]').tap()
   R['poseParity']=await page.evaluate('crownPoseParity()');assert all(v['maxMatrixDifference']<1e-12 and all(v[k]for k in['positionsExact','crownExact','windingExact','settingExact'])for v in R['poseParity'])
   final=await page.evaluate('mobileAuditSnapshot()');assert final['canvas']==initial['canvas'];assert final['timeOrigin']==initial['timeOrigin']
   R['newAssetRequests']=[u for u in requests[startrequests:] if any(u.split('?')[0].endswith(ext)for ext in['.glb','.gz','.bin'])];assert not R['newAssetRequests']
   await host.screenshot(path=str(OUT/'crown.png'),animations='disabled');assert not R['errors'];R['finalSealedAssetProof']=await page.evaluate('casebackIntegratedProof()');assert R['finalSealedAssetProof']==R['sealedAssetProof'];R['casebackCaptures']=[]
   for macro in [False,True]:
    R['casebackCaptures'].append(await page.evaluate('casebackIntegratedView',macro));await page.evaluate('mobileAuditFrames(4)');await page.locator('#assembly-canvas').screenshot(path=str(OUT/('caseback-'+('macro'if macro else'whole')+'.png')))
   await page.evaluate('releaseCapture({pose:0,explode:0,finish:true,viewName:"watch"})');await page.evaluate('releaseRing.setup()');await page.evaluate('releaseCapture({pose:0,explode:0,finish:true})')
   hit=await page.evaluate('releaseRing.pick()');await host.mouse.click(hit['x'],hit['y']);message=await page.locator('#viewer-status').text_content();assert hit['name'] in message;R['productionRingPicking']={'hit':hit,'announcement':message}
   await page.evaluate('releaseRing.restore()');await page.evaluate('releaseCapture({pose:0,explode:0,finish:true})')
   # Real user-facing JSON and PNG downloads through capture UI proxies.
   await page.locator('.task-dock [data-mode="capture"]').click()
   async with host.expect_download(timeout=300000)as dl:await page.locator('#context [data-proxy="export-config"]').click()
   download=await dl.value;await download.save_as(OUT/'aerial-view.json');config=json.loads((OUT/'aerial-view.json').read_text());assert build['viewerRevisionDigest'] in json.dumps(config),'Saved configuration provenance mismatch';R['configDownload']={'bytes':(OUT/'aerial-view.json').stat().st_size,'keys':list(config)}
   await page.wait_for_function('releaseFullProof().then(p=>!p.detail.required||p.detail.ready)',timeout=300000)
   async with host.expect_download(timeout=300000)as dl:await page.locator('#context [data-proxy="capture-scene"]').click()
   download=await dl.value;await download.save_as(OUT/'aerial-studio.png');png=(OUT/'aerial-studio.png').read_bytes();assert png.startswith(b'\x89PNG\r\n\x1a\n');im=Image.open(OUT/'aerial-studio.png');im.load();assert im.width>200 and im.height>200;assert max(ImageStat.Stat(im.convert('RGB')).stddev)>5;assert build['viewerRevisionDigest'].encode() in png,'PNG provenance missing exact release digest';R['pngDownload']={'bytes':len(png),'size':list(im.size),'detail':(await page.evaluate('releaseFullProof()'))['detail']}
   # Import the actual saved configuration; no synthetic import handler.
   await page.locator('#import-config').set_input_files(str(OUT/'aerial-view.json'));await page.wait_for_function('!window.assemblyInspect().loading');R['configurationRoundtrip']=True
   assert not R['errors'];R['requests']=requests
   if MODE in ['meshopt','default']:assert not any('/rebuild/assembly.glb' in u or '/premium-face/face-svg04.glb' in u for u in requests),'Unexpected compressed fallback'
   if MODE=='raw':assert any('/rebuild/assembly.glb' in u for u in requests)and any('/premium-face/face-svg04.glb' in u for u in requests),'Actual raw assets not exercised'
   if MODE=='fallback':assert R.get('forcedFaceFailures')==2 and any('/premium-face/face-svg04.glb' in u for u in requests),'Face fallback not exercised'
   R['passed']=True
  except Exception as e:R.update(passed=False,failure=repr(e),traceback=traceback.format_exc());raise
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));await browser.close()
asyncio.run(asyncio.wait_for(main(),2400))
