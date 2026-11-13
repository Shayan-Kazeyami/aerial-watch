import asyncio,json,pathlib,os
from playwright.async_api import async_playwright
O=pathlib.Path('marked-live');O.mkdir(exist_ok=True);R={'errors':[],'viewports':{},'setup':'Live GitHub Pages Chromium SwiftShader functional check; not hardware FPS'};rid=os.environ['EXPECTED_RELEASE']
async def run():
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=3,is_mobile=True,has_touch=True);page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   for attempt in range(20):
    await page.goto('https://shayan-kazeyami.github.io/aerial-watch/?mesh='+rid[:12],wait_until='domcontentloaded');await page.wait_for_timeout(15000);frames=[f for f in page.frames if rid in f.url]
    if frames:print('Release iframe found',flush=True);break
   assert frames,'Public loader does not select tested release';f=frames[0];await f.locator('body[data-ready=true]').wait_for(timeout=300000);await f.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000);print('Viewer ready',flush=True);R['release']=rid;R['url']=page.url
   for w,h in [(430,932),(932,430)]:
    print('Checking viewport',w,h,flush=True);await page.set_viewport_size({'width':w,'height':h});await page.wait_for_timeout(1500);before=await f.locator('#assembly-canvas').bounding_box();await f.locator('.task-dock [data-mode=explode]').tap(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating');assert f in page.frames;await page.screenshot(path=str(O/f'{w}-exploded.png'));await f.locator('#home').tap(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating');after=await f.locator('#assembly-canvas').bounding_box();assert before==after;(O/f'{w}-inspect.json').write_text(json.dumps(await f.evaluate('assemblyInspect()'),indent=2));R['viewports'][str(w)]={'explodeReset':True,'canvasStable':True};await page.screenshot(path=str(O/f'{w}-assembled.png'))
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
