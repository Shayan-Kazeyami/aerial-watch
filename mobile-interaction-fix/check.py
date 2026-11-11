import asyncio, json, os, pathlib, traceback
from playwright.async_api import async_playwright
OUT=pathlib.Path(os.environ.get('QA_OUTPUT','mobile-panel-evidence'));OUT.mkdir(exist_ok=True)
URL=os.environ.get('WATCH_URL','https://shayan-kazeyami.github.io/aerial-watch/?quality=efficient')
STRICT=os.environ.get('QA_STRICT','1')=='1'
R={'url':URL,'strict':STRICT,'errors':[],'requests':[],'navigation':[],'steps':[]}
INIT='''(()=>{window.__panelQA={contexts:[],writes:[],observer:[],started:performance.timeOrigin};for(const k of ['width','height']){const d=Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype,k);Object.defineProperty(HTMLCanvasElement.prototype,k,{...d,set(v){window.__panelQA.writes.push({id:this.id,k,v,t:performance.now()});return d.set.call(this,v)}})}document.addEventListener('webglcontextlost',e=>window.__panelQA.contexts.push({type:'lost',id:e.target.id,t:performance.now()}),true);document.addEventListener('webglcontextrestored',e=>window.__panelQA.contexts.push({type:'restored',id:e.target.id,t:performance.now()}),true);})();'''
SNAP='''()=>{const c=document.getElementById('assembly-canvas'),s=document.getElementById('stage'),r=s.getBoundingClientRect();return {timeOrigin:performance.timeOrigin,url:location.href,canvas:[c.width,c.height],stage:[r.width,r.height,r.x,r.y],status:document.body.dataset.presentation,ready:document.body.dataset.ready,explosion:assemblyInspect().explosion,qa:window.__panelQA}}'''
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=3,is_mobile=True,has_touch=True)
  async def instrument(route):
   response=await route.fetch()
   await route.fulfill(response=response,body=(await response.text())+'\n'+pathlib.Path('mobile-interaction-fix/inventory-append.js').read_text())
  await page.route('**/assembly-review.js*',instrument)
  page.set_default_timeout(90000);await page.add_init_script(INIT)
  page.on('pageerror',lambda e:R['errors'].append(str(e)))
  page.on('request',lambda req:R['requests'].append({'url':req.url,'type':req.resource_type}))
  page.on('framenavigated',lambda f:R['navigation'].append(f.url))
  try:
   await page.goto(URL,wait_until='domcontentloaded',timeout=120000)
   frame=page.main_frame
   if await page.locator('#watch-viewer').count():
    await page.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000)
    frame=next(f for f in page.frames if f!=page.main_frame and 'atelier-preview' in f.url)
   await frame.locator('body[data-ready=true]').wait_for(timeout=300000)
   await frame.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"',timeout=300000)
   print('READY',flush=True)
   # Real CDP touch: stationary offset must keep turning; center/release stops.
   dot=frame.locator('.crown-hotspot')
   await dot.wait_for(state='visible')
   box=await dot.bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
   cdp=await page.context.new_cdp_session(page)
   async def touch(kind,points):await cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':points})
   await touch('touchStart',[{'x':x,'y':y}]);await touch('touchMove',[{'x':x,'y':y-22}])
   await page.wait_for_timeout(800);a=await frame.evaluate('__crownQA()')
   await asyncio.wait_for(frame.wait_for_function('__crownQA().hotspot.turns>'+str(a['hotspot']['turns']),timeout=15000),20)
   bstate=await frame.evaluate('__crownQA()')
   assert bstate['state']['degrees']>a['state']['degrees']+.1,(a,bstate)
   await touch('touchMove',[{'x':x,'y':y}])
   await frame.wait_for_function('__crownQA().hotspot.pointerMoves>=2',timeout=30000)
   center=await frame.evaluate('__crownQA()')
   await frame.wait_for_function('__crownQA().hotspot.updates>='+str(center['hotspot']['updates']+2),timeout=30000)
   stopped=await frame.evaluate('__crownQA()');assert abs(center['state']['degrees']-stopped['state']['degrees'])<.001
   await touch('touchEnd',[]);await page.wait_for_timeout(500)
   released=await frame.evaluate('__crownQA()');assert not released['hotspot']['dragging'];assert not released['state']['pulled'];assert abs(released['state']['degrees']-center['state']['degrees'])<.001
   print('HOLD PASS',flush=True)
   R['crownHold']={'first':a,'continued':bstate,'center':center,'released':released}
   targets=await frame.locator('.task-dock button').evaluate_all('(els)=>els.map(e=>({width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))')
   assert all(t['width']>=44 and t['height']>=44 for t in targets),targets
   assert not await frame.locator('.motion-tools').is_visible()
   (OUT/'assembled-inventory.json').write_text(json.dumps(await frame.evaluate('watchGeometryInventory()'),indent=2))
   await page.screenshot(path=str(OUT/'assembled.png'))
   R['initial']=await frame.evaluate(SNAP);R['initialRequests']=len(R['requests']);R['initialNavigation']=len(R['navigation'])
   async def settle(name):
    await frame.wait_for_timeout(400)
    # Real rendered frame after layout, no arbitrary success from DOM alone.
    await frame.evaluate('''()=>new Promise((resolve,reject)=>{let n=0;const start=performance.now();function tick(){if(++n>=2)return resolve();if(performance.now()-start>60000)return reject(new Error('frame timeout'));requestAnimationFrame(tick)}requestAnimationFrame(tick)})''')
    print('STEP',name,flush=True)
    s=await frame.evaluate(SNAP);R['steps'].append({'name':name,**s})
    assert s['timeOrigin']==R['initial']['timeOrigin'],f'{name}: document restarted'
    assert not s['qa']['contexts'],f'{name}: context loss'
    assert s['ready']=='true',f'{name}: readiness lost'
    if STRICT:assert s['canvas']==R['initial']['canvas'],f'{name}: drawing buffer resized {s["canvas"]}'
   for mode in ['inside','explode','time','capture','quality','settings','explore']:
    target=frame.locator(f'button[data-mode="{mode}"]:visible').first
    if not await target.count():target=frame.locator(f'[data-mode="{mode}"]').first
    await target.tap(force=True);await settle(mode)
    if mode=='explode':
     await frame.wait_for_function('assemblyInspect().explosion.amount>.1',timeout=60000)
     await settle('explode-moved')
     (OUT/'exploded-inventory.json').write_text(json.dumps(await frame.evaluate('watchGeometryInventory()'),indent=2))
     await page.screenshot(path=str(OUT/'exploded.png'))
     await frame.locator('#atelier-explosion').evaluate("e=>{e.value='37';e.dispatchEvent(new Event('input',{bubbles:true}))}")
     amount=await frame.evaluate('assemblyInspect().explosion.amount')
     assert abs(amount-.37)<.001, f'slider did not immediately follow input: {amount}'
    if mode!='explore' and await frame.locator('#close').is_visible():
     await frame.locator('#close').tap(force=True);await settle(mode+'-close')
   # Repeated interaction catches stale listeners and allocation churn.
   for i in range(3):
    await frame.locator('.task-dock [data-mode="explode"]').tap(force=True);await settle(f'repeat-explode-{i}')
    if await frame.locator('#close').is_visible():await frame.locator('#close').tap(force=True)
    await frame.locator('#home').tap(force=True);await settle(f'reset-{i}')
   R['newNavigation']=R['navigation'][R['initialNavigation']:]
   R['newRequests']=R['requests'][R['initialRequests']:]
   assert not R['newNavigation'],'unexpected document navigation'
   repeated=[r for r in R['newRequests'] if any(r['url'].split('?')[0].endswith(x) for x in ['.glb','.ktx2','.bin','.gz'])]
   assert not repeated,f'asset reloads: {repeated}'
   R['writesAfterReady']=[w for w in R['steps'][-1]['qa']['writes'] if w['t']>R['initial']['qa']['writes'][-1]['t']] if R['initial']['qa']['writes'] else R['steps'][-1]['qa']['writes']
   if STRICT:assert not [w for w in R['writesAfterReady'] if w['id']=='assembly-canvas'],'canvas dimension write during UI interaction'
   assert not R['errors'],R['errors'];R['passed']=True
  except Exception as e:
   R['passed']=False;R['failure']=repr(e);R['traceback']=traceback.format_exc()
   try:
    R['crownFailure']=await asyncio.wait_for(frame.evaluate('__crownQA()'),5)
    await asyncio.wait_for(cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}),5)
   except Exception:pass
   raise
  finally:
   try:await asyncio.wait_for(page.screenshot(path=str(OUT/'final.png')),15)
   except Exception:pass
   (OUT/'report.json').write_text(json.dumps(R,indent=2));print('MOBILE_PANEL_REPORT',json.dumps({k:v for k,v in R.items() if k not in ['requests','steps']}),flush=True);await asyncio.wait_for(b.close(),15)
asyncio.run(asyncio.wait_for(main(),480))
