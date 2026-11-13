import asyncio,json,pathlib,hashlib,base64,os,traceback
from playwright.async_api import async_playwright
from PIL import Image
ARM=os.environ['QA_RELEASE'];RID={'e79':'e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6','f0d3':'f0d3fb50ee863df4f83ee20045d6a7a0b35c0b47594884e76683a588642e0179'}[ARM];PORT=8766 if ARM=='e79' else 8765
O=pathlib.Path('reset-framing-diagnostic/evidence-'+ARM);O.mkdir(parents=True,exist_ok=True);R={'arm':ARM,'release':RID,'scope':'paired observational actual mobile Reset framing diagnosis, not product acceptance','errors':[],'steps':[]}
async def run():
 async with async_playwright()as pw:
  b=await pw.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']);p=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=1,is_mobile=True,has_touch=True);p.set_default_timeout(180000)
  source=pathlib.Path(('preview-b/releases/'if ARM=='e79'else'coordinated-release-proposal/staging/preview-b/releases/')+RID+'/assembly-review.js').read_bytes();assert hashlib.sha256(source).hexdigest()=='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee'
  if os.environ.get('QA_FIX')=='1':
   import runpy
   source=runpy.run_path('mobile-reset-fit-fix/patch.py')['patched'](source);R['isolatedFixedModuleSHA256']=hashlib.sha256(source).hexdigest()
  wrapped=source+b'\n'+pathlib.Path('reset-framing-diagnostic/probe.js').read_bytes();R['wrapperSHA256']=hashlib.sha256(wrapped).hexdigest()
  async def alias(q):await q.fulfill(status=200,content_type='text/javascript',body=wrapped)
  async def boot(q):
   x=await q.fetch();text=await x.text();needle="import('./assembly-review.js?v=atelier-local-1')";assert text.count(needle)==1;await q.fulfill(response=x,body=text.replace(needle,"import('./assembly-reset-framing-diagnostic-private.js')"))
  p.on('pageerror',lambda e:R['errors'].append(str(e)));await p.route('**/atelier-preview.js',boot);await p.route('**/assembly-reset-framing-diagnostic-private.js',alias)
  try:
   await p.goto(f'http://127.0.0.1:{PORT}/?quality=efficient',wait_until='domcontentloaded');await p.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000);f=next(f for f in p.frames if RID in f.url);await f.wait_for_function('window.__resetDiag&&document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000);await f.wait_for_function('(()=>{const x=assemblyInspect().leatherCraft?.candidate;return !x||x.detail?.ready})()',timeout=300000);await f.evaluate('__resetDiag.pause()')
   async def settle():await f.wait_for_function('(()=>{const s=__resetDiag.snapshot();return !s.tween&&!s.explosion.animating&&!s.loading&&!s.failed})()');await f.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
   async def record(name,image=False):
    await settle();s=await f.evaluate('__resetDiag.snapshot()');R['steps'].append({'name':name,**s});print(ARM,name,s['camera'],flush=True)
    if image:(O/(name+'.png')).write_bytes(base64.b64decode((await f.evaluate('__resetDiag.capture()')).split(',')[1]))
    (O/'report.json').write_text(json.dumps(R,indent=2))
   async def tap(mode):
    x=f.locator(f'.task-dock [data-mode="{mode}"]:visible').first
    if not await x.count():x=f.locator(f'[data-mode="{mode}"]:visible').first
    await x.tap();await settle()
   await f.locator('#home').tap();await record('initial-reset',True)
   await tap('inside');await f.locator('#close').tap();await record('inside-close')
   await tap('explode');await record('full-exploded')
   box=await f.locator('#atelier-explosion').bounding_box();y=box['y']+box['height']/2;cdp=await p.context.new_cdp_session(p);await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':box['x']+box['width']*.2,'y':y}]})
   for v in [.85,.15,.75,.37]:await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':box['x']+box['width']*v,'y':y}]});await f.evaluate('()=>new Promise(r=>requestAnimationFrame(r))')
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});await f.locator('#close').tap();await record('scrub-close')
   for mode in ['capture','settings']:await tap(mode);await f.locator('#close').tap();await record(mode+'-close')
   for i in range(1,4):await f.locator('#home').tap();await record('post-reset-'+str(i),True)
   if os.environ.get('QA_FIX')=='1':
    base=R['steps'][0];initial=Image.open(O/'initial-reset.png').tobytes()
    for s in R['steps']:
     if s['name'].startswith('post-reset'):
      assert max(abs(a-b)for a,b in zip(base['camera']['p'],s['camera']['p']))<1e-7
      assert Image.open(O/(s['name']+'.png')).tobytes()==initial,s['name']+' image drift'
    R['isolatedFixedResetVerified']=True
   assert not R['errors'];R['diagnosticExecuted']=True;R['productAcceptance']=False
  except Exception as e:R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:(O/'report.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(run())
