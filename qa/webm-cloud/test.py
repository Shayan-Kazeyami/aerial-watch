import asyncio,json,pathlib,traceback,subprocess,hashlib,time,base64
from playwright.async_api import async_playwright
out=pathlib.Path('webm-output');out.mkdir(exist_ok=True)
r={'target':'https://shayan-kazeyami.github.io/aerial-watch/','expectedRelease':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','errors':[],'events':[]};save=lambda:(out/'report.json').write_text(json.dumps(r,indent=2));save()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':480,'height':480},accept_downloads=True);page=await c.new_page();page.on('pageerror',lambda e:r['errors'].append(str(e)));requests=[];page.on('request',lambda req:requests.append(req.url) if 'assembly-review.js' in req.url else None)
  async def proof(route):
   response=await route.fetch();s=await response.text();s+='\nwindow.__proof=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot()});';await route.fulfill(response=response,body=s)
  await page.route('**/assembly-review.js*',proof)
  async def recorder_probe(route):
   response=await route.fetch();src=await response.text();needle='export async function inspectWebM(blob)';assert needle in src
   src=src.replace(needle,'async function inspectWebMOriginal(blob)',1)
   src+="\nexport async function inspectWebM(blob){window.__qaBlob=blob;const result=await inspectWebMOriginal(blob);window.__qaInspection=result;return result;}\n"
   await route.fulfill(response=response,body=src)
  await page.route('**/assembly-recording.js*',recorder_probe)
  await c.add_init_script("""(()=>{window.__qa={raf:0,captures:[],events:[]};const raf=window.requestAnimationFrame.bind(window);window.requestAnimationFrame=(fn)=>raf((t)=>{window.__qa.raf++;fn(t)});const cap=HTMLCanvasElement.prototype.captureStream;HTMLCanvasElement.prototype.captureStream=function(f){window.__qa.captures.push({width:this.width,height:this.height,rate:f,raf:window.__qa.raf,time:performance.now()});return cap.call(this,f)};const start=MediaRecorder.prototype.start,stop=MediaRecorder.prototype.stop;MediaRecorder.prototype.start=function(...a){window.__qa.events.push({event:'start',raf:window.__qa.raf,time:performance.now(),mime:this.mimeType});this.addEventListener('dataavailable',e=>window.__qa.events.push({event:'data',size:e.data.size,raf:window.__qa.raf,time:performance.now()}));this.addEventListener('stop',()=>window.__qa.events.push({event:'stop',raf:window.__qa.raf,time:performance.now()}));return start.apply(this,a)};MediaRecorder.prototype.stop=function(...a){window.__qa.events.push({event:'stop-request',raf:window.__qa.raf,time:performance.now()});return stop.apply(this,a)}})()""")
  try:
   await page.goto(r['target']+'?quality=efficient&leather=craft14',wait_until='domcontentloaded',timeout=60000);await page.wait_for_function("document.querySelector('#watch-viewer')?.contentWindow?.location.href.includes('atelier-preview.html')",timeout=60000);q=await (await page.query_selector('#watch-viewer')).content_frame();await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000);r['requests']=requests;assert any(r['expectedRelease'] in x for x in requests),requests
   r['proof']=await q.evaluate('__proof()');proof=r['proof'];assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and proof['leather']['geometryVerification']['actualBytes']==8579970 and proof['hybrid']['active'] and proof['hybrid']['triangles']==501830
   r['browser']=b.version;r['before']=await q.evaluate('assemblyInspect()');await q.locator('[data-mode=capture]').first.click(timeout=90000);await q.wait_for_timeout(4000)
   r['events'].append({'event':'click','time':time.time()});save()
   try:
    async with page.expect_download(timeout=120000) as d: await q.locator('[data-proxy=record-scene]').click(timeout=90000)
    dl=await d.value;path=out/'aerial-motion.webm';await dl.save_as(path);r['events'].append({'event':'download','time':time.time(),'name':dl.suggested_filename,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    p1=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,timeout=60);r['ffprobe']={'returncode':p1.returncode,'out':p1.stdout,'err':p1.stderr}
    p2=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True,timeout=120);r['decode']={'returncode':p2.returncode,'err':p2.stderr}
    p3=subprocess.run(['ffmpeg','-y','-v','error','-i',str(path),'-vf','select=eq(n\\,0)+eq(n\\,10)+eq(n\\,30)','-vsync','0',str(out/'frame-%02d.png')],capture_output=True,text=True,timeout=120);r['frames']={'returncode':p3.returncode,'err':p3.stderr,'files':[x.name for x in out.glob('frame-*.png')]};r['status']='downloaded' if p1.returncode==0 and p2.returncode==0 else 'decode-failed'
   except Exception as e:r['status']='no-download';r['downloadException']=repr(e)
   r['diagnostic']=await q.evaluate("""async()=>{const b=window.__qaBlob;return {events:window.__qa,inspection:window.__qaInspection||null,blob:b?{size:b.size,type:b.type,base64:await new Promise((res,rej)=>{let f=new FileReader();f.onload=()=>res(f.result.split(',')[1]);f.onerror=()=>rej(f.error);f.readAsDataURL(b)})}:null}}""")
   if r['diagnostic']['blob']:
    blob=r['diagnostic']['blob'];data=base64.b64decode(blob.pop('base64'));path=out/'diagnostic-rejected.webm';path.write_bytes(data);blob['sha256']=hashlib.sha256(data).hexdigest()
    for name,cmd in [('ffprobe',['ffprobe','-v','error','-show_streams','-show_format','-count_frames','-of','json',str(path)]),('decode',['ffmpeg','-v','error','-i',str(path),'-f','null','-'])]:
     p3=subprocess.run(cmd,capture_output=True,text=True,timeout=120);r['diagnostic'][name]={'returncode':p3.returncode,'stdout':p3.stdout,'stderr':p3.stderr}
   r['after']=await q.evaluate('assemblyInspect()');r['viewerStatus']=await q.locator('#viewer-status').text_content();save()
  except Exception as e:r['status']='failed';r['exception']=repr(e);r['traceback']=traceback.format_exc()
  finally:save();await c.close();await b.close()
asyncio.run(main())
