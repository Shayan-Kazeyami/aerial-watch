import asyncio,json,hashlib,datetime,traceback
from pathlib import Path
from playwright.async_api import async_playwright
O=Path('live-poly-census/evidence');O.mkdir(parents=True,exist_ok=True)
RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
URL='https://shayan-kazeyami.github.io/aerial-watch/'
R={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':URL,'expectedRelease':RID,'readOnly':True,'errors':[],'requests':[],'methodology':{'sceneTriangles':'resident unique geometry triangles and instance-expanded resident; effective ancestor/material visibility + geometry groups/drawRange before frustum/occlusion culling','rendererTriangles':'Three renderer.info.render.triangles last frame, includes counted render passes, NOT unique visible mesh polygons','instrumentation':'Three devtools observe event target records constructor objects only; no route/source overlays or geometry mutation','device':'GitHub Actions Chromium SwiftShader software GPU; no user hardware/FPS claim'}}
INIT="""window.__censusObjects=[];window.__THREE_DEVTOOLS__=new EventTarget();window.__THREE_DEVTOOLS__.addEventListener('observe',e=>window.__censusObjects.push(e.detail));"""
CENSUS="""()=>{const s=assemblyInspect(),objects=window.__censusObjects||[],scenes=objects.filter(o=>o.isScene),renderers=objects.filter(o=>o.isWebGLRenderer);let scene=null,max=-1;for(const x of scenes){let count=0;x.traverse(o=>{if(o.isMesh)count++});if(count>max){scene=x;max=count}}if(!scene)throw Error('No observed scene');const all=[],geoms=new Set;let resident=0,unique=0,visible=0,visibleObjects=0;scene.traverse(o=>{if(!o.isMesh)return;const g=o.geometry,count=g.index?.count??g.attributes.position?.count??0,instances=o.isInstancedMesh?o.count:1,tri=count/3;resident+=tri*instances;if(!geoms.has(g)){geoms.add(g);unique+=tri}let effective=true;for(let p=o;p;p=p.parent)if(!p.visible)effective=false;let active=0;if(effective){const end=Math.min(count,g.drawRange.start+g.drawRange.count),start=g.drawRange.start;if(Array.isArray(o.material)){for(const group of g.groups){if(o.material[group.materialIndex]?.visible!==false)active+=Math.max(0,Math.min(end,group.start+group.count)-Math.max(start,group.start))/3}}else if(o.material?.visible!==false)active=Math.max(0,end-start)/3}if(active)visibleObjects++;visible+=active*instances;all.push({name:o.name,sourceIndex:o.userData.sourceIndex??null,assemblyId:o.userData.assemblyId??null,triangles:tri,instances,effectiveVisible:effective,visibleRangeTriangles:active*instances})});return {url:location.href,inspection:s,sceneMeshObjects:all.length,uniqueGeometryObjects:geoms.size,residentUniqueGeometryTriangles:unique,instanceExpandedResidentTriangles:resident,effectiveVisibleObjects:visibleObjects,effectiveVisibleRangeTrianglesBeforeCulling:visible,rendererInfo:renderers.map(r=>({render:{...r.info.render},memory:{...r.info.memory},canvas:[r.domElement.width,r.domElement.height]})),all,revisionScripts:[...document.scripts].map(x=>x.src),settings:[...document.querySelectorAll('input,select')].map(e=>({id:e.id,value:e.value,checked:e.checked})),observedSceneCounts:scenes.length,observedRendererCounts:renderers.length}}"""
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  context=await browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1,reduced_motion='reduce');await context.add_init_script(INIT)
  page=await context.new_page();page.on('pageerror',lambda e:R['errors'].append(str(e)));page.on('request',lambda req:R['requests'].append(req.url))
  try:
   resp=await page.goto(URL,wait_until='domcontentloaded',timeout=90000);R['navigationStatus']=resp.status
   await page.locator('#watch-viewer').wait_for(timeout=90000)
   # content_frame on locator is a FrameLocator in current Playwright.
   frame=page.frame_locator('#watch-viewer')
   await frame.locator('body[data-ready="true"]').wait_for(timeout=240000)
   f=next(x for x in page.frames if '/preview-b/releases/' in x.url);assert '/'+RID+'/' in f.url,f.url
   await f.wait_for_function('assemblyInspect().presentation.interactive&&!assemblyInspect().loading&&!assemblyInspect().failed',timeout=180000)
   await page.wait_for_timeout(3000)
   R['samples']=[]
   for i in range(3):
    R['samples'].append(await f.evaluate(CENSUS));await page.wait_for_timeout(500)
   R['runtimeSource']=await f.evaluate("async()=>{const u=new URL('./assembly-review.js?v=atelier-local-1',location.href);const r=await fetch(u);const b=await r.arrayBuffer();return {url:u.href,status:r.status,sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('')}}")
   R['viewport']={'width':1440,'height':1000,'deviceScaleFactor':1,'reducedMotion':'reduce'}
   R['browserVersion']=browser.version
   R['complete']=True;assert not R['errors'],R['errors']
   (O/'report.json').write_text(json.dumps(R,indent=2))
   try:
    import base64
    cdp=await context.new_cdp_session(page)
    shot=await asyncio.wait_for(cdp.send('Page.captureScreenshot',{'format':'png','fromSurface':True,'captureBeyondViewport':False}),60)
    (O/'live-default.png').write_bytes(base64.b64decode(shot['data']));R['screenshotSaved']=True
   except Exception as e:R['screenshotSaved']=False;R['screenshotFailure']=repr(e)
  except Exception as e:R['complete']=False;R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:
   R['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();(O/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps({k:v for k,v in R.items() if k not in ['requests','samples']},indent=2),flush=True);await browser.close()
asyncio.run(main())
