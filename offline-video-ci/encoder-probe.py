import asyncio,json,pathlib,time
from playwright.async_api import async_playwright
B=json.loads(pathlib.Path('offline-output/build.json').read_text())
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for mode in ['readpixels']:
   ctx=await browser.new_context(viewport={'width':640,'height':480});page=await ctx.new_page();page.set_default_timeout(90000)
   if mode=='software':await ctx.add_init_script("""(()=>{const fn=VideoEncoder.prototype.configure;VideoEncoder.prototype.configure=function(c){return fn.call(this,{...c,hardwareAcceleration:'prefer-software',latencyMode:'realtime'})}})()""")
   if mode=='cpu':await ctx.add_init_script("""(()=>{const Native=VideoFrame;window.VideoFrame=class extends Native{constructor(source,options){if(source instanceof HTMLCanvasElement){const c=document.createElement('canvas');c.width=source.width;c.height=source.height;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(source,0,0);const data=ctx.getImageData(0,0,c.width,c.height);super(data.data,{...options,format:'RGBA',codedWidth:c.width,codedHeight:c.height});}else super(source,options)}}})()""")
   if mode=='readpixels':await ctx.add_init_script("""(()=>{const Native=VideoFrame;window.VideoFrame=class extends Native{constructor(source,options){if(source instanceof HTMLCanvasElement){const gl=source.getContext('webgl2'),w=source.width,h=source.height,stride=w*4,data=new Uint8Array(stride*h),row=new Uint8Array(stride);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,data);for(let y=0;y<Math.floor(h/2);y++){const a=y*stride,b=(h-1-y)*stride;row.set(data.subarray(a,a+stride));data.copyWithin(a,b,b+stride);data.set(row,b);}super(data,{...options,format:'RGBA',codedWidth:w,codedHeight:h});}else super(source,options)}}})()""")
   try:
    await page.goto('http://127.0.0.1:8765/'+B['releasePath']+'/atelier-preview.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa',wait_until='domcontentloaded')
    await page.locator('body[data-ready="true"]').wait_for(timeout=240000);await page.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"')
    await page.locator('.task-dock [data-mode=capture]').click();await page.locator('[data-proxy=record-scene]').click();await page.locator('.aerial-video-dialog[open]').wait_for()
    start=time.monotonic();passed=False
    for _ in range(40):
     await page.wait_for_timeout(5000);state=await page.evaluate('({video:assemblyInspect().videoExport,status:document.getElementById("viewer-status").textContent})');print(mode,json.dumps(state),flush=True)
     if (state['video']['progress'] or {}).get('completed',0)>=8:passed=True;break
     if not state['video']['active']:break
    print('PROBE_RESULT',json.dumps({'mode':mode,'passed8frames':passed,'seconds':time.monotonic()-start,'state':state}),flush=True)
    if state['video']['active']:await page.locator('.aerial-video-dialog button').click();await page.wait_for_function('!assemblyInspect().videoExport.active')
   except Exception as e:print('PROBE_ERROR',mode,repr(e),flush=True)
   finally:await ctx.close()
  await browser.close()
asyncio.run(main())
