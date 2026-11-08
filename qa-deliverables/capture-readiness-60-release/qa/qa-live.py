import asyncio,json,os,pathlib,traceback,hashlib
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from PIL import Image
BASE=pathlib.Path(__file__).resolve().parent
def fixture_path(p):return p.resolve().relative_to(pathlib.Path.cwd().resolve()).as_posix()
CANCEL_RESPONSIVENESS_LIMIT_MS=30000 # Intentional stricter cancellation gate, not the runtime readiness deadline (60000 ms).
case=os.environ['CASE'];assert case in ['native','cross-origin-1','cross-origin-2','cross-origin-3','cancel']
receipt=json.loads(pathlib.Path(os.environ.get('RELEASE_RECEIPT','capture-readiness-60-output/sealed-release.json')).read_text())
root=receipt['releasePath'];rid=receipt['releaseId'];assert root=='preview-b/releases/'+rid
manifest=json.loads((pathlib.Path(root)/'deployment-manifest.json').read_text());assert manifest['releaseId']==rid
expected={f['path']:f['sha256'] for f in manifest['localFiles']}
modules=['atelier-preview.js','assembly-review.js','assembly-resolution.js','assembly-render-pipeline.js','assembly-overscan.js']
assert expected['atelier-preview.js']=='9fa6ab550905e783fcc515b6764fa5ce92043d00035083d0865b1a8eb93516c1'
homeURL='https://shayan-kazeyami.github.io/aerial-watch/?quality=efficient&leather=craft14'
wrapper=BASE/'generated-live-wrapper.html';wrapper.write_text('<!doctype html><meta charset="utf-8"><title>Cross-origin capture gate</title><div style="width:100%;height:min(850px,85vh);min-height:480px;background:#111616"><iframe title="Watch host" style="display:block;width:100%;height:100%;border:0" src="'+homeURL.replace('&','&amp;')+'" allowfullscreen></iframe></div>')
out=pathlib.Path('capture-readiness-60-live-output');out.mkdir(exist_ok=True)
r={'case':case,'mode':'live','homeURL':homeURL,'release':rid,'status':'starting','events':[],'errors':[],'modules':{},'scope':'Actual public default release in Efficient quality under Chromium SwiftShader; native PNG, controlled cross-origin stall and cancellation. Not default-Studio capture, real receiving-host integration, hardware, FPS or guaranteed reliability.'}
save=lambda:(out/(case+'.json')).write_text(json.dumps(r,indent=2));save()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640},accept_downloads=True);r['browser']=b.version
  await c.add_init_script('''(()=>{window.__trace=(kind,detail={})=>console.log('CAPTURE_TRACE '+JSON.stringify({kind,detail,at:performance.now()}));for(const type of ['pointerdown','pointerup','click'])document.addEventListener(type,e=>{let b=e.target.closest?.('[data-proxy=capture-scene],#capture-scene,[data-mode=time]');if(b)__trace('input-'+type,{target:b.id||b.dataset.proxy||b.dataset.mode,trusted:e.isTrusted})},true);for(const type of ['atelier:request-capture-frame','atelier:capture-frame-rendered'])document.addEventListener(type,e=>{if(type==='atelier:request-capture-frame')window.__qaCaptureRequested=true;__trace(type,e.detail||{})},true);const create=URL.createObjectURL.bind(URL);URL.createObjectURL=(blob)=>{let u=create(blob);if(blob instanceof Blob&&blob.type.includes('png'))__trace('png-object-url',{size:blob.size,type:blob.type});return u};const click=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){if(this.download)__trace('download-anchor',{name:this.download,hrefScheme:this.href.split(':')[0]});return click.call(this)};const toBlob=HTMLCanvasElement.prototype.toBlob;HTMLCanvasElement.prototype.toBlob=function(cb,...args){__trace('canvas-toBlob-start',{width:this.width,height:this.height});return toBlob.call(this,b=>{__trace('canvas-toBlob-end',{size:b?.size||0,type:b?.type||null});cb(b)},...args)}})();''')
  page=await c.new_page();page.on('pageerror',lambda e:r['errors'].append(str(e)))
  def console(m):
   if m.text.startswith('CAPTURE_TRACE '):
    try:r['events'].append(json.loads(m.text[len('CAPTURE_TRACE '):]));save()
    except:pass
  page.on('console',console);scripts=[];page.on('request',lambda x:scripts.append(x.url) if 'assembly-review.js' in x.url else None)
  async def instrument(route):
   res=await route.fetch();raw=await res.body();s=raw.decode();name=urlparse(route.request.url).path.split('/')[-1]
   digest=hashlib.sha256(raw).hexdigest();assert digest==expected[name],(name,digest,expected[name]);assert '/'+root+'/' in route.request.url;r['modules'][name]={'sha256':digest,'url':route.request.url}
   if name=='atelier-preview.js':
    replacements=[("function closeContext(){", "function closeContext(){window.__trace('close-context',{hidden:$('context').hidden});"), ("function proxy(id){const t=liveTarget(id);", "function proxy(id){const t=liveTarget(id);if(id==='capture-scene')window.__trace('proxy-invoke',{id,live:!!t});"), ("async function captureAtFullStage(id){\n if(captureHandoffPending||!liveTarget(id))return;", "async function captureAtFullStage(id){\n window.__trace('capture-entry',{id,pending:captureHandoffPending,live:!!liveTarget(id),ready,legacyDisabled:$('capture-scene')?.disabled});\n if(captureHandoffPending||!liveTarget(id)){window.__trace('capture-early-return',{id,pending:captureHandoffPending,live:!!liveTarget(id)});return;}"), (" try{await waitForCaptureLayout();exportNoticeMessage=null;", " try{await waitForCaptureLayout();window.__trace('capture-layout-ready');exportNoticeMessage=null;"), (" catch(error){exportNoticeMessage=error.message;showExportNotice(exportNoticeMessage);", " catch(error){window.__trace('capture-layout-error',{message:error.message});exportNoticeMessage=error.message;showExportNotice(exportNoticeMessage);")]
    for old,new in replacements:assert s.count(old)==1,(name,old);s=s.replace(old,new)
    if case.startswith('cross-origin-'):
     marker="window.addEventListener('pagehide',cancel,{once:true});document.addEventListener('atelier:capture-frame-rendered',rendered);";assert s.count(marker)==1;s=s.replace(marker,marker+"setTimeout(()=>{window.__trace('qa-stall-start');const until=performance.now()+11000;while(performance.now()<until){}window.__trace('qa-stall-end')},0);")
   elif name=='assembly-review.js':
    s+='\nwindow.__proof=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot()});'
    if case=='cancel':
     marker='const requestCaptureFrame=event=>{';assert s.count(marker)==1;s=s.replace(marker,marker+"if(window.__qaHoldCaptureFrame){window.__trace('qa-frame-held');return;}")
    replacements=[("if($('capture-scene'))$('capture-scene').onclick=async()=>{", "if($('capture-scene'))$('capture-scene').onclick=async()=>{window.__trace('legacy-capture-entry',{crownActive:crownInteraction.active,visualActive:!!crownVisual?.active,pending:pendingCaptures.has('capture-scene')});"), ("const configuration=captureConfiguration({clockStamp:stamp}),blob=await captureCanvasPNG(renderer.domElement);", "window.__trace('capture-composer-rendered');const configuration=captureConfiguration({clockStamp:stamp}),blob=await captureCanvasPNG(renderer.domElement);window.__trace('capture-blob-created',{size:blob?.size||0});"), ("downloadBlob(await embedPNGConfiguration(blob,configuration),'aerial-studio.png');", "window.__trace('capture-embed-start');downloadBlob(await embedPNGConfiguration(blob,configuration),'aerial-studio.png');window.__trace('capture-download-requested');")]
    for old,new in replacements:assert s.count(old)==1,(name,old);s=s.replace(old,new)
   await route.fulfill(response=res,body=s)
  for name in modules:await page.route('**/'+name+'*',instrument)
  q=None
  try:
   if case=='native':
    await page.goto(homeURL,wait_until='domcontentloaded',timeout=90000);host=page
   else:
    await page.goto('http://127.0.0.1:8766/'+fixture_path(wrapper),wait_until='domcontentloaded',timeout=90000)
    outer=await page.wait_for_selector('iframe',state='attached',timeout=60000);assert outer
    host=await outer.content_frame();assert host
   await host.wait_for_selector('#watch-viewer',timeout=90000)
   assert urlparse(host.url).scheme=='https' and urlparse(host.url).netloc=='shayan-kazeyami.github.io' and urlparse(host.url).path=='/aerial-watch/'
   r['homepageURL']=host.url;r['iframeEntry']=await host.locator('#watch-viewer').get_attribute('src');save()
   q=await (await host.query_selector('#watch-viewer')).content_frame();assert q
   await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000)
   assert urlparse(q.url).scheme=='https' and urlparse(q.url).netloc=='shayan-kazeyami.github.io' and urlparse(q.url).path=='/aerial-watch/'+root+'/atelier-preview.html'
   assert rid in r['iframeEntry'] and any(rid in x for x in scripts)
   r['quality']=await q.evaluate('assemblyInspect().renderQuality');assert r['quality']=='efficient'
   proof=await q.evaluate('__proof()');assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and proof['leather']['geometryVerification']['actualBytes']==8579970 and proof['hybrid']['active'] and proof['hybrid']['triangles']==501830
   r['proof']=proof;r['origins']={'host':await page.evaluate('location.origin'),'homepage':await host.evaluate('location.origin'),'viewer':await q.evaluate('location.origin')};r['frameURLs']=[f.url for f in page.frames]
   assert (r['origins']['host']!=r['origins']['viewer'])==(case!='native')
   assert set(r['modules'])==set(modules);r['status']='ready';save()
   await q.locator('[data-mode=capture]').first.click(timeout=60000);await q.wait_for_function("!document.querySelector('[data-proxy=capture-scene]').disabled",timeout=90000);r['status']='capture-ready';save()
   if case=='cancel':
    await q.evaluate('window.__qaHoldCaptureFrame=true');box=await q.locator('[data-mode=time]').first.bounding_box(timeout=60000);assert box;r['timeButtonBox']=box;save();await q.locator('[data-proxy=capture-scene]').click(timeout=60000);await asyncio.wait_for(page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2),30)
    for _ in range(120):
     if any(e['kind']=='capture-layout-error' for e in r['events']):break
     await asyncio.sleep(.5)
    errors=[e for e in r['events'] if e['kind']=='capture-layout-error'];assert errors and 'another tool' in errors[-1]['detail']['message'];assert not any(e['kind'] in ('proxy-invoke','download-anchor','png-object-url') for e in r['events']);clicks=[e for e in r['events'] if e['kind']=='input-click' and e['detail'].get('target')=='time' and e['detail'].get('trusted')];assert clicks;entries=[e for e in r['events'] if e['kind']=='capture-entry'];assert entries;r['heldFrameObserved']=any(e['kind']=='qa-frame-held' for e in r['events']);r['cancelPhase']='pending layout, before proxy/export';r['cancelLatencyMS']=errors[-1]['at']-clicks[-1]['at'];assert 0<=r['cancelLatencyMS']<CANCEL_RESPONSIVENESS_LIMIT_MS;r['status']='passed'
   else:
    async with page.expect_download(timeout=180000) as d:await q.locator('[data-proxy=capture-scene]').click(timeout=60000)
    dl=await d.value;file=out/(case+'.png');await dl.save_as(file)
    with Image.open(file) as im:im.verify()
    with Image.open(file) as im:im.load();r['file']={'bytes':file.stat().st_size,'format':im.format,'dimensions':list(im.size),'mode':im.mode,'alpha':im.getchannel('A').getextrema() if 'A'in im.getbands() else None}
    requests=[e for e in r['events'] if e['kind']=='atelier:request-capture-frame'];acks=[e for e in r['events'] if e['kind']=='atelier:capture-frame-rendered'];ready=[e for e in r['events'] if e['kind']=='capture-layout-ready'];assert requests and acks and ready
    matching=[a for a in acks if any(x['detail']['requestId']==a['detail']['requestId'] for x in requests) and a['at']<=ready[-1]['at']];assert matching;ack=matching[-1];assert ack['detail']['dimensions'][2:]==r['file']['dimensions'];r['matchingFrameAck']=ack
    if case.startswith('cross-origin-'):
     starts=[e for e in r['events'] if e['kind']=='qa-stall-start'];ends=[e for e in r['events'] if e['kind']=='qa-stall-end'];assert len(starts)==len(ends)==1;assert ends[0]['at']-starts[0]['at']>=11000;r['controlledStallMS']=ends[0]['at']-starts[0]['at']
    r['status']='passed'
   assert not r['errors']
  except Exception as e:
   r['status']='failed';r['exception']=repr(e);r['traceback']=traceback.format_exc()
   if q:
    try:r['diagnostics']=await asyncio.wait_for(q.evaluate('''()=>({status:document.getElementById('status').textContent,viewerStatus:document.getElementById('viewer-status').textContent,contextHidden:document.getElementById('context').hidden,button:document.querySelector('[data-proxy=capture-scene]')?.outerHTML})'''),20)
    except Exception as ex:r['diagnosticError']=repr(ex)
  finally:save()
  try:await asyncio.wait_for(c.close(),15)
  except:pass
  try:await asyncio.wait_for(b.close(),15)
  except:pass
asyncio.run(main())
if r['status']!='passed':raise SystemExit(1)
