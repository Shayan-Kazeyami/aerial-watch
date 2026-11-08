import asyncio,json,os,pathlib,traceback,time
from playwright.async_api import async_playwright
case=os.environ['CASE'];out=pathlib.Path('quality-triage-output');out.mkdir(exist_ok=True);r={'case':case,'release':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','events':[],'checks':[],'errors':[]};save=lambda:(out/(case+'.json')).write_text(json.dumps(r,indent=2));save()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640});r['browser']=b.version
  await c.add_init_script('''(()=>{window.__trace=(kind,detail={})=>console.log('QUALITY_TRACE '+JSON.stringify({kind,detail,at:performance.now()}));document.addEventListener('click',e=>{let x=e.target.closest?.('[data-quality],[data-mode=quality]');if(x)__trace('input-click',{quality:x.dataset.quality||null,mode:x.dataset.mode||null,trusted:e.isTrusted})},true);document.addEventListener('change',e=>{if(e.target.id==='render-quality')__trace('quality-change',{value:e.target.value})},true)})();''')
  page=await c.new_page();page.on('pageerror',lambda e:r['errors'].append(str(e)))
  def console(m):
   if m.text.startswith('QUALITY_TRACE '):
    try:r['events'].append(json.loads(m.text[len('QUALITY_TRACE '):]));save()
    except Exception:pass
  page.on('console',console);requests=[];page.on('request',lambda req:requests.append(req.url) if 'assembly-review.js' in req.url else None)
  async def instrument(route):
   res=await route.fetch();s=await res.text();old='function renderingQuality(name) {';assert s.count(old)==1;s=s.replace(old,old+"\n  window.__trace('quality-handler-start',{name});")
   for token,tag in [("  parametricCase?.setTextureQuality?.(name,renderer.capabilities.getMaxAnisotropy());",'texture'),("  quality=name; $('render-quality').value=name;",'set-quality'),("  if(!profile.shadows && key.shadow.map) { key.shadow.map.dispose(); key.shadow.map=null; }",'targets'),("  renderedFrames=0; frameWindow=performance.now(); resize();",'resize')]:
    assert s.count(token)==1,tag;s=s.replace(token,"  window.__trace('quality-phase-before',{name,phase:'"+tag+"'});\n"+token+"\n  window.__trace('quality-phase-after',{name,phase:'"+tag+"'});")
   old="  announce(`${({efficient:'Smooth',balanced:'Balanced',detail:'Sharp',studio:'Studio'})[name]} quality selected.`);";assert s.count(old)==1;s=s.replace(old,old+"\n  window.__trace('quality-handler-end',{name});")
   old='composer.render();renderedFrames++;';assert s.count(old)==1;s=s.replace(old,"composer.render();if(window.__qualityFrame!==quality){window.__qualityFrame=quality;window.__trace('quality-frame',{quality})}renderedFrames++;")
   anchor='if(passProfiling){try{const {createPassTiming}';assert s.count(anchor)==1
   instrument='''const qaWrap=(obj,key,label)=>{const old=obj[key];obj[key]=function(...args){const before={args,canvas:[renderer.domElement.width,renderer.domElement.height],rendererRatio:renderer.getPixelRatio(),composer:[composer._width,composer._height,composer._pixelRatio],targets:[[composer.renderTarget1.width,composer.renderTarget1.height],[composer.renderTarget2.width,composer.renderTarget2.height]]};window.__trace('size-call-start',{label,...before});const result=old.apply(this,args);window.__trace('size-call-end',{label,canvas:[renderer.domElement.width,renderer.domElement.height],rendererRatio:renderer.getPixelRatio(),composer:[composer._width,composer._height,composer._pixelRatio],targets:[[composer.renderTarget1.width,composer.renderTarget1.height],[composer.renderTarget2.width,composer.renderTarget2.height]]});return result}};qaWrap(renderer,'setSize','renderer.setSize');qaWrap(renderer,'setPixelRatio','renderer.setPixelRatio');qaWrap(composer,'setSize','composer.setSize');qaWrap(composer,'setPixelRatio','composer.setPixelRatio');qaWrap(composer.renderTarget1,'setSize','target1.setSize');qaWrap(composer.renderTarget2,'setSize','target2.setSize');\n'''
   s=s.replace(anchor,instrument+anchor)
   s+='\nwindow.__qa=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot(),inspect:assemblyInspect(),lastFrame:window.__qualityFrame||null});';await route.fulfill(response=res,body=s)
  await page.route('**/assembly-review.js*',instrument)
  async def probe(label):
   try:
    x=await asyncio.wait_for(q.evaluate('''()=>{let i=assemblyInspect();return {quality:i.renderQuality,interactive:i.presentation.interactive,loading:i.loading,failed:i.failed,lastFrame:window.__qualityFrame||null}}'''),20);r['checks'].append({'probe':label,'result':x})
   except Exception as e:r['checks'].append({'probe':label,'exception':repr(e)})
   save()
  async def select(name):
   attempt={'quality':name,'status':'running'};r['checks'].append(attempt);save()
   try:
    await q.locator('[data-quality="'+name+'"]').click(timeout=45000);attempt['status']='clicked';save();await q.wait_for_function('(name)=>assemblyInspect().renderQuality===name',arg=name,timeout=45000);attempt['status']='selected';save()
   except Exception as e:attempt['status']='timeout_or_failure';attempt['exception']=repr(e);save();await probe('after-failed-'+name);return False
   await probe('after-'+name);return True
  try:
   await page.goto('https://shayan-kazeyami.github.io/aerial-watch/?quality=efficient&leather=craft14',wait_until='domcontentloaded',timeout=60000);await page.wait_for_function("document.querySelector('#watch-viewer')?.contentWindow?.location.href.includes('atelier-preview.html')",timeout=60000);q=await (await page.query_selector('#watch-viewer')).content_frame();await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000);assert any(r['release'] in u for u in requests)
   proof=await q.evaluate('__qa()');r['proof']={'leather':proof['leather'],'hybrid':proof['hybrid']};assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and proof['leather']['geometryVerification']['actualBytes']==8579970 and proof['hybrid']['active'] and proof['hybrid']['triangles']==501830;await probe('ready')
   await q.locator('[data-mode=quality]').first.click(timeout=45000);sequence=['studio','efficient','balanced','detail','efficient']
   for name in sequence:
    if not await select(name):break
   await probe('final')
  except Exception as e:r['setup_error']=repr(e);r['traceback']=traceback.format_exc()
  finally:save();
  try:await asyncio.wait_for(c.close(),15)
  except:pass
  try:await asyncio.wait_for(b.close(),15)
  except:pass
asyncio.run(main())
