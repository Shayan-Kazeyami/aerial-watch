import asyncio,json,pathlib,traceback
from playwright.async_api import async_playwright
out=pathlib.Path('live-reset-output');out.mkdir(exist_ok=True);r={'release':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','checks':{},'errors':[]};save=lambda:(out/'report.json').write_text(json.dumps(r,indent=2));save()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640},accept_downloads=True);page=await c.new_page();page.on('pageerror',lambda e:r['errors'].append(str(e)));requests=[];page.on('request',lambda req:requests.append(req.url) if 'assembly-review.js' in req.url else None)
  async def proof(route):
   res=await route.fetch();s=await res.text();s+='\nwindow.__qa=()=>({config:captureConfiguration(),leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot()});';await route.fulfill(response=res,body=s)
  await page.route('**/assembly-review.js*',proof)
  async def click(sel):await q.locator(sel).first.click(timeout=40000)
  async def state():return (await q.evaluate('__qa()'))['config']
  async def step(name,fn,timeout=180):
   r['checks'][name]={'status':'running'};save()
   try:r['checks'][name]={'status':'passed','detail':await asyncio.wait_for(fn(),timeout)}
   except Exception as e:r['checks'][name]={'status':'failed','exception':repr(e),'traceback':traceback.format_exc()}
   save()
  async def export(name):
   await click('[data-mode=capture]');await q.wait_for_function("!document.querySelector('[data-proxy=export-config]').disabled",timeout=90000)
   async with page.expect_download(timeout=120000) as d:await click('[data-proxy=export-config]')
   dl=await d.value;path=out/name;await dl.save_as(path);return path,json.loads(path.read_text())
  try:
   await page.goto('https://shayan-kazeyami.github.io/aerial-watch/?quality=efficient&leather=craft14',wait_until='domcontentloaded',timeout=60000);await page.wait_for_function("document.querySelector('#watch-viewer')?.contentWindow?.location.href.includes('atelier-preview.html')",timeout=60000);q=await (await page.query_selector('#watch-viewer')).content_frame();await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000);assert any(r['release'] in x for x in requests),requests
   proof=await q.evaluate('__qa()');r['proof']={'leather':proof['leather'],'hybrid':proof['hybrid']};assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and proof['leather']['geometryVerification']['actualBytes']==8579970 and proof['hybrid']['active'] and proof['hybrid']['triangles']==501830;save()
   async def reset():
    await click('[data-mode=time]');await click('[data-proxy=crown-pull]');await q.wait_for_timeout(3000);await click('[data-proxy=crown-right]');await q.wait_for_timeout(4000);a=await state();assert a['crown']['pulled'] and a['settingSeconds']!=0,{'crown':a['crown'],'settingSeconds':a['settingSeconds']};await click('[data-mode=explode]');await q.locator('#atelier-explosion').fill('65');await q.wait_for_timeout(4000);before=await state();assert before['explosion']>0 and not before['crown']['pulled'];await click('#home');await q.wait_for_timeout(6000);after=await state();i=await q.evaluate('assemblyInspect()');assert after['explosion']==0 and after['settingSeconds']==0 and not after['crown']['pulled'] and after['crown']['degrees']==0;assert after['clock']['mechanism']==0 and after['clock']['hands']==0 and not after['clock']['running']['mechanism'] and not after['clock']['running']['hands'];assert i['openWork'] and i['finish'] and i['crystals'] and i['renderQuality']=='efficient' and not i['failed'] and i['hybridCase']['active'];return {'time_set':{'crown':a['crown'],'settingSeconds':a['settingSeconds']},'exploded':{'explosion':before['explosion'],'crown':before['crown']},'reset':{k:after[k] for k in ['view','camera','crown','settingSeconds','clock','explosion']},'inspect':{k:i[k] for k in ['renderQuality','openWork','finish','crystals','failed']}}
   await step('reset_after_time_and_explosion',reset,240)
   async def imports():
    # Two successive imports of the same actual saved configuration, then re-export.
    first,a=await export('first.json')
    for _ in range(2):
     await q.locator('#import-config').set_input_files(str(first));await q.wait_for_function("document.getElementById('import-config').value === '' && document.getElementById('viewer-status').textContent.includes('restored')",timeout=90000);await q.wait_for_timeout(1500)
    _,z=await export('after-second-import.json');fields=['view','camera','crown','settingSeconds','explosion'];comparison={k:a[k]==z[k] for k in fields};comparison['clockMechanism']=a['clock']['mechanism']==z['clock']['mechanism'];comparison['clockHands']=a['clock']['hands']==z['clock']['hands'];assert all(comparison.values()),comparison;return {'matches':comparison,'initialRunning':a['clock']['running'],'restoredRunning':z['clock']['running']}
   await step('second_import_reexport',imports,360)
  except Exception as e:r['setup_error']=repr(e);r['traceback']=traceback.format_exc()
  finally:save();await c.close();await b.close()
asyncio.run(main())
