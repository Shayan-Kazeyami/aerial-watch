import asyncio,json,hashlib,io
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from playwright.async_api import async_playwright
Q=Path(__file__).resolve().parent;identities=json.loads((Q/'QA_CLOSURE.json').read_text());errors=[];console=[];requests=[];rows=[]
seed="""(()=>{let s=0x317;Math.random=()=>{s=(1664525*s+1013904223)>>>0;return s/4294967296;};})();"""
async def run():
 result={'passed':False,'errors':errors,'rows':rows,'scope':'Targeted actual viewer ownership/material/pointer/lifecycle gate. AO disabled identically; seeded Math.random. Synthetic PageTransitionEvent exercises actual pagehide handler. Not physical-device/GPU destruction proof.'};browser=None
 try:
  async with async_playwright()as p:
   try:
    browser=await asyncio.wait_for(p.chromium.launch(headless=True,chromium_sandbox=True),45);result['browserVersion']=browser.version
    for route in ['raw','meshopt']:
     pictures={};states={}
     for label,arm,glass in [('A','baseline',False),('B','candidate',False),('A2','baseline',False),('AG','baseline',True),('BG','candidate',True)]:
      result['currentArm']={'route':route,'label':label,'arm':arm,'sourceGlass':glass}
      context=await browser.new_context(viewport={'width':1280,'height':900},device_scale_factor=1);await context.add_init_script(seed);page=await context.new_page();page.set_default_timeout(30000);page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda e:console.append({'type':e.type,'text':e.text}));arm_requests=[];page.on('request',lambda r:arm_requests.append(r.url));rid=identities[arm]['rid'];base=f'http://127.0.0.1:8873/prepared-{arm}/preview-b/releases/{rid}/';url=base+f'g317-qa.html?quality=efficient&face=svg04&leather=craft14&finish=studio4&crystal=clear&cap=satin&assets={route}&light=studio4&antialias=smaa&paused=1&normalStream=1&ao=off&view=back'+('&backplate=source'if glass else'')
      await page.goto(url,wait_until='domcontentloaded',timeout=120000);await page.wait_for_function('window.__g317QA?.ready()',timeout=600000)
      for name,expected in identities[arm]['namedQAFiles'].items():
       data=await(await page.request.get(base+name)).body();assert hashlib.sha256(data).hexdigest()==expected,name
      assert any('/g317-qa-review.js' in u for u in arm_requests),'named QA script not requested'
      async def settled():
       await page.wait_for_function('__g317QA.ready()',timeout=60000)
       ack=await page.evaluate("""()=>new Promise((resolve,reject)=>{const id=(window.__g317FrameSerial=(window.__g317FrameSerial||900000)+1);let timer;const done=e=>{if(e.detail?.requestId!==id)return;clearTimeout(timer);document.removeEventListener('atelier:capture-frame-rendered',done);resolve(e.detail);};document.addEventListener('atelier:capture-frame-rendered',done);timer=setTimeout(()=>{document.removeEventListener('atelier:capture-frame-rendered',done);reject(Error('No matching real composer-render acknowledgement'));},60000);document.dispatchEvent(new CustomEvent('atelier:request-capture-frame',{detail:{requestId:id}}));})""")
       state=await page.evaluate('__g317QA.state()');assert ack['dimensions'][2:]==state['canvas'];rows.append({'route':route,'label':label,'renderAck':ack});return state
      async def settings():
       await page.locator('.atelier-more[data-mode="settings"]').click();await page.locator('#context[data-tool="settings"] #atelier-inspection-host').wait_for(state='visible');await settled()
      async def close_panel():
       if await page.locator('#close').is_visible():await page.locator('#close').click()
       return await settled()
      async def pick_cover():
       target=await page.evaluate('__g317QA.pickTarget()');assert target;await page.mouse.click(target['x'],target['y']);await page.wait_for_function("window.assemblyInspect().selected.includes('Backplate / satin metal rear cover insert')");await settled();await page.locator('#context[data-tool="selection"] [data-proxy="clear"]').click();await close_panel();assert not(await settled())['inspection']['selected'];return target
      state=await settled();assert state['backend']=='WebGL2'and state['ao']is False;assert state['shared']==(arm=='candidate');assert state['inspection']['backplate']['audit'].get('geometryOwnership')==('borrowed-source-root'if arm=='candidate'else None)
      hashes=await page.evaluate('__g317QA.hashes()');assert hashes=={'position':'3a51a001b8f2aea611c4e9c9c770edd4c0fdfe2f4d15696d978a0b13ccaf9145','normal':'c9ff1c1cc73215addf85f0aca31e057c35260108d893d98bab7820dae50c4372','uv':'8ff20efa0cff3bc1add910a589bcd4bcede7966f87d17f832184e22bcc6de2cb','index':'2323dce09ee845a79da797feaabf4e4a43c5ccd7210a75a2753f34a1577924cc'}
      # Explore intentionally resets Face; restore Reverse through visible Settings controls afterward.
      await page.locator('.task-dock [data-mode="explore"]').click();await settled();await settings();await page.locator('#context[data-tool="settings"] [data-camera="back"]').click();await settled()
      await page.locator('#atelier-inspection-host [data-inspection="hideStrap"]').click();await settled();await close_panel()
      state=await settled();assert state['inspection']['view']=='back'and state['inspection']['inspectionDisplay']['hideStrap']is True;assert state['inspection']['backplate']['visible']==(not glass);assert not glass or state['sourceVisible'];assert glass or(state['coverMaterial']['name']=='Ruthenium / circular brushed charcoal'and state['coverMaterial']['color']==0x3f464d and state['coverMaterial']['metalness']==1 and state['coverMaterial']['roughness']==.39 and state['coverMaterial']['opacity']==1 and not state['coverMaterial']['transparent'])
      picture=await asyncio.wait_for(page.locator('#assembly-canvas').screenshot(path=str(Q/f'{route}-{label}.png')),120);image=Image.open(io.BytesIO(picture)).convert('RGBA');assert max(ImageStat.Stat(image.convert('RGB')).stddev)>5,'blank canvas';pictures[label]=image;states[label]=state;rows.append({'route':route,'label':label,'arm':arm,'state':state,'sourceGeometryHashes':hashes,'canvasPngSHA256':hashlib.sha256(picture).hexdigest()})
      if label=='B':
       target=await pick_cover();await settings();material=state['coverMaterial'];source_material=state['sourceMaterial']
       for key in ['transparentBackplate','solidWireframe']:
        control=page.locator(f'#atelier-inspection-host [data-inspection="{key}"]');await control.click();on=await settled();assert on['inspection']['inspectionDisplay'][key]is True
        if key=='transparentBackplate':assert on['coverMaterial']['opacity']==.12 and on['coverMaterial']['transparent']and not on['coverMaterial']['depthWrite']
        else:assert on['overlayCount']>0 and on['inspection']['inspectionDisplay']['materialVariants']>0
        await page.locator('#assembly-canvas').screenshot(path=str(Q/f'{route}-B-{key}-rendered.png'))
        await control.click();off=await settled();assert off['inspection']['inspectionDisplay'][key]is False and off['coverMaterial']==material and off['sourceMaterial']==source_material and off['overlayCount']==0
       await close_panel();restored=Image.open(io.BytesIO(await page.locator('#assembly-canvas').screenshot(path=str(Q/f'{route}-B-restored.png')))).convert('RGB');assert ImageChops.difference(pictures['B'].convert('RGB'),restored).getbbox()is None,'opaque restoration pixel mismatch'
       # Native bridge view buttons exercise real production handlers, not visibility overrides.
       await page.locator('[data-view="interior"]').evaluate('(e)=>e.click()');await settled();assert not(await settled())['inspection']['backplate']['visible'];await page.locator('[data-view="back"]').evaluate('(e)=>e.click()');await settled();assert(await settled())['inspection']['backplate']['visible']
       await page.locator('.task-dock [data-mode="explode"]').click();await page.locator('#atelier-explode-full').click();await settled();assert(await settled())['inspection']['explosion']['amount']>0
       await page.locator('#atelier-reassemble').click();await settled();await close_panel();await page.locator('[data-view="back"]').evaluate('(e)=>e.click()');await settled();repeat_target=await pick_cover();rows.append({'route':route,'repeatPointerAfterReset':repeat_target})
       before=await settled();await page.evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:false}))");after=await page.evaluate('__g317QA.state()');assert after['disposed']and after['resources']['disposed']and not after['resources']['active']and not after['coverAttached'];assert after['observed']['sourceDispose']==1 and after['observed']['privateMaterialDispose']==1;assert not any('Viewer resource cleanup failed' in x['text']for x in console)
       await page.reload(wait_until='domcontentloaded');await page.wait_for_function('__g317QA?.ready()',timeout=600000);assert(await settled())['shared'];rows.append({'route':route,'target':target,'beforeDispose':before,'afterDispose':after,'freshReloadRecreated':True})
      expected_marker='/optimized-assets/rebuild__assembly.meshopt.glb.gz'if route=='meshopt'else'/rebuild/assembly.glb';assert any(expected_marker in u for u in arm_requests),'requested asset route missing';assert route!='meshopt'or not any('/rebuild/assembly.glb' in u for u in arm_requests),'compressed route fell back to raw';requests.append({'route':route,'label':label,'urls':arm_requests});await context.close()
     for left,right in [('A','A2'),('A','B'),('AG','BG')]:
      assert pictures[left].size==pictures[right].size;diff=ImageChops.difference(pictures[left].convert('RGB'),pictures[right].convert('RGB'));assert diff.getbbox()is None,f'{route} pixel mismatch {left}/{right}'
      assert states[left]['sourceMaterial']==states[right]['sourceMaterial'];assert states[left]['canvas']==states[right]['canvas']and states[left]['camera']==states[right]['camera']and states[left]['projection']==states[right]['projection'];rows.append({'route':route,'pixelExactPair':[left,right]})
    assert not errors;result['passed']=True
   finally:
    if browser:await asyncio.wait_for(browser.close(),30)
 finally:
  result['console']=console;result['requests']=requests;(Q/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
asyncio.run(asyncio.wait_for(run(),1350))
