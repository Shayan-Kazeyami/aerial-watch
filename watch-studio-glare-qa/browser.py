import asyncio,hashlib,json,os,pathlib
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).resolve().parent
O=P/'output';O.mkdir(exist_ok=True)
RID='a9b5db9042cf25036cd74c1471cbb87c48b966b8c68cbf2992d134b45b9f9ac7'
U=f'https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/{RID}/'
W,H=map(int,os.environ.get('VIEW','960x650').split('x'))
Q=os.environ.get('QUALITY','studio')
S=['face','lug']
MODES=['control','no-bloom','no-key','no-rim','no-direct','no-ibl','restore']
h=lambda b:hashlib.sha256(b).hexdigest()
R={'immutable_base':RID,'qaOnly':'Never seal this overlay','softwareOnly':True,'view':[W,H],'quality':Q,'shots':{},'errors':[]}
STATE="""()=>{const s=assemblyInspect(),c=document.querySelector('#assembly-canvas');return {camera:s.camera,target:s.target,view:s.view,css:[c.clientWidth,c.clientHeight],buffer:[c.width,c.height],motion:[s.animation,s.interiorAnimation],elapsed:[s.mechanismElapsed,s.balanceElapsed,s.illustrativeElapsed],geometry:[s.triangles,s.sourceVisible],backend:window.__aerialBackend.actual,exposure:__glareQA.snapshot().exposure};}"""
async def main():
 async with async_playwright() as e:
  b=await e.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'])
  p=await b.new_page(viewport={'width':W,'height':H},device_scale_factor=1,reduced_motion='reduce')
  p.set_default_timeout(180000)
  p.on('pageerror',lambda error:R['errors'].append(str(error)))
  p.on('response',lambda a:R['errors'].append(f'HTTP {a.status} {a.url}') if a.status>=400 and '/preview-b/releases/' in a.url else None)
  try:
   original=await(await p.request.get(U+'deployment-manifest.json')).json();assert original['releaseId']==RID
   row=next(r for r in original['localFiles'] if r['path']=='assembly-review.js')
   async def overlay(route):
    response=await route.fetch();raw=await response.body();assert response.ok and h(raw)==row['sha256']
    instrumented=(P/'assembly-review.js').read_bytes()
    R['overlay']={'path':'assembly-review.js','unmodified':h(raw),'qa':h(instrumented)}
    await route.fulfill(response=response,body=instrumented)
   await p.route(U+'assembly-review.js*',overlay)
   await p.goto(U+f'atelier-preview.html?quality={Q}&light=softbox&normalStream=0',wait_until='domcontentloaded')
   await p.locator('body[data-ready=true]').wait_for(timeout=360000)
   await p.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'")
   await p.evaluate("document.querySelector('#reset-hands').click()")
   for v in S:
    await p.evaluate("(v)=>document.querySelector('[data-view='+v+']').click()",v)
    await p.wait_for_function("(v)=>assemblyInspect().view===v&&document.querySelector('#stage').dataset.cameraReady==='true'",arg=v)
    R['shots'][v]={'state':await p.evaluate(STATE),'passes':{}}
    ref=R['shots'][v]['state']
    assert ref['elapsed']==[0,0,0] and ref['motion']==[False,False] and ref['backend']=='WebGL2',ref
    for mode in MODES:
     ticket=await p.evaluate("(m)=>__glareQA.set(m)",mode)
     await p.wait_for_function("(id)=>__glareQA.snapshot().completed===id",arg=ticket)
     hits=await p.evaluate("()=>__glareQA.snapshot()")
     assert hits['issued']==hits['completed']==ticket and hits['mode']==mode
     assert hits['bloom']==(Q=='studio' and mode in ('control','restore')),hits
     if mode=='no-key':assert hits['lightIntensities'][0]==0
     if mode=='no-rim':assert hits['lightIntensities'][1]==0
     if mode=='no-direct':assert hits['lightIntensities']==[0,0,0]
     if mode=='no-ibl':assert hits['ibl']==0
     bbox=await p.locator('#assembly-canvas').bounding_box();assert bbox
     png=await p.screenshot(path=str(O/f'{v}.{mode}.png'),clip=bbox,animations='disabled',timeout=180000)
     after=await p.evaluate(STATE)
     assert all(ref[k]==after[k] for k in ref if k not in ('camera','target')),(ref,after)
     assert max(abs(x-y) for z in ('camera','target') for x,y in zip(ref[z],after[z]))<1e-7
     R['shots'][v]['passes'][mode]={**hits,'png_sha256':h(png)}
     (O/'REPORT.json').write_text(json.dumps(R,indent=2))
    a,z=[R['shots'][v]['passes'][m] for m in ('control','restore')]
    for k in ('bloom','lightIntensities','ibl','exposure','shadow','ao'):assert a[k]==z[k],(k,a,z)
   assert not R['errors'],R['errors'];R['passed']=True
  finally:
   (O/'REPORT.json').write_text(json.dumps(R,indent=2))
   await b.close()
if __name__=='__main__':asyncio.run(main())
