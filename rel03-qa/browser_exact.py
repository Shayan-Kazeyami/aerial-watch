"""Exercise the exact REL-03 sealed checkout, without interception or overlays."""
import asyncio,json,hashlib,pathlib,subprocess,time,os
from playwright.async_api import async_playwright

RID='e1d6f75a57a44d0ceba1ff3be1d92e7205fdc0e95b256a576a305bea27ad4f9b'
URL=f'http://127.0.0.1:8765/preview-b/releases/{RID}/'
NAMES=('assembly-offline-video.js','assembly-video-dialog.js','assembly-video-export.js')
HERE=pathlib.Path(__file__).resolve().parent;OUT=HERE/'output';OUT.mkdir(exist_ok=True)
dhash=lambda d:hashlib.sha256(d).hexdigest()
policy=os.getenv('REL03_TEST_SIZE');assert policy in ('view','compact')
report={'tested_size':policy,'base_release':RID,'production_changed':False,'software_browser_only':True,'bound_modules':{},'route_overlays':0,'release_http_errors':[],'page_errors':[],'downloads':{}}
def inspect(path):
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]))
    s=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert int(s['nb_read_frames'])==240 and s['r_frame_rate']=='30/1',s
    assert abs(float(probe['format']['duration'])-8)<.025,probe['format']
    first=path.with_suffix('.first.png');middle=path.with_suffix('.seek.png')
    for stem,sec in [(first,'0'),(middle,'4.0')]:
        subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-ss',sec,'-i',str(path),'-frames:v','1',str(stem)],check=True)
        assert stem.stat().st_size>1024
    return {'width':s['width'],'height':s['height'],'frame_count':240,'duration':float(probe['format']['duration']),'codec':s['codec_name'],'file_bytes':path.stat().st_size,'sha256':dhash(path.read_bytes()),'seek_decoded':True}
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'])
    page=await b.new_page(viewport={'width':360,'height':500},device_scale_factor=1,is_mobile=True,has_touch=True,reduced_motion='reduce',accept_downloads=True)
    page.set_default_timeout(180000)
    page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
    page.on('response',lambda r:report['release_http_errors'].append({'url':r.url,'status':r.status}) if '/preview-b/releases/' in r.url and r.status>=400 else None)
    requested=set()
    page.on('request',lambda r:requested.add(r.url.split('?')[0]))
    count=[];page.on('download',lambda d:count.append(d))
    try:
      response=await page.request.get(URL+'deployment-manifest.json');assert response.ok
      manifest=await response.json();assert manifest['releaseId']==RID
      items={r['path']:r for r in manifest['localFiles'] if r['path'] in NAMES}
      assert len(items)==3
      for n, spec in items.items():
        module=await page.request.get(URL+n);body=await module.body()
        assert module.ok and dhash(body)==spec['sha256'] and len(body)==spec['sizeBytes'],n
        assert body==(HERE/'runtime'/n).read_bytes(),n
        report['bound_modules'][n]=spec['sha256']
      await page.goto(URL+'atelier-preview.html?quality=efficient',wait_until='domcontentloaded')
      await page.locator('body[data-ready=true]').wait_for(timeout=300000)
      await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"')
      await page.evaluate("""()=>{for(const id of ['animate','animate-movement']){const e=document.getElementById(id);if(e?.checked){e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}}}""")
      dock=page.locator('.task-dock [data-mode=capture]')
      button=page.locator('#context [data-proxy=record-scene]')
      dialog=page.get_by_role('dialog')
      canvas=page.locator('#assembly-canvas')
      async def begin_video():
        # Existing full-stage capture handoff intentionally closes the capture panel.
        await dock.click(force=True)
        await button.wait_for(state='visible')
        await page.wait_for_function('!document.querySelector("#context [data-proxy=record-scene]").disabled')
        await button.click()
        await dialog.get_by_role('group',name='Video resolution').wait_for()
        assert await page.locator('#context').evaluate('(e)=>e.hidden')
        assert not await page.evaluate('assemblyInspect().videoExport.active')
        assert await dialog.locator('[value=view]').is_checked()
      async def closed_cleanly():
        await dialog.wait_for(state='hidden')
        await page.wait_for_function('!assemblyInspect().videoExport.active')
        assert await dock.evaluate('(e)=>document.activeElement===e')
        assert await canvas.bounding_box()==box
        assert await canvas.evaluate('(c)=>[c.width,c.height]')==dims
        after=await page.evaluate('assemblyInspect()')
        assert after['camera']==baseline['camera'] and after['target']==baseline['target']
        assert not after['animation'] and not after['interiorAnimation']
      await begin_video()
      box=await canvas.bounding_box()
      dims=await canvas.evaluate('(c)=>[c.width,c.height]')
      baseline=await page.evaluate('assemblyInspect()')
      report['source_dims']=dims
      assert set(report['bound_modules'])==set(NAMES) and all(URL+n in requested for n in NAMES)
      await page.screenshot(path=str(OUT/'resolution-choices.png'))
      await page.keyboard.press('Escape');await closed_cleanly()
      assert len(count)==0
      report['cancel_before_render']=True
      await begin_video();await dialog.locator('[value=compact]').check()
      await dialog.get_by_role('button',name='Render 8s video').click()
      await page.wait_for_function('assemblyInspect().videoExport.progress?.completed>=1')
      cancelled_at=(await page.evaluate('assemblyInspect().videoExport.progress')).get('completed')
      assert cancelled_at>=1
      await dialog.get_by_role('button',name='Cancel render').click()
      await closed_cleanly()
      assert len(count)==0
      report['cancel_active_render']=True
      report['cancelled_at_frame']=cancelled_at
      report['cancel_restored_focus_camera_and_canvas']=True
      for size in [policy]:
        await begin_video();await dialog.locator(f'[value={size}]').check()
        desc=await dialog.locator(f'[data-video-size={size}]').inner_text()
        encoded=list(map(int,desc.split('·')[-1].strip().split(' × ')))
        started=time.monotonic();trace=[];report['progress_trace']=trace
        async def track():
          while True:
            try:
              state=await page.evaluate('assemblyInspect().videoExport')
              sample={'seconds':round(time.monotonic()-started,2),'state':state}
              trace.append(sample)
              (OUT/'RENDER_PROGRESS.json').write_text(json.dumps(trace,indent=2))
              print(json.dumps(sample),flush=True)
            except Exception: pass
            await asyncio.sleep(15)
        monitor=asyncio.create_task(track())
        try:
          async with page.expect_download(timeout=900000) as evt:await dialog.get_by_role('button',name='Render 8s video').click()
          download=await evt.value
        finally:
          monitor.cancel()
          try:await monitor
          except asyncio.CancelledError:pass
        target=OUT/f'{size}.webm';await download.save_as(target)
        await closed_cleanly()
        r=await asyncio.to_thread(inspect,target)
        assert [r['width'],r['height']]==encoded,(r,encoded)
        if size=='view':assert encoded==dims
        else:assert all(a<b for a,b in zip(encoded,dims)) and max(encoded)<=540
        report['downloads'][size]={**r,'displayed_dimensions':encoded,'live_canvas_restored':True,'wall_seconds':round(time.monotonic()-started,2)}
      assert len(count)==1 and not report['page_errors'] and not report['release_http_errors'], report
      report['passed']=True
    except Exception as e:
      report['passed']=False;report['failure']=repr(e)
      try:await asyncio.wait_for(page.screenshot(path=str(OUT/'failure.png')),10)
      except Exception:pass
      raise
    finally:
      (OUT/'BROWSER_REPORT.json').write_text(json.dumps(report,indent=2))
      await b.close()
asyncio.run(main())
