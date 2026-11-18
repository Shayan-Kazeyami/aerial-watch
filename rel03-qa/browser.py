"""Exercise the real Watch capture UI on its pinned immutable public base with exact branch-module overlays."""
import asyncio,json,hashlib,pathlib,subprocess
from playwright.async_api import async_playwright

RID='145aba103999de275e202eb0529fc66850c0e64a068f81ef876e5cfc495c70d4'
URL=f'https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/{RID}/'
NAMES=('assembly-offline-video.js','assembly-video-dialog.js','assembly-video-export.js')
HERE=pathlib.Path(__file__).resolve().parent;OUT=HERE/'output';OUT.mkdir(exist_ok=True)
dhash=lambda d:hashlib.sha256(d).hexdigest()
report={'base_release':RID,'production_changed':False,'software_browser_only':True,'overlay':{},'page_errors':[],'downloads':{}}
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
    count=[];page.on('download',lambda d:count.append(d))
    try:
      response=await page.request.get(URL+'deployment-manifest.json');assert response.ok
      manifest=await response.json();assert manifest['releaseId']==RID
      items={r['path']:r for r in manifest['localFiles'] if r['path'] in NAMES}
      assert len(items)==3
      async def overlay(route):
        name=route.request.url.split('?',1)[0].split('/')[-1];spec=items[name]
        original=await route.fetch();body=await original.body()
        assert original.ok and dhash(body)==spec['sha256'] and len(body)==spec['sizeBytes'],name
        changed=(HERE/'runtime'/name).read_bytes()
        report['overlay'][name]={'original_sha256':spec['sha256'],'candidate_sha256':dhash(changed)}
        await route.fulfill(response=original,body=changed)
      for n in NAMES:await page.route(URL+n+'*',overlay)
      await page.goto(URL+'atelier-preview.html?quality=efficient',wait_until='domcontentloaded')
      await page.locator('body[data-ready=true]').wait_for(timeout=300000)
      await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"')
      await page.evaluate("""()=>{for(const id of ['animate','animate-movement']){const e=document.getElementById(id);if(e?.checked){e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}}}""")
      await page.locator('.task-dock [data-mode=capture]').click(force=True)
      button=page.locator('#context [data-proxy=record-scene]');await page.wait_for_function('!document.querySelector("#context [data-proxy=record-scene]").disabled')
      dialog=page.get_by_role('dialog')
      box=await page.locator('#assembly-canvas').bounding_box()
      dims=await page.locator('#assembly-canvas').evaluate('(c)=>[c.width,c.height]')
      report['source_dims']=dims
      assert set(report['overlay'])==set(NAMES)
      await button.click();await dialog.get_by_role('group',name='Video resolution').wait_for()
      assert await dialog.locator('[value=view]').is_checked()
      await page.screenshot(path=str(OUT/'resolution-choices.png'))
      await page.keyboard.press('Escape');await dialog.wait_for(state='hidden')
      await page.wait_for_function('!assemblyInspect().videoExport.active')
      assert len(count)==0 and await button.is_enabled()
      report['cancel_before_render']=True
      await button.click();await dialog.locator('[value=compact]').check()
      await dialog.get_by_role('button',name='Render 8s video').click()
      await dialog.get_by_role('button',name='Cancel render').click()
      await dialog.wait_for(state='hidden');await page.wait_for_function('!assemblyInspect().videoExport.active')
      assert len(count)==0 and await button.is_enabled()
      report['cancel_active_render']=True
      for size in ['view','compact']:
        await button.click();await dialog.locator(f'[value={size}]').check()
        desc=await dialog.locator(f'[data-video-size={size}]').inner_text()
        encoded=list(map(int,desc.split('·')[-1].strip().split(' × ')))
        async with page.expect_download(timeout=420000) as evt:await dialog.get_by_role('button',name='Render 8s video').click()
        download=await evt.value;target=OUT/f'{size}.webm';await download.save_as(target)
        await dialog.wait_for(state='hidden');await page.wait_for_function('!assemblyInspect().videoExport.active')
        assert await button.is_enabled()
        assert await page.locator('#assembly-canvas').bounding_box()==box
        assert await page.locator('#assembly-canvas').evaluate('(c)=>[c.width,c.height]')==dims
        r=await asyncio.to_thread(inspect,target)
        assert [r['width'],r['height']]==encoded,(r,encoded)
        if size=='view':assert encoded==dims
        else:assert all(a<b for a,b in zip(encoded,dims)) and max(encoded)<=540
        report['downloads'][size]={**r,'displayed_dimensions':encoded,'live_canvas_restored':True}
      assert len(count)==2 and not report['page_errors'],report['page_errors']
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
