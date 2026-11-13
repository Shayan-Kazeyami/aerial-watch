import asyncio,json,pathlib,time,traceback
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
P=pathlib.Path('normal-stream-qa');O=pathlib.Path('normal-stream-evidence');O.mkdir(exist_ok=True)
R={'setup':'Chromium SwiftShader, fresh contexts, cache disabled, 4 Mbit/s throughput and 80 ms latency; not physical-phone speed','cases':[]}
BASE='https://shayan-kazeyami.github.io/aerial-watch/'
async def run_case(p,name,stream,fail=False,camera=None):
 b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=1,is_mobile=True,has_touch=True);page.set_default_timeout(180000)
 out={'name':name,'errors':[],'responses':[],'transfers':[]};R['cases'].append(out)
 async def module(route):await route.fulfill(status=200,content_type='text/javascript',body=(P/'assembly-review-capture-draft.js').read_text()+'\n'+(P/'probe.js').read_text())
 async def fetch_module(route):await route.fulfill(status=200,content_type='text/javascript',body=(P/'assembly-fetch-progressive-normal.js').read_text())
 await page.route('**/assembly-capture-detail-policy.js',lambda route:route.fulfill(status=200,content_type='text/javascript',body=(P/'assembly-capture-detail-policy.js').read_text()));await page.route('**/assembly-review.js*',module);await page.route('**/assembly-fetch-progressive-normal.js',fetch_module)
 upgrade_gate=asyncio.Event()
 if stream and not fail:
  async def gate_high_chunk(route):
   await upgrade_gate.wait();await route.continue_()
  await page.route('**/outer-normal-4k.ktx2.part1',gate_high_chunk)
 if fail:
  async def reject_range(route):
   if route.request.headers.get('range'):await route.fulfill(status=503,body='Upgrade unavailable')
   else:await route.continue_()
  await page.route('**/outer-normal-4k.ktx2.part0',reject_range)
 page.on('pageerror',lambda e:out['errors'].append(str(e)))
 cdp=await page.context.new_cdp_session(page);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{'cacheDisabled':True});await cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':80,'downloadThroughput':500000,'uploadThroughput':125000})
 def response(e):
  r=e['response'];out['responses'].append({'url':r['url'],'status':r['status'],'headers':r.get('headers',{}),'timestamp':e['timestamp'],'requestId':e['requestId']})
 cdp.on('Network.responseReceived',response);cdp.on('Network.loadingFinished',lambda e:out['transfers'].append(e))
 start=time.monotonic()
 try:
  await page.goto(BASE+f'?quality=efficient&normalStream={int(stream)}&qa=normal-{name}',wait_until='domcontentloaded',timeout=180000);await page.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=360000);f=next(x for x in page.frames if 'atelier-preview' in x.url);out['observedReadyMs']=(time.monotonic()-start)*1000;out['ready']=await f.evaluate('normalQA.snapshot()');out['captureReady']=await f.evaluate('normalQA.auditCapture()');print('READY',name,out['observedReadyMs'],out['ready']['state'],flush=True)
  await f.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=180000)
  await f.add_style_tag(content='.crown-hotspot,.crown-halo,.atelier-first-use{visibility:hidden!important}')
  out['frozen']=await f.evaluate('c=>normalQA.freeze(c)',camera);camera=out['frozen']['camera'];out['camera']=camera
  await f.locator('#assembly-canvas').screenshot(path=str(O/f'{name}-initial.png'),timeout=180000)
  if stream:
   if fail:
    await f.wait_for_function('normalQA.snapshot().state==="failed"',timeout=180000);out['failedUpgrade']=await f.evaluate('normalQA.snapshot()');assert not out['failedUpgrade']['failed'];assert any(t.get('width')==2048 for t in out['failedUpgrade']['filtering']['textures'])
   else:
    # Make direct hold visible again and test it during remaining upgrade work.
    await f.add_style_tag(content='.crown-hotspot{visibility:visible!important}')
    dot=f.locator('.crown-hotspot');box=await dot.bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
    out['variantsBefore']=[await f.evaluate('m=>normalQA.variant(m)',m) for m in ['wireframe','solid','clay','transparent']];await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-22}]});a=await f.evaluate('normalQA.frames(3)');assert a['state']=='upgrading',a;upgrade_gate.set();out['upgradeCompletionGate']='Final high chunk released only after real held input; does not affect first-interactive timing';await f.wait_for_function('normalQA.snapshot().state==="full"',timeout=240000);z=await f.evaluate('normalQA.frames(3)');assert z['crown']['degrees']>a['crown']['degrees'],(a,z);out['heldAcrossUpgrade']={'before':a['state'],'after':z['state'],'degreesBefore':a['crown']['degrees'],'degreesAfter':z['crown']['degrees']}
    await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});a=await f.evaluate('normalQA.frames(3)');z=await f.evaluate('normalQA.frames(3)');assert a['crown']['degrees']==z['crown']['degrees'];out['releasedStops']=True;out['adoptedVariant']=await f.evaluate('normalQA.snapshot()');assert out['adoptedVariant']['detail']['ready'];out['variantsAfter']=[await f.evaluate('m=>normalQA.variant(m)',m) for m in ['transparent','wireframe','solid','clay','normal']];assert all(v['detail']['ready'] and all(b['same'] for b in v['bindings']) for v in out['variantsAfter'])
    await f.add_style_tag(content='.crown-hotspot{visibility:hidden!important}');await f.evaluate('c=>normalQA.freeze(c)',camera)
  out['final']=await f.evaluate('normalQA.snapshot()');out['captureFinal']=await f.evaluate('normalQA.auditCapture()');out['observedFullMs']=(time.monotonic()-start)*1000
  if not fail:
   assert any(t.get('width')==4096 for t in out['final']['filtering']['textures']);await f.locator('#assembly-canvas').screenshot(path=str(O/f'{name}-final.png'),timeout=180000)
  assert not out['errors'];out['passed']=True;return camera
 except Exception as e:out['passed']=False;out['failure']=repr(e);out['traceback']=traceback.format_exc();raise
 finally:
  (O/'report.json').write_text(json.dumps(R,indent=2))
  try:await asyncio.wait_for(b.close(),20)
  except:pass
async def main():
 async with async_playwright() as p:
  cam=await run_case(p,'direct',False)
  await run_case(p,'stream',True,camera=cam)
  await run_case(p,'upgrade-failure',True,fail=True,camera=cam)
 for kind in ['initial','final']:
  a=Image.open(O/'direct-final.png').convert('RGB');b=Image.open(O/f'stream-{kind}.png').convert('RGB');assert a.size==b.size
  diff=ImageChops.difference(a,b);stats=ImageStat.Stat(diff);R[kind+'Difference']={'mean':sum(stats.mean)/3,'max':max(v[1]for v in diff.getextrema())};diff.save(O/f'{kind}-difference.png')
 assert R['finalDifference']['mean']<.05,R['finalDifference']
 R['firstInteractiveDifferenceMs']=R['cases'][0]['ready']['firstInteractiveMs']-R['cases'][1]['ready']['firstInteractiveMs'];R['passed']=True;(O/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps({k:v for k,v in R.items()if k!='cases'}),flush=True)
asyncio.run(main())
