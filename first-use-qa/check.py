import asyncio,json,pathlib,os
from playwright.async_api import async_playwright
OUT=pathlib.Path('first-use-output');OUT.mkdir(exist_ok=True);URL=os.environ['WATCH_URL'];R={'url':URL,'errors':[],'checks':{}}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  try:
   page=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,reduced_motion='reduce');page.set_default_timeout(30000)
   async def instrument(route):
    resp=await route.fetch();await route.fulfill(response=resp,body=await resp.text()+'\n'+pathlib.Path('first-use-qa/append.js').read_text())
   await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
   await page.goto(URL,wait_until='domcontentloaded',timeout=120000);await page.locator('body[data-ready=true]').wait_for(timeout=300000)
   cue=page.locator('.atelier-first-use');await cue.wait_for(state='visible');R['checks']['firstTouchCueVisible']=True
   R['checks']['text']=await cue.text_content();R['checks']['pointerEvents']=await cue.evaluate('e=>getComputedStyle(e).pointerEvents');assert R['checks']['pointerEvents']=='none'
   shown=await page.locator('#assembly-canvas').bounding_box();await cue.evaluate('e=>e.hidden=true');hidden=await page.locator('#assembly-canvas').bounding_box();await cue.evaluate('e=>e.hidden=false');assert shown==hidden;R['checks']['unchangedCanvasBounds']=shown
   R['checks']['focusNotStolen']=await page.evaluate('document.activeElement===document.body');assert R['checks']['focusNotStolen']
   await page.screenshot(path=str(OUT/'first-use-portrait.png'),timeout=180000)
   await page.evaluate('caseQA.init()');await page.wait_for_function('caseQA.settled()');await page.evaluate('caseQA.pose(null)');await page.evaluate('caseQA.set(true)')
   before=await page.evaluate('startupSnapshot().totalFrames');await page.wait_for_timeout(500);after=await page.evaluate('startupSnapshot().totalFrames');R['checks']['pausedAdditionalFrames']=after-before;assert after-before<=1
   await page.evaluate("window.touchTrace=[];for(const n of ['pointerdown','pointerup','touchstart','touchend','click'])document.addEventListener(n,e=>touchTrace.push({type:n,target:e.target.outerHTML.slice(0,160),x:e.clientX,y:e.clientY}),true)")
   cdp=await page.context.new_cdp_session(page);await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':150,'y':300}]});await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':190,'y':315}]});await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});await cue.wait_for(state='hidden');R['checks']['completionStored']=await page.evaluate("localStorage.getItem('aerial.touch-guide.v1')");assert R['checks']['completionStored']=='done'
   await page.wait_for_timeout(350);box=await page.locator('.task-dock [data-mode=explode]').bounding_box();await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':box['x']+box['width']/2,'y':box['y']+box['height']/2}]});await page.wait_for_timeout(60);await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});await page.wait_for_timeout(1000);R['checks']['touchTrace']=await page.evaluate('touchTrace');R['checks']['postTapExplosion']=await page.evaluate('assemblyInspect().explosion');await page.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating');assert not await cue.is_visible();R['checks']['explodeUnaffected']=True
   box=await page.locator('#home').bounding_box();await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':box['x']+box['width']/2,'y':box['y']+box['height']/2}]});await page.wait_for_timeout(60);await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});await page.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating');assert not await cue.is_visible();R['checks']['noReplayOnReset']=True
   await page.reload(wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=300000);assert not await cue.is_visible();R['checks']['noReplayAfterReload']=True
   await page.set_viewport_size({'width':844,'height':390});await page.wait_for_timeout(500);await page.screenshot(path=str(OUT/'return-visit-landscape.png'),timeout=180000)
   assert not R['errors'];R['passed']=True
  except Exception as e:
   R['passed']=False;R['failure']=repr(e)
   try:
    R['failureState']=await page.evaluate('({explosion:assemblyInspect().explosion,ready:document.body.dataset.ready,mode:document.querySelector("#context").dataset.tool})');await page.screenshot(path=str(OUT/'failure.png'),timeout=30000)
   except Exception:pass
   raise
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True)
   try:await asyncio.wait_for(b.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())
