import asyncio,json,pathlib,hashlib,base64,traceback,os
from playwright.async_api import async_playwright
DEVICE=os.environ.get('QA_DEVICE','mobile');MOBILE=DEVICE=='mobile'
O=pathlib.Path('mobile-lifecycle-f0d3/evidence-'+DEVICE);O.mkdir(parents=True,exist_ok=True)
RID='f0d3fb50ee863df4f83ee20045d6a7a0b35c0b47594884e76683a588642e0179'
R={'scope':'exact staged f0d3 authentic tap/mouse lifecycle and reload; not physical phone FPS or export acceptance','errors':[],'navigation':[],'requests':[],'viewports':[]}
INIT="""(()=>{window.__lifecycleTrace={writes:[],contexts:[]};for(const k of ['width','height']){const d=Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype,k);Object.defineProperty(HTMLCanvasElement.prototype,k,{...d,set(v){window.__lifecycleTrace.writes.push({id:this.id,k,value:v,t:performance.now()});return d.set.call(this,v)}})}for(const type of ['webglcontextlost','webglcontextrestored'])document.addEventListener(type,e=>window.__lifecycleTrace.contexts.push({type,t:performance.now()}),true)})();"""
async def run():
 async with async_playwright()as pw:
  b=await pw.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=await b.new_context(viewport=({'width':430,'height':932}if MOBILE else {'width':1440,'height':900}),device_scale_factor=1,is_mobile=MOBILE,has_touch=MOBILE);await ctx.add_init_script(INIT);p=await ctx.new_page();p.set_default_timeout(120000)
  p.on('pageerror',lambda e:R['errors'].append(str(e)));p.on('request',lambda q:R['requests'].append({'url':q.url,'type':q.resource_type}));p.on('framenavigated',lambda f:R['navigation'].append(f.url))
  source=pathlib.Path('coordinated-release-proposal/staging/preview-b/releases',RID,'assembly-review.js').read_bytes();assert hashlib.sha256(source).hexdigest()=='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee';R['baselineModuleSHA256']=hashlib.sha256(source).hexdigest()
  if os.environ.get('QA_FIX')=='1':
   import runpy
   source=runpy.run_path('mobile-reset-fit-fix/patch.py')['patched'](source);R['isolatedFixedModuleSHA256']=hashlib.sha256(source).hexdigest()
  wrapped=source+b'\n'+pathlib.Path('mobile-lifecycle-f0d3/probe.js').read_bytes();R['expectedQAWrapperSHA256']=hashlib.sha256(wrapped).hexdigest()
  async def module(route):assert RID in route.request.url;await route.fulfill(status=200,content_type='text/javascript',body=wrapped)
  async def atelier(route):
   response=await route.fetch();body=await response.text();needle="import('./assembly-review.js?v=atelier-local-1')";assert body.count(needle)==1;await route.fulfill(response=response,body=body.replace(needle,"import('./assembly-review-mobile-lifecycle-private-qa.js')"))
  async def receipt(response):
   if 'assembly-review-mobile-lifecycle-private-qa.js'in response.url:R['executedQAWrapperSHA256']=hashlib.sha256(await response.body()).hexdigest()
  p.on('response',receipt);await p.route('**/atelier-preview.js',atelier);await p.route('**/assembly-review-mobile-lifecycle-private-qa.js',module)
  try:
   await p.goto('http://127.0.0.1:8765/?quality=efficient',wait_until='domcontentloaded',timeout=120000)
   await p.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000);f=next(f for f in p.frames if RID in f.url);R['frameURL']=f.url
   await f.wait_for_function('window.__mobileLifecycle && document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000)
   await f.wait_for_function('(()=>{const x=assemblyInspect().leatherCraft?.candidate;return !x||x.detail?.ready})()',timeout=300000)
   await f.evaluate('__mobileLifecycle.pause()')
   async def settle():
    await f.wait_for_function('(()=>{const s=__mobileLifecycle.snapshot();return !s.cameraTween&&!s.explosion.animating&&!s.loading&&!s.failed})()',timeout=180000);await f.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
   async def snap():return await f.evaluate('__mobileLifecycle.snapshot()')
   async def action(el):
    if MOBILE:await el.tap()
    else:await el.click()
   async def tap(mode):
    el=f.locator(f'.task-dock [data-mode="{mode}"]:visible').first
    if not await el.count():el=f.locator(f'[data-mode="{mode}"]:visible').first
    assert await el.count(),mode+' has no authentic visible control'
    await action(el);await settle()
   nav_start=len(R['navigation']);req_start=len(R['requests'])
   profiles=([('portrait',{'width':430,'height':932},3),('landscape',{'width':932,'height':430},1)]if MOBILE else [('desktop',{'width':1440,'height':900},3),('desktop-narrow',{'width':1024,'height':768},1)])
   for label,viewport,repeats in profiles:
    await p.set_viewport_size(viewport);await action(f.locator('#home'));await settle();base=await snap();entry={'label':label,'viewport':viewport,'baseline':base,'steps':[]};R['viewports'].append(entry);write_start=len(base['qa']['writes'])
    async def record(name,expected_camera=None):
     s=await snap();entry['steps'].append({'name':name,'state':s});assert s['timeOrigin']==base['timeOrigin'],name+' restarted document';assert s['buffer']==base['buffer'],name+' resized drawing buffer';assert s['canvasCSS']==base['canvasCSS'] and s['stage']==base['stage'],name+' changed viewer dimensions';assert not s['qa']['contexts'] and not s['context'],name+' lost graphics context'
     if expected_camera is not None:
      diffs=[abs(a-b) for k in ['p','q','target']for a,b in zip(s['camera'][k],expected_camera[k])]+[abs(s['camera']['zoom']-expected_camera['zoom'])];assert max(diffs)<=1e-7,(name,'camera drift',diffs)
     (O/'report.json').write_text(json.dumps(R,indent=2));print(label,name,flush=True)
    for i in range(repeats):
     await tap('inside');await record(f'{i}-inside');await action(f.locator('#close'));await settle();await record(f'{i}-inside-close')
     await tap('explode');await record(f'{i}-explode')
     slider=f.locator('#atelier-explosion');box=await slider.bounding_box();y=box['y']+box['height']/2
     cdp=await ctx.new_cdp_session(p)if MOBILE else None;values=[]
     x=box['x']+box['width']*.2
     if MOBILE:await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
     else:await p.mouse.move(x,y);await p.mouse.down()
     for fraction in [.85,.15,.75,.37]:
      x=box['x']+box['width']*fraction
      if MOBILE:await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y}]})
      else:await p.mouse.move(x,y,steps=5)
      await f.evaluate('()=>new Promise(r=>requestAnimationFrame(r))');value=float(await slider.input_value());state=await snap();assert abs(state['explosion']['amount']-value/100)<.001,('native slider follow',value,state['explosion']);values.append(value)
     if MOBILE:await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
     else:await p.mouse.up()
     assert len(set(values))>=3,('native slider did not track drag',values);entry.setdefault('nativeSliderDrags',[]).append(values)
     await action(f.locator('#close'));await settle();await record(f'{i}-scrub-close')
     for mode in ['capture','settings']:
      old=(await snap())['camera'];await tap(mode);await record(f'{i}-{mode}',old);await action(f.locator('#close'));await settle();await record(f'{i}-{mode}-close',old)
     await action(f.locator('#home'));await settle();await record(f'{i}-reset',base['camera'])
    final=await snap();writes=final['qa']['writes'][write_start:];entry['canvasWritesAfterViewportBaseline']=[w for w in writes if w['id']=='assembly-canvas'];assert not entry['canvasWritesAfterViewportBaseline'],(label,entry['canvasWritesAfterViewportBaseline'])
    frame=await f.evaluate('__mobileLifecycle.capture()');(O/f'{label}-actual-canvas.png').write_bytes(base64.b64decode(frame.pop('png').split(',')[1]));entry['finalRenderedFrame']=frame
   if MOBILE:
    # Restore portrait and exercise real touch cancellation on the projected crown control.
    await p.set_viewport_size({'width':430,'height':932});await action(f.locator('#home'));await settle();await tap('time');dot=f.locator('.crown-hotspot');await dot.wait_for(state='visible');box=await dot.bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2;cdp=await ctx.new_cdp_session(p)
    for kind,points in [('touchStart',[{'x':x,'y':y}]),('touchMove',[{'x':x,'y':y-22}])]:await cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':points})
    await f.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');held=await snap();assert held['hotspot']['dragging']
    await cdp.send('Input.dispatchTouchEvent',{'type':'touchCancel','touchPoints':[]});await f.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');cancel=await snap();await f.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');after=await snap();assert not after['hotspot']['dragging'] and after['crown']['degrees']==cancel['crown']['degrees'];R['crownCancellation']={'entry':'authentic Time tool focuses crown before projected-dot gesture','held':held,'cancel':cancel,'after':after};await action(f.locator('#close'));await action(f.locator('#home'));await settle()
   R['newNavigation']=R['navigation'][nav_start:];assert not R['newNavigation']
   before={q['url'] for q in R['requests'][:req_start]};R['repeatedAssets']=[q for q in R['requests'][req_start:]if q['url']in before and any(q['url'].split('?')[0].endswith(s)for s in ['.glb','.ktx2','.gz','.bin'])];assert not R['repeatedAssets'],R['repeatedAssets'];assert not R['errors'];assert R['executedQAWrapperSHA256']==R['expectedQAWrapperSHA256']
   # One explicit whole-page reload is intentional; subsequent mode changes must not reload again.
   old=await snap();await p.reload(wait_until='domcontentloaded');await p.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000);f=next(q for q in p.frames if RID in q.url);await f.wait_for_function('window.__mobileLifecycle',timeout=300000);await f.evaluate('__mobileLifecycle.pause()');await action(f.locator('#home'));await settle();fresh=await snap();assert fresh['timeOrigin']!=old['timeOrigin'];assert await p.locator('#watch-viewer').count()==1
   nav_after_reload=len(R['navigation']);await tap('explode');await action(f.locator('#close'));await tap('capture');await action(f.locator('#close'));await action(f.locator('#home'));await settle();restored=await snap();assert restored['timeOrigin']==fresh['timeOrigin'] and restored['buffer']==fresh['buffer'] and not restored['qa']['contexts'];assert len(R['navigation'])==nav_after_reload
   R['explicitReload']={'before':old,'after':fresh,'postInteraction':restored};assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:(O/'report.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(run())
