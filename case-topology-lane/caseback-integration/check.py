import asyncio,json,os,pathlib,traceback,hashlib
from playwright.async_api import async_playwright
P=pathlib.Path('crown-unified-qa');OUT=pathlib.Path('case-topology-lane/caseback-integration/evidence-'+os.environ['QA_ASSETS']+'-'+os.environ['QA_VIEWPORT']);OUT.mkdir(exist_ok=True)
RID=(P/'release-id.txt').read_text().strip();W,H=map(int,os.environ.get('QA_VIEWPORT','430x932').split('x'))
MODE=os.environ['QA_ASSETS'];REQUEST_MODE='meshopt'if MODE=='fallback'else MODE;Q=pathlib.Path('case-topology-lane/caseback-integration');source=pathlib.Path('preview-b/releases',RID,'assembly-review.js').read_bytes().decode();needle='function initializeBaseline(result,metadata){';assert source.count(needle)==1;wrapper=(source.replace(needle,needle+'window.casebackLoadedAssetDelivery=result.metrics?.assetDelivery;')+'\n'+(P/'probe.js').read_bytes().decode()+'\n'+(Q/'proof.js').read_bytes().decode()).encode();EXPECTED_WRAPPER=hashlib.sha256(wrapper).hexdigest()
R={'assetMode':MODE,'expectedQAWrapperSHA256':EXPECTED_WRAPPER,'release':RID,'viewport':[W,H],'errors':[],'setup':'Chromium SwiftShader touch emulation, not physical-device FPS'}
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await browser.new_page(viewport={'width':W,'height':H},device_scale_factor=1,is_mobile=True,has_touch=True);page.set_default_timeout(180000)
  requests=[];page.on('request',lambda q:requests.append(q.url));page.on('pageerror',lambda e:R['errors'].append(str(e)))
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
  try:
   await page.goto('http://127.0.0.1:8765/preview-b/releases/'+RID+'/atelier-preview.html?quality=efficient&assets='+REQUEST_MODE,wait_until='domcontentloaded',timeout=120000)
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
   assert proof['delivery']['used']==('raw'if MODE=='fallback'else MODE),proof['delivery']
   if MODE=='fallback':assert proof['delivery']['fallbackReason'] and R['forcedCompressedFailures']==1,proof['delivery']
   else:assert not proof['delivery']['fallbackReason'],proof['delivery']
   await page.evaluate('prepareCrownMeshTouch()');await page.evaluate('mobileAuditFrames(4)')
   point=await page.evaluate('crownMeshPoint()');assert point,'No ray-confirmed mesh point outside hotspot';R['meshPoint']=point
   cdp=await page.context.new_cdp_session(page)
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

   await page.locator('.crown-hotspot').focus();before=await page.evaluate('mobileAuditSnapshot()');await page.keyboard.press('ArrowUp');after=await page.evaluate('mobileAuditFrames(4)');assert after['state']['degrees']>before['state']['degrees'];R['keyboardTurns']=True
   await page.locator('.task-dock [data-mode="time"]').tap();assert await page.locator('#context[data-tool="time"]').is_visible();R['explicitTimePanel']=True
   await page.locator('.task-dock [data-mode="explore"]').tap()
   R['poseParity']=await page.evaluate('crownPoseParity()');assert all(v['maxMatrixDifference']<1e-12 and all(v[k]for k in['positionsExact','crownExact','windingExact','settingExact'])for v in R['poseParity'])
   final=await page.evaluate('mobileAuditSnapshot()');assert final['canvas']==initial['canvas'];assert final['timeOrigin']==initial['timeOrigin']
   R['newAssetRequests']=[u for u in requests[startrequests:] if any(u.split('?')[0].endswith(ext)for ext in['.glb','.gz','.bin'])];assert not R['newAssetRequests']
   await page.screenshot(path=str(OUT/'crown.png'),animations='disabled');assert not R['errors'];R['finalSealedAssetProof']=await page.evaluate('casebackIntegratedProof()');assert R['finalSealedAssetProof']==R['sealedAssetProof'];R['casebackCaptures']=[]
   for macro in [False,True]:
    R['casebackCaptures'].append(await page.evaluate('casebackIntegratedView',macro));await page.evaluate('mobileAuditFrames(4)');await page.locator('#assembly-canvas').screenshot(path=str(OUT/('caseback-'+('macro'if macro else'whole')+'.png')))
   R['passed']=True
  except Exception as e:R.update(passed=False,failure=repr(e),traceback=traceback.format_exc());raise
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));await browser.close()
asyncio.run(asyncio.wait_for(main(),1100))
