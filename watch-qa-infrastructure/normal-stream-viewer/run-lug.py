import asyncio,json,os,time
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image,ImageStat
from gates import assert_snapshot,stable,assert_same_texture_bindings
Q=Path(__file__).resolve().parent;arm=os.environ['QA_ARM'];assert arm in ['baseline','candidate'];E=Q/('evidence-lug-'+arm);E.mkdir(exist_ok=False)
RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
URL=f'http://127.0.0.1:8765/preview-b/releases/{RID}/atelier-preview.html?leather=craft14&normalStream=1&paused=1&quality=balanced'
async def main():
 r={'passed':False,'arm':arm,'url':URL,'requests':[],'responses':[],'pageErrors':[],'consoleWarnings':[],'scope':'actual premium viewer normal decode/adoption diagnostic; manual rendered leather approval remains HOLD'};browser=None
 try:
  async with async_playwright() as p:
   try:
    browser=await asyncio.wait_for(p.chromium.launch(headless=True,chromium_sandbox=True),45);r['browser']=browser.version
    page=await browser.new_page(viewport={'width':1280,'height':900},device_scale_factor=1);page.set_default_timeout(30000)
    page.on('pageerror',lambda e:r['pageErrors'].append(str(e)))
    page.on('console',lambda m:r['consoleWarnings'].append(m.text) if m.type in ['warning','error'] else None)
    page.on('request',lambda x:r['requests'].append({'url':x.url,'range':x.headers.get('range')}))
    page.on('response',lambda x:r['responses'].append({'url':x.url,'status':x.status}))
    await page.goto(URL,wait_until='domcontentloaded',timeout=120000)
    await page.wait_for_function("window.__normalStreamViewerQA && window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().presentation.interactive && __normalStreamViewerQA().detail.phase==='full'",timeout=600000)
    # Native visible route only; no hidden bridge click, event injection or camera mutation.
    await page.locator('button[data-mode="settings"]').click(timeout=30000)
    lug=page.locator('#atelier-tools button[data-camera="lug"]')
    await lug.wait_for(state='visible',timeout=30000);await lug.click(timeout=30000)
    await page.locator('#close').click(timeout=30000)
    await page.wait_for_function("(()=>{const s=window.__normalStreamViewerQA();return s.inspect.view==='lug'&&s.configuration.camera.target.every((v,i)=>Math.abs(v-[0,22.4,-.95][i])<1e-7)&&document.getElementById('context').hidden})()",timeout=30000)
    r['nativeCameraRoute']='visible Studio tools → Lugs → Close; actual camera target settled'
    r['before']=await asyncio.wait_for(page.evaluate('window.__normalStreamViewerQA()'),30);assert_snapshot(r['before']);r['stableBefore']=stable(r['before'])
    stage=page.locator('#stage');box=await stage.bounding_box(timeout=30000);assert box and box['width']>400 and box['height']>400
    await asyncio.wait_for(page.screenshot(path=str(E/'stage.png'),clip=box),180)
    im=Image.open(E/'stage.png').convert('RGB');assert abs(im.width-round(box['width']))<=1 and abs(im.height-round(box['height']))<=1;assert max(ImageStat.Stat(im).stddev)>5
    # Preserve full original image. Crop is contextual enlargement only; manual leather identification required.
    # No arbitrary crop: complete original stage must show identifiable leather for manual approval.
    r['after']=await asyncio.wait_for(page.evaluate('window.__normalStreamViewerQA()'),30);assert_snapshot(r['after']);assert_same_texture_bindings(r['before'],r['after']);assert stable(r['after'])==r['stableBefore'],'render state changed during screenshot'
    assert not r['pageErrors'],r['pageErrors'];parts=[x for x in r['responses'] if 'outer-normal-4k.ktx2.part' in x['url']];assert len(parts)==2 and sorted(x['status'] for x in parts)==[200,206],parts
    r['captured']=True;r['stage']=box;r['manualVisualApproved']=False
   except BaseException as e:r['failure']=repr(e);raise
   finally:
    if browser:
     try:await asyncio.wait_for(browser.close(),30);r['normalClose']=True
     except BaseException as e:r['cleanupFailure']=repr(e);raise
  r['passed']=True
 finally:(E/'REPORT.json').write_text(json.dumps(r,indent=2))
asyncio.run(asyncio.wait_for(main(),1200))
