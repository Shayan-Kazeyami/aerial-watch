"""Read-only real public PNG and JSON regression via the current home iframe."""
import asyncio,hashlib,json,os,pathlib,struct,time,zlib
from playwright.async_api import async_playwright
RID='e1d6f75a57a44d0ceba1ff3be1d92e7205fdc0e95b256a576a305bea27ad4f9b'
ROOT='https://shayan-kazeyami.github.io/aerial-watch/'
PORT=os.environ['REL04_VIEWPORT']
w,h=map(int,PORT.split('x'))
OUT=pathlib.Path('rel04-public-output');OUT.mkdir(exist_ok=True)
R={'release':RID,'viewport':[w,h],'production_mutation':False,'release_http_errors':[],'javascript_errors':[],'software_chromium_only':True}
sha=lambda b:hashlib.sha256(b).hexdigest()
def png(data):
 assert data[:8]==b'\x89PNG\r\n\x1a\n'
 at=8; config=None; size=None; count=0
 while at<len(data):
  n=int.from_bytes(data[at:at+4],'big'); tag=data[at+4:at+8]; s=at+8; e=s+n
  assert e+4<=len(data)
  chunk=data[s:e]; assert int.from_bytes(data[e:e+4],'big')==zlib.crc32(tag+chunk)
  at=e+4
  if tag==b'IHDR':size=struct.unpack('>II',chunk[:8])
  if tag==b'iTXt' and chunk.startswith(b'AerialView\x00\x00\x00\x00\x00'):
   assert config is None;config=json.loads(chunk[15:])
  if tag==b'IDAT':count+=len(chunk)
  if tag==b'IEND':break
 assert at==len(data) and size and min(size)>100 and count>1024 and config
 return size,config
def vec(a,b):
 return len(a)==len(b) and all(abs(x-y)<.001 for x,y in zip(a,b))
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':w,'height':h},device_scale_factor=1,is_mobile=True,has_touch=True,reduced_motion='reduce',accept_downloads=True)
  page.set_default_timeout(180000)
  page.on('pageerror',lambda e:R['javascript_errors'].append(str(e)))
  page.on('response',lambda r:R['release_http_errors'].append([r.status,r.url]) if '/preview-b/releases/' in r.url and r.status>=400 else None)
  downloads=[];page.on('download',lambda d:downloads.append(d))
  try:
   for i in range(45):
    await page.goto(ROOT+'?rel04='+str(time.time_ns()),wait_until='domcontentloaded',timeout=30000)
    try:
     await page.wait_for_function('rid=>document.querySelector("#watch-viewer")?.src.includes(rid)',arg=RID,timeout=12000)
     break
    except Exception:
     if i==44:raise
   f=page.frame_locator('#watch-viewer')
   await f.locator('body[data-ready=true]').wait_for(timeout=300000)
   frame=next(x for x in page.frames if (ROOT+'preview-b/releases/'+RID+'/') in x.url)
   R['actual_frame_url']=frame.url
   rev=await page.request.get(ROOT+'preview-b/releases/'+RID+'/quality-study/viewer-revision.json'); assert rev.ok
   revision=(await rev.json())['digest']
   ready=lambda:frame.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"')
   await ready()
   await frame.locator('.task-dock [data-mode=inside]').click(force=True)
   await frame.locator('#context [data-camera=balance]').click(force=True)
   await frame.wait_for_function('assemblyInspect().view==="balance"'); await ready()
   live=await frame.evaluate('assemblyInspect()')
   assert live['view']=='balance'
   capture=frame.locator('.task-dock [data-mode=capture]')
   async def open_capture():
    if not await frame.locator('#context').evaluate('(e)=>!e.hidden&&e.dataset.tool==="capture"'):
     await capture.click(force=True)
    await frame.locator('#context[data-tool=capture]').wait_for(state='visible')
   async def save(selector,filename):
    await open_capture()
    loc=frame.locator(selector)
    async with page.expect_download(timeout=240000) as evt:await loc.click(force=False)
    d=await evt.value;assert d.suggested_filename==filename,d.suggested_filename
    path=OUT/filename;await d.save_as(path);return path.read_bytes()
   png_bytes=await save('#context [data-proxy=capture-scene]','aerial-studio.png')
   size,pngcfg=png(png_bytes)
   assert size==(pngcfg['viewport']['drawingBufferWidth'],pngcfg['viewport']['drawingBufferHeight'])
   assert pngcfg['view']=='balance' and vec(pngcfg['camera']['position'],live['camera']) and vec(pngcfg['camera']['target'],live['target'])
   assert pngcfg['sourceAtCapture']['status']=='verified' and pngcfg['sourceAtCapture']['digest']==revision
   jbytes=await save('#context [data-proxy=export-config]','aerial-view.json')
   saved=json.loads(jbytes)
   assert saved['version']==1 and saved['view']=='balance' and saved['options']==pngcfg['options']
   assert vec(saved['camera']['position'],pngcfg['camera']['position']) and vec(saved['camera']['target'],pngcfg['camera']['target'])
   assert saved['sourceAtCapture']['status']=='verified' and saved['sourceAtCapture']['digest']==revision
   R['exports']={'png':{'dimensions':size,'sha256':sha(png_bytes),'crc_and_itxt':True},'json':{'bytes':len(jbytes),'sha256':sha(jbytes)},'view':'balance','verified_source_digest':revision}
   await frame.locator('.task-dock [data-mode=explore]').click(force=True)
   await frame.wait_for_function('assemblyInspect().view==="face"');await ready()
   snapshot=await frame.evaluate('assemblyInspect()')
   await open_capture()
   async def load(name,data):
    async with page.expect_file_chooser(timeout=30000) as evt:await frame.locator('#atelier-import').click()
    fc=await evt.value;await fc.set_files({'name':name,'mimeType':'application/json','buffer':data})
   await load('malformed-view.json',b'{"not":"a valid Watch view"}')
   await frame.wait_for_function('[...document.querySelectorAll("#status,#atelier-panel-status")].some(x=>/Could not restore view/.test(x.textContent))')
   after_bad=await frame.evaluate('assemblyInspect()')
   assert after_bad['view']==snapshot['view'] and vec(after_bad['camera'],snapshot['camera']) and vec(after_bad['target'],snapshot['target'])
   await open_capture()
   await load('aerial-view.json',jbytes)
   await frame.wait_for_function('c=>{const v=assemblyInspect();return v.view===c.view&&c.camera.position.every((x,i)=>Math.abs(v.camera[i]-x)<.001)&&c.camera.target.every((x,i)=>Math.abs(v.target[i]-x)<.001)&&!v.animation&&!v.interiorAnimation;}',arg=saved)
   await ready()
   restored=await frame.evaluate('assemblyInspect()')
   assert restored['renderQuality']==saved['options']['quality'] and restored['crystals']==saved['options']['crystals']
   assert restored['movementOnly']==saved['options']['movementOnly']
   assert await frame.locator('#import-config').evaluate('(e)=>e.value===""')
   await page.screenshot(path=str(OUT/'restored-view.png'))
   await open_capture()
   assert await frame.locator('#context [data-proxy=export-config]').is_enabled()
   assert len(downloads)==2 and not R['javascript_errors'] and not R['release_http_errors'], R
   R.update(passed=True,invalid_import_left_scene_unchanged=True,valid_import_after_invalid=True,view_restored=restored['view'],import_pauses_motion=True,viewport_orientation='landscape' if w>h else 'portrait')
  except Exception as e:
   R.update(passed=False,failure=repr(e))
   try:await asyncio.wait_for(page.screenshot(path=str(OUT/'failure.png')),8)
   except Exception:pass
   raise
  finally:
   (OUT/'REPORT.json').write_text(json.dumps(R,indent=2)+'\n')
   await b.close()
asyncio.run(run())
