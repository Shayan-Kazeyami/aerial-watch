import asyncio,json,os,pathlib,traceback
from playwright.async_api import async_playwright
P=pathlib.Path('crown-unified-qa');OUT=pathlib.Path('crown-unified-evidence');OUT.mkdir(exist_ok=True)
RID=(P/'release-id.txt').read_text().strip();W,H=map(int,os.environ.get('QA_VIEWPORT','430x932').split('x'))
R={'release':RID,'viewport':[W,H],'errors':[],'setup':'Chromium SwiftShader touch emulation, not physical-device FPS'}
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await browser.new_page(viewport={'width':W,'height':H},device_scale_factor=1,is_mobile=True,has_touch=True);page.set_default_timeout(180000)
  requests=[];page.on('request',lambda q:requests.append(q.url));page.on('pageerror',lambda e:R['errors'].append(str(e)))
  async def instrument(route):
   res=await route.fetch();await route.fulfill(response=res,body=(await res.text())+'\n'+(P/'probe.js').read_text())
  await page.route('**/assembly-review.js*',instrument)
  try:
   await page.goto('http://127.0.0.1:8765/preview-b/releases/'+RID+'/atelier-preview.html?quality=efficient',wait_until='domcontentloaded',timeout=120000)
   await page.locator('body[data-ready=true]').wait_for(timeout=300000)
   await page.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"',timeout=300000)
   inventory=await page.evaluate('watchGeometryInventory()')
   expected={'SVG_broad_sloped_champagne_wall':21172,'SVG_champagne_aperture_rim':6080,'SVG_lower_champagne_rim_lip':5888}
   R['faceGeometry']={r['name']:r['triangles'] for r in inventory['rows'] if r['name'] in expected}
   assert R['faceGeometry']==expected,R['faceGeometry']
   expectedParts={'CASE':239896,'CROWN':20540,'CROWN-TUBE':1536}
   R['integratedGeometry']={r['userData'].get('assemblyId'):r['triangles'] for r in inventory['rows'] if r['userData'].get('assemblyId') in expectedParts}
   assert R['integratedGeometry']==expectedParts,R['integratedGeometry']
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
   await page.screenshot(path=str(OUT/'crown.png'),animations='disabled');assert not R['errors'];R['passed']=True
  except Exception as e:R.update(passed=False,failure=repr(e),traceback=traceback.format_exc());raise
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));await browser.close()
asyncio.run(asyncio.wait_for(main(),1100))
