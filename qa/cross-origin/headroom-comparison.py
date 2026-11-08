import asyncio,json,os,pathlib,traceback
from playwright.async_api import async_playwright
from PIL import Image
case=os.environ['CASE'];out=pathlib.Path('capture-headroom-output');out.mkdir(exist_ok=True);r={'case':case,'release':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','status':'starting','events':[],'errors':[]};save=lambda:(out/(case+'.json')).write_text(json.dumps(r,indent=2));save()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640},accept_downloads=True);r['browser']=b.version
  await c.add_init_script('''(()=>{window.__trace=(kind,detail={})=>console.log('CAPTURE_TRACE '+JSON.stringify({kind,detail,at:performance.now()}));for(const type of ['pointerdown','pointerup','click'])document.addEventListener(type,e=>{let b=e.target.closest?.('[data-proxy=capture-scene],#capture-scene');if(b)__trace('input-'+type,{target:b.id||b.dataset.proxy,trusted:e.isTrusted})},true);for(const type of ['atelier:request-capture-frame','atelier:capture-frame-rendered'])document.addEventListener(type,e=>{if(type==='atelier:request-capture-frame')window.__qaCaptureRequested=true;__trace(type,e.detail||{})},true);const create=URL.createObjectURL.bind(URL);URL.createObjectURL=(blob)=>{let u=create(blob);if(blob instanceof Blob&&blob.type.includes('png'))__trace('png-object-url',{size:blob.size,type:blob.type});return u};const click=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){if(this.download)__trace('download-anchor',{name:this.download,hrefScheme:this.href.split(':')[0]});return click.call(this)};const toBlob=HTMLCanvasElement.prototype.toBlob;HTMLCanvasElement.prototype.toBlob=function(cb,...args){__trace('canvas-toBlob-start',{width:this.width,height:this.height});return toBlob.call(this,b=>{__trace('canvas-toBlob-end',{size:b?.size||0,type:b?.type||null});cb(b)},...args)}})();''')
  page=await c.new_page();page.on('pageerror',lambda e:r['errors'].append(str(e)))
  def console(m):
   if m.text.startswith('CAPTURE_TRACE '):
    try:r['events'].append(json.loads(m.text[len('CAPTURE_TRACE '):]));save()
    except:pass
  page.on('console',console);scripts=[];page.on('request',lambda x:scripts.append(x.url) if 'assembly-review.js' in x.url else None)
  async def instrument(route):
   res=await route.fetch();s=await res.text();name=route.request.url.split('/')[-1].split('?')[0]
   if name=='atelier-preview.js':
    replacements=[("function closeContext(){", "function closeContext(){window.__trace('close-context',{hidden:$('context').hidden});"), ("function proxy(id){const t=liveTarget(id);", "function proxy(id){const t=liveTarget(id);if(id==='capture-scene')window.__trace('proxy-invoke',{id,live:!!t});"), ("async function captureAtFullStage(id){\n if(captureHandoffPending||!liveTarget(id))return;", "async function captureAtFullStage(id){\n window.__trace('capture-entry',{id,pending:captureHandoffPending,live:!!liveTarget(id),ready,legacyDisabled:$('capture-scene')?.disabled});\n if(captureHandoffPending||!liveTarget(id)){window.__trace('capture-early-return',{id,pending:captureHandoffPending,live:!!liveTarget(id)});return;}"), (" try{await waitForCaptureLayout();exportNoticeMessage=null;", " try{await waitForCaptureLayout();window.__trace('capture-layout-ready');exportNoticeMessage=null;"), (" catch(error){exportNoticeMessage=error.message;showExportNotice(exportNoticeMessage);", " catch(error){window.__trace('capture-layout-error',{message:error.message});exportNoticeMessage=error.message;showExportNotice(exportNoticeMessage);")]
    for old,new in replacements:assert s.count(old)==1,(name,old);s=s.replace(old,new)
    if case in ('baseline','candidate'):
     marker="window.addEventListener('pagehide',cancel,{once:true});document.addEventListener('atelier:capture-frame-rendered',rendered);";assert s.count(marker)==1;s=s.replace(marker,marker+"setTimeout(()=>{window.__trace('qa-stall-start');const until=performance.now()+11000;while(performance.now()<until){}window.__trace('qa-stall-end')},0);")
    if case in ('candidate','cancel'):
     marker="const timeout=setTimeout(()=>finish(new Error('The full watch view did not finish resizing. Please try again.')),10000);";assert s.count(marker)==1;s=s.replace(marker,marker.replace('10000','30000'))
   elif name=='assembly-review.js':
    s+='\nwindow.__proof=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot()});'
    if case=='cancel':
     marker='const requestCaptureFrame=event=>{';assert s.count(marker)==1;s=s.replace(marker,marker+"if(window.__qaHoldCaptureFrame){window.__trace('qa-frame-held');return;}")
    replacements=[("if($('capture-scene'))$('capture-scene').onclick=async()=>{", "if($('capture-scene'))$('capture-scene').onclick=async()=>{window.__trace('legacy-capture-entry',{crownActive:crownInteraction.active,visualActive:!!crownVisual?.active,pending:pendingCaptures.has('capture-scene')});"), ("const configuration=captureConfiguration({clockStamp:stamp}),blob=await captureCanvasPNG(renderer.domElement);", "window.__trace('capture-composer-rendered');const configuration=captureConfiguration({clockStamp:stamp}),blob=await captureCanvasPNG(renderer.domElement);window.__trace('capture-blob-created',{size:blob?.size||0});"), ("downloadBlob(await embedPNGConfiguration(blob,configuration),'aerial-studio.png');", "window.__trace('capture-embed-start');downloadBlob(await embedPNGConfiguration(blob,configuration),'aerial-studio.png');window.__trace('capture-download-requested');")]
    for old,new in replacements:assert s.count(old)==1,(name,old);s=s.replace(old,new)
   await route.fulfill(response=res,body=s)
  await page.route('**/atelier-preview.js*',instrument);await page.route('**/assembly-review.js*',instrument);q=None
  try:
   await page.goto('http://127.0.0.1:8766/qa/cross-origin/wrapper.html',wait_until='domcontentloaded');host=await (await page.query_selector('iframe')).content_frame();await host.wait_for_function("document.querySelector('#watch-viewer')?.contentWindow?.location.href.includes('atelier-preview.html')",timeout=60000);q=await (await host.query_selector('#watch-viewer')).content_frame();await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000);assert any(r['release'] in x for x in scripts);proof=await q.evaluate('__proof()');assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and proof['leather']['geometryVerification']['actualBytes']==8579970 and proof['hybrid']['active'] and proof['hybrid']['triangles']==501830;r['proof']=proof;r['origins']={'host':await page.evaluate('location.origin'),'viewer':await q.evaluate('location.origin')};assert r['origins']['host']!=r['origins']['viewer'];r['status']='ready';save()
   await q.locator('[data-mode=capture]').first.click(timeout=60000);await q.wait_for_function("!document.querySelector('[data-proxy=capture-scene]').disabled",timeout=90000);r['status']='capture-ready';save()
   if case=='cancel':
    await q.evaluate('window.__qaHoldCaptureFrame=true');await q.locator('[data-proxy=capture-scene]').click(timeout=60000);await q.wait_for_function('window.__qaCaptureRequested===true',timeout=90000);await q.locator('[data-mode=time]').first.click(timeout=60000)
    for _ in range(120):
     if any(e['kind']=='capture-layout-error' for e in r['events']):break
     await asyncio.sleep(.5)
    errors=[e for e in r['events'] if e['kind']=='capture-layout-error'];assert errors and 'another tool' in errors[-1]['detail']['message'];assert not any(e['kind'] in ('proxy-invoke','download-anchor') for e in r['events']);r['status']='passed'
   else:
    async with page.expect_download(timeout=180000) as d:await q.locator('[data-proxy=capture-scene]').click(timeout=60000)
    dl=await d.value;file=out/(case+'.png');await dl.save_as(file)
    with Image.open(file) as im:im.verify()
    with Image.open(file) as im:im.load();r['file']={'bytes':file.stat().st_size,'format':im.format,'dimensions':list(im.size),'mode':im.mode,'alpha':im.getchannel('A').getextrema() if 'A'in im.getbands() else None}
    r['status']='passed'
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
