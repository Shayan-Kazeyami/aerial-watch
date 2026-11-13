import asyncio,json,pathlib,traceback
from playwright.async_api import async_playwright
P=pathlib.Path('compact-explode-qa');O=pathlib.Path('compact-explode-evidence');O.mkdir(exist_ok=True);R={'errors':[],'cases':[],'requests':[],'navigation':[]}
INIT='''window.__dimensionWrites=[];for(const k of ['width','height']){const d=Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype,k);Object.defineProperty(HTMLCanvasElement.prototype,k,{...d,set(v){window.__dimensionWrites.push({id:this.id,k,v});return d.set.call(this,v)}})}'''
SNAP='''()=>{const c=document.querySelector('#assembly-canvas');return {canvas:[c.width,c.height],box:JSON.stringify(c.getBoundingClientRect()),writes:window.__dimensionWrites.length,origin:performance.timeOrigin}}'''
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':430,'height':932},is_mobile=True,has_touch=True,device_scale_factor=1);page.set_default_timeout(90000);await page.add_init_script(INIT)
  for name in ['atelier-preview.js','atelier-preview.css']:
   async def patch(route,n=name):await route.fulfill(status=200,body=(P/n).read_bytes(),content_type='text/css' if n.endswith('css') else 'text/javascript')
   await page.route('**/'+name,patch)
  page.on('pageerror',lambda e:R['errors'].append(str(e)));page.on('request',lambda q:R['requests'].append(q.url));page.on('framenavigated',lambda f:R['navigation'].append(f.url))
  try:
   await page.goto('http://127.0.0.1:8765/?quality=efficient',wait_until='domcontentloaded');await page.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000);f=next(f for f in page.frames if 'atelier-preview' in f.url);await f.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000);print('READY',flush=True)
   requests=len(R['requests']);nav=len(R['navigation'])
   for w,h in [(430,932),(360,800),(932,430),(740,360),(1440,1000)]:
    await page.set_viewport_size({'width':w,'height':h});await f.wait_for_timeout(1500);await f.locator('#home').tap(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating');before=await f.evaluate(SNAP)
    await f.locator('.task-dock [data-mode=explode]').tap(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating');after=await f.evaluate(SNAP);assert before==after,(before,after)
    panel=await f.locator('#context').bounding_box();assert w>1050 or panel['height']<=130.5,panel
    assert await f.locator('#context').evaluate('e=>e.scrollHeight<=e.clientHeight+1')
    labels=await f.locator('#context-title,#atelier-explosion-value,#close').evaluate_all('(es)=>es.map(e=>{let r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})')
    if w<=1050:
     assert labels[0]['x']+labels[0]['w']<=labels[1]['x']+1,labels
     assert labels[1]['x']+labels[1]['w']<=labels[2]['x']+1,labels
    controls=await f.locator('#context button:visible,#context input:visible').evaluate_all('(es)=>es.map(e=>{let r=e.getBoundingClientRect();return {id:e.id,w:r.width,h:r.height,left:r.left,right:r.right,top:r.top,bottom:r.bottom}})');assert all(c['w']>=44 and c['h']>=44 for c in controls),controls;assert all(c['left']>=0 and c['right']<=w and c['top']>=0 and c['bottom']<=h for c in controls),controls
    rng=f.locator('#atelier-explosion');await rng.focus();await rng.press('Home');assert await f.evaluate('assemblyInspect().explosion.amount')==0;await rng.press('ArrowRight');assert abs(await f.evaluate('assemblyInspect().explosion.amount')-.01)<.001;await rng.press('End');assert await f.evaluate('assemblyInspect().explosion.amount')==1
    await rng.evaluate("e=>{e.value='37';e.dispatchEvent(new Event('input',{bubbles:true}))}");assert abs(await f.evaluate('assemblyInspect().explosion.amount')-.37)<.001
    await f.locator('#atelier-reassemble').tap(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating');await f.locator('#atelier-explode-full').tap(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
    await page.screenshot(path=str(O/f'{w}-exploded.png'),animations='disabled');await f.locator('#close').click(force=True);assert await f.locator('.task-dock [data-mode=explode]').evaluate('e=>document.activeElement===e');assert await f.locator('#context').is_hidden();await f.locator('.task-dock [data-mode=explode]').tap(force=True);await f.locator('#close').click(force=True)
    final=await f.evaluate(SNAP);assert final==before,(final,before);R['cases'].append({'viewport':[w,h],'panel':panel,'controls':controls,'canvasStable':True,'keyboardRange':True,'actions':True,'closeFocus':True});print('PASS',w,h,flush=True)
   assert len(R['navigation'])==nav;assert not [u for u in R['requests'][requests:]if u.split('?')[0].endswith(('.glb','.gz','.bin','.ktx2'))];assert not R['errors'];R['passed']=True
  except Exception as e:
   R['passed']=False;R['failure']=repr(e);R['traceback']=traceback.format_exc()
   try:await asyncio.wait_for(page.screenshot(path=str(O/'failure.png')),15)
   except:pass
   raise
  finally:
   (O/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps({k:v for k,v in R.items()if k not in ['requests','navigation']}),flush=True)
   try:await asyncio.wait_for(b.close(),15)
   except:pass
asyncio.run(run())
