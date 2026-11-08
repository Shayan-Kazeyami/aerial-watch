import asyncio,json,pathlib,base64,os
from playwright.async_api import async_playwright
BASE=pathlib.Path('qa/overscan-budget');OUT=pathlib.Path('budget-output');OUT.mkdir(exist_ok=True)
ROOT='preview-b/releases/0c468cf914b608e0d67036aa0a25fe16bb6c2802b0e90a940677f43466e19ff1'
PATCHES=json.loads((BASE/'patches.json').read_text());HOOK=(BASE/'qa-hook.js').read_text()
READY='window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden'
SEED='''(()=>{let seed=123456789;Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};})();'''
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for variant in [os.environ['BUDGET_VARIANT']]:
   report={'variant':variant,'errors':[],'captures':[],'patched':[],'backend':'Chromium SwiftShader','browser':b.version};context=await b.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1);await context.add_init_script(SEED);q=await context.new_page();q.on('pageerror',lambda e:report['errors'].append(str(e)))
   async def instrument(route):
    name=route.request.url.split('/')[-1].split('?')[0];r=await route.fetch();s=await r.text()
    if variant=='candidate' and name in PATCHES:
     for op in PATCHES[name]:
      if 'append'in op:s+=op['append'];continue
      assert op['old']in s,(name,op['old'][:150]);s=s.replace(op['old'],op['new'],1)
     report['patched'].append(name)
    if name=='assembly-review.js':s=s.replace('composer.render();','budgetQaApply();composer.render();');s+='\n'+HOOK
    if name=='three.module.js':
     old='_this.setRenderTarget( transmissionRenderTarget );';assert old in s
     s=s.replace(old,old+'''\n globalThis.__qaTransmissionTarget={width:transmissionRenderTarget.width,height:transmissionRenderTarget.height,viewport:Array.from(_gl.getParameter(_gl.VIEWPORT)),scale:_this.transmissionResolutionScale};''')
    await route.fulfill(response=r,body=s)
   for name in [*PATCHES,'three.module.js']:await q.route('**/'+name+'*',instrument)
   try:
    await q.goto('http://127.0.0.1:8765/'+ROOT+'/atelier-preview.html?quality=efficient&leather=craft14',wait_until='domcontentloaded');await q.wait_for_function(READY,timeout=300000);report['setup']=await q.evaluate('__strapQaSetup()')
    proof=report['setup']['leather']['diagnostics']['geometryVerification'];assert proof['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7';assert report['setup']['inspect']['hybridCase']['active']
    for quality,view in [('balanced','front'),('detail','front'),('studio','front')]:
     print(variant,quality,view,flush=True);report['pending']={'quality':quality,'view':view,'stage':'configure'};(OUT/f'{variant}.json').write_text(json.dumps(report,indent=2));config=await asyncio.wait_for(q.evaluate('(a)=>__budgetConfigure(...a)',[quality,view]),120);report['pending']['stage']='capture';(OUT/f'{variant}.json').write_text(json.dumps(report,indent=2));cap=await asyncio.wait_for(q.evaluate('__budgetCapture()'),180);(OUT/f'{variant}-{quality}-{view}.png').write_bytes(base64.b64decode(cap.pop('png').split(',')[1]));cap['config']=config;report['captures'].append(cap);(OUT/f'{variant}.json').write_text(json.dumps(report,indent=2))
     target=cap['actualTarget'];assert target and len(target['viewport'])==4
     if variant=='candidate':
      t=cap['transmission'];assert t['revision']=='expanded-target-budget-v1';assert target['viewport'][2]*target['viewport'][3]<=t['maxPixels'];assert abs(target['scale']-t['effectiveScale'])<1e-12
    assert not report['errors'];report['passed']=True
   except Exception as exc:
    report['exception']=repr(exc);raise
   finally:
    (OUT/f'{variant}.json').write_text(json.dumps(report,indent=2))
    try:await asyncio.wait_for(context.close(),15)
    except:pass
  try:await asyncio.wait_for(b.close(),15)
  except:pass
asyncio.run(run())
