import asyncio,json,hashlib,io,base64,math,os,importlib.util
from identity import ResponseIdentity,expected_named
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from playwright.async_api import async_playwright
Q=Path(__file__).resolve().parent;identities=json.loads((Q/'QA_CLOSURE.json').read_text());errors=[];console=[];requests=[];rows=[];expected=json.loads((Q/'EXPECTED_EXECUTION.json').read_text());assert identities==expected['g317'];executed=[]
def same_pixels(a,b):
 return a.size==b.size and ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox()is None and ImageChops.difference(a.getchannel('A'),b.getchannel('A')).getbbox()is None
def target_stats(image,roi,required=False):
 pixels=[image.getpixel(tuple(point))for point in roi['samples']];luma=sorted(.2126*r+.7152*g+.0722*b for r,g,b,a in pixels);n=len(luma);mean=sum(luma)/n;std=math.sqrt(sum((v-mean)**2 for v in luma)/n);p05=luma[int((n-1)*.05)];p95=luma[int((n-1)*.95)];black=sum(all(c<=2 for c in rgba[:3])for rgba in pixels)/n;white=sum(any(c>=253 for c in rgba[:3])for rgba in pixels)/n
 stats={'samples':n,'p05':p05,'p95':p95,'range90':p95-p05,'std':std,'blackClipFraction':black,'anyChannelWhiteClipFraction':white,'opaqueFraction':sum(p[3]>=250 for p in pixels)/n,'scope':'Target-ray attributed readback region numerical witness, not material acceptance. Human paired near/grazing review mandatory.'}
 if required:assert p95-p05>=12 and std>=4 and black<.2 and white<.2 and stats['opaqueFraction']>=.99,'Target opaque ROI lacks nonblank/nonclipped highlight structure'
 return stats
seed="""(()=>{let s=0x317;Math.random=()=>{s=(1664525*s+1013904223)>>>0;return s/4294967296;};})();"""
async def run():
 result={'executedSourceReceipts':executed,'githubCommit':os.environ.get('GITHUB_SHA'),'passed':False,'errors':errors,'rows':rows,'scope':'Targeted actual viewer ownership/material/pointer/lifecycle gate. AO disabled identically; seeded Math.random. Synthetic PageTransitionEvent exercises actual pagehide handler. Not physical-device/GPU destruction proof.'};browser=None
 try:
  async with async_playwright()as p:
   try:
    browser=await asyncio.wait_for(p.chromium.launch(headless=True,chromium_sandbox=True),45);result['browserVersion']=browser.version
    for route in ['raw','meshopt']:
     pictures={};states={};grazing_pictures={};grazing_states={}
     for label,arm,glass in [('A','baseline',False),('B','candidate',False),('A2','baseline',False),('AG','baseline',True),('BG','candidate',True)]:
      result['currentArm']={'route':route,'label':label,'arm':arm,'sourceGlass':glass}
      context=await browser.new_context(viewport={'width':1280,'height':900},device_scale_factor=1);await context.add_init_script(seed);page=await context.new_page();page.set_default_timeout(30000);page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda e:console.append({'type':e.type,'text':e.text}));arm_requests=[];page.on('request',lambda r:arm_requests.append(r.url));rid=identities[arm]['rid'];base=f'http://127.0.0.1:8873/prepared-{arm}/preview-b/releases/{rid}/';url=base+f'g317-qa.html?quality=efficient&face=svg04&leather=craft14&finish=studio4&crystal=clear&cap=satin&assets={route}&light=studio4&antialias=smaa&paused=1&normalStream=1&ao=off&view=back'+('&backplate=source'if glass else'')
      collector=ResponseIdentity(page,expected_named(base,expected['g317'][arm]['namedQAFiles']));executed.append({'route':route,'label':label,'records':collector.records,'errors':collector.errors})
      await page.goto(url,wait_until='domcontentloaded',timeout=120000);await page.wait_for_function('window.__g317QA?.ready()',timeout=600000)
      for name,expected in identities[arm]['namedQAFiles'].items():
       data=await(await page.request.get(base+name)).body();assert hashlib.sha256(data).hexdigest()==expected,name
      assert any('/g317-qa-review.js' in u for u in arm_requests),'named QA script not requested'
      async def settled():
       await page.wait_for_function('__g317QA.ready()',timeout=60000)
       ack=await page.evaluate("""()=>new Promise((resolve,reject)=>{const id=(window.__g317FrameSerial=(window.__g317FrameSerial||900000)+1);let timer;const done=e=>{if(e.detail?.requestId!==id)return;clearTimeout(timer);document.removeEventListener('atelier:capture-frame-rendered',done);resolve(e.detail);};document.addEventListener('atelier:capture-frame-rendered',done);timer=setTimeout(()=>{document.removeEventListener('atelier:capture-frame-rendered',done);reject(Error('No matching real composer-render acknowledgement'));},60000);document.dispatchEvent(new CustomEvent('atelier:request-capture-frame',{detail:{requestId:id}}));})""")
       state=await page.evaluate('__g317QA.state()');assert ack['dimensions'][2:]==state['canvas'];rows.append({'route':route,'label':label,'renderAck':ack});return state
      async def capture_canvas(path):
       await page.wait_for_function('window.__g317QA?.ready()',timeout=60000)
       value=await page.evaluate("""()=>new Promise((resolve,reject)=>{const id=(window.__g317FrameSerial=(window.__g317FrameSerial||900000)+1);let timer;const done=e=>{if(e.detail?.requestId!==id)return;clearTimeout(timer);document.removeEventListener('atelier:capture-frame-rendered',done);try{const png=window.__g317QA.canvasPNG(),roi=window.__g317QA.targetRegion();resolve({ack:e.detail,png,roi});}catch(error){reject(error);}};document.addEventListener('atelier:capture-frame-rendered',done);timer=setTimeout(()=>{document.removeEventListener('atelier:capture-frame-rendered',done);reject(Error('No real render before canvas readback'));},60000);document.dispatchEvent(new CustomEvent('atelier:request-capture-frame',{detail:{requestId:id}}));})""")
       assert value['png'].startswith('data:image/png;base64,');data=base64.b64decode(value['png'].split(',',1)[1],validate=True);image=Image.open(io.BytesIO(data)).convert('RGBA');assert list(image.size)==value['ack']['dimensions'][2:];path.write_bytes(data);roi=value['roi'];assert roi['viewport']==list(image.size) and roi['visibleSamples']>=100 and roi['visibleFraction']>=.6,'Insufficient actual target ray region';assert roi['camera']==(await page.evaluate('__g317QA.cameraMatrices().world')) and roi['projection']==(await page.evaluate('__g317QA.cameraMatrices().projection'))
       stats=target_stats(image,roi,required=not glass and roi['targetOpaque'])
       path.with_suffix('.roi.json').write_text(json.dumps({'roi':roi,'stats':stats,'renderAck':value['ack']},indent=2)+'\n');rows.append({'route':route,'label':label,'canvasReadbackRenderAck':value['ack'],'file':path.name,'sha256':hashlib.sha256(data).hexdigest(),'targetRegionStats':stats,'targetRegionFile':path.with_suffix('.roi.json').name,'readback':'Synchronous inside production composer-render acknowledgement, no HTML overlay pixels'});return data
      async def settings():
       await page.locator('.atelier-more[data-mode="settings"]').click();await page.locator('#context[data-tool="settings"] #atelier-inspection-host').wait_for(state='visible');await settled()
      async def close_panel():
       if await page.locator('#close').is_visible():await page.locator('#close').click()
       return await settled()
      async def pick_cover():
       target=await page.evaluate('__g317QA.pickTarget()');assert target;await page.mouse.click(target['x'],target['y']);await page.wait_for_function("window.assemblyInspect().selected.includes('Backplate / satin metal rear cover insert')");await settled();await page.locator('#context[data-tool="selection"] [data-proxy="clear"]').click();await close_panel();assert not(await settled())['inspection']['selected'];return target
      state=await settled();assert state['backend']=='WebGL2'and state['ao']is False;assert state['shared']==(arm=='candidate');assert state['inspection']['backplate']['audit'].get('geometryOwnership')==('borrowed-source-root'if arm=='candidate'else None)
      hashes=await page.evaluate('__g317QA.hashes()');assert hashes=={'position':'3a51a001b8f2aea611c4e9c9c770edd4c0fdfe2f4d15696d978a0b13ccaf9145','normal':'c9ff1c1cc73215addf85f0aca31e057c35260108d893d98bab7820dae50c4372','uv':'8ff20efa0cff3bc1add910a589bcd4bcede7966f87d17f832184e22bcc6de2cb','index':'2323dce09ee845a79da797feaabf4e4a43c5ccd7210a75a2753f34a1577924cc'}
      if route=='raw'and label in ['A','B']:
       inventory=await page.evaluate('__g317QA.inventory()');(Q/f'inventory-{label}.json').write_text(json.dumps(inventory,indent=2)+'\n');rows.append({'route':route,'label':label,'residentMeshes':inventory['meshes'],'residentUniqueGeometries':inventory['uniqueGeometryIdentities']})
      # Explore intentionally resets Face; restore Reverse through visible Settings controls afterward.
      await page.locator('.task-dock [data-mode="explore"]').click();await settled();await settings();await page.locator('#context[data-tool="settings"] [data-camera="back"]').click();await settled()
      await page.locator('#atelier-inspection-host [data-inspection="hideStrap"]').click();await settled();await close_panel()
      state=await settled();assert state['inspection']['view']=='back'and state['inspection']['inspectionDisplay']['hideStrap']is True;assert state['inspection']['backplate']['visible']==(not glass);assert not glass or state['sourceVisible'];assert glass or(state['coverMaterial']['name']=='Ruthenium / circular brushed charcoal'and state['coverMaterial']['color']==0x3f464d and state['coverMaterial']['metalness']==1 and state['coverMaterial']['roughness']==.39 and state['coverMaterial']['opacity']==1 and not state['coverMaterial']['transparent'])
      macro=await page.evaluate('__g317QA.frameCover(false)');await settled();state=await settled();rows.append({'route':route,'label':label,'macroCalibration':macro});assert state['coverProjectedBounds']['height']>=state['canvas'][1]*.65
      picture=await asyncio.wait_for(capture_canvas(Q/f'{route}-{label}.png'),120);image=Image.open(io.BytesIO(picture)).convert('RGBA');assert max(ImageStat.Stat(image.convert('RGB')).stddev)>5,'blank canvas';pictures[label]=image;states[label]=state;
      if not glass:
       point=await page.evaluate('__g317QA.pickTarget()');assert point;rect=await page.locator('#assembly-canvas').bounding_box();px=int((point['x']-rect['x'])/rect['width']*image.width);py=int((point['y']-rect['y'])/rect['height']*image.height);assert image.getpixel((px,py))[3]>=250,'opaque target absent in actual graphics readback';rows.append({'route':route,'label':label,'opaqueTargetPixel':[px,py],'alpha':image.getpixel((px,py))[3]})
      rows.append({'route':route,'label':label,'arm':arm,'state':state,'sourceGeometryHashes':hashes,'canvasPngSHA256':hashlib.sha256(picture).hexdigest()})
      grazing=await page.evaluate('__g317QA.frameCover(true)');await settled();await page.screenshot(path=str(Q/f'{route}-{label}-context.png'));grazing_bytes=await capture_canvas(Q/f'{route}-{label}-grazing.png');grazing_pictures[label]=Image.open(io.BytesIO(grazing_bytes)).convert('RGBA');grazing_states[label]=await settled();rows.append({'route':route,'label':label,'grazingCalibration':grazing,'grazingState':await settled()});await page.evaluate('__g317QA.frameCover(false)');await settled()
      if label=='B':
       target=await pick_cover();await settings();material=state['coverMaterial'];source_material=state['sourceMaterial']
       for key in ['transparentBackplate','solidWireframe']:
        control=page.locator(f'#atelier-inspection-host [data-inspection="{key}"]');await control.click();on=await settled();assert on['inspection']['inspectionDisplay'][key]is True
        if key=='transparentBackplate':assert on['coverMaterial']['opacity']==.12 and on['coverMaterial']['transparent']and not on['coverMaterial']['depthWrite']
        else:assert on['overlayCount']>0 and on['inspection']['inspectionDisplay']['materialVariants']>0
        await capture_canvas(Q/f'{route}-B-{key}-rendered.png')
        await control.click();off=await settled();assert off['inspection']['inspectionDisplay'][key]is False and off['coverMaterial']==material and off['sourceMaterial']==source_material and off['overlayCount']==0
       await close_panel();restored=Image.open(io.BytesIO(await capture_canvas(Q/f'{route}-B-restored.png'))).convert('RGBA');assert same_pixels(pictures['B'],restored),'opaque restoration pixel mismatch'
       # Native bridge view buttons exercise real production handlers, not visibility overrides.
       await page.locator('[data-view="interior"]').evaluate('(e)=>e.click()');await settled();assert not(await settled())['inspection']['backplate']['visible'];await page.locator('[data-view="back"]').evaluate('(e)=>e.click()');await settled();assert(await settled())['inspection']['backplate']['visible']
       await page.locator('.task-dock [data-mode="explode"]').click();await page.locator('#atelier-explode-full').click();await settled();assert(await settled())['inspection']['explosion']['amount']>0
       await page.locator('#atelier-reassemble').click();await settled();await close_panel();await page.locator('[data-view="back"]').evaluate('(e)=>e.click()');await settled();repeat_target=await pick_cover();rows.append({'route':route,'repeatPointerAfterReset':repeat_target})
       before=await settled();await page.evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:false}))");after=await page.evaluate('__g317QA.state()');assert after['disposed']and after['resources']['disposed']and not after['resources']['active']and not after['coverAttached'];assert after['observed']['sourceDispose']==1 and after['observed']['privateMaterialDispose']==1;assert not any('Viewer resource cleanup failed' in x['text']for x in console)
       await page.reload(wait_until='domcontentloaded');await page.wait_for_function('window.__g317QA?.ready()',timeout=600000);assert(await settled())['shared'];rows.append({'route':route,'target':target,'beforeDispose':before,'afterDispose':after,'freshReloadRecreated':True})
      expected_marker=expected['assetRoutePaths'][route]['assembly'];assert any(expected_marker in u for u in arm_requests),'requested asset route missing';assert route!='meshopt'or not any('/rebuild/assembly.glb' in u for u in arm_requests),'compressed route fell back to raw';requests.append({'route':route,'label':label,'urls':arm_requests});rows.append({'route':route,'label':label,'executedIdentity':await collector.finish()});await context.close()
     for left,right in [('A','A2'),('A','B'),('AG','BG')]:
      assert same_pixels(grazing_pictures[left],grazing_pictures[right]),f'{route} grazing mismatch {left}/{right}';assert grazing_states[left]['camera']==grazing_states[right]['camera']and grazing_states[left]['projection']==grazing_states[right]['projection'];assert same_pixels(pictures[left],pictures[right]),f'{route} pixel mismatch {left}/{right}'
      assert states[left]['sourceMaterial']==states[right]['sourceMaterial'];assert states[left]['canvas']==states[right]['canvas']and states[left]['camera']==states[right]['camera']and states[left]['projection']==states[right]['projection'];rows.append({'route':route,'pixelExactPair':[left,right]})
    # Fresh face contexts, sequential private targets; never reuse backplate mutation state.
    face_path=Q.parent/'watch-face-evidence-batch-v3'/'driver.py';spec=importlib.util.spec_from_file_location('exact_face_evidence',face_path);face_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(face_module)
    for route in expected['routes']:
     context=await browser.new_context(viewport={'width':1280,'height':900},device_scale_factor=1);await context.add_init_script(face_module.SEED_SCRIPT);page=await context.new_page();page.set_default_timeout(60000);page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda e:console.append({'type':e.type,'text':e.text}));face_requests=[];page.on('request',lambda r:face_requests.append(r.url));rid=expected['face']['rid'];base=f'http://127.0.0.1:8873/prepared-baseline/preview-b/releases/{rid}/';collector=ResponseIdentity(page,expected_named(base,expected['face']['namedQAFiles']));executed.append({'route':route,'label':'FACE','records':collector.records,'errors':collector.errors})
     try:
      url=base+f'face-evidence.html?quality=efficient&face=svg04&leather=craft14&finish=studio4&crystal=clear&cap=satin&assets={route}&light=studio4&antialias=smaa&paused=1&normalStream=1&ao=off&view=face';await page.goto(url,wait_until='domcontentloaded',timeout=120000);records=await face_module.run_face_evidence(page,base,Q/('face-'+route));assert set(r['key']for r in records)==set(expected['face']['expectedFrameKeysPerRoute'])and len(records)==46
      marker=expected['assetRoutePaths'][route]['face'];assert any(marker in u for u in face_requests),'Actual face asset route missing';assert route!='meshopt'or not any('/premium-face/face-svg04.glb' in u for u in face_requests),'Face codec fell back to raw';rows.append({'route':route,'faceEvidenceFrames':len(records),'executedIdentity':await collector.finish(),'qualityStatus':'CAPTURED_PENDING_HUMAN_QUALITY','actualRequests':face_requests})
     finally:await context.close()
    assert not errors and not[c for c in console if c['type']=='error'];assert os.environ.get('GITHUB_SHA');result['passed']=True
   except Exception as failure:
    result['failure']=repr(failure)
    if 'page'in locals():
     try:await page.screenshot(path=str(Q/'failure-context.png'),timeout=15000)
     except Exception as screenshot_error:result['failureScreenshotError']=repr(screenshot_error)
    raise
   finally:
    if browser:await asyncio.wait_for(browser.close(),30)
 finally:
  result['console']=console;result['requests']=requests;(Q/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
asyncio.run(asyncio.wait_for(run(),1350))
