import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('watch-flow-output');C=pathlib.Path(json.loads((O/'build.json').read_text())['releasePath']);C=C.relative_to(pathlib.Path.cwd()) if C.is_absolute() else C
BASE=pathlib.Path('preview-b/releases/922fcc6539853bd0c0306ef90315f1dd65708110e367657e96d8f5928b74af4d')
HOOK="""
window.__flowQA={pause(){stopTour();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();dirty=true},state(){return {moving:!!cameraTween,crown:crownInteraction.snapshot(),camera:camera.position.toArray(),target:controls.target.toArray(),view:currentView,revision:assemblyInspect().sourceRevision,explosion:explosion?.snapshot?.()}},redraw(){dirty=true},async shot(){cancelAnimationFrame(animationFrame);composer.render();const c=renderer.domElement,r=c.getBoundingClientRect(),im=new Image();im.id=c.id;im.src=c.toDataURL('image/png');im.style.cssText=`position:fixed;left:${r.left}px;top:${r.top}px;width:${r.width}px;height:${r.height}px;max-width:none;max-height:none;object-fit:fill;mask-image:none;transform:none;z-index:0`;c.replaceWith(im);await im.decode();}};
"""
for root in [BASE,C]:
 (root/'qa-review.js').write_text((root/'assembly-review.js').read_text().replace('composer.render();','composer.render();window.__flowFrames=(window.__flowFrames||0)+1;')+'\n'+HOOK)
 (root/'qa-atelier.js').write_text((root/'atelier-preview.js').read_text().replace('./assembly-review.js?v=atelier-local-1','./qa-review.js'))
 (root/'qa-atelier.html').write_text((root/'atelier-preview.html').read_text().replace('atelier-preview.js','qa-atelier.js'))
async def main():
 report={'checks':[],'errors':[],'scope':'Actual candidate and baseline, Chromium SwiftShader. Software rendering; no hardware FPS claim. Screenshots use the exact synchronous canvas render replaced with a static PNG after interactive checks.'}
 async with async_playwright() as p:
  browser=None
  async def fresh(root=C,mobile=False,hook=True,quality='efficient'):
   nonlocal browser
   if browser:await browser.close()
   browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=await browser.new_context(viewport={'width':430 if mobile else 1180,'height':850 if mobile else 820},device_scale_factor=1,is_mobile=mobile,has_touch=mobile);page=await ctx.new_page();page.set_default_timeout(45000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
   await page.goto(f'http://127.0.0.1:8765/{root}/{"qa-atelier" if hook else "atelier-preview"}.html?quality={quality}',wait_until='domcontentloaded');await page.wait_for_function('window.assemblyInspect && assemblyInspect().presentation.interactive',timeout=240000)
   if hook:await page.evaluate('__flowQA.pause()');await settle(page)
   return page
  async def settle(page):await page.wait_for_function('!__flowQA.state().moving',timeout=120000)
  def record(name,data=None):report['checks'].append({'name':name,'data':data});print(name,json.dumps(data),flush=True);(O/'report.json').write_text(json.dumps(report,indent=2))
  async def shot(page,name):
   f=await page.evaluate('window.__flowFrames||0');await page.evaluate('__flowQA.redraw()');await page.wait_for_function('(f)=>(window.__flowFrames||0)>f',arg=f,timeout=90000);await page.evaluate('__flowQA.shot()');await page.screenshot(path=str(O/name),timeout=30000,animations='disabled')
  async def pose(page):return await page.evaluate('({camera:assemblyInspect().camera,target:assemblyInspect().target,view:assemblyInspect().view,interior:assemblyInspect().interiorView})')
  async def mode(page,name):await page.locator(f'.task-dock [data-mode="{name}"]').click();await settle(page)
  async def close(page):await page.locator('#close').click()
  try:
   page=await fresh(BASE);await shot(page,'desktop-before.png');record('baseline actual render captured')
   page=await fresh();assert await page.locator('.inspection-tools').count()==0;record('engineering toolbar absent from the main object view')
   await mode(page,'inside');before=await pose(page);await page.locator('.quality').click();assert await page.locator('.task-dock [data-mode=inside]').get_attribute('aria-pressed')=='true';assert await pose(page)==before;await page.keyboard.press('Escape');assert await page.locator('#context').is_hidden();assert await page.locator('.quality').get_attribute('aria-pressed')=='false';assert await pose(page)==before
   await mode(page,'inside');assert await pose(page)==before;await mode(page,'inside');assert await page.locator('#context').is_hidden();assert await pose(page)==before;record('Inside survives Quality, Escape and repeated dock open/close without camera changes')
   await mode(page,'inside');await page.locator('#context [data-mode=components]').click();await page.locator('#atelier-search').fill('Balance');await page.locator('#atelier-component-list button').first.click();assert await page.locator('[data-return-selection]').is_visible();await page.locator('[data-return-selection]').focus();await page.keyboard.press('Enter');assert await page.locator('#close').evaluate('(e)=>e===document.activeElement');assert await page.locator('#atelier-search').is_visible();assert await page.locator('.task-dock [data-mode=inside]').get_attribute('aria-pressed')=='true';record('component inspection returns to the originating component finder in Inside')
   await mode(page,'time');await page.locator('#context [data-proxy=crown-pull]').click();await page.wait_for_function('__flowQA.state().crown.pulled');before=await pose(page);await mode(page,'capture');assert await page.locator('.task-dock [data-mode=time]').get_attribute('aria-pressed')=='true';await close(page);assert await page.evaluate('__flowQA.state().crown.pulled');assert await pose(page)==before;record('Capture dismissal preserves pulled crown and time-setting view')
   await mode(page,'explode');await page.locator('#atelier-explosion').fill('45');await page.wait_for_timeout(1500);before=await pose(page);await page.locator('.atelier-more').click();await page.locator('[data-inspection=wireframe]').click();await page.wait_for_function('assemblyInspect().inspectionDisplay.wireframe');assert '1' in await page.locator('.atelier-more').inner_text();await close(page);assert await page.locator('.task-dock [data-mode=explode]').get_attribute('aria-pressed')=='true';await page.locator('.atelier-more').click();assert await page.locator('[data-inspection=wireframe]').get_attribute('aria-pressed')=='true';await page.locator('#atelier-inspection-reset').click();await page.wait_for_function('!assemblyInspect().inspectionDisplay.wireframe');assert await page.locator('.atelier-more').inner_text()=='Studio tools';await close(page);await mode(page,'explode');assert await page.locator('#atelier-explosion').input_value()=='45';assert await pose(page)==before;record('inspection settings persist with active badge and reset, without losing explosion')
   await page.locator('#home').click();await settle(page);assert await page.locator('.task-dock [data-mode=explore]').get_attribute('aria-pressed')=='true';assert await page.locator('#context').is_hidden();assert not await page.evaluate('__flowQA.state().crown.pulled');await shot(page,'desktop-after.png');record('Reset restores complete watch and clean Explore view')
   page=await fresh(mobile=True);await mode(page,'time');await page.locator('.task-dock [data-mode=time]').click();assert await page.locator('#context').is_hidden();await page.locator('.crown-hotspot').tap();await page.wait_for_function('__flowQA.state().crown.pulled');record('mobile direct crown tap still pulls after panel toggle')
   await page.locator('#home').click();await settle(page);await page.locator('.atelier-more').tap();buttons=await page.locator('.inspection-tools button:not([hidden])').evaluate_all('(els)=>els.map(e=>({text:e.textContent,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))');assert all(x['height']>=44 and x['width']>=44 for x in buttons);assert await page.locator('#context').evaluate('(e)=>e.getBoundingClientRect().bottom<=innerHeight');record('mobile inspection controls remain reachable with at least 44px targets',buttons);await shot(page,'mobile-tools.png')
   page=await fresh(mobile=True);await shot(page,'mobile-clean.png');record('mobile clean object view captured')
   page=await fresh(hook=False,quality='studio');report['runtime']=await page.evaluate('assemblyInspect()');record('exact unmodified candidate loads in Studio quality');assert not report['errors'],report['errors'];report['passed']=True
  except Exception as e:report['passed']=False;report['failure']=repr(e);raise
  finally:
   (O/'report.json').write_text(json.dumps(report,indent=2));
   try:await asyncio.wait_for(browser.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())
