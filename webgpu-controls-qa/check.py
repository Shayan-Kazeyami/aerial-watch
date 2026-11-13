import asyncio,json,os,pathlib,traceback
from playwright.async_api import async_playwright
P=pathlib.Path('webgpu-controls-qa');OUT=pathlib.Path('webgpu-controls-evidence');OUT.mkdir(exist_ok=True)
RID=(P/'release-id.txt').read_text().strip();mode=os.environ.get('QA_MODE','fallback');W,H=(430,932)if mode=='fallback'else(740,360)
R={'release':RID,'mode':mode,'viewport':[W,H],'errors':[],'notes':'Chromium software-rendered functional benchmark workflow verification, not physical-device speed comparison'}
async def main():
 async with async_playwright() as p:
  args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']
  if mode.startswith('webgpu'):args+=['--enable-unsafe-webgpu']
  if mode=='webgpu-vulkan':args+=['--use-vulkan=swiftshader','--enable-features=Vulkan']
  R['browserFlags']=args
  browser=await p.chromium.launch(args=args);ctx=await browser.new_context(viewport={'width':W,'height':H},device_scale_factor=1,is_mobile=True,has_touch=True,accept_downloads=True)
  await ctx.add_init_script("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.qaCopied=text;}}});")
  if mode=='fallback':await ctx.add_init_script("Object.defineProperty(navigator,'gpu',{value:undefined});")
  page=await ctx.new_page();page.on('pageerror',lambda e:R['errors'].append(str(e)));page.set_default_timeout(300000)
  async def getframe():
   for _ in range(600):
    frames=[f for f in page.frames if RID+'/atelier-preview.html'in f.url]
    if frames:return frames[0]
    await asyncio.sleep(.5)
   raise AssertionError('no viewer frame')
  async def instrument(route):
   response=await route.fetch();probe='\nwindow.qaBenchmarkView=()=>({camera:{position:camera.position.toArray(),target:controls.target.toArray(),zoom:camera.zoom,fov:camera.fov},quality,clock:clock.snapshot(),crown:crownInteraction.snapshot(),explosion:explosion?.amount??0,options:{openWork,interiorView,powerPath,inspectionDisplay}});'
   await route.fulfill(response=response,body=(await response.text())+probe)
  await page.route('**/assembly-review.js*',instrument)
  try:
   await page.goto('http://127.0.0.1:8765/?quality=efficient&paused=1',wait_until='domcontentloaded');frame=await getframe();await frame.locator('body[data-ready=true]').wait_for();await frame.locator('.masthead .quality').click();await frame.locator('.debug-benchmark summary').click();await frame.locator('#atelier-benchmark-start').wait_for(state='visible');await frame.wait_for_function("!document.getElementById('atelier-benchmark-start').disabled",timeout=300000)
   R['initialIndicator']=await frame.locator('#atelier-backend-indicator').inner_text();assert R['initialIndicator']=='WebGL2';await page.screenshot(path=str(OUT/'controls-before.png'),full_page=True)
   initialURL=page.url;initialView=await frame.evaluate('qaBenchmarkView()');await frame.locator('#atelier-benchmark-start').click()
   # The real run uses production durations and renderer reloads, not synthetic frames.
   await page.wait_for_function("(()=>{const s=JSON.parse(sessionStorage.getItem('aerial.debug.benchmark.v1')||'null');return s?.phase==='done'})()",timeout=1100000)
   state=await page.evaluate("JSON.parse(sessionStorage.getItem('aerial.debug.benchmark.v1'))");R['runState']=state;assert len(state['rows'])==8,state;assert state['status']=='complete',state
   assert all(x['status']in('complete','failed')and x['actualBackend']=='WebGL2' for x in state['rows'][:4]);assert any(x['status']=='complete'for x in state['rows'][:4]);assert {x['preset']for x in state['rows'][:4]}=={'efficient','balanced','detail','studio'}
   gpu=state['rows'][4:];assert all(x['requestedBackend']=='webgpu'for x in gpu)
   if mode=='fallback':assert all(x['status']=='fallback'and x['actualBackend']=='WebGL2'and x['metrics'] is None for x in gpu)
   else:assert all((x['status']=='complete'and x['actualBackend']=='WebGPU')or(x['status']=='fallback'and x['actualBackend']=='WebGL2')or(x['status']=='failed'and bool(x.get('reason'))and x.get('metrics')is None)for x in gpu),gpu
   assert state['restored'] and not state.get('restoreError');assert page.url==initialURL,(page.url,initialURL)
   frame=await getframe();await frame.locator('#atelier-benchmark-copy').wait_for(state='visible');await frame.locator('#atelier-benchmark-copy').click();copied=await frame.evaluate('JSON.parse(window.qaCopied)');assert len(copied['presets'])==8;assert copied['restoredQuality']=='efficient';assert all(x.get('gpuTimeMs')is None for x in copied['presets']);(OUT/'benchmark.json').write_text(json.dumps(copied,indent=2))
   async with page.expect_download()as info:await frame.locator('#atelier-benchmark-download').click()
   download=await info.value;await download.save_as(str(OUT/'download.json'));assert json.loads((OUT/'download.json').read_text())==copied
   R['copyAndDownload']=True;finalView=await frame.evaluate('qaBenchmarkView()');assert initialView==finalView,(initialView,finalView);R['exactPausedViewRestoration']=True;R['restoredIndicator']=await frame.locator('#atelier-backend-indicator').inner_text();assert R['restoredIndicator']=='WebGL2';await page.screenshot(path=str(OUT/'controls-results.png'),full_page=True)
   # Failure to use Clipboard still exposes selectable JSON.
   await frame.evaluate("Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw Error('denied')}}})");await frame.locator('#atelier-benchmark-copy').click();assert await frame.locator('#atelier-benchmark-json').is_visible();assert json.loads(await frame.locator('#atelier-benchmark-json').input_value())==copied;R['manualCopyFallback']=True
   # Explicit switch is labeled reload and preserves other query choices.
   assert 'reload'in(await frame.locator('#atelier-backend-toggle').inner_text()).lower();R['actualWebGPUValidated']=all(x['status']=='complete'and x['actualBackend']=='WebGPU'for x in gpu)
   if mode=='fallback':
    await frame.locator('#atelier-backend-toggle').click();await page.wait_for_url('**backend=webgpu*');frame=await getframe();await frame.locator('body[data-ready=true]').wait_for();assert 'WebGL2'in await frame.locator('#atelier-backend-indicator').inner_text();assert 'fallback'in await frame.locator('#atelier-backend-indicator').inner_text();await frame.locator('.masthead .quality').click();assert 'navigator.gpu unavailable'in await frame.locator('#atelier-backend-detail').inner_text();await frame.locator('#atelier-backend-toggle').click();await page.wait_for_url('**backend=webgl2*');frame=await getframe();await frame.locator('body[data-ready=true]').wait_for();assert await frame.locator('#atelier-backend-indicator').inner_text()=='WebGL2';R['actualToggleRoundtrip']=True
   # Dawn error-scope rejections following a recorded device loss are retained as environment failures, never GPU success.
   expectedLoss=all(x['status']=='failed'and 'Instance reference' in x.get('reason','') for x in gpu)
   R['expectedDeviceLossErrors']=[x for x in R['errors']if expectedLoss and x=='Instance dropped in popErrorScope']
   R['unexpectedErrors']=[x for x in R['errors']if x not in R['expectedDeviceLossErrors']]
   R['passed']=not R['unexpectedErrors'];assert R['passed'],R['unexpectedErrors']
  finally:
   try:await page.screenshot(path=str(OUT/'final.png'),full_page=True)
   except:pass
   (OUT/'report.json').write_text(json.dumps(R,indent=2));await browser.close()
try:asyncio.run(main())
except Exception as e:R['failure']=str(e);R['traceback']=traceback.format_exc();(OUT/'report.json').write_text(json.dumps(R,indent=2));raise
