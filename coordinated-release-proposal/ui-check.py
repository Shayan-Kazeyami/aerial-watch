"""Complementary real-UI quality and desktop smoke for exact staged proposal.
No route interception, source injection, programmatic UI events or force=True.
Long mobile lifecycle/reload sweeps belong to the independent recovery worker.
"""
import asyncio, json, os, pathlib, traceback, time
from playwright.async_api import async_playwright
from PIL import Image, ImageStat
Q=pathlib.Path('coordinated-release-proposal')
RID='f0d3fb50ee863df4f83ee20045d6a7a0b35c0b47594884e76683a588642e0179'
assert (Q/'release-id.txt').read_text().strip()==RID
KIND=os.getenv('QA_UI_KIND','desktop');assert KIND in ['desktop','mobile','landscape']
W,H=map(int,os.getenv('QA_VIEWPORT',{'desktop':'1280x800','mobile':'430x932','landscape':'740x360'}[KIND]).split('x'))
MOBILE=KIND!='desktop';O=Q/('evidence-ui-'+KIND);O.mkdir(exist_ok=True)
URL='http://127.0.0.1:8765/?quality=efficient&normalStream=1'
R={'release':RID,'url':URL,'kind':KIND,'viewport':[W,H],'deviceScaleFactor':1,'isMobile':MOBILE,'hasTouch':MOBILE,'errors':[],'navigation':[],'requests':[],'steps':[],'passed':False,'scope':'Unintercepted packaged root iframe, real UI controls and Chromium SwiftShader; not physical phone/GPU/FPS or WebGPU proof','limits':['Mobile repeated lifecycle/reload/interruption coverage handled by separate worker','Screenshots require actual pixel inspection after artifact download','No video encoding proof']}
INIT="""(()=>{window.__proposalUI={contexts:[],initialTimeOrigin:performance.timeOrigin};document.addEventListener('webglcontextlost',e=>window.__proposalUI.contexts.push({type:'lost',id:e.target.id}),true);document.addEventListener('webglcontextrestored',e=>window.__proposalUI.contexts.push({type:'restored',id:e.target.id}),true)})();"""
SNAP="""()=>{const c=document.getElementById('assembly-canvas'),s=document.getElementById('stage'),a=assemblyInspect();window.__proposalCanvas??=c;return {timeOrigin:performance.timeOrigin,url:location.href,canvasSame:c===window.__proposalCanvas,canvas:[c.width,c.height],stage:s.getBoundingClientRect().toJSON(),ready:document.body.dataset.ready,cameraReady:s.dataset.cameraReady,renderQuality:a.renderQuality,sourceMeshes:a.sourceMeshes,sourceVisible:a.sourceVisible,explosion:a.explosion,camera:a.camera,target:a.target,failed:a.failed,loading:a.loading,presentation:a.presentation,contexts:window.__proposalUI.contexts,media:{fine:matchMedia('(pointer:fine)').matches,hover:matchMedia('(hover:hover)').matches},contextHidden:document.getElementById('context').hidden}}"""
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  context=await browser.new_context(viewport={'width':W,'height':H},device_scale_factor=1,is_mobile=MOBILE,has_touch=MOBILE)
  host=await context.new_page();host.set_default_timeout(90000);await host.add_init_script(INIT)
  host.on('pageerror',lambda e:R['errors'].append(str(e)))
  host.on('framenavigated',lambda f:R['navigation'].append(f.url))
  host.on('request',lambda r:R['requests'].append({'url':r.url,'type':r.resource_type}))
  frame=None
  try:
   await host.goto(URL,wait_until='domcontentloaded',timeout=120000)
   await host.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000)
   frame=next(f for f in host.frames if '/'+RID+'/' in f.url)
   assert frame.url.split('/preview-b/releases/')[1].split('/')[0]==RID
   await frame.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"&&window.assemblyInspect?.().presentation.interactive',timeout=300000)
   await host.locator('#watch-loading').wait_for(state='hidden',timeout=120000)
   R['initial']=await frame.evaluate(SNAP);assert R['initial']['sourceMeshes']==166
   assert R['initial']['ready']=='true' and not R['initial']['failed']
   R['identity']={'releaseURL':frame.url,'rootURL':host.url,'revision':await frame.evaluate("async()=> (await import('./quality-study/viewer-revision.js')).default")}
   build=json.loads((Q/'build-report.json').read_text());assert R['identity']['revision']['digest']==build['viewerRevisionDigest']
   initial_nav=len(R['navigation']);initial_requests=len(R['requests']);origin=R['initial']['timeOrigin']
   cdp=await context.new_cdp_session(host)
   async def settle(name):
    await frame.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    s=await frame.evaluate(SNAP);R['steps'].append({'name':name,**s});(O/'report.json').write_text(json.dumps(R,indent=2))
    assert s['timeOrigin']==origin and s['canvasSame'],(name,'document/canvas replaced')
    assert '/'+RID+'/' in s['url'] and s['ready']=='true' and s['cameraReady']=='true'
    assert not s['failed'] and not s['loading'] and s['presentation']['interactive'],(name,s)
    assert not s['contexts'],(name,'context loss/restoration',s['contexts'])
    assert s['canvas'][0]>0 and s['canvas'][1]>0
    assert len(R['navigation'])==initial_nav,(name,'unexpected navigation',R['navigation'][initial_nav:])
    assert not R['errors'],R['errors']
    print('UI',KIND,name,flush=True);return s
   async def activate(selector):
    target=frame.locator(selector);assert await target.count()==1,selector
    if MOBILE:await target.tap()
    else:await target.click()
   async def close_panel():
    if await frame.locator('#close').is_visible():
     await activate('#close');await frame.locator('#context').wait_for(state='hidden')
   async def capture(name):
    await settle(name+'-capture');path=O/(name+'.png');await frame.locator('#assembly-canvas').screenshot(path=str(path),animations='disabled',timeout=180000)
    im=Image.open(path).convert('RGB');stat=ImageStat.Stat(im);colors=len(im.getcolors(maxcolors=10000000)or[])
    assert max(stat.stddev)>5 and colors>100,(name,'plausibly blank canvas',stat.stddev,colors)
    R.setdefault('captures',[]).append({'name':name,'size':list(im.size),'stddev':stat.stddev,'colors':colors})
   async def drag_slider(fraction):
    slider=frame.locator('#atelier-explosion');await slider.wait_for(state='visible');assert await slider.is_enabled()
    box=await slider.bounding_box();v=float(await slider.input_value())/100
    x0=box['x']+8+(box['width']-16)*v;y=box['y']+box['height']/2;x1=box['x']+8+(box['width']-16)*fraction
    iframe=await host.locator('#watch-viewer').bounding_box()
    hit=await frame.evaluate('p=>document.elementFromPoint(p.x,p.y)?.id',{'x':x0-iframe['x'],'y':y-iframe['y']})
    assert hit=='atelier-explosion',('Slider thumb obscured',hit,box)
    if MOBILE:
     await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x0,'y':y}]})
     for i in range(1,9):await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x0+(x1-x0)*i/8,'y':y}]})
     await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    else:
     await host.mouse.move(x0,y);await host.mouse.down();await host.mouse.move(x1,y,steps=8);await host.mouse.up()
    await frame.wait_for_function('v=>Math.abs(assemblyInspect().explosion.amount-v)<.06',arg=fraction,timeout=60000)
    value=float(await slider.input_value())/100;s=await settle('native-range-drag');assert abs(value-fraction)<.06 and abs(s['explosion']['amount']-value)<.025,(value,s)
    return {'target':fraction,'actualInput':value,'actualExplosion':s['explosion']['amount'],'input':'CDP native touch drag'if MOBILE else'native mouse drag'}
   async def explode_reset(label,expected_quality):
    await close_panel();await activate('.task-dock [data-mode="explode"]');await frame.locator('#atelier-explosion').wait_for(state='visible')
    await frame.wait_for_function('assemblyInspect().explosion.amount>.1',timeout=60000)
    drag=await drag_slider(.37)
    await activate('#atelier-reassemble');await frame.wait_for_function('assemblyInspect().explosion.amount<.001',timeout=60000)
    reassembled=await settle(label+'-reassembled');assert reassembled['renderQuality']==expected_quality,reassembled;await close_panel();await activate('#home')
    await frame.wait_for_function('assemblyInspect().explosion.amount<.001',timeout=60000)
    state=await settle(label+'-home-reset');return {'drag':drag,'qualityBeforeReset':reassembled['renderQuality'],'qualityAfterReset':state['renderQuality']}
   await capture('initial-uninstrumented')
   if not MOBILE:
    assert R['initial']['media']=={'fine':True,'hover':True},R['initial']['media']
    await frame.locator('.masthead button[data-mode="quality"]').hover()
    assert await frame.locator('.masthead button[data-mode="quality"]').evaluate("e=>e.matches(':hover')")
    await frame.locator('.task-dock [data-mode="capture"]').hover()
    assert await frame.locator('.task-dock [data-mode="capture"]').evaluate("e=>e.matches(':hover')")
    R['desktopHover']={'quality':True,'capture':True};await settle('desktop-real-hover')
    canvas=frame.locator('#assembly-canvas');box=await canvas.bounding_box();iframe=await host.locator('#watch-viewer').bounding_box()
    x=box['x']+box['width']*.17;y=box['y']+box['height']*.35
    assert await frame.evaluate('p=>document.elementFromPoint(p.x,p.y)?.id',{'x':x-iframe['x'],'y':y-iframe['y']})=='assembly-canvas'
    before=await frame.evaluate(SNAP);await host.mouse.move(x,y);await host.mouse.down();await host.mouse.move(x+55,y+20,steps=10);await host.mouse.up()
    await frame.wait_for_function('a=>assemblyInspect().camera.some((v,i)=>Math.abs(v-a[i])>.00001)',arg=before['camera'],timeout=60000)
    after=await settle('desktop-real-mouse-orbit');R['desktopOrbit']={'before':before['camera'],'after':after['camera']};await activate('#home');await settle('desktop-orbit-reset')
   R['qualityCycles']=[]
   for quality in ['efficient','balanced','detail','studio','efficient']:
    await close_panel();await activate('.masthead button[data-mode="quality"]')
    target=frame.locator('#context [data-quality="'+quality+'"]');await target.wait_for(state='visible')
    assert await target.is_enabled()
    if MOBILE:await target.tap()
    else:await target.click()
    await frame.wait_for_function('q=>assemblyInspect().renderQuality===q',arg=quality,timeout=120000)
    await frame.wait_for_function('q=>[...document.querySelectorAll("#context [data-quality]")].find(e=>e.dataset.quality===q)?.getAttribute("aria-pressed")==="true"',arg=quality,timeout=30000)
    selected=await settle('quality-'+quality+'-selected');await close_panel();await capture('quality-'+quality+'-'+str(len(R['qualityCycles'])))
    behavior=await explode_reset('quality-'+quality,quality);assert behavior['qualityAfterReset']==R['initial']['renderQuality'],behavior
    R['qualityCycles'].append({'requested':quality,'selected':selected,'behavior':behavior})
   R['newNavigation']=R['navigation'][initial_nav:];R['newAssetRequests']=[r for r in R['requests'][initial_requests:]if r['url'].split('?')[0].endswith(('.glb','.gz','.bin'))]
   assert not R['newNavigation'];assert not R['newAssetRequests'],R['newAssetRequests']
   await capture('final-efficient');R['final']=await frame.evaluate(SNAP);assert not R['errors'];R['passed']=True
  except Exception as e:
   R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:
   (O/'report.json').write_text(json.dumps(R,indent=2))
   try:await host.screenshot(path=str(O/'final-page.png'),animations='disabled',timeout=30000)
   except Exception as e:R['finalScreenshotError']=repr(e);(O/'report.json').write_text(json.dumps(R,indent=2))
   await browser.close()
asyncio.run(asyncio.wait_for(main(),2000))
