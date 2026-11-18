import asyncio,hashlib,json,os,pathlib,time
from playwright.async_api import async_playwright
H=pathlib.Path(__file__).resolve().parent; OUT=H/'output'; OUT.mkdir(exist_ok=True)
RID='a9b5db9042cf25036cd74c1471cbb87c48b966b8c68cbf2992d134b45b9f9ac7'
URL=f'https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/{RID}/'
W,T=map(int,os.environ.get('VIEW','1440x900').split('x'))
LITE=os.environ.get('LIGHT','softbox')
QUALITY=os.environ.get('QUALITY','studio')
sha=lambda b:hashlib.sha256(b).hexdigest()
report={'immutable_release':RID,'light':LITE,'materials':'brushed (unchanged)','software_only':True,'views':{},'errors':[]}
state="""()=>{const s=assemblyInspect(),c=document.querySelector('#assembly-canvas'),p=new URL(location.href).searchParams;return {view:s.view,quality:s.renderQuality,backend:window.__aerialBackend,css:[c.clientWidth,c.clientHeight],buffer:[c.width,c.height],dpr:devicePixelRatio,params:Object.fromEntries(p),camera:s.camera,target:s.target,elapsed:[s.mechanismElapsed,s.balanceElapsed,s.illustrativeElapsed],motion:[s.animation,s.interiorAnimation],triangles:s.triangles,leather:s.leatherCompatibility,crystals:s.crystals,openWork:s.openWork,visible:s.sourceVisible}}"""
async def main():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'])
  p=await b.new_page(viewport={'width':W,'height':T},device_scale_factor=1,reduced_motion='reduce')
  p.set_default_timeout(200000)
  p.on('pageerror',lambda e:report['errors'].append(str(e)))
  p.on('response',lambda r:report['errors'].append(f'HTTP {r.status} {r.url}') if r.status>=400 and '/preview-b/releases/' in r.url else None)
  try:
   res=await p.request.get(URL+'deployment-manifest.json');assert res.ok
   m=await res.json();assert m['releaseId']==RID
   names=['assembly-review.js','atelier-defaults.js','assembly-lighting.js','assembly-materials.js']
   for name in names:
    row=next(x for x in m['localFiles'] if x['path']==name)
    body=await (await p.request.get(URL+name)).body()
    assert len(body)==row['sizeBytes'] and sha(body)==row['sha256'],name
   report['boundModules']={x['path']:x['sha256'] for x in m['localFiles'] if x['path'] in names}
   if LITE=='rear-study':
    async def overlay(route):
     original=await route.fetch();raw=await original.body()
     assert original.ok and sha(raw)==report['boundModules']['assembly-lighting.js']
     trial=(H/'assembly-lighting.js').read_bytes()
     report['qaOverlay']={'module':'assembly-lighting.js','baseline':sha(raw),'candidate':sha(trial)}
     await route.fulfill(response=original,body=trial)
    await p.route(URL+'assembly-lighting.js*',overlay)
   light='softbox' if LITE=='rear-study' else LITE
   await p.goto(URL+f'atelier-preview.html?quality={QUALITY}&light={light}'+('&normalStream=0' if QUALITY=='efficient' else ''),wait_until='domcontentloaded')
   await p.locator('body[data-ready=true]').wait_for(timeout=360000)
   await p.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'")
   await p.evaluate("document.querySelector('#reset-hands').click()")
   for view in ['face','showcase','interior','balance','lug']:
    await p.evaluate("(v)=>document.querySelector('[data-view='+v+']').click()",view)
    await p.wait_for_function("(v)=>assemblyInspect().view===v&&document.querySelector('#stage').dataset.cameraReady==='true'",arg=view)
    before=await p.evaluate(state)
    await p.locator('#assembly-canvas').screenshot(path=str(OUT/(view+'.png')),animations='disabled',timeout=180000)
    after=await p.evaluate(state)
    fields=('view','css','buffer','elapsed','motion','triangles')
    assert max(abs(a-b) for f in ('camera','target') for a,b in zip(before[f],after[f]))<1e-7
    assert all(before[f]==after[f] for f in fields),(view,{f:(before[f],after[f]) for f in fields if before[f]!=after[f]})
    assert before['motion']==[False,False] and before['elapsed']==[0,0,0] and before['quality']==QUALITY and before['params']['finish']=='brushed' and before['openWork'],before
    report['views'][view]=after
    (OUT/'REPORT.json').write_text(json.dumps(report,indent=2))
   if LITE=='rear-study': assert report['qaOverlay']['candidate']!=report['qaOverlay']['baseline']
   assert not report['errors'],report['errors']
   report['passed']=True
  finally:
   (OUT/'REPORT.json').write_text(json.dumps(report,indent=2))
   await b.close()
if __name__=='__main__':asyncio.run(main())
