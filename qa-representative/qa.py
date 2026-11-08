import asyncio,json,pathlib,base64,os,hashlib
from urllib.parse import urlparse
from playwright.async_api import async_playwright
BASE=pathlib.Path(__file__).parent
MODE=os.environ.get('RELEASE_QA_MODE','sealed');assert MODE in ['sealed','live']
SUPPLEMENTAL=os.environ.get('RELEASE_QA_SUPPLEMENTAL','0');assert SUPPLEMENTAL in ['0','add','only']
SOURCE_GLASS=os.environ.get('RELEASE_QA_SOURCE_GLASS','0')=='1';assert not SOURCE_GLASS or SUPPLEMENTAL=='only'
OUT=pathlib.Path(os.environ.get('RELEASE_QA_OUTPUT','transmission-qa-output'));OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=json.loads(pathlib.Path(os.environ.get('RELEASE_RECEIPT','transmission-output/sealed-release.json')).read_text())
ROOT=RECEIPT['releasePath'];RID=RECEIPT['releaseId'];assert ROOT=='preview-b/releases/'+RID
MANIFEST=json.loads((pathlib.Path(ROOT)/'deployment-manifest.json').read_text());assert MANIFEST['releaseId']==RID
EXPECTED={f['path']:f['sha256']for f in MANIFEST['localFiles']}
MODULES=['assembly-review.js','assembly-resolution.js','assembly-render-pipeline.js','assembly-overscan.js']
assert all(n in EXPECTED for n in MODULES)
HOOK=(BASE/'qa-hook.js').read_text()
READY='window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden'
SEED='''(()=>{let seed=123456789;Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};})();'''
GEOMETRY='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7'
def target_gate(cap):
 t=cap['transmission'];v=cap['actualTarget'];assert t['revision']=='expanded-target-budget-v1'
 assert v and len(v['viewport'])==4
 assert v['viewport'][2]*v['viewport'][3]<=t['maxPixels']
 assert abs(v['scale']-t['effectiveScale'])<1e-12
 return v['viewport'][2]*v['viewport'][3]
def invariants(d):
 assert d['sameGeometry'] and d['sameMaterials'] and d['sameMaps'];assert d['triangles']==247231
 assert d['hybrid']['active'] and d['hybrid']['triangles']==501830
async def run():
 report={'mode':MODE,'supplemental':SUPPLEMENTAL,'sourceGlass':SOURCE_GLASS,'releaseId':RID,'releasePath':ROOT,'errors':[],'captures':[],'modules':{},'backend':'Chromium SwiftShader','scope':'Native target allocation and visual correctness; not hardware FPS or WebGPU/mobile certification.'}
 def save(): (OUT/(MODE+'.json')).write_text(json.dumps(report,indent=2))
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);report['browser']=b.version
  context=await b.new_context(viewport=({'width':800,'height':640} if MODE=='live' else {'width':1440,'height':1000}),device_scale_factor=1);await context.add_init_script(SEED);page=await context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
  async def instrument(route):
   name=urlparse(route.request.url).path.split('/')[-1];r=await route.fetch();raw=await r.body();s=raw.decode()
   if name in MODULES:
    digest=hashlib.sha256(raw).hexdigest();assert digest==EXPECTED[name],(name,digest,EXPECTED[name]);assert '/'+ROOT+'/' in route.request.url;report['modules'][name]={'sha256':digest,'url':route.request.url}
   if name=='assembly-review.js':
    assert 'composer.render();'in s;s=s.replace('composer.render();','budgetQaApply();composer.render();');s+='\n'+HOOK
   if name=='three.module.js':
    old='_this.setRenderTarget( transmissionRenderTarget );';assert old in s
    s=s.replace(old,old+'\n globalThis.__qaTransmissionTarget={width:transmissionRenderTarget.width,height:transmissionRenderTarget.height,viewport:Array.from(_gl.getParameter(_gl.VIEWPORT)),scale:_this.transmissionResolutionScale};')
   await route.fulfill(response=r,body=s)
  for name in [*MODULES,'three.module.js']:await page.route('**/'+name+'*',instrument)
  try:
   if MODE=='live':
    await page.goto('https://shayan-kazeyami.github.io/aerial-watch/'+('?backplate=source' if SOURCE_GLASS else ''),wait_until='domcontentloaded',timeout=90000)
    await page.wait_for_function('(r)=>document.getElementById("watch-viewer")?.src.includes(r)',arg=ROOT,timeout=90000)
    report['liveEntry']=await page.locator('#watch-viewer').get_attribute('src');assert ROOT in report['liveEntry']
    q=await (await page.locator('#watch-viewer').element_handle()).content_frame();assert q
   else:
    await page.goto('http://127.0.0.1:8765/'+ROOT+'/atelier-preview.html?quality=efficient&leather=craft14'+('&backplate=source' if SOURCE_GLASS else ''),wait_until='domcontentloaded',timeout=90000);q=page
   await q.wait_for_function(READY,timeout=300000)
   if MODE=='live':
    report['bareDefaultProof']={'inspect':await q.evaluate('assemblyInspect()'),'viewport':page.viewport_size,'entry':report['liveEntry']};save()
   report['setup']=await q.evaluate('__strapQaSetup()');proof=report['setup']['leather']['diagnostics']['geometryVerification'];assert proof['actualSha256']==GEOMETRY and proof['actualBytes']==8579970
   assert report['setup']['inspect']['hybridCase']['active'] and report['setup']['inspect']['hybridCase']['triangles']==501830
   if MODE=='live':
    assert await asyncio.wait_for(q.evaluate("__strapQaQuality('efficient')"),120)=='efficient'
    await page.wait_for_timeout(1000)
    report['startupDrain']=await asyncio.wait_for(q.evaluate('__releaseDrain()'),120);assert report['startupDrain']['quality']=='efficient';save()
    await page.set_viewport_size({'width':1440,'height':1000})
    await asyncio.wait_for(q.evaluate("__budgetConfigure('efficient','front')"),120)
    await page.wait_for_timeout(500)
   report['initialInvariant']=await q.evaluate('__releaseInvariant()');invariants(report['initialInvariant'])
   for quality,view in ([] if SUPPLEMENTAL=='only' else [('balanced','front'),('detail','front'),('studio','front')]):
    report['pending']={'quality':quality,'stage':'configure'};save();config=await asyncio.wait_for(q.evaluate('(a)=>__budgetConfigure(...a)',[quality,view]),120);report['pending']['stage']='capture';save()
    cap=await asyncio.wait_for(q.evaluate('__budgetCapture()'),180);(OUT/f'{MODE}-{quality}-{view}.png').write_bytes(base64.b64decode(cap.pop('png').split(',')[1]));cap['config']=config;report['captures'].append(cap);save();target_gate(cap)
   if SUPPLEMENTAL!='0':
    report['supplementalCaptures']=[]
    for label,name,clear in ([('rear-source-glass','back',False),('oblique-source-glass','three-quarter',False)] if SOURCE_GLASS else [(v,v,False) for v in ['side','lug','buckle']]):
     report['pending']={'quality':'detail','view':label,'stage':'configure'};save()
     config=await asyncio.wait_for(q.evaluate('(a)=>__releaseSupportedView(...a)',['detail',name,clear]),120)
     assert config['intendedView']==config['actualView']==name
     assert config['inspectionDisplay']['transparentBackplate']==clear
     if SOURCE_GLASS:assert config['rearCrystal']['visible'] and config['rearCrystal']['transmission']>0 and not config['backplate']['visible']
     assert config['actualView']==name
     report['pending']['stage']='capture';save()
     cap=await asyncio.wait_for(q.evaluate('__budgetCapture()'),180);(OUT/f'{MODE}-detail-{label}.png').write_bytes(base64.b64decode(cap.pop('png').split(',')[1]));cap['config']=config;report['supplementalCaptures'].append(cap);save();target_gate(cap)
    await q.evaluate('__releaseRestoreBackplate()')
   if SUPPLEMENTAL!='only' and os.environ.get('RELEASE_QA_RESIZE','1')=='1':
    await asyncio.wait_for(q.evaluate("__budgetConfigure('detail','front')"),120)
    report['resize']=[]
    for size in [[800,600],[400,300],[800,600]]:
     state=await asyncio.wait_for(q.evaluate('(a)=>__releaseResize(...a)',size),180);report['resize'].append(state);target_gate(state);save()
    a,small,c=report['resize'];assert a['transmission']['requestedScale']==small['transmission']['requestedScale']==c['transmission']['requestedScale']
    assert small['transmission']['effectiveScale']>=a['transmission']['effectiveScale'];assert abs(a['transmission']['effectiveScale']-c['transmission']['effectiveScale'])<1e-12
    assert a['actualTarget']['viewport']==c['actualTarget']['viewport']
   report['qualityStableMaps']=await q.evaluate('__releaseQualityStableMaps()');invariants(report['qualityStableMaps']['stable'])
   report['controls']=await q.evaluate('__strapControls()');assert report['controls']['sameGeometry'] and report['controls']['sameMaterials']
   report['finalInvariant']=await q.evaluate('__releaseInvariant()');invariants(report['finalInvariant']);assert set(report['modules'])==set(MODULES)
   assert not report['errors'];report['passed']=True;report.pop('pending',None)
  except Exception as exc:report['exception']=repr(exc);raise
  finally:
   save()
   try:await asyncio.wait_for(context.close(),15)
   except:pass
   try:await asyncio.wait_for(b.close(),15)
   except:pass
asyncio.run(run())
