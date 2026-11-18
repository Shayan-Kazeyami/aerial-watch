import asyncio,hashlib,json,pathlib,os,time,re
from playwright.async_api import async_playwright
HERE=pathlib.Path(__file__).resolve().parent
OUT=pathlib.Path(os.environ.get('ART13_OUT',HERE/'output'));OUT.mkdir(exist_ok=True,parents=True)
RID='a9b5db9042cf25036cd74c1471cbb87c48b966b8c68cbf2992d134b45b9f9ac7'
URL=f'http://127.0.0.1:8765/preview-b/releases/{RID}/'
N=('assembly-review.js','atelier-preview.js')
h=lambda b:hashlib.sha256(b).hexdigest()
report={'immutable_base':RID,'exact_modules':{},'module_overlays':False,'cases':{},'errors':[],'software_rendering_only':True}
async def check(b,width,height,motion):
 label=f'{width}x{height}-{motion}'; pg=await b.new_page(viewport={'width':width,'height':height},reduced_motion=motion,device_scale_factor=1)
 pg.set_default_timeout(180000)
 pg.on('pageerror',lambda e:report['errors'].append(str(e)))
 pg.on('response',lambda r:report['errors'].append('HTTP '+str(r.status)+' '+r.url) if r.status>=400 and '/preview-b/releases/' in r.url else None)
 m=await (await pg.request.get(URL+'deployment-manifest.json')).json();assert m['releaseId']==RID
 expected={x['path']:x for x in m['localFiles']if x['path'] in N};assert set(expected)==set(N)
 for name,row in expected.items():
  resp=await pg.request.get(URL+name);data=await resp.body()
  assert resp.ok and h(data)==row['sha256'] and len(data)==row['sizeBytes'],name
  report['exact_modules'][name]=h(data)
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
 last_pose=await pg.evaluate("()=>{const a=assemblyInspect();return [...a.camera,...a.target];}")
 for shot,title in shots:
  await nextb.click()
  await pg.wait_for_function("(t)=>document.querySelector('#atelier-tour-state').textContent.includes(t)",arg=title)
  await pg.wait_for_timeout(1100) # clear the previous frame's cameraReady marker
  await pg.wait_for_function("(s)=>assemblyInspect().view===s&&document.querySelector('#stage').dataset.cameraReady==='true'",arg=shot,timeout=120000)
  before=await pg.evaluate("()=>{const a=assemblyInspect();return [...a.camera,...a.target];}")
  await pg.wait_for_timeout(500)
  settled=await pg.evaluate("()=>{const a=assemblyInspect();return [...a.camera,...a.target];}")
  delta=max(abs(a-b) for a,b in zip(before,settled))
  movement=max(abs(a-b) for a,b in zip(settled,last_pose))
  assert delta<1e-7 and movement>.25,(shot,before,settled,last_pose,delta,movement)
  last_pose=settled
  rs=await pg.evaluate(rects)
  st,pa=rs['stage'],rs['panel']
  side=width>=681 or width>=568 and width>height
  gap=pa['l']-st['r'] if side else pa['t']-st['b']
  dockgap=rs['controls']['t']-st['b']
  assert gap>=11 and dockgap>=11 and st['w']>=190 and st['h']>=155,(label,shot,rs)
  actual=await pg.evaluate("()=>{const s=assemblyInspect();return {camera:s.camera,target:s.target};}")
  assert all(isinstance(v,(int,float)) for k in ('camera','target') for v in actual[k])
  evidence.append({'shot':shot,'title':title,'geometry':rs,'gap':gap,'dockgap':dockgap,'poseMaxAbsoluteComponentDelta':delta,'movementFromPreviousShot':movement,**actual})
  await pg.screenshot(path=str(OUT/(label+'-'+shot+'.png')))
 await pg.locator('#close').click()
 await pg.wait_for_function("document.body.style.getPropertyValue('--tour-stage-end')===''")
 after=(await pg.evaluate(rects))['stage']
 assert after==original,(after,original)
 assert await pg.locator('.atelier-more').evaluate('(b)=>document.activeElement===b')
 report['cases'][label]={'shots':evidence,'original':original,'restored':after}
 if width==820:
  await pg.locator('.task-dock [data-mode=explode]').click()
  await pg.wait_for_function("document.querySelector('#atelier-explosion')!==null")
  assert (await pg.evaluate(rects))['stage']==original
  await pg.locator('#atelier-layer-focus').select_option('balance')
  await pg.wait_for_function("document.querySelector('#atelier-explosion-note').textContent.includes('Oscillates')")
  await pg.locator('#atelier-reassemble').click()
  await pg.locator('#close').click()
  await pg.locator('.task-dock [data-mode=capture]').click()
  await pg.wait_for_function("!document.querySelector('#context [data-proxy=record-scene]').disabled")
  await pg.locator('#context [data-proxy=record-scene]').click()
  await pg.wait_for_function("document.querySelector('dialog[open]')!==null")
  await pg.keyboard.press('Escape')
  await pg.wait_for_function("document.querySelector('dialog[open]')===null")
  report['cases'][label]['nonTourCompatibility']=True
 await pg.close()
async def main():
 width,height=map(int,os.environ.get('VIEW','820x600').split('x'))
 motion=os.environ.get('MOTION','reduce')
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'])
  try:
   await check(b,width,height,motion)
   assert set(report['exact_modules'])==set(N) and not report['errors'],report
   report['passed']=True
  finally:
   (OUT/'REPORT.json').write_text(json.dumps(report,indent=2))
   await b.close()
if __name__=='__main__':asyncio.run(main())
