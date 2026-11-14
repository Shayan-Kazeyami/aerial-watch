"""Isolated full e79 viewer; intercept only two guarded source modules, no deploy."""
import asyncio,json,pathlib,hashlib,threading,http.server,functools,base64
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).parent;O=P/'ci-evidence';O.mkdir(exist_ok=True);RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6';B=pathlib.Path('preview-b/releases')/RID
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
controller=(B/'assembly-explode.js').read_text();viewer=(B/'assembly-review.js').read_text();needle='    setAmount(value,{instant=false}={}){';assert controller.count(needle)==1
setter="""    setDuration(value){
      if(!Number.isFinite(value)||value<0)throw new TypeError('Invalid explosion duration.');
      if(disposed||value===duration)return api;
      duration=value;
      if(duration===0){amount=from=target;elapsed=0;render();}
      else {from=amount;elapsed=amount===target?duration:0;}
      return api;
    },
"""
candidate=controller.replace(needle,setter+needle);marker='  controls.enableDamping = !event.matches;';assert viewer.count(marker)==1
candidate_viewer=viewer.replace(marker,marker+'\n  explosion?.setDuration(event.matches?0:.55);')
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory='.'));threading.Thread(target=server.serve_forever,daemon=True).start();port=server.server_port
R={'scope':'Real full e79 viewer with Playwright media preference toggles; two source-response substitutions only in candidate arm; no release/main edits','source':{'controller':sha(controller),'viewer':sha(viewer)},'candidate':{'controller':sha(candidate),'viewer':sha(candidate_viewer)},'arms':{}}
async def arm(browser,name,initial):
 ctx=await browser.new_context(viewport={'width':430,'height':932},is_mobile=True,has_touch=True,reduced_motion=initial);page=await ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));executed={}
 async def route(r):
  key='controller' if r.request.url.split('?')[0].endswith('/assembly-explode.js') else 'viewer';body=(candidate if key=='controller' else candidate_viewer) if name=='proposal' else (controller if key=='controller' else viewer);executed[key]=sha(body);await r.fulfill(status=200,content_type='text/javascript',body=body)
 await page.route('**/assembly-explode.js*',route);await page.route('**/assembly-review.js*',route)
 await page.goto(f'http://127.0.0.1:{port}/preview-b/releases/{RID}/atelier-preview.html?atelier=1',wait_until='domcontentloaded',timeout=120000)
 await page.wait_for_function('document.body.dataset.ready==="true"&&window.assemblyInspect?.().presentation.interactive&&document.getElementById("stage").dataset.cameraReady==="true"',timeout=300000)
 # Event observer is registered after the actual viewer callback; snapshots are post-policy, pre-next-frame.
 await page.evaluate("""()=>{window.mediaSamples=[];matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change',e=>mediaSamples.push({matches:e.matches,explosion:assemblyInspect().explosion}));window.clickSamples=[];document.addEventListener('click',e=>{if(e.target.closest('[data-mode=explode],#atelier-reassemble,#atelier-explode-full'))queueMicrotask(()=>clickSamples.push(assemblyInspect().explosion));});}""")
 if initial=='reduce':
  await page.locator('[data-mode=explode]').click();assert (await page.evaluate('assemblyInspect().explosion.amount'))==1
  await page.emulate_media(reduced_motion='no-preference');await page.wait_for_function('mediaSamples.length===1');await page.locator('#atelier-reassemble').click();await page.wait_for_function('clickSamples.length===2');click=await page.evaluate('clickSamples.at(-1)');assert click['animating']==(name=='proposal'),click
  await page.emulate_media(reduced_motion='reduce');await page.wait_for_function('mediaSamples.length===2');end=await page.evaluate('mediaSamples.at(-1)');assert end['explosion']['amount']==0 and not end['explosion']['animating']
 else:
  await page.locator('[data-mode=explode]').click();await page.wait_for_function('clickSamples.length===1');click=await page.evaluate('clickSamples[0]');assert click['animating'],click
  await page.emulate_media(reduced_motion='reduce');await page.wait_for_function('mediaSamples.length===1');end=await page.evaluate('mediaSamples.at(-1)')
  if name=='proposal':assert end['explosion']['amount']==1 and not end['explosion']['animating'],end
  # Baseline may settle before OS event on slow GPU; record without manufacturing a failure.
  (O/f'{name}-{initial}-midphase.json').write_text(json.dumps({'media':end,'actual':await page.evaluate('assemblyInspect()')},indent=2))
  if name=='proposal':await page.wait_for_function('!assemblyInspect().explosion.animating',timeout=30000)
  await page.locator('#atelier-reassemble').click();await page.wait_for_function('clickSamples.length===2');nextclick=await page.evaluate('clickSamples.at(-1)');assert nextclick['target']==0,nextclick
  if name=='proposal':assert nextclick['amount']==0 and not nextclick['animating'],nextclick
 result={'initial_preference':initial,'click_samples':await page.evaluate('clickSamples'),'media_samples':await page.evaluate('mediaSamples'),'executed_sha256':executed,'errors':errors,'final':await page.evaluate('assemblyInspect()')};assert not errors;assert executed==R['candidate' if name=='proposal' else 'source'];(O/f'{name}-{initial}.json').write_text(json.dumps(result,indent=2));cdp=await ctx.new_cdp_session(page)
 try:
  shot=await asyncio.wait_for(cdp.send('Page.captureScreenshot',{'format':'png','fromSurface':True,'captureBeyondViewport':False}),90);(O/f'{name}-{initial}.png').write_bytes(base64.b64decode(shot['data']));result['screenshot']='PASS'
 except Exception as error:result['screenshot']='UNAVAILABLE '+str(error)
 await cdp.detach();await ctx.close();return result
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']);R['browser']=b.version
  try:
   for name in ['baseline','proposal']:
    R['arms'][name]=[]
    for pref in ['no-preference','reduce']:
     R['arms'][name].append(await arm(b,name,pref));(O/'REPORT.json').write_text(json.dumps(R,indent=2))
   R['result']='PASS'
  finally:
   (O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close();server.shutdown()
asyncio.run(main())
