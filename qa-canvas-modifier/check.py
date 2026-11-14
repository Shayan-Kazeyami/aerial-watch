import asyncio,json,os,traceback
from pathlib import Path
from playwright.async_api import async_playwright
P=Path('qa-canvas-modifier');O=P/'evidence';O.mkdir(exist_ok=True);R={'passed':False,'errors':[],'routes':[]}
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for route in ['raw','meshopt']:
    page=await browser.new_page(viewport={'width':1000,'height':800},device_scale_factor=1);page.on('pageerror',lambda e:R['errors'].append(str(e)));requests=[];page.on('request',lambda q:requests.append(q.url))
    await page.goto('http://127.0.0.1:8874/qa-canvas-modifier/runtime/atelier-preview.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets='+route+'&light=softbox&antialias=smaa&tickBatch=1&paused=1',wait_until='domcontentloaded')
    await page.wait_for_function('window.__modifierQA?.snapshot().ready',timeout=300000);await page.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"',timeout=300000)
    canvas=page.locator('#assembly-canvas');await canvas.focus();await page.wait_for_timeout(500)
    rr={'route':route,'cases':[],'requests':requests};R['routes'].append(rr)
    for chord in ['Control+=','Control+-','Meta+=','Meta+-','Alt+=','Alt+-']:
     before=await page.evaluate('__modifierQA.snapshot()');assert before['focusCanvas']
     await page.keyboard.press(chord);await page.wait_for_timeout(250)
     after=await page.evaluate('__modifierQA.snapshot()');event=await page.evaluate('__modifierQA.events.at(-1)')
     assert after['zoom']==before['zoom'],(route,chord,before,after)
     assert after['camera']==before['camera'] and after['target']==before['target'],(route,chord,'camera moved')
     assert not event['prevented'],(route,chord,event)
     rr['cases'].append({'chord':chord,'before':before,'after':after,'event':event,'browserZoomObserved':after['dpr']!=before['dpr'] or after['innerWidth']!=before['innerWidth'] or after['visualScale']!=before['visualScale']})
    for chord,factor in [('=',1.15),('-',1/1.15),('Shift+Equal',1.15),('Shift+Minus',1/1.15)]:
     before=await page.evaluate('__modifierQA.snapshot()');await page.keyboard.press(chord);await page.wait_for_timeout(250);after=await page.evaluate('__modifierQA.snapshot()');event=await page.evaluate('__modifierQA.events.at(-1)')
     assert abs(after['zoom']-before['zoom']*factor)<1e-10,(route,chord,before,after)
     assert event['prevented'],(route,chord,event)
     if chord=='Shift+Equal':assert event['key']=='+',event
     if chord=='Shift+Minus':assert event['key']=='_',event
     rr['cases'].append({'chord':chord,'before':before,'after':after,'event':event,'plainWatchZoomVerified':True})
    await page.screenshot(path=str(O/(route+'-canvas-focused.png')))
    rr['delivery']=await page.evaluate('assemblyInspect().delivery||assemblyInspect().assets||null')
    assert any('/rebuild/assembly.glb' in u for u in requests) if route=='raw' else any('/optimized-assets/rebuild__assembly.meshopt.glb.gz' in u for u in requests)
    if route=='meshopt':assert not any('/rebuild/assembly.glb' in u for u in requests),'unexpected raw fallback'
    await page.close();(O/'report.json').write_text(json.dumps(R,indent=2))
   assert not R['errors'];R['passed']=True
  except Exception as e:R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:
   R['scope']='Real canonical full viewer, canvas-focused browser key events. Browser UI zoom is claimed only where observed; headless CDP shortcut behavior may not exercise browser-chrome zoom.'
   (O/'report.json').write_text(json.dumps(R,indent=2));await browser.close()
asyncio.run(main())
