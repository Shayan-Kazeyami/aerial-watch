import asyncio,json,pathlib,os,base64,textwrap
from playwright.async_api import async_playwright
O=pathlib.Path('explode-output');C=pathlib.Path(json.loads((O/'build.json').read_text())['releasePath']);BASE=pathlib.Path('preview-b/releases/99d5275244fdabbc301fba262d59e612e7f511121e5e79a5dae5bf936e222e75');SCOPE=os.environ.get('QA_SCOPE','desktop')
HOOK="""
window.__explodeQA={pause(){stopTour();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();dirty=true},state(){model.updateWorldMatrix(true,true);return {amount:explosion.amount,target:explosion.target,moving:!!cameraTween||explosion.animating,camera:camera.position.toArray(),layers:explosion.snapshot?.().layers||[],parts:source.map(m=>({id:m.userData.sourceIndex,local:m.matrix.toArray(),world:new THREE.Vector3().setFromMatrixPosition(m.matrixWorld).toArray(),wrapper:!!m.parent.userData.assemblyExplosion})),wrappers:(()=>{let n=0;model.traverse(m=>{if(m.userData.assemblyExplosion)n++});return n})(),memory:renderer.info.memory,render:renderer.info.render}},shot(){composer.render();return renderer.domElement.toDataURL('image/png')}};
"""
for root in [BASE,C]:
 (root/'qa-explode-runtime.js').write_text((root/'assembly-review.js').read_text()+'\n'+HOOK)
 (root/'qa-explode-shell.js').write_text((root/'atelier-preview.js').read_text().replace('./assembly-review.js?v=atelier-local-1','./qa-explode-runtime.js'))
 (root/'qa-explode.html').write_text((root/'atelier-preview.html').read_text().replace('atelier-preview.js','qa-explode-shell.js'))
async def main():
 report={'scope':SCOPE,'checks':[],'errors':[],'renderer':'Chromium SwiftShader; no device FPS claim','build':json.loads((O/'build.json').read_text())}
 async with async_playwright() as p:
  browser=None
  async def fresh(root=C,mobile=False):
   nonlocal browser
   if browser:await browser.close()
   browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=await browser.new_context(viewport={'width':430 if mobile else 1180,'height':850 if mobile else 820},device_scale_factor=1,is_mobile=mobile,has_touch=mobile);page=await ctx.new_page();page.set_default_timeout(60000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
   await page.goto(f'http://127.0.0.1:8765/{root}/qa-explode.html?quality=efficient',wait_until='domcontentloaded');await page.wait_for_function('window.assemblyInspect && assemblyInspect().presentation.interactive',timeout=240000);await page.evaluate('__explodeQA.pause()');await settle(page);return page
  async def settle(page):await page.wait_for_function('!__explodeQA.state().moving',timeout=120000)
  def record(name,data=None):report['checks'].append({'name':name,'data':data});print('CHECK',name,json.dumps(data),flush=True);(O/(SCOPE+'-report.json')).write_text(json.dumps(report,indent=2))
  async def shot(page,name):
   data=await page.evaluate('__explodeQA.shot()');b=base64.b64decode(data.split(',')[1]);(O/name).write_bytes(b);print('IMAGE_START '+name,flush=True)
   for line in textwrap.wrap(base64.b64encode(b).decode(),1000):print(line)
   print('IMAGE_END '+name,flush=True)
  async def state(page):return await page.evaluate('__explodeQA.state()')
  try:
   mobile=SCOPE=='mobile'
   if not mobile:
    page=await fresh(BASE);await page.locator('.task-dock [data-mode=explode]').click();await settle(page);assert (await state(page))['amount']==0;await page.locator('#atelier-explosion').fill('100');await settle(page);s=await state(page);assert not any(x['wrapper'] for x in s['parts']);await shot(page,'before-exploded.png');record('baseline reproduces tab no-op and stationary internals')
   page=await fresh(mobile=mobile);before=await state(page);await shot(page,SCOPE+'-assembled.png')
   b=page.locator('.task-dock [data-mode=explode]');await (b.tap() if mobile else b.click());await settle(page);after=await state(page)
   assert after['amount']==1 and after['target']==1;assert all(x['wrapper'] for x in after['parts']);assert all(a['local']==b['local'] for a,b in zip(before['parts'],after['parts']));assert sum(l['sourceParts'] for l in after['layers'])==166;assert len([l for l in after['layers'] if l['sourceParts']])==6
   assert all(sum((a-b)**2 for a,b in zip(x['world'],y['world']))>25 for x,y in zip(before['parts'],after['parts']))
   record('one click/tap separates all 166 internal parts in six mechanism layers',{'layers':after['layers'],'resourcesBefore':before['memory'],'resourcesAfter':after['memory'],'draws':after['render']});await shot(page,SCOPE+'-exploded.png')
   await page.locator('#atelier-explosion').fill('45');await settle(page);partial=await state(page);assert abs(partial['amount']-.45)<1e-8
   await page.locator('.quality').click();await page.keyboard.press('Escape');await b.click();assert await page.locator('#atelier-explosion').input_value()=='45';assert all(abs(x-y)<1e-10 for x,y in zip((await state(page))['camera'],partial['camera']));record('utility panel and Escape preserve partial explosion')
   await page.locator('#atelier-explode-full').click();await settle(page);await page.locator('#atelier-reassemble').click();await settle(page);rest=await state(page);assert rest['amount']==0 and rest['wrappers']==0;assert all(x['local']==y['local'] for x,y in zip(before['parts'],rest['parts']));assert all(sum((a-b)**2 for a,b in zip(x['world'],y['world']))<1e-16 for x,y in zip(before['parts'],rest['parts']));record('reassembly restores exact source transforms and removes every wrapper')
   await b.click();await settle(page);assert (await state(page))['amount']==1;record('dock click explodes again after reassembly')
   await page.locator('#atelier-explosion').fill('20');await page.locator('#atelier-explosion').fill('85');await page.locator('#atelier-reassemble').click();await page.locator('#atelier-explode-full').click();await settle(page);assert (await state(page))['amount']==1;record('interrupted and reversed transitions settle correctly')
   await page.locator('.task-dock [data-mode=inside]').click();await settle(page);assert (await state(page))['amount']==0;record('Inside restores assembled movement')
   await b.click();await settle(page);await page.locator('#home').click();await settle(page);assert (await state(page))['amount']==0;assert await page.locator('.task-dock [data-mode=explore]').get_attribute('aria-pressed')=='true';record('Reset restores assembled Explore')
   if mobile:
    await b.tap();await settle(page);buttons=await page.locator('#atelier-reassemble,#atelier-explode-full').evaluate_all('(els)=>els.map(e=>({height:e.getBoundingClientRect().height,width:e.getBoundingClientRect().width}))');assert all(x['height']>=44 and x['width']>=44 for x in buttons);record('touch controls meet 44px minimum',buttons)
   assert not report['errors'],report['errors'];report['passed']=True
  except Exception as e:report['passed']=False;report['failure']=repr(e);raise
  finally:
   (O/(SCOPE+'-report.json')).write_text(json.dumps(report,indent=2));print('REPORT '+json.dumps(report),flush=True)
   if browser:
    try:await asyncio.wait_for(browser.close(),15)
    except asyncio.TimeoutError:pass
asyncio.run(main())
