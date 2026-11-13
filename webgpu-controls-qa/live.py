import asyncio,json,pathlib,os,time,re,urllib.request,urllib.parse
from playwright.async_api import async_playwright
O=pathlib.Path('webgpu-controls-live');O.mkdir(exist_ok=True);R={'errors':[],'viewports':{},'setup':'Live GitHub Pages Chromium SwiftShader functional check; not hardware FPS'};rid=os.environ['EXPECTED_RELEASE']
async def run():
 # Wait for deployment with cheap HTTP reads before initializing the expensive viewer.
 base='https://shayan-kazeyami.github.io/aerial-watch/'
 for attempt in range(120):
  try:
   root=await asyncio.to_thread(lambda:urllib.request.urlopen(base+'?release-probe='+rid[:12]+'&attempt='+str(attempt),timeout=20).read().decode())
   scripts=re.findall(r'<script[^>]+src=[\"\']([^\"\']+)',root)
   loader=next(s for s in scripts if 'watch-home-' in s)
   body=await asyncio.to_thread(lambda:urllib.request.urlopen(urllib.parse.urljoin(base,loader)+'?release-probe='+rid[:12],timeout=20).read().decode())
   if rid in body:print('Public loader ready before browser startup',flush=True);break
  except Exception as error:print('Deployment preflight',type(error).__name__,flush=True)
  await asyncio.sleep(5)
 else:raise AssertionError('Deployment preflight did not find expected release')
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':932,'height':430},device_scale_factor=3,is_mobile=True,has_touch=True);page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  async def instrument(route):
   response=await route.fetch();await route.fulfill(response=response,body=(await response.text())+'\n'+pathlib.Path('crown-unified-qa/probe.js').read_text())
  await page.route('**/assembly-review.js*',instrument)
  attempts=0
  async def transient_failure(route):
   nonlocal attempts
   if route.request.headers.get('range'):
    attempts+=1
    if attempts==1:await route.fulfill(status=503,body='Controlled recovery check');return
   await route.continue_()
  await page.route('**/outer-normal-4k.ktx2.part0',transient_failure)
  try:
   for attempt in range(20):
    await page.goto('https://shayan-kazeyami.github.io/aerial-watch/?mesh='+rid[:12],wait_until='domcontentloaded');await page.wait_for_timeout(15000);frames=[f for f in page.frames if rid in f.url]
    if frames:print('Release iframe found',flush=True);break
   assert frames,'Public loader does not select tested release';f=frames[0];await f.locator('body[data-ready=true]').wait_for(timeout=300000);await f.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000);print('Viewer ready',flush=True);R['release']=rid;R['url']=page.url;R['initialQuality']=(await f.evaluate('assemblyInspect()'))['renderQuality'];assert R['initialQuality']=='efficient';assert 'normalStream=1' in f.url
   inventory=await f.evaluate('watchGeometryInventory()')
   expected={'SVG_broad_sloped_champagne_wall':21172,'SVG_champagne_aperture_rim':6080,'SVG_lower_champagne_rim_lip':5888}
   R['faceGeometry']={r['name']:r['triangles'] for r in inventory['rows'] if r['name'] in expected}
   assert R['faceGeometry']==expected,R['faceGeometry']
   assert 'normalStream=1' in f.url,f.url
   await f.wait_for_function('''()=>{document.getElementById('refresh-diagnostics').click();return JSON.parse(document.getElementById('diagnostics-report').textContent).progressiveNormal==='failed'}''',timeout=240000)
   await f.locator('.task-dock [data-mode=capture]').tap(force=True)
   assert await f.locator('#context [data-proxy=capture-scene]').is_disabled()
   assert await f.locator('#context [data-proxy=export-config]').is_enabled()
   await f.locator('#atelier-retry-detail').click()
   await f.wait_for_function('''()=>{document.getElementById('refresh-diagnostics').click();return JSON.parse(document.getElementById('diagnostics-report').textContent).progressiveNormal==='full'}''',timeout=240000)
   R['inPlaceRetry']={'controlledFailures':1,'rangeAttempts':attempts};assert attempts==2
   assert await f.locator('#context [data-proxy=capture-scene]').is_enabled()
   await f.locator('#close').click()
   config=await f.evaluate('''()=>{document.getElementById('refresh-diagnostics').click();return JSON.parse(document.getElementById('diagnostics-report').textContent)}''');detail=config['leatherCraft']['candidate']['detail'];assert detail['ready'] and detail['activeNormalIdentity']['width']==4096;assert detail['activeNormalIdentity']['sha256']=='bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585';R['detail']=detail;R['normalTransfer']=config['progressiveNormalMetrics']
   (O/'full-detail-config.json').write_text(json.dumps(config,indent=2))
   canvasBeforeTools=await f.locator('#assembly-canvas').bounding_box()
   await f.locator('.masthead .quality').click();assert await f.locator('#atelier-backend-indicator').inner_text()=='WebGL2';assert 'Try WebGPU' in await f.locator('#atelier-backend-toggle').inner_text();await f.locator('.debug-benchmark summary').click();await f.wait_for_function("!document.getElementById('atelier-benchmark-start').disabled");assert '8 cases' in await f.locator('#atelier-benchmark-start').inner_text();assert await f.evaluate("getComputedStyle(document.querySelector('.crown-hotspot')).visibility==='hidden'");assert canvasBeforeTools==await f.locator('#assembly-canvas').bounding_box();await page.screenshot(path=str(O/'backend-benchmark-controls.png'));await f.locator('#close').click();R['publicBackendControls']={'actual':'WebGL2','experimentalToggle':True,'eightCaseBenchmarkAvailable':True,'canvasStable':True,'sceneAffordanceBelowPanel':True}
   await f.evaluate('prepareCrownMeshTouch()');await f.evaluate('mobileAuditFrames(4)')
   point=await f.evaluate('crownMeshPoint()');assert point,'No public direct crown surface'
   iframe=await page.locator('#watch-viewer').bounding_box();x=point['x']+iframe['x'];y=point['y']+iframe['y']
   cdp=await page.context.new_cdp_session(page)
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-22}]})
   a=await f.evaluate('mobileAuditFrames(4)');bstate=await f.evaluate('mobileAuditFrames(4)');assert bstate['state']['degrees']>a['state']['degrees']+.1
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
   a=await f.evaluate('mobileAuditFrames(4)');bstate=await f.evaluate('mobileAuditFrames(4)');assert a['state']['degrees']==bstate['state']['degrees']
   assert not await f.locator('#context[data-tool="time"]').is_visible()
   R['directCrownHold']={'continued':True,'releaseStopped':True,'noPopup':True,'point':point}
   await page.screenshot(path=str(O/'direct-crown.png'));await f.evaluate('crownQAReset()')
   for w,h in [(430,932),(932,430)]:
    print('Checking viewport',w,h,flush=True);await page.set_viewport_size({'width':w,'height':h});await page.wait_for_timeout(1500);before=await f.locator('#assembly-canvas').bounding_box();await f.locator('.task-dock [data-mode=explode]').tap(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating');assert f in page.frames;panel=await f.locator('#context').bounding_box();assert panel['height']<=165,panel;await page.screenshot(path=str(O/f'{w}-exploded.png'));
    await f.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'");
    await f.locator('#atelier-layer-focus').focus();await f.locator('#atelier-layer-focus').press('ArrowDown');await f.locator('#atelier-layer-focus').press('Enter');await f.wait_for_function('assemblyInspect().layerFocus.selected==="plate"');
    await f.locator('#atelier-layer-focus').select_option('balance');await f.wait_for_function('assemblyInspect().layerFocus.selected==="balance"');await page.wait_for_timeout(1000);await page.screenshot(path=str(O/f'{w}-balance.png'));assert before==await f.locator('#assembly-canvas').bounding_box();await f.locator('#atelier-layer-overview').tap(force=True);await f.wait_for_function('!assemblyInspect().layerFocus.selected');assert (await f.evaluate('assemblyInspect()'))['explosion']['amount']==1;await f.locator('#home').tap(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating');after=await f.locator('#assembly-canvas').bounding_box();assert before==after;(O/f'{w}-inspect.json').write_text(json.dumps(await f.evaluate('assemblyInspect()'),indent=2));R['viewports'][str(w)]={'explodeReset':True,'canvasStable':True,'panelHeight':panel['height']};await page.screenshot(path=str(O/f'{w}-assembled.png'))
   assert not R['errors'];R['passed']=True
  except Exception as e:
   R['passed']=False;R['failure']=repr(e);print(json.dumps(R),flush=True)
   try:await asyncio.wait_for(page.screenshot(path=str(O/'failure.png')),15)
   except Exception:pass
   raise
  finally:
   (O/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True)
   try:await asyncio.wait_for(b.close(),15)
   except Exception:pass
asyncio.run(run())
