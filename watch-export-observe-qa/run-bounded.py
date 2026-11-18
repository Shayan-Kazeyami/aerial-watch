"""One authorized native 8s export diagnostic. Never a full-pass/release gate."""
import asyncio,json,pathlib,subprocess,time
from playwright.async_api import async_playwright
from observe import install
from instrument import RID
P=pathlib.Path(__file__).parent;O=P/'output';O.mkdir(exist_ok=True)
R={'scope':'ONE instrumented native held-watch export observation, not uninstrumented release proof or hardware performance','release':RID,'completedFullExport':False,'cleanup':{},'limitAfterSubmitSeconds':120}
def save(): (O/'OBSERVATION.json').write_text(json.dumps(R,indent=2))
async def main():
 server=subprocess.Popen(['python','-m','http.server','8766','--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);browser=None;page=None
 try:
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await browser.new_page(viewport={'width':640,'height':600},device_scale_factor=1,reduced_motion='reduce');page.set_default_timeout(180000);ledger,snapshot=await install(page,'http://127.0.0.1:8766');R['ledger']=ledger;downloads=[];page.on('download',lambda d:downloads.append(d))
   await page.goto(f'http://127.0.0.1:8766/preview-b/releases/{RID}/atelier-preview.html?quality=efficient&assets=meshopt&normalStream=1',wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=360000)
   config=json.loads((P/'config.json').read_text());config['options']['quality']='efficient';await page.locator('#import-config').set_input_files({'name':'paused.json','mimeType':'application/json','buffer':json.dumps(config).encode()});await page.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'");await page.locator('.atelier-first-use').wait_for(state='hidden',timeout=15000)
   await page.wait_for_function("()=>{document.querySelector('#refresh-diagnostics').click();return JSON.parse(document.querySelector('#diagnostics-report').textContent).progressiveNormal==='full'}",timeout=240000)
   R['preExport']=await page.evaluate("()=>{document.querySelector('#refresh-diagnostics').click();return JSON.parse(document.querySelector('#diagnostics-report').textContent)}");assert ledger['overlay'];R['sequence']='fresh native export, no prior cancel cycle; same held source/camera/quality/8s compact settings, not exact previous post-cancel sequence';save()
   await page.locator('#record-scene').evaluate('(e)=>e.click()');await page.locator('.aerial-video-choice').wait_for(state='visible');await page.locator('.aerial-video-choice [value=compact]').check();R['choiceText']=await page.locator('.aerial-video-choice').inner_text()
   start=time.monotonic();R['submitHostMonotonic']=start;save()
   try:await asyncio.wait_for(page.locator('.aerial-video-choice button').evaluate('(e)=>e.click()'),5)
   except asyncio.TimeoutError:R['submitCallUnresponsive']=True
   # Bounded sampling through 100s, leaving cancellation/cleanup time by120s.
   for offset in [5,20,40,60,80,95,100]:
    if time.monotonic()-start<offset:await asyncio.sleep(offset-(time.monotonic()-start))
    row=await snapshot(f'post-submit-{offset}s');save();print(json.dumps({'offset':offset,'result':row['result'].get('active'),'status':row['result'].get('status'),'unresponsive':row['result'].get('unresponsiveSample')}),flush=True)
    if downloads:
     R['downloadEventSeen']=True
     try:await asyncio.wait_for(downloads[0].save_as(O/'native-watch.webm'),min(10,max(1,115-(time.monotonic()-start))));R['completedFullExport']=True
     except Exception as e:R['downloadSaveError']=repr(e)
     break
    status=row['result'].get('status',{})
    if str(status.get('viewerStatus','')).startswith('Could not save video') and status.get('dialogOpen') is False:R['nativeRefusal']=status['viewerStatus'];break
   if not downloads:
    R['cleanup']['cancelRequestedAtSeconds']=time.monotonic()-start
    try:
     await asyncio.wait_for(page.locator('.aerial-video-cancel').evaluate('(e)=>{if(e.closest("dialog").open)e.click()}'),5)
     await page.wait_for_function("!document.querySelector('.aerial-video-dialog').open&&!document.querySelector('#record-scene').disabled",timeout=5000);R['cleanup']['nativeRestored']=True
    except Exception as e:R['cleanup']['nativeRestored']=False;R['cleanup']['error']=repr(e)
   R['elapsedAtCleanupSeconds']=time.monotonic()-start
   await snapshot('after-cleanup');save()
   try:await asyncio.wait_for(browser.close(),5);R['cleanup']['browserClosed']=True
   except Exception as e:R['cleanup']['browserClosed']=False;R['cleanup']['browserCloseError']=repr(e)
   browser=None;save()
 except Exception as e:R['failure']=repr(e);save();raise
 finally:
  if browser:
   try:await asyncio.wait_for(browser.close(),5);R['cleanup']['browserClosed']=True
   except Exception as e:R['cleanup']['browserCloseError']=repr(e)
  server.terminate();save()
asyncio.run(main())
