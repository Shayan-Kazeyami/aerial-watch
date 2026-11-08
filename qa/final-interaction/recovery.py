import asyncio,json,pathlib,os,traceback
from playwright.async_api import async_playwright
case=os.environ['CASE'];out=pathlib.Path('recovery-output');out.mkdir(exist_ok=True);r={'case':case,'release':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','status':'starting','errors':[]};save=lambda:(out/(case+'.json')).write_text(json.dumps(r,indent=2));save()
ready='window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden'
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);q=await b.new_page(viewport={'width':800,'height':640});r['browser']=b.version;q.on('pageerror',lambda e:r['errors'].append(str(e)));base='http://127.0.0.1:8766/preview-b/releases/'+r['release']+'/atelier-preview.html?quality=efficient&leather=craft14'
  async def proof(route):
   response=await route.fetch();s=await response.text();s+='\nwindow.__proof=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot(),context:renderer.getContext()});';await route.fulfill(response=response,body=s)
  await q.route('**/assembly-review.js*',proof)
  entered=asyncio.Event();release=asyncio.Event();once=True
  async def asset(route):
   nonlocal once
   if once:
    once=False;entered.set()
    if case=='slow':await release.wait();await route.continue_();return
    if case=='failure':await route.abort('failed');return
   await route.continue_()
  try:
   if case in ['slow','failure']:await q.route('**/rebuild/assembly.glb*',asset)
   await q.goto(base,wait_until='domcontentloaded',timeout=60000)
   if case=='slow':
    await asyncio.wait_for(entered.wait(),60);await q.wait_for_timeout(1500);r['gated']=await q.evaluate('({loading:!document.getElementById("loading").hidden,interactive:window.assemblyInspect?.().presentation.interactive,disabled:document.querySelector("[data-mode=inside]").disabled})');assert r['gated']['loading'] and not r['gated']['interactive'] and r['gated']['disabled'];save();release.set()
   if case=='failure':
    await asyncio.wait_for(entered.wait(),60);await q.wait_for_function('window.assemblyInspect && assemblyInspect().failed && !document.getElementById("atelier-retry").hidden',timeout=180000);r['failure']=await q.evaluate('({inspect:assemblyInspect(),retryVisible:!document.getElementById("atelier-retry").hidden})');save();await q.locator('#atelier-retry').click()
   await q.wait_for_function(ready,timeout=300000);v=await q.evaluate('({leather:__proof().leather,hybrid:__proof().hybrid})');r['proof']=v;assert v['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and v['leather']['geometryVerification']['actualBytes']==8579970 and v['hybrid']['active'] and v['hybrid']['triangles']==501830;save()
   if case=='context':
    supported=await q.evaluate('!!__proof().context.getExtension("WEBGL_lose_context")');r['extension']=supported;assert supported;await q.evaluate('__proof().context.getExtension("WEBGL_lose_context").loseContext()');await q.wait_for_function('assemblyInspect().failed && !document.getElementById("atelier-retry").hidden',timeout=30000);r['lost']=await q.evaluate('({failed:assemblyInspect().failed,message:document.getElementById("load-message").textContent})');save();await q.locator('#atelier-retry').click();await q.wait_for_function(ready,timeout=300000);v=await q.evaluate('({leather:__proof().leather,hybrid:__proof().hybrid})');assert v['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and v['hybrid']['active'];r['recovered']=True
   r['status']='passed'
  except Exception as e:r['status']='failed';r['exception']=repr(e);r['traceback']=traceback.format_exc()
  finally:save();await b.close()
asyncio.run(main())
