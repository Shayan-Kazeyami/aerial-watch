import asyncio,json,pathlib,base64,hashlib,traceback,time
from playwright.async_api import async_playwright
R=pathlib.Path('hardware-normal-qa');O=R/'offline-bake/evidence';O.mkdir(exist_ok=True)
RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
BASE='.'
URL=f'http://127.0.0.1:8886/{BASE}/preview-b/releases/{RID}/atelier-preview.html?quality=efficient&normalStream=1&paused=1'
probe=(R/'probe.js').read_text().replace('mechanismBatch?.build(source);renderer.info.reset();','ao.enabled=false;mechanismBatch?.build(source);renderer.info.reset();')
# AO is deliberately off identically for both sides to avoid stochastic AO as a confound.
extra='''\nwindow.__normalQa.toggle=(enabled)=>{if(window.__hardwareNormalAudit)window.__hardwareNormalAudit.restore();window.__hardwareNormalAudit=enabled?repairHardwareCurvatureNormals(source):null;mechanismBatch?.build(source);return window.__normalQa.audit();};\n'''
report={'mainCommit':'f3c23832f6cb8af3463248355dd7f69ab5e7b6bf','release':RID,'url':URL,'AO':'disabled in both sides','errors':[],'runs':{},'sourceIntegrity':[]}
async def main():
 assert hashlib.sha256(pathlib.Path(f'preview-b/releases/{RID}/rebuild/assembly.glb').read_bytes()).hexdigest()=='4a4ae04e5808e705c9a2a96778343578365d100edfed3991d8ff90aeba85d06f'
 assert hashlib.sha256(pathlib.Path(f'preview-b/releases/{RID}/assembly-review.js').read_bytes()).hexdigest()=='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee'
 async with async_playwright()as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for mode in ['candidate','baked']:
    context=await browser.new_context(viewport={'width':800,'height':800},device_scale_factor=1);page=await context.new_page();page.set_default_timeout(180000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
    async def route(r):
     response=await r.fetch();body=await response.body();report.setdefault('baselineModuleSHA256',hashlib.sha256(body).hexdigest())
     if mode=='candidate':
      body=b"import {repairHardwareCurvatureNormals} from '/hardware-normal-qa/repair.js';\n"+body
      marker=b'  const rearWindow=exterior.find';assert marker in body
      body=body.replace(marker,b"  window.__hardwareNormalAudit=repairHardwareCurvatureNormals(source);resources.own('hardware normal QA rollback',()=>window.__hardwareNormalAudit.restore());\n"+marker,1)
     body+=probe.encode();report.setdefault('executedModuleSHA256',{})[mode]=hashlib.sha256(body).hexdigest();await r.fulfill(response=response,body=body)
    await page.route('**/assembly-review.js*',route)
    if mode=='baked':
     async def baked_route(r):
      report.setdefault('bakedRouteURLs',[]).append(r.request.url)
      await r.fulfill(path=str(R/'e79-rebase/assembly-normal-candidate.glb'))
     await page.route('**/rebuild/assembly.glb*',baked_route)
    await page.goto(URL,wait_until='domcontentloaded');await page.wait_for_function('window.__normalQa&&window.assemblyInspect?.().presentation.interactive',timeout=300000);print(mode,'ready',flush=True)
    await page.evaluate('__reuseQa.show({view:"movement",pose:0})');record={'audit':await page.evaluate('__normalQa.audit()'),'protectedNormals':await page.evaluate('__normalQa.protectedNormals()'),'hashes':await page.evaluate('__reuseQa.hashSources()'),'poses':await page.evaluate('__reuseQa.validatePoses()'),'states':[]};report['runs'][mode]=record
    cases=[('assembled',dict(view='watch')),('exploded',dict(view='watch',explode=1)),('movement',dict(view='movement'))]+[(f'part-{sid}',dict(sid=sid,view='movement',zoom=1.4))for sid in [9,12,21,26,39,71,125,126,128]]
    if mode=='baseline-repeat':cases=[cases[0],cases[2],cases[4]]
    for name,params in cases:
     state=await page.evaluate('(p)=>__reuseQa.show(p)',params);image=state.pop('image');(O/f'{mode}-{name}.png').write_bytes(base64.b64decode(image.split(',')[1]));state['case']=name;record['states'].append(state);(O/'report.json').write_text(json.dumps(report,indent=2));print(mode,name,flush=True)
    await context.close()
   a=report['runs']['candidate'];b=report['runs']['baked'];assert report.get('bakedRouteURLs'), 'baked route did not intercept any request';assert a['hashes']==b['hashes'];report['runtimeNormalParity']=True;
   # Remaining protected normal/pose/draw checks
   assert a['poses']==b['poses'];assert a['protectedNormals']==b['protectedNormals'];assert len(a['audit']['applied'])==92;assert not a['audit']['skipped']
   for x,y in zip(a['hashes'],b['hashes']):assert x['sid']==y['sid']and x['index']==y['index']and x['attributes']['position']==y['attributes']['position']
   for x,y in zip(a['states'],b['states']):
    assert x['case']==y['case'];assert x['camera']==y['camera'];assert x['rendererInfo']['render']['triangles']==y['rendererInfo']['render']['triangles'];assert [{k:v for k,v in o.items()if k not in ['normalVersion','positionVersion']}for o in x['source']]==[{k:v for k,v in o.items()if k not in ['normalVersion','positionVersion']}for o in y['source']]
   assert not report['errors'];report['passed']=True
  except Exception as e:report['failure']=repr(e);report['traceback']=traceback.format_exc();raise
  finally:(O/'report.json').write_text(json.dumps(report,indent=2));await browser.close()
asyncio.run(main())
