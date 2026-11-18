import asyncio,hashlib,json,os,pathlib
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).resolve().parent;O=P/'output';O.mkdir(exist_ok=True)
RID='a09e63edcfc275e017ff9655270f0c1c733a95d075f55c0306e84ba70d1a07a8'
ROOT='https://shayan-kazeyami.github.io/aerial-watch/'
U=ROOT+f'preview-b/releases/{RID}/'
W,H=map(int,os.environ.get('VIEW','820x600').split('x'))
C=os.environ.get('ARM','candidate')
R={'base':RID,'arm':C,'viewport':[W,H],'overlays':{},'errors':[]}
h=lambda b:hashlib.sha256(b).hexdigest()
async def main():
 async with async_playwright() as e:
  b=await e.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'])
  p=await b.new_page(viewport={'width':W,'height':H},reduced_motion='reduce')
  p.set_default_timeout(180000)
  p.on('pageerror',lambda e:R['errors'].append(str(e)))
  p.on('response',lambda e:R['errors'].append('HTTP '+str(e.status)+' '+e.url) if e.status>=400 and '/preview-b/releases/' in e.url else None)
  try:
   manifest=await(await p.request.get(U+'deployment-manifest.json')).json()
   assert manifest['releaseId']==RID
   names=('atelier-preview.js','assembly-review.js')
   rows={q['path']:q for q in manifest['localFiles'] if q['path'] in names}
   assert set(rows)==set(names)
   for name in names:
    x=await p.request.get(U+name); raw=await x.body()
    assert x.ok and h(raw)==rows[name]['sha256'] and len(raw)==rows[name]['sizeBytes']
    R.setdefault('exactModules',{})[name]=h(raw)
   top=p
   await top.goto(ROOT+'?quality=efficient&reset-proof='+RID[:12],wait_until='domcontentloaded')
   await top.wait_for_function('(rid)=>document.querySelector("#watch-viewer")?.src.includes(rid)',arg=RID,timeout=120000)
   await top.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=360000)
   p=next(f for f in top.frames if RID in f.url)
   R['publicLoader']=top.url;R['publicIframe']=p.url
   await p.locator('body[data-ready=true]').wait_for(timeout=360000)
   await p.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'")
   state="""()=>{const s=assemblyInspect();return {pose:[...s.camera,...s.target],view:s.view,quality:s.renderQuality,finish:s.finish,glass:s.crystals,layer:s.layerFocus.selected,amount:s.explosion.amount,open:s.openWork,inside:s.interiorView,visible:s.sourceVisible,motion:[s.animation,s.interiorAnimation],time:[s.mechanismElapsed,s.balanceElapsed,s.illustrativeElapsed],panel:!document.querySelector('#context').hidden,mode:document.querySelector('#context').dataset.tool};}"""
   async def read():return await p.evaluate(state)
   await p.locator('.task-dock [data-mode=explode]').click()
   await p.wait_for_function("assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating")
   await p.locator('#atelier-explosion').evaluate("""b=>{b.value='42';b.dispatchEvent(new Event('input',{bubbles:true}));}""")
   await p.wait_for_function("Math.abs(assemblyInspect().explosion.amount-.42)<.011&&!assemblyInspect().explosion.animating")
   await p.evaluate("""()=>{for(const [id,value]of [['render-quality','balanced'],['crystals',false]]){const n=document.getElementById(id);if(typeof value==='boolean')n.checked=value;else n.value=value;n.dispatchEvent(new Event('change',{bubbles:true}));}}""")
   await p.locator('#atelier-layer-focus').select_option('balance')
   await p.wait_for_function("assemblyInspect().layerFocus.selected==='balance'")
   initial=await read();R['before']=initial
   assert initial['panel'] and initial['mode']=='explode' and initial['quality']=='balanced' and not initial['glass'] and initial['layer']=='balance'
   await p.locator('#home').click()
   await p.wait_for_timeout(400)
   home=await read();R['afterClick']=home
   keep=['view','quality','finish','glass','layer','amount','open','inside','visible','motion','time','panel','mode']
   if C=='live':
    assert home['amount']==0 and home['layer'] is None and home['quality']=='efficient' and home['glass'] and not home['panel'],home
   else:
    for key in keep:assert home[key]==initial[key],(key,initial[key],home[key])
    await top.screenshot(path=str(O/'camera-reset-preserves-inspection.png'))
    await p.locator('button.atelier-more').click()
    await p.locator('#atelier-reset-studio').click()
    reset=await read();R['afterFullReset']=reset
    assert reset['amount']==0 and reset['layer'] is None and reset['quality']=='efficient' and reset['glass'] and not reset['panel'],reset
    await p.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'&&document.body.style.getPropertyValue('--atelier-panel-height')==='0px'")
    # Canonical reset is measured with the same closed panel and viewport.
    await p.locator('#home').click()
    await p.locator('#assembly-canvas').focus()
    before=await read()
    await top.keyboard.press('ArrowRight')
    await p.wait_for_function("(x)=>assemblyInspect().target.some((v,i)=>Math.abs(v-x[i])>.001)",arg=before['pose'][3:])
    moved=await read();await top.keyboard.press('Home')
    await p.wait_for_function("(x)=>assemblyInspect().target.some((v,i)=>Math.abs(v-x[i])>.01)",arg=moved['pose'][3:])
    after=await read()
    assert sum(abs(x-y) for x,y in zip(before['pose'],after['pose']))<.15,(before,after)
    assert after['panel']==before['panel'] and after['quality']==before['quality']
    R['keyboard']={'before':before,'panned':moved,'reset':after}
    await p.evaluate("""()=>{const b=document.getElementById('animate');b.checked=true;b.dispatchEvent(new Event('change',{bubbles:true}));}""")
    await p.wait_for_function('assemblyInspect().animation&&assemblyInspect().illustrativeElapsed>.05')
    motion_before=await read()
    await p.locator('#home').click()
    motion_after=await read()
    assert motion_after['motion']==motion_before['motion'] and motion_after['time'][2]>=motion_before['time'][2]>.05
    R['runningMotion']={'before':motion_before,'after':motion_after}
   assert not R['errors'],R['errors'];R['passed']=True
  finally:
   (O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
if __name__=='__main__':asyncio.run(main())
