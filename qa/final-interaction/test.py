import asyncio,json,pathlib,os,traceback
from playwright.async_api import async_playwright
out=pathlib.Path('qa-deliverables/final-interaction-regression/output');out.mkdir(exist_ok=True)
r={'release':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','tests':{},'errors':[],'backend':'local Chromium SwiftShader'}
def save(): (out/'report.json').write_text(json.dumps(r,indent=2))
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640},accept_downloads=True);q=await c.new_page();r['browser']=b.version;q.on('pageerror',lambda e:r['errors'].append(str(e)))
  async def hook(route):
   response=await route.fetch();s=await response.text();s+='\nwindow.__proof=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot()});';await route.fulfill(response=response,body=s)
  await q.route('**/assembly-review.js*',hook)
  async def test(name,fn,timeout=90):
   r['tests'][name]={'status':'running'};save()
   try:r['tests'][name]={'status':'passed','detail':await asyncio.wait_for(fn(),timeout)}
   except Exception as e:r['tests'][name]={'status':'failed','exception':repr(e)}
   save()
  async def click(sel):await q.locator(sel).first.click(timeout=20000)
  try:
   root='preview-b/releases/'+r['release'];await q.goto('http://127.0.0.1:8766/'+root+'/atelier-preview.html?quality=efficient&leather=craft14',wait_until='domcontentloaded');await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000)
   proof=await q.evaluate('__proof()');r['proof']=proof;assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7';assert proof['leather']['geometryVerification']['actualBytes']==8579970;assert proof['hybrid']['active'] and proof['hybrid']['triangles']==501830;save()
   async def crown():
    await click('[data-mode=time]');await click('[data-proxy=crown-left]');await q.wait_for_timeout(2500);await click('[data-proxy=crown-pull]');await q.wait_for_timeout(2500);assert await q.locator('#crown-pull').get_attribute('aria-pressed')=='true';await click('[data-proxy=crown-right]');await q.wait_for_timeout(2500);await click('[data-mode=explode]');await q.wait_for_timeout(2500);assert await q.locator('#crown-pull').get_attribute('aria-pressed')=='false';await q.locator('#atelier-explosion').fill('65');await q.wait_for_timeout(2500);await click('[data-mode=time]');await q.wait_for_timeout(2500);return {'crown':await q.locator('#crown-state').text_content(),'explosion':await q.locator('#atelier-explosion-value').text_content() if await q.locator('#atelier-explosion-value').count() else 'time mode reassembled'}
   await test('crown_explode_transition',crown)
   async def modes():
    for mode in ['inside','explode','time','capture','explore','inside','explore']:
     await click('[data-mode="'+mode+'"]')
    await click('[data-mode=settings]');return {'inspect':await q.evaluate('assemblyInspect()')}
   await test('rapid_modes',modes)
   async def qualities():
    await click('[data-mode=quality]')
    for quality in ['balanced','detail','studio','efficient']:
     await click('[data-quality="'+quality+'"]')
    await q.wait_for_timeout(2500);i=await q.evaluate('assemblyInspect()');assert i['renderQuality']=='efficient';return {'final':i['renderQuality']}
   await test('rapid_quality',qualities)
   async def keyboard():
    await q.locator('[data-mode=time]').focus();await q.keyboard.press('Enter');await q.wait_for_timeout(500);a=await q.evaluate('document.activeElement.id');assert a=='close',a;await q.keyboard.press('Escape');await q.wait_for_timeout(500);return {'focus_after_enter':a,'focus_after_escape':await q.evaluate('document.activeElement.outerHTML')}
   await test('keyboard_focus',keyboard)
   async def exports():
    result=[]
    for i in range(2):
     await click('[data-mode=capture]');await q.wait_for_timeout(4000)
     async with q.expect_download(timeout=120000) as d:await click('[data-proxy=export-config]')
     dl=await d.value;path=out/f'view-{i}.json';await dl.save_as(path);data=json.loads(path.read_text());assert data;await q.locator('#import-config').set_input_files(str(path));await q.wait_for_timeout(4000)
     result.append({'file':dl.suggested_filename,'bytes':path.stat().st_size,'status':await q.locator('#viewer-status').text_content()})
    return result
   await test('json_export_import_twice',exports,300)
   async def png():
    await click('[data-mode=capture]');await q.wait_for_timeout(5000)
    async with q.expect_download(timeout=120000) as d:await click('[data-proxy=capture-scene]')
    dl=await d.value;path=out/'capture.png';await dl.save_as(path);assert path.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n';return {'bytes':path.stat().st_size,'file':dl.suggested_filename}
   await test('png_download',png,180)
   async def reset():
    await click('#home');await q.wait_for_timeout(4000);i=await q.evaluate('assemblyInspect()');assert i['hybridCase']['active'] and not i['failed'];return {'view':i['view'],'quality':i['renderQuality']}
   await test('reset',reset)
  except Exception as e:r['setup_error']=repr(e);r['traceback']=traceback.format_exc()
  finally:save();await c.close();await b.close()
asyncio.run(main())
