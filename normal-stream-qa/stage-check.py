"""Actual immutable release defaults/export gate. No candidate module substitution.
CPU/software-rendered browser evidence only, not physical-device timings.
Run a static server serving the checked-out repository on 127.0.0.1:8765 first.
"""
import asyncio,hashlib,json,pathlib,struct,traceback,time,os
from playwright.async_api import async_playwright
from PIL import Image
P=pathlib.Path('normal-stream-qa');O=pathlib.Path('normal-stream-stage-evidence');O.mkdir(exist_ok=True)
RID='5de340263d2bcb0a992914d7b0aa64176493934711907480b62bcad07bd486ca'
BASE=f'http://127.0.0.1:8765/preview-b/releases/{RID}/atelier-preview.html'
FULL='bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585';LOW='5d8aa10702589424c1157d9a58a7f75aca265569d7c8fac09525a00af19455bc'
R={'release':RID,'setup':'Staged immutable viewer; Chromium SwiftShader; fresh contexts. Not physical-device performance or public-site verification. Probe appended to actual script response only; no source substitution.','cases':[]}
INIT="""window.__stageQADimWrites=[];for(const k of ['width','height']){const d=Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype,k);Object.defineProperty(HTMLCanvasElement.prototype,k,{...d,set(v){if(this.id==='assembly-canvas')window.__stageQADimWrites.push({k,v});return d.set.call(this,v)}})}"""
SNAP="""()=>{const c=document.getElementById('assembly-canvas');window.__stageQACanvas??=c;const r=c.getBoundingClientRect();return {sameCanvas:c===window.__stageQACanvas,css:[r.x,r.y,r.width,r.height],buffer:[c.width,c.height],writes:window.__stageQADimWrites.length,timeOrigin:performance.timeOrigin}}"""
def png_config(path):
 data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';at=8;found=[]
 while at<len(data):
  size=struct.unpack('>I',data[at:at+4])[0];kind=data[at+4:at+8];body=data[at+8:at+8+size];assert at+12+size<=len(data)
  prefix=b'AerialView\0\0\0\0\0'
  if kind==b'iTXt' and body.startswith(prefix):found.append(json.loads(body[len(prefix):]))
  at+=12+size
 assert len(found)==1,'Expected exactly one embedded AerialView config'
 with Image.open(path)as image:assert image.width>0 and image.height>0;image.verify()
 return found[0]
def assert_identity(config,sha,width,ready):
 c=config['leatherCraft']['candidate'];n=c['normalIdentity'];assert n['sha256']==sha and n['width']==width and n['verified'],n
 assert c['detail']['ready'] is ready,c['detail'];assert c['detail']['requestedNormalIdentity']['sha256']==FULL
async def evaluate(page,expression,*args):
 return await asyncio.wait_for(page.evaluate(expression,*args),180)
async def download(page,button,name):
 async with page.expect_download(timeout=180000)as pending:await evaluate(page,'(id)=>document.getElementById(id).onclick()',button)
 d=await pending.value;path=O/name;await d.save_as(path);assert await d.failure() is None;return path
def flush():
 (O/'report.json').write_text(json.dumps(R,indent=2))
async def checkpoint(page,out,label):
 item={'label':label,'at':time.time()};out['steps'].append(item);flush();print(out['name'],label,flush=True)
 try:item['snapshot']=await asyncio.wait_for(page.evaluate('window.normalQA?.snapshot()'),10)
 except Exception as e:item['snapshotError']=repr(e)
 flush()
async def wait_full(page,out):
 deadline=time.monotonic()+240
 while time.monotonic()<deadline:
  sample_started=time.monotonic();state=await asyncio.wait_for(page.evaluate('normalQA.snapshot()'),min(90,max(1,deadline-time.monotonic())));out.setdefault('upgradeSnapshotDurationsMs',[]).append((time.monotonic()-sample_started)*1000)
  out['lastUpgradeSnapshot']=state;out['lastUpgradeSnapshotAt']=time.time();flush()
  if state['state']=='full':return
  assert state['state']!='failed',state
  await asyncio.sleep(2)
 raise TimeoutError('Full adoption not reached within 240 seconds; see lastUpgradeSnapshot')
async def case(browser,name,query,mobile,progressive,switch_only=False):
 context=await browser.new_context(viewport=({'width':320,'height':568}if switch_only and not name.endswith('-large') else{'width':430,'height':932})if mobile else{'width':740,'height':480},device_scale_factor=1,is_mobile=mobile,has_touch=mobile,accept_downloads=True)
 page=await context.new_page();page.set_default_timeout(180000);await page.add_init_script(INIT)
 out={'name':name,'errors':[],'moduleHashes':[],'requests':[],'navigations':[],'downloads':[],'console':[],'requestFailures':[],'steps':[],'cleanupErrors':[]};R['cases'].append(out);gate=asyncio.Event()
 async def module(route):
  if route.request.resource_type!='script':await route.continue_();return
  response=await route.fetch(timeout=180000);assert response.status==200;source=await response.body();out['moduleHashes'].append({'url':route.request.url,'sha256':hashlib.sha256(source).hexdigest()});await route.fulfill(response=response,body=source+b'\n'+(P/'probe.js').read_bytes())
 await page.route('**/assembly-review.js*',module)
 if progressive:
  async def hold_upgrade(route):
   out['gateRequestedAt']=time.time();flush()
   await gate.wait();out['gateContinuedAt']=time.time();flush()
   try:await route.continue_()
   except Exception as e:out['gateError']=repr(e);flush()
  await page.route('**/outer-normal-4k.ktx2.part1',hold_upgrade)
 page.on('console',lambda m:out['console'].append({'at':time.time(),'type':m.type,'text':m.text}));page.on('requestfailed',lambda q:out['requestFailures'].append({'at':time.time(),'url':q.url,'failure':q.failure}));page.on('response',lambda r:out.setdefault('upgradeResponses',[]).append({'at':time.time(),'url':r.url,'status':r.status})if 'outer-normal-4k.ktx2.part' in r.url else None)
 page.on('pageerror',lambda e:out['errors'].append(str(e)));page.on('request',lambda q:out['requests'].append({'url':q.url,'range':q.headers.get('range'),'type':q.resource_type}));page.on('framenavigated',lambda f:out['navigations'].append(f.url));page.on('download',lambda d:out['downloads'].append(d.suggested_filename))
 try:
  await checkpoint(page,out,'before-navigation')
  await page.goto(BASE+query,wait_until='domcontentloaded',timeout=180000);await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('window.normalQA&&document.querySelector("#stage").dataset.cameraReady==="true"',timeout=180000)
  await checkpoint(page,out,'ready')
  out['effectiveURL']=page.url;out['initial']=await evaluate(page,'normalQA.snapshot()');state=out['initial'];params=await evaluate(page,'Object.fromEntries(new URL(location.href).searchParams)');out['params']=params
  assert state['quality']==('efficient'if mobile else'studio'),state['quality'];assert params.get('normalStream')==('1'if progressive else'0'if name.startswith('explicit-zero')else None),params
  manifest=await (await context.request.get(BASE.rsplit('/',1)[0]+'/deployment-manifest.json')).json();entry=next(x for x in manifest['localFiles']if x['path']=='assembly-review.js');assert all(x['sha256']==entry['sha256']for x in out['moduleHashes']),out['moduleHashes']
  if progressive:
   await checkpoint(page,out,'before-pending-checks')
   await page.wait_for_function('normalQA.snapshot().state==="upgrading"');assert state['detail']['installedDetail']=='initial',state
   if not switch_only:
    pending_path=await download(page,'export-config','pending-view.json');pending=json.loads(pending_path.read_text());assert_identity(pending,LOW,2048,False);out['pendingConfigIdentity']=pending['leatherCraft']['candidate']
    # Real handler attempts must not download unfinished PNG/video. Configuration
    # remains available and honest. No encoder stubs are needed for these refusals.
    count=len(out['downloads']);await evaluate(page,'document.getElementById("capture-scene").onclick()');await evaluate(page,'document.getElementById("record-scene").onclick()');assert len(out['downloads'])==count
   await checkpoint(page,out,'pending-checks-complete')
   before=await evaluate(page,SNAP);nav=len(out['navigations']);start=len(out['requests'])
   if switch_only:
    for quality in ['detail','efficient']:
     await checkpoint(page,out,'before-quality-'+quality)
     await evaluate(page,"q=>{const e=document.getElementById('render-quality');e.value=q;e.dispatchEvent(new Event('change',{bubbles:true}))}",quality);await evaluate(page,'normalQA.frames(2)');current=await evaluate(page,SNAP);assert current['sameCanvas']and current['css']==before['css']and current['timeOrigin']==before['timeOrigin'],(before,current)
    settled=await evaluate(page,SNAP);assert settled['buffer']==before['buffer'];assert len(out['navigations'])==nav
    assert not any(x['type']=='document'or x['url'].split('?')[0].endswith(('.glb','.glb.gz','/geometry.bin'))for x in out['requests'][start:]),out['requests'][start:]
    out['qualitySwitch']={'before':before,'afterExplicitChanges':settled,'note':'Drawing-buffer changes from deliberate quality selection are expected; CSS extent and canvas identity must remain stable.'}
   else:settled=before
   await checkpoint(page,out,'before-gate-release')
   out['gateReleasedAt']=time.time()
   gate.set();await wait_full(page,out);await evaluate(page,'normalQA.frames(2)');adopted=await evaluate(page,SNAP);assert adopted==settled,(settled,adopted);out['upgradeCanvasStable']=True
  else:
   assert state['state']=='disabled'and state['detail']['ready'],state;assert state['detail']['activeNormalIdentity']['sha256']==FULL;assert not any(x['range']for x in out['requests']if 'outer-normal-4k.ktx2.part'in x['url'])
   if switch_only:
    before=await evaluate(page,SNAP);nav=len(out['navigations']);start=len(out['requests'])
    for quality in ['detail','efficient']:
     await checkpoint(page,out,'before-quality-'+quality)
     await evaluate(page,"q=>{const e=document.getElementById('render-quality');e.value=q;e.dispatchEvent(new Event('change',{bubbles:true}))}",quality);await evaluate(page,'normalQA.frames(2)');current=await evaluate(page,SNAP);assert current['sameCanvas']and current['css']==before['css']and current['timeOrigin']==before['timeOrigin'],(before,current)
    settled=await evaluate(page,SNAP);assert settled['buffer']==before['buffer'];assert len(out['navigations'])==nav
    assert not any(x['type']=='document'or x['url'].split('?')[0].endswith(('.glb','.glb.gz','/geometry.bin'))for x in out['requests'][start:]),out['requests'][start:]
    out['qualitySwitch']={'before':before,'afterExplicitChanges':settled,'note':'Drawing-buffer changes from deliberate quality selection are expected; CSS extent and canvas identity must remain stable.'}
  await checkpoint(page,out,'full-adopted')
  out['final']=await evaluate(page,'normalQA.freeze()');assert out['final']['detail']['ready'];assert out['final']['detail']['activeNormalIdentity']['sha256']==FULL
  if progressive and not switch_only:
   await checkpoint(page,out,'before-full-exports')
   await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=180000)
   path=await download(page,'capture-scene','full-detail.png');configuration=png_config(path);assert_identity(configuration,FULL,4096,True);out['png']={'bytes':path.stat().st_size,'identity':configuration['leatherCraft']['candidate'],'dimensions':list(Image.open(path).size)}
   path=await download(page,'export-config','full-detail-view.json');configuration=json.loads(path.read_text());assert_identity(configuration,FULL,4096,True);out['fullConfigIdentity']=configuration['leatherCraft']['candidate']
  await checkpoint(page,out,'checks-complete')
  assert not out['errors'],out['errors'];out['passed']=True;print('PASS',name,flush=True)
 except Exception as e:
  out['passed']=False;out['failure']=repr(e);out['traceback']=traceback.format_exc()
  await checkpoint(page,out,'failure-final-state')
  try:await asyncio.wait_for(page.screenshot(path=str(O/(name+'-failure.png'))),15)
  except Exception as screenshot_error:out['screenshotError']=repr(screenshot_error)
  raise
 finally:
  gate.set();flush()
  try:await asyncio.wait_for(context.close(),20)
  except Exception as close_error:out['cleanupErrors'].append(repr(close_error))
  flush()
async def main():
 cases=[('quality-switch-large','?qa=stage-quality-switch-large',True,True,True),
        ('explicit-zero-switch-large','?normalStream=0&qa=stage-direct-switch-large',True,False,True),
        ('default-smooth','?qa=stage-default-smooth',True,True,False),
        ('explicit-zero-switch-small','?normalStream=0&qa=stage-direct-switch',True,False,True),
        ('quality-switch-small','?qa=stage-quality-switch',True,True,True),
        ('explicit-zero','?normalStream=0&qa=stage-full-first',True,False,False),
        ('default-studio','?qa=stage-default-studio',False,False,False)]
 selected=os.environ.get('STAGE_CASE')
 if selected:
  cases=[x for x in cases if x[0]==selected];assert cases,'Unknown STAGE_CASE'
 async with async_playwright()as p:
  for args in cases:
   browser=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
   try:await case(browser,*args)
   except Exception as e:R.setdefault('caseFailures',[]).append({'name':args[0],'error':repr(e)})
   finally:
    flush()
    try:await asyncio.wait_for(browser.close(),20)
    except Exception as e:R.setdefault('browserCloseErrors',[]).append({'name':args[0],'error':repr(e)})
    flush()
 R['passed']=len(R['cases'])==len(cases)and all(x.get('passed')for x in R['cases']);flush()
 print(json.dumps({'passed':R['passed'],'cases':[(x['name'],x.get('passed',False))for x in R['cases']]}),flush=True)
 assert R['passed'],'One or more staged cases failed; see report.json'
asyncio.run(main())
