import asyncio,hashlib,json,pathlib,os,time,re
from playwright.async_api import async_playwright
HERE=pathlib.Path(__file__).resolve().parent
OUT=pathlib.Path(os.environ.get('ART13_OUT',HERE/'output'));OUT.mkdir(exist_ok=True,parents=True)
RID='78f11a43161421beddc94469318c7530f2e5b9afeb14f7517e79c7a3e564c4e0'
URL=f'https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/{RID}/'
N=('assembly-review.js','atelier-preview.js')
h=lambda b:hashlib.sha256(b).hexdigest()
report={'immutable_base':RID,'overlay':{},'cases':{},'errors':[],'software_rendering_only':True}
async def check(b,width,height,motion):
 label=f'{width}x{height}-{motion}'; pg=await b.new_page(viewport={'width':width,'height':height},reduced_motion=motion,device_scale_factor=1)
 pg.set_default_timeout(180000)
 pg.on('pageerror',lambda e:report['errors'].append(str(e)))
 pg.on('response',lambda r:report['errors'].append('HTTP '+str(r.status)+' '+r.url) if r.status>=400 and '/preview-b/releases/' in r.url else None)
 m=await (await pg.request.get(URL+'deployment-manifest.json')).json();assert m['releaseId']==RID
 expected={x['path']:x for x in m['localFiles']if x['path'] in N};assert set(expected)==set(N)
 async def overlay(route):
  name=route.request.url.split('?')[0].split('/')[-1];orig=await route.fetch();data=await orig.body()
  assert orig.ok and h(data)==expected[name]['sha256'] and len(data)==expected[name]['sizeBytes']
  v=(HERE/name).read_bytes();report['overlay'][name]={'base':h(data),'candidate':h(v)}
  await route.fulfill(response=orig,body=v)
 for n in N:await pg.route(URL+n+'*',overlay)
 await pg.goto(URL+'atelier-preview.html?quality=efficient',wait_until='domcontentloaded')
 await pg.locator('body[data-ready=true]').wait_for(timeout=300000)
 await pg.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=80000)

 rects="""() => {const rect=(s)=>{const r=document.querySelector(s).getBoundingClientRect();return {l:r.left,t:r.top,r:r.right,b:r.bottom,w:r.width,h:r.height};};return {stage:rect('#assembly-canvas'),panel:rect('#context'),dock:rect('.task-dock'),controls:rect('.bottom-zone'),host:rect('#atelier-stage-host')};}"""
 original=(await pg.evaluate(rects))['stage']
 await pg.locator('button.atelier-more').click()
 await pg.locator('#context [data-mode=tour]').click()
 await pg.wait_for_function("document.body.style.getPropertyValue('--tour-stage-end')!==''")
 state=pg.locator('#atelier-tour-state')
 nextb=pg.locator('#context [data-proxy=tour-next]')
 shots=(('showcase','Complete watch'),('face','Dial and hands'),('interior','Movement overview'),('balance','Balance and hairspring'),('train','Gear train'),('lug','Lugs and strap'))
 evidence=[]
 for shot,title in shots:
  await nextb.click()
  await pg.wait_for_function("(t)=>document.querySelector('#atelier-tour-state').textContent.includes(t)",arg=title)
  await pg.wait_for_function("(s)=>assemblyInspect().view===s&&document.querySelector('#stage').dataset.cameraReady==='true'",arg=shot,timeout=120000)
  rs=await pg.evaluate(rects)
  st,pa=rs['stage'],rs['panel']
  side=width>=681 or width>=568 and width>height
  gap=pa['l']-st['r'] if side else pa['t']-st['b']
  dockgap=rs['controls']['t']-st['b']
  assert gap>=11 and dockgap>=11 and st['w']>=190 and st['h']>=155,(label,shot,rs)
  actual=await pg.evaluate("()=>{const s=assemblyInspect();return {camera:s.camera,target:s.target};}")
  assert all(isinstance(v,(int,float)) for k in ('camera','target') for v in actual[k])
  evidence.append({'shot':shot,'title':title,'geometry':rs,'gap':gap,'dockgap':dockgap,**actual})
  await pg.screenshot(path=str(OUT/(label+'-'+shot+'.png')))
 await pg.locator('#close').click()
 await pg.wait_for_function("document.body.style.getPropertyValue('--tour-stage-end')===''")
 after=(await pg.evaluate(rects))['stage']
 assert after==original,(after,original)
 assert await pg.locator('.atelier-more').evaluate('(b)=>document.activeElement===b')
 report['cases'][label]={'shots':evidence,'original':original,'restored':after}
 await pg.close()
async def main():
 width,height=map(int,os.environ.get('VIEW','820x600').split('x'))
 motion=os.environ.get('MOTION','reduce')
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'])
  try:
   await check(b,width,height,motion)
   assert set(report['overlay'])==set(N) and not report['errors'],report
   report['passed']=True
  finally:
   (OUT/'REPORT.json').write_text(json.dumps(report,indent=2))
   await b.close()
if __name__=='__main__':asyncio.run(main())
