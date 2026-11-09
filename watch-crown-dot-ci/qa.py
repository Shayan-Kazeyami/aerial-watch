import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('watch-crown-dot-output');C=pathlib.Path(json.loads((O/'build.json').read_text())['releasePath']);C=C.relative_to(pathlib.Path.cwd()) if C.is_absolute() else C
HOOK="""
window.__polishQA={freeze(){cancelAnimationFrame(animationFrame)},snapshotCanvas(){cancelAnimationFrame(animationFrame);composer.render();const c=renderer.domElement,r=c.getBoundingClientRect(),image=new Image();image.id=c.id;image.src=c.toDataURL('image/png');image.style.cssText=`position:fixed;left:${r.left}px;top:${r.top}px;width:${r.width}px;height:${r.height}px;max-width:none;max-height:none;object-fit:fill;mask-image:none;transform:none;z-index:0`;c.replaceWith(image);return image.decode()},pause(){stopTour();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();dirty=true},focus(){view('crown')},redraw(){dirty=true},state(){return {moving:!!cameraTween,crown:crownInteraction.snapshot(),hotspot:crownHotspot.snapshot(),viewport:assemblyInspect().viewport,revision:assemblyInspect().sourceRevision,camera:camera.position.toArray()}}};
window.__polishCost={calls:0,ms:0};const oldUpdate=crownHotspot.update;crownHotspot.update=()=>{const t=performance.now();try{return oldUpdate()}finally{__polishCost.calls++;__polishCost.ms+=performance.now()-t}};
"""
(C/'qa-review.js').write_text((C/'assembly-review.js').read_text().replace('composer.render();','composer.render();window.__polishFrames=(window.__polishFrames||0)+1;')+'\n'+HOOK);(C/'qa-atelier.js').write_text((C/'atelier-preview.js').read_text().replace('./assembly-review.js?v=atelier-local-1','./qa-review.js'));(C/'qa-atelier.html').write_text((C/'atelier-preview.html').read_text().replace('atelier-preview.js','qa-atelier.js'))
async def main():
 report={'checks':[],'errors':[],'states':[],'scope':'Actual candidate in Chromium SwiftShader; not hardware FPS. Diagnostic screenshot freezes CSS motion and replaces canvas with exact synchronous render PNG to avoid software GPU compositor capture deadlock.'}
 async with async_playwright() as p:
  browser=None
  async def fresh(mobile=False,hook=True):
   nonlocal browser
   if browser:await browser.close()
   browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=await browser.new_context(viewport={'width':430 if mobile else 900,'height':850 if mobile else 740},device_scale_factor=1,is_mobile=mobile,has_touch=mobile);page=await ctx.new_page();page.set_default_timeout(45000);page.on('pageerror',lambda e:report['errors'].append(str(e)));await page.goto(f'http://127.0.0.1:8765/{C}/{"qa-atelier" if hook else "atelier-preview"}.html?quality=efficient',wait_until='domcontentloaded');await page.wait_for_function('window.assemblyInspect && assemblyInspect().presentation.interactive',timeout=180000)
   if hook:await page.evaluate('__polishQA.pause();__polishQA.focus()');await page.wait_for_function('!__polishQA.state().moving');await page.wait_for_timeout(500)
   return page,ctx
  def record(name,data=None):report['checks'].append({'name':name,'data':data});print(name,json.dumps(data),flush=True);(O/'polish-report.json').write_text(json.dumps(report,indent=2))
  async def shot(page,name):
   await page.evaluate('__polishQA.pause()');f=await page.evaluate('window.__polishFrames||0');await page.evaluate('__polishQA.redraw()');await page.wait_for_function('(f)=>(window.__polishFrames||0)>f',arg=f,timeout=90000);await page.evaluate('__polishQA.snapshotCanvas()');await page.wait_for_timeout(1000);await page.screenshot(path=str(O/name),timeout=30000,animations='disabled')
  try:
   page,ctx=await fresh(True);dot=page.locator('.crown-hotspot');assert await dot.get_attribute('data-near')=='true';r=await dot.bounding_box();x=r['x']+22;y=r['y']+22;await page.touchscreen.tap(x,y);await page.wait_for_function('__polishQA.state().crown.pulled');await page.wait_for_timeout(1500);r=await dot.bounding_box();x=r['x']+22;y=r['y']+22;session=await ctx.new_cdp_session(page);await session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});await page.wait_for_function("document.querySelector('.crown-hotspot').dataset.held==='true'",timeout=10000);assert await dot.get_attribute('data-held')=='true'
   for dy in [6,12,18]:await session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-dy}]})
   await session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert (await page.evaluate('__polishQA.state().crown'))['pulled'];record('touch visible, tap pulls, hold/drag turns');record('projected update CPU cost',await page.evaluate('__polishCost'));await page.wait_for_function("!!document.querySelector('.crown-halo polygon')",timeout=10000);await page.add_style_tag(content='.crown-halo{animation:none!important;opacity:.45!important}');await shot(page,'mobile-outline-dot.png');await page.emulate_media(reduced_motion='reduce');assert await page.locator('.crown-hotspot-dot').evaluate('(e)=>getComputedStyle(e).animationName')=='none';record('reduced motion disables animation');assert not report['errors'],report['errors'];report['passed']=True
  except Exception as e:report['passed']=False;report['failure']=repr(e);raise
  finally:
   (O/'polish-report.json').write_text(json.dumps(report,indent=2));
   try:await asyncio.wait_for(browser.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())
