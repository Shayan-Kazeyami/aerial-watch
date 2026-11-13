"""Exact immutable candidate iframe/matchMedia gate, not a public-site or phone benchmark.
Serve candidate root on127.0.0.1:8765. A read-only probe is appended to the
actual assembly module; no source substitution or forced default quality.
"""
import asyncio,hashlib,json,os,pathlib,time,traceback
from playwright.async_api import async_playwright
P=pathlib.Path('landscape-budget-qa');O=pathlib.Path('landscape-budget-evidence');O.mkdir(exist_ok=True)
BASELINE='5de340263d2bcb0a992914d7b0aa64176493934711907480b62bcad07bd486ca'
RID='fad7fffe84d3b72678dc0cfc7864c18e6bf779b4da88bb40d11aefedddcbb91c'
PROBE=b'''\nwindow.landscapeQA=()=>({quality,profile:qualityProfiles[quality],ao:ao.enabled,shadows:renderer.shadowMap.enabled,bloom:bloom.enabled,pixelRatio:renderer.getPixelRatio(),normalStream:new URL(location.href).searchParams.get('normalStream'),canvas:[renderer.domElement.width,renderer.domElement.height],origin:performance.timeOrigin});'''
R={'baselineMain':'8363a039','baselineRelease':BASELINE,'candidateRelease':RID,'candidateDefaultsSHA256':hashlib.sha256((P/'atelier-defaults.js').read_bytes()).hexdigest(),'stageRevision':os.getenv('GITHUB_SHA'),'scope':'Exact immutable candidate root iframe + actual matchMedia; read-only probe only. Software GPU; no physical-device speed claim. Desktop/explicit Studio verify initialized policy without waiting for expensive completed rendering.','cases':[]}
def save():(O/'report.json').write_text(json.dumps(R,indent=2))
async def ev(frame,expression,arg=None):return await asyncio.wait_for(frame.evaluate(expression,arg),90)
async def run_case(browser,name,width,height,touch,query,expected,stream,render=False):
 out={'name':name,'viewport':[width,height],'touch':touch,'errors':[],'requests':[],'navigations':[],'console':[],'startedAt':time.time()};R['cases'].append(out)
 ctx=await browser.new_context(viewport={'width':width,'height':height},is_mobile=touch,has_touch=touch,device_scale_factor=1);page=await ctx.new_page();page.set_default_timeout(90000)
 async def instrument(route):
  if route.request.resource_type!='script':await route.continue_();return
  response=await route.fetch();source=await response.body();assert response.status==200
  out['assemblyModule']={'url':route.request.url,'sha256':hashlib.sha256(source).hexdigest()}
  await route.fulfill(response=response,body=source+PROBE)
 await page.route('**/assembly-review.js*',instrument)
 page.on('pageerror',lambda e:out['errors'].append(str(e)));page.on('request',lambda r:out['requests'].append({'url':r.url,'type':r.resource_type}));page.on('framenavigated',lambda f:out['navigations'].append(f.url));page.on('console',lambda m:out['console'].append({'type':m.type,'text':m.text}))
 try:
  await page.goto('http://127.0.0.1:8765/'+query,wait_until='domcontentloaded',timeout=180000)
  await page.frame_locator('#watch-viewer').locator('body').wait_for()
  f=next(f for f in page.frames if 'atelier-preview' in f.url);assert RID in f.url,f.url
  await f.wait_for_function('!!window.landscapeQA',timeout=300000)
  out['iframeURL']=f.url;out['media']=await ev(f,"({coarse:matchMedia('(pointer:coarse)').matches,width:innerWidth,height:innerHeight})")
  assert out['media']=={'coarse':touch,'width':width,'height':height},out['media']
  state=await ev(f,'landscapeQA()');out['initial']=state
  assert state['quality']==expected and state['normalStream']==stream,state
  assert state['ao']==(expected!='efficient')and state['shadows']==(expected!='efficient'),state
  assert state['bloom']==(expected=='studio'),state
  manifest=await(await ctx.request.get(f.url.split('atelier-preview.html')[0]+'deployment-manifest.json')).json()
  entry=next(x for x in manifest['localFiles']if x['path']=='assembly-review.js');assert entry['sha256']==out['assemblyModule']['sha256']
  defaults=await(await ctx.request.get(f.url.split('atelier-preview.html')[0]+'atelier-defaults.js')).body();assert hashlib.sha256(defaults).hexdigest()==R['candidateDefaultsSHA256']
  out['defaultsSHA256']=hashlib.sha256(defaults).hexdigest();out['policyPassed']=True;save()
  if render:
   await f.locator('body[data-ready=true]').wait_for(timeout=300000)
   await f.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=240000)
   before=await ev(f,"()=>{window.__landscapeCanvas=document.getElementById('assembly-canvas');return landscapeQA()}")
   # Real quality control: deliberate Balanced must survive both rotations.
   await f.locator('[data-mode=quality]').first.click(force=True)
   await f.locator('#context [data-quality=balanced]').click(force=True)
   await f.locator('#close').click(force=True)
   assert(await ev(f,'landscapeQA()'))['quality']=='balanced'
   count=len(out['requests']);nav=len(out['navigations'])
   out['rotations']=[]
   for w,h in [(height,width),(width,height)]:
    await page.set_viewport_size({'width':w,'height':h});await f.wait_for_function('innerWidth===%d&&innerHeight===%d'%(w,h))
    state=await ev(f,'landscapeQA()');out['rotations'].append(state)
    assert state['quality']=='balanced'and state['origin']==before['origin']and state['normalStream']==stream,state
    assert await ev(f,"document.getElementById('assembly-canvas')===window.__landscapeCanvas")
   assert len(out['navigations'])==nav
   assert not any(r['type']=='document'or r['url'].split('?')[0].endswith(('.glb','.glb.gz','/geometry.bin'))for r in out['requests'][count:])
   out['rotationPassed']=True
   await asyncio.wait_for(page.screenshot(path=str(O/(name+'.png'))),45)
  assert not out['errors'],out['errors'];out['passed']=True
 except Exception as e:
  out['passed']=False;out['failure']=repr(e);out['traceback']=traceback.format_exc()
  try:out['lastState']=await asyncio.wait_for(f.evaluate('window.landscapeQA?.()'),10)
  except Exception as diagnostic:out['diagnosticFailure']=repr(diagnostic)
 finally:
  out['finishedAt']=time.time();save()
  try:await asyncio.wait_for(ctx.close(),20)
  except Exception as e:out['closeError']=repr(e)
  save()
async def main():
 cases=[('touch-landscape',932,430,True,'?qa=landscape-default','efficient','1',True),('touch-portrait',430,932,True,'?qa=portrait-default','efficient','1',True),('fine-desktop',1440,800,False,'?qa=desktop-default','studio',None,False),('touch-explicit-studio',932,430,True,'?quality=studio&qa=explicit-studio','studio',None,False),('touch-explicit-zero',932,430,True,'?normalStream=0&qa=explicit-zero','efficient','0',False)]
 selected=os.getenv('LANDSCAPE_CASE')
 if selected:cases=[x for x in cases if x[0]==selected];assert cases,'Unknown LANDSCAPE_CASE'
 async with async_playwright()as p:
  for case in cases:
   b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
   try:await run_case(b,*case)
   finally:
    try:await asyncio.wait_for(b.close(),20)
    except Exception as e:R.setdefault('closeErrors',[]).append(repr(e))
    save()
 R['passed']=len(R['cases'])==len(cases)and all(c.get('passed')for c in R['cases']);save();print(json.dumps({'passed':R['passed'],'cases':[(c['name'],c.get('passed'))for c in R['cases']]}),flush=True);assert R['passed']
asyncio.run(main())
