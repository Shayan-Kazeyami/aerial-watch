import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('watch-bevel-output');build=json.loads((O/'build.json').read_text());C=pathlib.Path(build['releasePath']);C=C.relative_to(pathlib.Path.cwd()) if C.is_absolute() else C
HOOK=r'''
window.__contextQA={
 focus(name){view(name);},
 snapshot(){return {crown:crownInteraction.snapshot(),interior:interiorView,cameraMoving:!!cameraTween,controls:controls.enabled}},
 target(id){
  const mesh=exterior.find(m=>m.userData.assemblyId===id);if(!mesh)return null;
  scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
  const r=renderer.domElement.getBoundingClientRect(),box=new THREE.Box3().setFromObject(mesh),points=[];
  for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){const p=new THREE.Vector3(x,y,z).project(camera);points.push({x:r.left+(p.x+1)*r.width/2,y:r.top+(1-p.y)*r.height/2})}
  const minX=Math.max(r.left+2,Math.min(...points.map(p=>p.x))),maxX=Math.min(r.right-2,Math.max(...points.map(p=>p.x))),minY=Math.max(r.top+2,Math.min(...points.map(p=>p.y))),maxY=Math.min(r.bottom-2,Math.max(...points.map(p=>p.y)));
  const candidates=[...meshes(),...craftParts,...openPlates,...(premiumFace?.meshes||[])].filter(m=>{if(!m.visible||m.userData.inspectionTransparent)return false;for(let p=m.parent;p;p=p.parent)if(!p.visible)return false;return true});
  for(const fx of [.5,.4,.6,.3,.7,.2,.8,.1,.9])for(const fy of [.5,.4,.6,.3,.7,.2,.8,.1,.9]){const x=minX+(maxX-minX)*fx,y=minY+(maxY-minY)*fy,ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((x-r.left)/r.width*2-1,-(y-r.top)/r.height*2+1),camera);const hit=ray.intersectObjects(candidates,false)[0];if(hit?.object===mesh)return {x,y,id,name:mesh.name}}
  return {missing:true,id,bounds:{minX,maxX,minY,maxY}};
 }
};
'''
# qa.py already created separate instrumented files; add read-only diagnostic targets and ordinary camera command.
p=C/'qa-review.js';p.write_text(p.read_text()+'\n'+HOOK)
async def main():
 report={'scope':'Actual sealed app modules through separate QA entry; real mesh raycasts and Playwright pointer/touch input; software rendering only.','checks':[],'errors':[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  async def ready(context):
   page=await context.new_page();page.set_default_timeout(60000);page.on('pageerror',lambda e:report['errors'].append(str(e)));await page.goto(f'http://127.0.0.1:8765/{C}/qa-atelier.html?quality=efficient',wait_until='domcontentloaded');await page.wait_for_function('window.__contextQA && window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().presentation.interactive',timeout=240000);return page
  async def target(page,part,view):
   await page.evaluate('(name)=>__contextQA.focus(name)',view);await page.wait_for_function('!__contextQA.snapshot().cameraMoving',timeout=30000);await page.wait_for_timeout(250);point=await page.evaluate('(id)=>__contextQA.target(id)',part);assert point and not point.get('missing'),point;return point
  try:
   context=await browser.new_context(viewport={'width':1000,'height':800},device_scale_factor=1);page=await ready(context);card=page.locator('.watch-object-actions')
   point=await target(page,'CROWN','crown');await page.mouse.move(point['x'],point['y']);await card.wait_for(state='visible',timeout=15000);assert await card.locator('strong').inner_text()=='Crown';report['checks'].append({'check':'real crown hover','target':point});await page.screenshot(path=str(O/'context-crown-hover.png'),timeout=180000)
   await card.get_by_role('button',name='Pull out · set time',exact=True).click();await page.wait_for_function('__contextQA.snapshot().crown.pulled');await card.wait_for(state='hidden');report['checks'].append({'check':'crown pull action','state':await page.evaluate('__contextQA.snapshot()')})
   point=await target(page,'CROWN','crown');await page.mouse.move(point['x']+2,point['y']);await page.mouse.move(point['x'],point['y']);await card.wait_for(state='visible',timeout=15000);assert await card.get_by_role('button',name='Push crown in',exact=True).count()==1;await page.keyboard.press('Escape');await card.wait_for(state='hidden');report['checks'].append({'check':'Escape hides card'})
   # Touching ordinary blank canvas begins orbit without exposing object actions.
   canvas=page.locator('#assembly-canvas');rect=await canvas.bounding_box();x=rect['x']+rect['width']*.2;y=rect['y']+rect['height']*.2;await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+80,y+40,steps=5);assert not await card.is_visible();await page.mouse.up();assert not await card.is_visible();report['checks'].append({'check':'orbit drag suppresses card'})
   point=await target(page,'CASE','lug');await page.mouse.move(point['x'],point['y']);await card.wait_for(state='visible',timeout=15000);await card.get_by_role('button',name='Look inside',exact=True).click();await page.wait_for_function('__contextQA.snapshot().interior');report['checks'].append({'check':'case look-inside action','target':point});await page.screenshot(path=str(O/'context-case-action.png'),timeout=180000)
   await context.close()
   touch=await browser.new_context(viewport={'width':430,'height':850},device_scale_factor=1,is_mobile=True,has_touch=True);page=await ready(touch);card=page.locator('.watch-object-actions');point=await target(page,'CROWN','crown');await page.touchscreen.tap(point['x'],point['y']);await card.wait_for(state='visible',timeout=15000);assert await card.locator('strong').inner_text()=='Crown';bounds=await card.bounding_box();assert bounds['x']>=0 and bounds['x']+bounds['width']<=430 and bounds['y']>=0 and bounds['y']+bounds['height']<=850,bounds;await page.screenshot(path=str(O/'context-touch-crown.png'),timeout=180000);await card.get_by_role('button',name='Pull out · set time',exact=True).tap();await page.wait_for_function('__contextQA.snapshot().crown.pulled');report['checks'].append({'check':'touch tap and crown action','target':point,'cardBounds':bounds});await touch.close()
   assert not report['errors'],report['errors'];report['passed']=True
  except Exception as e:
   report['passed']=False;report['failure']=repr(e);raise
  finally:
   (O/'contextual-qa-report.json').write_text(json.dumps(report,indent=2));await browser.close()
asyncio.run(main())
