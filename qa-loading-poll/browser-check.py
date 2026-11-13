import asyncio,json,pathlib,hashlib,base64
from playwright.async_api import async_playwright
O=pathlib.Path('qa-loading-poll/evidence');O.mkdir(parents=True,exist_ok=True)
R={'scope':'Actual public e79 root and iframe, injected one failed core module, authentic Reload button; isolated wrapper response only','arms':{}}
async def arm(browser,name):
 ctx=await browser.new_context(viewport={'width':430,'height':932},is_mobile=True,has_touch=True,device_scale_factor=1)
 page=await ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 async def capture(path):
  cdp=await ctx.new_cdp_session(page)
  result=await asyncio.wait_for(cdp.send('Page.captureScreenshot',{'format':'png','fromSurface':True,'captureBeyondViewport':False}),90)
  path.write_bytes(base64.b64decode(result['data']))
  await cdp.detach()
 await page.add_init_script("""if(window===top){const set=window.setInterval.bind(window),clear=window.clearInterval.bind(window);window.pollProbe={ticks:0,active:[]};window.setInterval=(f,ms,...a)=>{let id=set(()=>{if(ms===250)pollProbe.ticks++;f(...a)},ms);if(ms===250)pollProbe.active.push(id);return id};window.clearInterval=id=>{pollProbe.active=pollProbe.active.filter(x=>x!==id);clear(id)}}""")
 src=pathlib.Path('qa-loading-poll/'+name+'.mjs').read_text()
 async def wrapper(route):
  await route.fulfill(status=200,content_type='text/javascript',body=src)
 await page.route('**/watch-home-caseback-e79b2236.js*',wrapper)
 failures=0
 async def core(route):
  nonlocal failures
  if failures==0:
   failures+=1;await route.fulfill(status=503,content_type='text/javascript',body='/* controlled terminal import failure */')
  else:await route.continue_()
 await page.route('**/assembly-review.js*',core)
 await page.goto('https://shayan-kazeyami.github.io/aerial-watch/?poll-qa='+name,wait_until='domcontentloaded',timeout=120000)
 await page.wait_for_function("document.querySelector('#watch-viewer').contentDocument?.body?.dataset.failed==='true'",timeout=180000)
 f=page.frames[1]
 await page.wait_for_timeout(1000)
 first=await page.evaluate('JSON.parse(JSON.stringify(pollProbe))')
 await page.wait_for_timeout(1500)
 second=await page.evaluate('JSON.parse(JSON.stringify(pollProbe))')
 assert await page.locator('#watch-loading').is_hidden()
 if name=='candidate':assert first['active']==second['active']==[] and first['ticks']==second['ticks']
 else:assert len(second['active'])==1 and second['ticks']>first['ticks']
 await capture(O/(name+'-failed.png'))
 # Actual supported fatal-failure recovery is reload, not Retry detail.
 await f.locator('#atelier-retry').tap()
 await page.wait_for_function("document.querySelector('#watch-viewer').contentDocument?.body?.dataset.ready==='true'",timeout=360000)
 f=page.frames[1]
 await page.wait_for_timeout(1500)
 ready=await page.evaluate('JSON.parse(JSON.stringify(pollProbe))')
 assert ready['active']==[]
 assert await page.locator('#watch-loading').is_hidden()
 R['arms'][name]={'failureFirst':first,'failureSecond':second,'ready':ready,'recoveryReady':True,'rootReloadReady':False};(O/'report.json').write_text(json.dumps(R,indent=2))
 await capture(O/(name+'-recovered.png'))
 # Repeat fatal flow through explicit root reload, then real iframe reload recovery.
 await page.reload(wait_until='domcontentloaded')
 await page.wait_for_function("document.querySelector('#watch-viewer').contentDocument?.body?.dataset.ready==='true'",timeout=360000)
 await page.wait_for_timeout(1000)
 assert await page.evaluate('pollProbe.active.length')==0
 R['arms'][name]={'injectedFailures':failures,'failureFirst':first,'failureSecond':second,'ready':ready,'recoveryReady':True,'rootReloadReady':True,'pageerrors':errors,'wrapperSHA256':hashlib.sha256(src.encode()).hexdigest()}
 await ctx.close()
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for name in ['original','candidate']:await arm(browser,name)
   R['pass']=True
  except Exception as e:R['pass']=False;R['failure']=repr(e);raise
  finally:
   (O/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True);await browser.close()
asyncio.run(main())
