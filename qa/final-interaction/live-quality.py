import asyncio,json,pathlib,traceback,time
from playwright.async_api import async_playwright
out=pathlib.Path('live-quality-output');out.mkdir(exist_ok=True);r={'release':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','viewport':{'width':800,'height':640},'checks':{},'errors':[],'checkpoints':[]};save=lambda:(out/'report.json').write_text(json.dumps(r,indent=2));save()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport=r['viewport']);page=await c.new_page();r['browser']=b.version;page.on('pageerror',lambda e:r['errors'].append(str(e)));requests=[];page.on('request',lambda req:requests.append(req.url) if 'assembly-review.js' in req.url else None)
  async def proof(route):
   res=await route.fetch();s=await res.text();old='composer.render();renderedFrames++;';assert s.count(old)==1;s=s.replace(old,'composer.render();window.__qualityFrames=(window.__qualityFrames||0)+1;window.__lastQualityFrame=quality;renderedFrames++;');s+='\nwindow.__qa=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot(),frames:window.__qualityFrames||0,inspect:assemblyInspect()});';await route.fulfill(response=res,body=s)
  await page.route('**/assembly-review.js*',proof)
  async def checkpoint(name):
   x=await q.evaluate('''()=>{const i=assemblyInspect();return {quality:i.renderQuality,interactive:i.presentation.interactive,loading:i.loading,failed:i.failed,frames:window.__qualityFrames||0,status:document.getElementById('render-status').textContent}}''');r['checkpoints'].append({'name':name,**x});save();return x
  async def click_quality(name):
   await q.locator('[data-mode=quality]').first.click(timeout=90000);await q.locator('[data-quality="'+name+'"]').click(timeout=90000)
  async def step(name,fn,timeout):
   r['checks'][name]={'status':'running'};save()
   try:r['checks'][name]={'status':'passed','detail':await asyncio.wait_for(fn(),timeout)}
   except Exception as e:r['checks'][name]={'status':'failed','exception':repr(e),'traceback':traceback.format_exc()}
   save()
  async def switch(name):
   before=await checkpoint('before-'+name);await click_quality(name);await q.wait_for_function('(name)=>assemblyInspect().renderQuality===name',arg=name,timeout=90000);selected=await checkpoint('selected-'+name);await q.wait_for_function('([n,name])=>(window.__qualityFrames||0)>n && window.__lastQualityFrame===name',arg=[before['frames'],name],timeout=150000);after=await checkpoint('rendered-'+name);assert after['quality']==name and after['interactive'] and not after['loading'] and not after['failed'];return {'before':before,'selected':selected,'rendered':after}
  try:
   await page.goto('https://shayan-kazeyami.github.io/aerial-watch/?quality=efficient&leather=craft14',wait_until='domcontentloaded',timeout=60000);await page.wait_for_function("document.querySelector('#watch-viewer')?.contentWindow?.location.href.includes('atelier-preview.html')",timeout=60000);q=await (await page.query_selector('#watch-viewer')).content_frame();await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000);assert any(r['release'] in x for x in requests),requests
   proof=await q.evaluate('__qa()');r['proof']={'leather':proof['leather'],'hybrid':proof['hybrid']};assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and proof['leather']['geometryVerification']['actualBytes']==8579970 and proof['hybrid']['active'] and proof['hybrid']['triangles']==501830 and proof['inspect']['renderQuality']=='efficient';await checkpoint('ready-efficient')
   await step('efficient_to_studio',lambda:switch('studio'),300)
   # Always attempt recovery, even if Studio times out.
   await step('studio_to_efficient',lambda:switch('efficient'),300)
   if all(r['checks'][k]['status']=='passed' for k in ['efficient_to_studio','studio_to_efficient']):
    async def rapid():
     start=(await checkpoint('rapid-start'))['frames']
     for name in ['balanced','detail','efficient']:
      await click_quality(name);await q.wait_for_function('(name)=>assemblyInspect().renderQuality===name',arg=name,timeout=90000);await checkpoint('rapid-'+name)
     await checkpoint('rapid-final-selected');await q.wait_for_function('(n)=>(window.__qualityFrames||0)>n && window.__lastQualityFrame==="efficient"',arg=start,timeout=150000);x=await checkpoint('rapid-final-rendered');assert x['quality']=='efficient' and x['interactive'] and not x['failed'];return x
    await step('rapid_sequence_and_efficient_recovery',rapid,360)
   else:r['checks']['rapid_sequence_and_efficient_recovery']={'status':'unrun','reason':'isolated switch did not pass'};save()
  except Exception as e:r['setup_error']=repr(e);r['traceback']=traceback.format_exc()
  finally:save();await c.close();await b.close()
asyncio.run(main())
