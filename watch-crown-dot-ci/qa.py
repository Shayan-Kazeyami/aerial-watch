import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('watch-crown-dot-output');C=pathlib.Path(json.loads((O/'build.json').read_text())['releasePath']);C=C.relative_to(pathlib.Path.cwd()) if C.is_absolute() else C
HOOK="""
window.__polishQA={pause(){stopTour();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();dirty=true},focus(){view('crown')},redraw(){dirty=true},state(){return {moving:!!cameraTween,crown:crownInteraction.snapshot(),hotspot:crownHotspot.snapshot(),viewport:assemblyInspect().viewport,revision:assemblyInspect().sourceRevision,camera:camera.position.toArray()}}};
window.__polishCost={calls:0,ms:0};const oldUpdate=crownHotspot.update;crownHotspot.update=()=>{const t=performance.now();try{return oldUpdate()}finally{__polishCost.calls++;__polishCost.ms+=performance.now()-t}};
"""
(C/'qa-review.js').write_text((C/'assembly-review.js').read_text().replace('composer.render();','composer.render();window.__polishFrames=(window.__polishFrames||0)+1;')+'\n'+HOOK);(C/'qa-atelier.js').write_text((C/'atelier-preview.js').read_text().replace('./assembly-review.js?v=atelier-local-1','./qa-review.js'));(C/'qa-atelier.html').write_text((C/'atelier-preview.html').read_text().replace('atelier-preview.js','qa-atelier.js'))
async def main():
 report={'checks':[],'errors':[],'states':[],'scope':'Actual candidate in Chromium SwiftShader; not hardware FPS. Diagnostic screenshots freeze CSS motion to show affordance.'}
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
   await page.evaluate('__polishQA.pause()');f=await page.evaluate('window.__polishFrames||0');await page.evaluate('__polishQA.redraw()');await page.wait_for_function('(f)=>(window.__polishFrames||0)>f',arg=f,timeout=90000);await page.screenshot(path=str(O/name),timeout=90000)
  try:
   page,ctx=await fresh(hook=False);record('unmodified sealed startup ready',await page.evaluate('assemblyInspect().presentation'))
   page,ctx=await fresh();dot=page.locator('.crown-hotspot');r=await dot.bounding_box();x=r['x']+22;y=r['y']+22;await page.mouse.move(1,1);await page.wait_for_timeout(250);assert await dot.evaluate('(e)=>getComputedStyle(e).opacity')=='0';await page.mouse.move(x+55,y);await page.wait_for_timeout(250);assert await dot.get_attribute('data-near')=='true';record('far hidden, near reveal')
   await page.mouse.move(x,y);assert await page.locator('.crown-hotspot-track').evaluate('(e)=>getComputedStyle(e).opacity')=='0';assert await page.locator('.crown-hotspot-dot').evaluate('(e)=>getComputedStyle(e).animationName')=='crown-press';record('hover press/direction cue without scroll track')
   await page.mouse.down();await page.wait_for_timeout(400);assert await dot.get_attribute('data-held')=='true';assert await page.locator('.crown-hotspot-track').evaluate('(e)=>getComputedStyle(e).opacity')=='1';await page.mouse.move(x,y-18,steps=3);await page.mouse.up();assert await dot.get_attribute('data-held') is None;assert abs((await page.evaluate('__polishQA.state().crown.degrees')))>1;record('hold reveals track; drag rotates; release clears')
   await dot.click();await page.wait_for_function('__polishQA.state().crown.pulled');await dot.focus();await page.keyboard.press('ArrowUp');await page.keyboard.press('Escape');record('click pull, keyboard turn, escape')
   await page.mouse.move(1,1);await page.wait_for_function("document.querySelector('.crown-halo').dataset.lit==='true' && !!document.querySelector('.crown-halo polygon')",timeout=12000);points=await page.locator('.crown-halo polygon').get_attribute('points');assert len(points)>20;record('startup/periodic projected outline',points)
   await page.add_style_tag(content='.crown-halo[data-lit=true]{animation:none!important;opacity:.5!important}.crown-hotspot-dot,.crown-hotspot-arrows{animation-play-state:paused!important}');await shot(page,'desktop-outline.png')
   await page.mouse.move(x,y);await shot(page,'desktop-hover.png');report['states'].append(await page.evaluate('__polishQA.state()'));record('projected update CPU cost',await page.evaluate('__polishCost'))
   await page.emulate_media(reduced_motion='reduce');assert await page.locator('.crown-hotspot-dot').evaluate('(e)=>getComputedStyle(e).animationName')=='none';record('reduced motion disables cue animation')
   page,ctx=await fresh(True);dot=page.locator('.crown-hotspot');assert await dot.get_attribute('data-near')=='true';r=await dot.bounding_box();x=r['x']+22;y=r['y']+22;await page.touchscreen.tap(x,y);await page.wait_for_function('__polishQA.state().crown.pulled');session=await ctx.new_cdp_session(page);await session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});await page.wait_for_timeout(400);assert await dot.get_attribute('data-held')=='true'
   for dy in [6,12,18]:await session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-dy}]})
   await session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert (await page.evaluate('__polishQA.state().crown'))['pulled'];record('touch visible, tap pulls, hold/drag turns');await shot(page,'mobile-dot.png');assert not report['errors'],report['errors'];report['passed']=True
  except Exception as e:report['passed']=False;report['failure']=repr(e);raise
  finally:(O/'polish-report.json').write_text(json.dumps(report,indent=2));await browser.close()
asyncio.run(main())
