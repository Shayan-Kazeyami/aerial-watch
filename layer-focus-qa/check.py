import asyncio,json,os,pathlib,time,traceback,hashlib
from playwright.async_api import async_playwright
P=pathlib.Path('layer-focus-qa');O=pathlib.Path('layer-focus-evidence');O.mkdir(exist_ok=True)
RID=(P/'release-id.txt').read_text().strip();W,H=map(int,os.getenv('FOCUS_VIEWPORT','430x932').split('x'))
BASE=f'http://127.0.0.1:8765/preview-b/releases/{RID}/atelier-preview.html'
R={'release':RID,'revision':os.getenv('GITHUB_SHA'),'viewport':[W,H],'errors':[],'scope':'SwiftShader functional and visual evidence, not physical-device performance'}
PROBE='''\nwindow.layerQA=()=>{const all=[];model.traverse(m=>{if(m.isMesh)all.push(m)});const members=id=>all.filter(m=>{if(assemblyExplosionLayer(m)?.id!==id)return false;for(let p=m;p;p=p.parent)if(!p.visible)return false;return true});return {focus:layerFocus?.snapshot(),detail:currentCaptureDetail(),safe:layerFocusFrameOptions(),camera:{p:camera.position.toArray(),q:camera.quaternion.toArray(),t:controls.target.toArray(),zoom:camera.zoom},ready:!loading&&!failed&&!cameraTween&&!explosion?.animating,amount:explosion?.amount,quality,canvasSame:renderer.domElement===(window.__layerCanvas??=renderer.domElement),timeOrigin:performance.timeOrigin,parts:all.map(m=>({id:m.uuid,source:m.userData.sourceIndex??null,visible:m.visible,position:m.position.toArray(),rotation:m.quaternion.toArray(),scale:m.scale.toArray(),geometry:m.geometry.uuid,material:(Array.isArray(m.material)?m.material:[m.material]).map(x=>x.uuid)})),projections:Object.fromEntries(['plate','keyless','train','bridges','balance','calendar'].map(id=>{const points=[];for(const m of members(id)){m.geometry.computeBoundingBox();const b=m.geometry.boundingBox;for(const x of[b.min.x,b.max.x])for(const y of[b.min.y,b.max.y])for(const z of[b.min.z,b.max.z])points.push(new THREE.Vector3(x,y,z).applyMatrix4(m.matrixWorld).project(camera).toArray())}return[id,points]}))};};'''
# Import read-only classifier into the instrumented module, matching the actual release dependency.
PROBE="\nimport {assemblyExplosionLayer} from './assembly-explode.js';"+PROBE
save=lambda:(O/'report.json').write_text(json.dumps(R,indent=2))
async def ev(p,s):return await asyncio.wait_for(p.evaluate(s),180)
async def settle(p):
 end=time.monotonic()+90;prev=None;count=0
 while time.monotonic()<end:
  await ev(p,'new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');s=await ev(p,'layerQA()')
  count=count+1 if s['ready'] and prev and s['camera']==prev['camera'] else 0
  if count>=2:return s
  prev=s;await asyncio.sleep(.25)
 raise TimeoutError('Camera did not settle exactly')
def invariant(s):return [{k:v for k,v in p.items()if k!='visible'}for p in s['parts']]
def area(points):
 return(max(p[0]for p in points)-min(p[0]for p in points))*(max(p[1]for p in points)-min(p[1]for p in points))
async def shot(p,n):await p.screenshot(path=str(O/(n+'.png')),timeout=180000)
async def layout(p):
 return await ev(p,"""(()=>{const r=document.querySelector('#context').getBoundingClientRect(),s=document.querySelector('#stage').getBoundingClientRect();return {panel:[r.x,r.y,r.width,r.height],stage:[s.x,s.y,s.width,s.height],overflow:document.documentElement.scrollWidth>innerWidth+1,targets:[...document.querySelectorAll('#context button,#context input,#context select')].filter(x=>x.getClientRects().length).map(x=>({id:x.id,w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height}))}})()""")
async def main():
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=await b.new_context(viewport={'width':W,'height':H},device_scale_factor=2,is_mobile=True,has_touch=True);page=await ctx.new_page();page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)));requests=[];page.on('request',lambda r:requests.append(r.url));gate=asyncio.Event()
  async def route(r):
   response=await r.fetch();body=await response.body();expected=json.loads(pathlib.Path(f'preview-b/releases/{RID}/deployment-manifest.json').read_text());entry=next(f for f in expected['localFiles']if f['path']=='assembly-review.js');assert hashlib.sha256(body).hexdigest()==entry['sha256'];R['executedModuleSHA']=entry['sha256'];await r.fulfill(response=response,body=body+PROBE.encode())
  async def delay_upgrade(r):
   if r.request.headers.get('range'):await gate.wait()
   await r.continue_()
  await page.route('**/outer-normal-4k.ktx2.part0',delay_upgrade)
  await page.route('**/assembly-review.js*',route)
  try:
   await page.goto(BASE,wait_until='domcontentloaded');await page.wait_for_function('window.layerQA&&window.assemblyInspect?.().presentation.interactive',timeout=240000)
   await page.locator('[data-mode=explode]').first.click(force=True);before=await settle(page);assert before['amount']==1;R['before']=before;R['layout']=await layout(page);assert not R['layout']['overflow'];assert all(t['w']>=44 and t['h']>=44 for t in R['layout']['targets']);await shot(page,'overview');start=len(requests)
   R['layers']={}
   for id in ['plate','keyless','train','bridges','balance','calendar']:
    await page.locator('#atelier-layer-focus').select_option(id);s=await settle(page);assert s['focus']['selected']==id;assert invariant(s)==invariant(before);assert s['amount']==1 and s['canvasSame']and s['quality']==before['quality']
    points=s['projections'][id];ratio=area(points)/area(before['projections'][id]);assert ratio>=2,(id,ratio)
    rect=s['safe'].get('rect',{'left':0,'top':0,'right':1,'bottom':1});assert all(rect['left']<=(v[0]+1)/2<=rect['right'] and rect['top']<=(1-v[1])/2<=rect['bottom'] and -1<=v[2]<=1 for v in points),(id,'outside safe rectangle',rect)
    R['layers'][id]={'ratio':ratio,'state':s};save()
    if id in ['train','balance']:await shot(page,id)
   # Material adoption must not resurrect hidden nonmembers or reset the user's view.
   pending=await settle(page);assert not pending['detail']['ready'];gate.set();await page.wait_for_function('layerQA().detail.ready',timeout=180000);upgraded=await settle(page);R['upgradeWhileFocused']={'before':pending,'after':upgraded};assert upgraded['focus']['selected']==pending['focus']['selected'];assert upgraded['camera']==pending['camera'];assert [x['visible']for x in upgraded['parts']]==[x['visible']for x in pending['parts']]
   await shot(page,'full-detail-focused')
   await page.locator('#atelier-layer-overview').click();back=await settle(page);R['overviewReturn']=back;assert back['camera']==before['camera'];assert back['parts']==before['parts'];assert back['amount']==before['amount'];assert await page.locator('#atelier-layer-focus').evaluate('e=>e===document.activeElement')
   await page.locator('#atelier-layer-focus').select_option('balance');await settle(page)
   await page.set_viewport_size({'width':H,'height':W});rotated=await settle(page);R['rotated']=rotated;await shot(page,'rotated-focus');assert rotated['focus']['selected']=='balance';assert invariant(rotated)==invariant(before)
   await page.locator('[data-mode=capture]').first.click(force=True);left=await settle(page);assert not left['focus']['selected'];assert left['parts']==before['parts'];R['leaveFocus']=True
   await page.locator('[data-mode=explode]').first.click(force=True);await page.locator('#atelier-reassemble').click();assembled=await settle(page);assert assembled['amount']==0 and not assembled['focus']['selected'];assert invariant(assembled)==invariant(before);R['reassembled']=True
   assert not any(u.split('?')[0].endswith(('.glb','.glb.gz','/geometry.bin'))for u in requests[start:]);assert not R['errors'];R['passed']=True
  except Exception as e:
   R.update(passed=False,error=repr(e),traceback=traceback.format_exc())
   try:R['failureState']=await ev(page,'layerQA()');await shot(page,'failure')
   except Exception as e:R['diagnosticError']=repr(e)
  finally:gate.set();save();await ctx.close();await b.close()
 if not R.get('passed'):raise SystemExit(1)
asyncio.run(main())
