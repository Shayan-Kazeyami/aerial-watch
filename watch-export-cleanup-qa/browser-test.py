import asyncio,json,pathlib,subprocess,hashlib
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).parent;O=P/'output';O.mkdir(exist_ok=True)
async def main():
 server=subprocess.Popen(['python','-m','http.server','8765','--bind','127.0.0.1'],cwd=P,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--js-flags=--expose-gc']);page=await browser.new_page();await page.goto('http://127.0.0.1:8765/');results=[]
   for variant in ['baseline','candidate']:
    await page.goto('http://127.0.0.1:8765/')
    await page.evaluate('''async variant=>{
     const {createOfflineVideoExport}=await import('/'+variant+'/assembly-offline-video.js');
     const Native=VideoFrame;window.refs=[];window.frameCounts={opened:0,closed:0};
     window.VideoFrame=class extends Native{constructor(input,metadata){super(input,metadata);refs.push(new WeakRef(input));frameCounts.opened++;}close(){super.close();frameCounts.closed++;}};
     const canvas=document.createElement('canvas');canvas.width=3840;canvas.height=1638;canvas.style.width='384px';document.body.append(canvas);const gl=canvas.getContext('webgl2',{preserveDrawingBuffer:false});if(!gl)throw Error('No WebGL2');window.ended=0;window.scenario='success';window.renders=0;
     window.exporter=createOfflineVideoExport({canvas,gl,begin:()=>({}),renderFrame:(t,{index})=>{if(scenario==='reject')throw Error('intentional frame rejection');gl.clearColor(index/10,.2,.6,1);gl.clear(gl.COLOR_BUFFER_BIT);renders++;},end:()=>ended++,onProgress:p=>{if(p.completed===1&&scenario==='abort')exporter.cancel();if(p.completed===1&&scenario==='dispose')exporter.dispose();}});
    }''',variant)
    for scenario in ['success','success','abort','reject','success','dispose']:
     r=await page.evaluate('''async scenarioName=>{scenario=scenarioName;refs=[];let result,error=null;try{result=await exporter.start({durationMs:200,frameRate:30,size:'compact'});}catch(e){error={name:e.name,message:e.message};}window.lastBlob=result?.blob;return {scenario,error,active:exporter.active,progress:exporter.progress,ended,renders,counts:{...frameCounts},video:result?{width:result.width,height:result.height,frameCount:result.frameCount,durationMs:result.durationMs,codec:result.codec}:null};}''',scenario)
     await page.evaluate('()=>gc()');await page.wait_for_timeout(50)
     r['retainedScratchBytes']=await page.evaluate('()=>[...new Set(refs.map(r=>r.deref()).filter(Boolean))].reduce((n,b)=>n+b.byteLength,0)');r['variant']=variant
     assert not r['active'] and r['progress'] is None
     assert r['counts']['opened']==r['counts']['closed']
     if scenario=='success':
      assert r['error'] is None,r
      async with page.expect_download()as d:
       await page.evaluate('()=>{const a=document.createElement("a");a.href=URL.createObjectURL(lastBlob);a.download="video.webm";a.click();}')
      path=O/f'{variant}-{len(results)}.webm';await(await d.value).save_as(path);r['file']=path.name
     else:assert r['error'],r
     if variant=='candidate':assert r['retainedScratchBytes']==0,r
     elif scenario=='success':assert r['retainedScratchBytes']>=25159680,r
     results.append(r);print(variant,scenario,r['retainedScratchBytes'],flush=True)
   (O/'BROWSER_RESULT.json').write_text(json.dumps({'passed':True,'scope':'isolated exact modules, real software WebGL2 and WebCodecs, synthetic deterministic frames; NOT full watch or hardware performance','results':results},indent=2));await browser.close()
 finally:server.terminate()
asyncio.run(main())
