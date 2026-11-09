import asyncio,json,pathlib,base64
from playwright.async_api import async_playwright
O=pathlib.Path('watch-crown-dot-output');C=pathlib.Path(json.loads((O/'build.json').read_text())['releasePath']);C=C.relative_to(pathlib.Path.cwd()) if C.is_absolute() else C;B=pathlib.Path('preview-b/releases/457c5eba8f27ffecf7710adc2fb3ef10a2ac326af781f19232fad75328dc2bd4')
HOOK=r'''
window.__dotQA={
 pause(){stopTour();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();dirty=true},focus(){view('crown')},redraw(){dirty=true},
 snapshot(){return {crown:crownInteraction.snapshot(),camera:camera.position.toArray(),target:controls.target.toArray(),moving:!!cameraTween,stage:renderer.domElement.getBoundingClientRect().toJSON(),mode:document.body.dataset.mode,metrics:window.__dotMetrics,hotspot:typeof crownHotspot==='undefined'?null:crownHotspot.snapshot()}},
 center(){const mesh=exterior.find(m=>m.userData.assemblyId==='CROWN'),p=new THREE.Box3().setFromObject(mesh).getCenter(new THREE.Vector3()).project(camera),r=renderer.domElement.getBoundingClientRect();return {x:r.left+(p.x+1)*r.width/2,y:r.top+(1-p.y)*r.height/2}},
 resetMetrics(){__dotMetrics.calls=0;__dotMetrics.ms=0;__dotMetrics.updateCalls=0;__dotMetrics.updateMs=0}
};
window.__dotMetrics={calls:0,ms:0,updateCalls:0,updateMs:0};
const origRay=THREE.Raycaster.prototype.intersectObjects;THREE.Raycaster.prototype.intersectObjects=function(...args){const t=performance.now();try{return origRay.apply(this,args)}finally{__dotMetrics.calls++;__dotMetrics.ms+=performance.now()-t}};
if(typeof crownHotspot!=='undefined'){const update=crownHotspot.update;crownHotspot.update=()=>{const t=performance.now();try{return update()}finally{__dotMetrics.updateCalls++;__dotMetrics.updateMs+=performance.now()-t}};}
'''
for root in [B,C]:
 (root/'qa-review.js').write_text((root/'assembly-review.js').read_text().replace('composer.render();','composer.render();window.__dotFrames=(window.__dotFrames||0)+1;')+'\n'+HOOK);(root/'qa-atelier.js').write_text((root/'atelier-preview.js').read_text().replace('./assembly-review.js?v=atelier-local-1','./qa-review.js'));(root/'qa-atelier.html').write_text((root/'atelier-preview.html').read_text().replace('atelier-preview.js','qa-atelier.js'))
async def main():
 report={'checks':[],'profiles':[],'errors':[],'scope':'Fresh desktop/mobile visual and touch follow-up. Desktop gesture/performance gates already passed in42625881793 and42627185699; same sealed release. SwiftShader, not physical FPS.'}
 async with async_playwright() as p:
  browser=None
  async def fresh(root,mobile=False):
   nonlocal browser
   if browser:await browser.close()
   browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);context=await browser.new_context(viewport={'width':430 if mobile else 1000,'height':850 if mobile else 800},device_scale_factor=1,is_mobile=mobile,has_touch=mobile);page=await context.new_page();page.set_default_timeout(45000);page.on('pageerror',lambda e:report['errors'].append(str(e)));await page.goto(f'http://127.0.0.1:8765/{root}/qa-atelier.html?quality=efficient',wait_until='domcontentloaded');await page.wait_for_function('window.__dotQA && assemblyInspect().presentation.interactive',timeout=240000);await page.evaluate('__dotQA.pause();__dotQA.focus()');await page.wait_for_function('!__dotQA.snapshot().moving',timeout=45000);return page,context
  async def shot(page,name):
   await page.evaluate('__dotQA.pause()');await page.wait_for_timeout(2000);frames=await page.evaluate('window.__dotFrames||0');await page.evaluate('__dotQA.redraw()');await page.wait_for_function('(f)=>(window.__dotFrames||0)>f',arg=frames,timeout=60000);await page.screenshot(path=str(O/name),timeout=90000)
  def record(name,data=None):report['checks'].append({'check':name,'data':data});print(name,json.dumps(data),flush=True);(O/'qa-report.json').write_text(json.dumps(report,indent=2))
  try:
   page,context=await fresh(C,True);dot=page.locator('.crown-hotspot');await dot.wait_for(state='visible');rect=await dot.bounding_box();x=rect['x']+22;y=rect['y']+22;before=await page.evaluate('__dotQA.snapshot()');await page.touchscreen.tap(x,y);await page.wait_for_function('__dotQA.snapshot().crown.pulled');assert before['stage']==(await page.evaluate('__dotQA.snapshot()'))['stage'];record('touch tap pulls without panel resize')
   old=await page.evaluate('__dotQA.snapshot().crown.degrees');session=await context.new_cdp_session(page);await session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});
   for dy in [6,12,18,24]:await session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-dy}]})
   await session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});await page.wait_for_function('(d)=>Math.abs(__dotQA.snapshot().crown.degrees-d)>1',arg=old);state=await page.evaluate('__dotQA.snapshot()');assert state['crown']['pulled'];record('touch drag turns without toggling',state['crown']);await page.wait_for_timeout(800);assert not report['errors'],report['errors'];await shot(page,'mobile-dot.png');record('settled mobile visual captured');report['passed']=True
  except Exception as e:report['passed']=False;report['failure']=repr(e);raise
  finally:(O/'qa-report.json').write_text(json.dumps(report,indent=2));await browser.close()
asyncio.run(main())
