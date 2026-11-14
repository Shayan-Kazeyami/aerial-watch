import asyncio,json,os
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image,ImageStat
from normal_gates import assert_snapshot,stable,assert_same_texture_bindings
Q=Path(__file__).resolve().parent;arm=os.environ['QA_ARM'];kind=os.environ['QA_KIND'];assert arm in ['baseline','candidate'] and kind in ['desktop','portrait'];E=Q/('evidence-'+arm+'-'+kind);E.mkdir(exist_ok=False);RID={'baseline':'3448182496cf6c2b906abe4b5a7128a9537ab745e8f992d4d55783fd389879e6','candidate':'c9d2d1a59b4efacb6d4b44824baefd047dab96351b0086fa8bfe1032168c31bc'}[arm];W,H=(1280,900) if kind=='desktop' else (430,932)
INIT="""(()=>{window.__composedTelemetry={timeOrigin:performance.timeOrigin,contexts:[]};document.addEventListener('webglcontextlost',e=>window.__composedTelemetry.contexts.push('lost'),true);document.addEventListener('webglcontextrestored',e=>window.__composedTelemetry.contexts.push('restored'),true)})()"""
SNAP="""()=>{window.__initialCanvas??=document.getElementById('assembly-canvas');const c=document.getElementById('assembly-canvas');return {runtime:window.__normalStreamViewerQA(),telemetry:window.__composedTelemetry,canvasSame:c===window.__initialCanvas,canvas:[c.width,c.height],stage:document.getElementById('stage').getBoundingClientRect().toJSON(),ready:document.body.dataset.ready}}"""
async def main():
 r={'passed':False,'arm':arm,'kind':kind,'RID':RID,'errors':[],'navigation':[],'requests':[],'responses':[],'steps':[],'manualVisualApproved':False,'scope':'scoped composed viewer startup/panel/explode/reset/Lugs/rear checks; not15taskcompletion'};browser=None
 try:
  async with async_playwright() as p:
   try:
    browser=await asyncio.wait_for(p.chromium.launch(headless=True,chromium_sandbox=True),45);r['browser']=browser.version
    ctx=await browser.new_context(viewport={'width':W,'height':H},device_scale_factor=1,is_mobile=kind=='portrait',has_touch=kind=='portrait');await ctx.add_init_script(INIT)
    host=await ctx.new_page();host.set_default_timeout(30000);host.on('pageerror',lambda e:r['errors'].append(str(e)));host.on('framenavigated',lambda f:r['navigation'].append(f.url));host.on('request',lambda x:r['requests'].append({'url':x.url,'kind':x.resource_type,'range':x.headers.get('range')}))
    host.on('response',lambda x:r['responses'].append({'url':x.url,'status':x.status,'contentRange':x.headers.get('content-range')}))
    await host.goto('http://127.0.0.1:8765/?quality=balanced&normalStream=1&paused=1',wait_until='domcontentloaded',timeout=120000)
    await host.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=600000);f=next(x for x in host.frames if '/'+RID+'/' in x.url);assert '/'+RID+'/' in f.url
    await f.wait_for_function("window.__normalStreamViewerQA && __normalStreamViewerQA().detail.phase==='full'&&assemblyInspect().presentation.interactive",timeout=600000);await host.locator('#watch-loading').wait_for(state='hidden',timeout=30000)
    initial=await asyncio.wait_for(f.evaluate(SNAP),30);assert_snapshot(initial['runtime']);assert initial['canvasSame'] and not initial['telemetry']['contexts'];r['initial']=initial;nav=len(r['navigation']);origintime=initial['telemetry']['timeOrigin'];canvas=initial['canvas'];modelRequests=lambda:sum('rebuild/assembly.glb' in x['url'] or 'optimized-assets/rebuild__assembly.' in x['url'] for x in r['requests']);initialModelRequests=modelRequests();assert initialModelRequests>0
    async def snap(label):
     s=await asyncio.wait_for(f.evaluate(SNAP),30);assert s['canvasSame'] and s['canvas']==canvas and s['telemetry']['timeOrigin']==origintime and not s['telemetry']['contexts'];assert len(r['navigation'])==nav,'navigation/reload';assert modelRequests()==initialModelRequests,'baseline model requested again during UI flow';assert_snapshot(s['runtime']);r['steps'].append({'name':label,'snapshot':s});return s
    async def capture(label):
     before=await snap(label+'-before');box=await host.frame_locator('#watch-viewer').locator('#stage').bounding_box(timeout=30000);assert box and box['width']>200 and box['height']>200
     await asyncio.wait_for(host.screenshot(path=str(E/(label+'.png')),clip=box),180);im=Image.open(E/(label+'.png')).convert('RGB');assert abs(im.width-round(box['width']))<=1 and abs(im.height-round(box['height']))<=1 and max(ImageStat.Stat(im).stddev)>5
     after=await snap(label+'-after');assert_same_texture_bindings(before['runtime'],after['runtime']);assert stable(before['runtime'])==stable(after['runtime']);return after
    async def close():
     if await f.locator('#context').is_visible():await f.locator('#close').click(timeout=30000)
    await capture('front')
    await f.locator('button[data-mode="settings"]').click(timeout=30000);await snap('settings-panel-canvas-stable');await f.locator('#atelier-tools button[data-camera="lug"]').click(timeout=30000);await close();await f.wait_for_function("assemblyInspect().view==='lug'&&__composedCameraSettled()&&__normalStreamViewerQA().configuration.camera.target.every((v,i)=>Math.abs(v-[0,22.4,-.95][i])<1e-7)",timeout=30000);await capture('lugs')
    await f.locator('#home').click(timeout=30000);await f.wait_for_function("assemblyInspect().view!=='lug'&&__composedCameraSettled()",timeout=30000);await snap('reset-from-lugs')
    await f.locator('.task-dock [data-mode="explode"]').click(timeout=30000);await f.locator('#atelier-explosion').wait_for(state='visible',timeout=30000);await f.wait_for_function('assemblyInspect().explosion.amount>.5',timeout=60000);await snap('exploded-panel-canvas-stable');await f.locator('#atelier-reassemble').click(timeout=30000);await f.wait_for_function('assemblyInspect().explosion.amount<.001',timeout=60000);await close();await f.locator('#home').click(timeout=30000);s=await snap('reassembled-reset');assert s['runtime']['inspect']['renderQuality']=='balanced'
    await f.locator('button[data-mode="settings"]').click(timeout=30000);await f.locator('#atelier-tools button[data-camera="back"]').click(timeout=30000);await close();await f.wait_for_function("assemblyInspect().view==='back'&&__composedCameraSettled()",timeout=30000);await capture('rear')
    parts=[x for x in r['responses'] if 'outer-normal-4k.ktx2.part' in x['url']];assert len(parts)==2 and sorted(x['status'] for x in parts)==[200,206],parts
    ranged=next(x for x in parts if x['status']==206);assert ranged['contentRange']=='bytes 4389496-8388607/8388608'
    assert not r['errors'];r['functionalComplete']=True
   except BaseException as e:r['failure']=repr(e);raise
   finally:
    if browser:
     try:await asyncio.wait_for(browser.close(),30);r['normalClose']=True
     except BaseException as e:r['cleanupFailure']=repr(e);raise
  r['passed']=True
 finally:(E/'REPORT.json').write_text(json.dumps(r,indent=2))
asyncio.run(asyncio.wait_for(main(),1200))
