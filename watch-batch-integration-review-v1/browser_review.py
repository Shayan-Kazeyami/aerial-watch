"""Local-only CI software WebGL gate. Never deploys or uses repository secrets."""
import asyncio,json,pathlib,threading,http.server,socketserver
from playwright.async_api import async_playwright
from PIL import Image
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'watch-batch-browser-evidence';OUT.mkdir(exist_ok=True)
RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
PROBE=(ROOT/'next-bottleneck-qa/probe.js').read_text()+'''\nwindow.batchReviewFixedPose=()=>{settingSeconds=0;applyClockPose(clock.seek(0));dirty=true;};window.batchReviewContext=()=>{const gl=renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return {webgl2:gl instanceof WebGL2RenderingContext,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),vendor:ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):gl.getParameter(gl.VENDOR),batch:mechanismBatch?.snapshot(),backend:GPU?'webgpu':'webgl',normalState:progressiveNormalState,clock:clock.snapshot(),camera:camera.matrixWorld.elements.slice(),projection:camera.projectionMatrix.elements.slice(),readyForReview:!cameraTween&&!['waiting-for-first-frame','upgrading'].includes(progressiveNormalState)};};'''
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def log_message(self,*a):pass
server=socketserver.TCPServer(('127.0.0.1',8765),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
report={'software_rendering_requested':True,'physical_gpu_or_device_performance_verified':False,'deployed':False,'runs':[]}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for rid in [RID,'watch-batch-review-local']:
    page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=1,is_mobile=True,has_touch=True);page.set_default_timeout(240000)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    async def intercept(route):
     response=await route.fetch();await route.fulfill(response=response,body=(await response.text())+'\n'+PROBE)
    await page.route('**/assembly-review.js*',intercept)
    result={'release':rid,'errors':errors};report['runs'].append(result)
    await page.goto(f'http://127.0.0.1:8765/preview-b/releases/{rid}/atelier-preview.html?quality=efficient',wait_until='domcontentloaded')
    await page.locator('body[data-ready=true]').wait_for();await page.wait_for_function('typeof batchReviewContext==="function"');await page.evaluate('bottleneckQA.freeze()');await page.wait_for_function('batchReviewContext().readyForReview');await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"');await page.wait_for_timeout(2000);await page.evaluate('batchReviewFixedPose()')
    result['context']=await page.evaluate('batchReviewContext()')
    assert result['context']['backend']=='webgl' and result['context']['webgl2'],result
    assert result['context']['batch']['batches']>0,'No batches exercised, cannot accept GPU gate'
    samples=[]
    for enabled in [True,False]:
     sample=await page.evaluate('(batch)=>bottleneckQA.sample({batch,profile:"efficient",explode:0,finish:true})',enabled);samples.append(sample)
     await page.locator('#assembly-canvas').screenshot(path=str(OUT/f'{rid}-{enabled}.png'),style='.crown-hotspot,.crown-halo,.atelier-first-use{visibility:hidden!important}')
    result['samples']=samples
    a=np.asarray(Image.open(OUT/f'{rid}-True.png')).astype(float);c=np.asarray(Image.open(OUT/f'{rid}-False.png')).astype(float);d=np.abs(a-c)
    result['pixel_diff']={'mean':float(d.mean()),'fraction_over_8':float((d.max(axis=2)>8).mean()),'image_std':float(a.std())}
    assert a.std()>2,'Blank render'
    assert samples[0]['render']['triangles']==samples[1]['render']['triangles'],'Geometry count changed'
    result['batch_original_pixel_gate_pass']=bool(d.mean()<.1 and (d.max(axis=2)>8).mean()<.001)
    if rid=='watch-batch-review-local':assert result['batch_original_pixel_gate_pass'],'Candidate batch/original visual mismatch'
    assert not errors,errors
    await page.close()
   cross=[]
   for mode in [True,False]:
    a=np.asarray(Image.open(OUT/f'{RID}-{mode}.png')).astype(float);c=np.asarray(Image.open(OUT/f'watch-batch-review-local-{mode}.png')).astype(float);d=np.abs(a-c)
    item={'mode':mode,'mean':float(d.mean()),'fraction_over_8':float((d.max(axis=2)>8).mean())};cross.append(item)
   report['fixed_pose_baseline_candidate']=cross
   assert all(x['mean']<.1 and x['fraction_over_8']<.001 for x in cross),'Fixed-pose baseline/candidate mismatch'
   report['passed']=True
  finally:
   (OUT/'REPORT.json').write_text(json.dumps(report,indent=2));await b.close()
try:asyncio.run(main())
finally:server.shutdown()
