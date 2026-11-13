"""Exact staged retry acceptance, software renderer; no physical-device timing claim."""
import asyncio,hashlib,json,os,pathlib,struct,time,traceback
from playwright.async_api import async_playwright
P=pathlib.Path('normal-retry-qa');O=pathlib.Path('normal-retry-evidence');O.mkdir(exist_ok=True)
RID=os.getenv('RETRY_RELEASE')or(P/'release-id.txt').read_text().strip()
BASE=f'http://127.0.0.1:8765/preview-b/releases/{RID}/atelier-preview.html'
FULL='bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585';LOW='5d8aa10702589424c1157d9a58a7f75aca265569d7c8fac09525a00af19455bc'
PROBE=b'''\nwindow.retryQA=()=>({detail:currentCaptureDetail(),controller:progressiveNormal?.snapshot(),state:progressiveNormalState,crownActive:crownInteraction.active||!!crownVisual?.active,warnings:loadWarnings.filter(x=>x==='Full-resolution leather normal unavailable'),stable:{camera:{p:camera.position.toArray(),t:controls.target.toArray(),zoom:camera.zoom},quality,explosion:explosion?.amount,crown:crownInteraction.snapshot(),geometry:craftParts.map(x=>x.geometry.uuid),normals:(leatherDetails?.meshes??[]).map(x=>{const m=finishMaterials.get(x)||x.material;return {name:m.name,scale:m.normalScale?.toArray()??null}}),origin:performance.timeOrigin},canvasSame:renderer.domElement===(window.__retryCanvas??=renderer.domElement)});'''
R={'release':RID,'stageRevision':os.getenv('GITHUB_SHA'),'scope':'Exact module with read-only appended probe, controlled HTTP503 faults; still-view softwareGPU QA.','cases':[]}
def save():(O/'report.json').write_text(json.dumps(R,indent=2))
async def ev(f,s):return await asyncio.wait_for(f.evaluate(s),180)
async def state(f,phase):
 end=time.monotonic()+240
 while time.monotonic()<end:
  s=await ev(f,'retryQA()')
  if s['state']==phase:return s
  await asyncio.sleep(.5)
 raise TimeoutError('Expected '+phase)
async def shot(page,name,timeout=180):await asyncio.wait_for(page.screenshot(path=str(O/(name+'.png')),timeout=timeout*1000),timeout)
async def layout(page,out,label):
 result=await page.locator('#context').evaluate("""p=>{const r=p.getBoundingClientRect();return {box:[r.x,r.y,r.width,r.height],viewport:[innerWidth,innerHeight],horizontal:p.scrollWidth>p.clientWidth+1,controls:[...p.querySelectorAll('button,input')].filter(x=>x.getClientRects().length).map(x=>({id:x.id,w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height}))}}""")
 x,y,w,h=result['box'];vw,vh=result['viewport'];assert x>=-1 and y>=-1 and x+w<=vw+1 and y+h<=vh+1,result
 assert not result['horizontal']and all(c['w']>=44 and c['h']>=44 for c in result['controls']),result
 out.setdefault('layouts',{})[label]=result
async def download(page,button,name):
 async with page.expect_download(timeout=180000)as pending:await page.locator(button).click(force=True)
 d=await pending.value;path=O/name;await d.save_as(path);assert await d.failure()is None;return path
async def run(browser,w,h):
 name=f'{w}x{h}';out={'name':name,'errors':[],'requests':[],'faults':[]};R['cases'].append(out);gate=asyncio.Event();ctx=await browser.new_context(viewport={'width':w,'height':h},is_mobile=True,has_touch=True,device_scale_factor=1,accept_downloads=True);page=await ctx.new_page();page.set_default_timeout(180000)
 async def module(route):
  if route.request.resource_type!='script':await route.continue_();return
  r=await route.fetch();b=await r.body();assert r.status==200;out['moduleSHA']=hashlib.sha256(b).hexdigest();await route.fulfill(response=r,body=b+PROBE)
 async def fault(route):
  if not route.request.headers.get('range'):await route.continue_();return
  n=len(out['faults'])+1;out['faults'].append({'attempt':n,'at':time.time(),'range':route.request.headers['range']});save()
  if n<=2:await route.fulfill(status=503,body='QA transient failure')
  else:await gate.wait();await route.continue_()
 await page.route('**/assembly-review.js*',module);await page.route('**/outer-normal-4k.ktx2.part0',fault)
 page.on('pageerror',lambda e:out['errors'].append(str(e)));page.on('request',lambda r:out['requests'].append({'url':r.url,'type':r.resource_type}))
 try:
  await page.goto(BASE,wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('!!window.retryQA',timeout=180000)
  initial=await state(page,'failed');assert initial['detail']['activeNormalIdentity']['sha256']==LOW and not initial['detail']['ready'];assert len(initial['warnings'])==1
  manifest=await(await ctx.request.get(BASE.replace('atelier-preview.html','deployment-manifest.json'))).json();assert out['moduleSHA']==next(x['sha256']for x in manifest['localFiles']if x['path']=='assembly-review.js')
  out['pause']=await ev(page,"""()=>{const read=()=>[document.getElementById('animate').checked,document.getElementById('animate-movement').checked];const before=read();if(before.some(Boolean))document.getElementById('play-motion').onclick();return {before,after:read()}}""")
  assert not any(out['pause']['after'])
  # Use actual exposed crown controls, then partial explosion. No pose injection.
  await page.locator('[data-mode=time]').first.click(force=True);await page.locator('#context [data-proxy=crown-right]').click(force=True);await page.wait_for_function('!retryQA().crownActive');await page.locator('#close').click(force=True)
  await page.locator('[data-mode=explode]').first.click(force=True);await page.locator('#atelier-explosion').evaluate("e=>{e.value='37';e.dispatchEvent(new Event('input',{bubbles:true}))}");await page.wait_for_function('Math.abs(retryQA().stable.explosion-.37)<.001');await page.locator('#close').click(force=True)
  await page.locator('[data-mode=capture]').first.click(force=True);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"');await layout(page,out,'failed');await shot(page,name+'-failed')
  for id in ['capture-scene','record-scene']:assert await page.locator(f'#context [data-proxy={id}]').is_disabled()
  assert await page.locator('#context [data-proxy=export-config]').is_enabled()
  p=await download(page,'#context [data-proxy=export-config]',name+'-pending.json');c=json.loads(p.read_text())['leatherCraft']['candidate'];assert c['normalIdentity']['sha256']==LOW and not c['detail']['ready'];out['pendingIdentity']=c['normalIdentity']
  before=await ev(page,'retryQA()');start=len(out['requests'])
  await page.locator('#atelier-retry-detail').click();second=await state(page,'failed');assert second['controller']['attempts']==2 and len(second['warnings'])==1;assert second['stable']==before['stable'];assert second['canvasSame']
  # DOM click honors disabled state; repeated user-equivalent click cannot restart.
  await page.locator('#atelier-retry-detail').evaluate('(b)=>{b.click();b.click();b.click()}');await page.wait_for_function('retryQA().state==="upgrading"');await asyncio.sleep(.2)
  pending=await ev(page,'retryQA()');assert pending['controller']['attempts']==3 and len(out['faults'])==3;assert pending['stable']==before['stable'];assert not pending['detail']['ready'];assert pending['detail']['activeNormalIdentity']['sha256']==LOW
  await layout(page,out,'pending')
  try:await shot(page,name+'-pending',30)
  finally:gate.set()
  full=await state(page,'full');assert full['detail']['ready']and full['detail']['activeNormalIdentity']['sha256']==FULL;assert full['stable']==before['stable']and full['canvasSame'];assert full['controller']['retainedLowBytes']==0 and full['controller']['attempts']==3 and not full['warnings'];assert len(out['faults'])==3
  assert not any(r['type']=='document'or r['url'].split('?')[0].endswith(('.glb','.glb.gz','/geometry.bin'))for r in out['requests'][start:])
  for id in ['capture-scene','record-scene']:assert await page.locator(f'#context [data-proxy={id}]').is_enabled()
  await layout(page,out,'full');await shot(page,name+'-full');out['final']=full
  if w<500:
   p=await download(page,'#context [data-proxy=capture-scene]',name+'-full.png');b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';at=8;configs=[]
   while at<len(b):
    n=struct.unpack('>I',b[at:at+4])[0];body=b[at+8:at+8+n]
    if b[at+4:at+8]==b'iTXt'and body.startswith(b'AerialView\0\0\0\0\0'):configs.append(json.loads(body[15:]))
    at+=n+12
   assert len(configs)==1;candidate=configs[0]['leatherCraft']['candidate'];assert candidate['normalIdentity']['sha256']==FULL and candidate['detail']['ready'];out['png']={'bytes':len(b),'identity':candidate['normalIdentity']}
  assert not out['errors'];out['passed']=True
 except Exception as e:out.update(passed=False,failure=repr(e),traceback=traceback.format_exc())
 finally:
  gate.set();save()
  try:await asyncio.wait_for(ctx.close(),20)
  except Exception as e:out['closeError']=repr(e)
  save()
async def main():
 selected=os.getenv('RETRY_VIEWPORT');sizes=[(430,932),(740,360)]
 if selected:sizes=[tuple(map(int,selected.split('x')))];assert sizes[0]in[(430,932),(740,360)]
 async with async_playwright()as p:
  for size in sizes:
   b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
   try:await run(b,*size)
   finally:
    try:await asyncio.wait_for(b.close(),20)
    except Exception as e:R.setdefault('closeErrors',[]).append(repr(e))
 R['passed']=all(c.get('passed')for c in R['cases']);save();assert R['passed'],R
asyncio.run(main())
