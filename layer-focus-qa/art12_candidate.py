"""Branch-only ART-12 UI overlay test against the unchanged public release."""
import asyncio, json, os, pathlib, urllib.request, urllib.parse, re
from playwright.async_api import async_playwright

RID='145aba103999de275e202eb0529fc66850c0e64a068f81ef876e5cfc495c70d4'
BASE='http://127.0.0.1:8765/'

OUT=pathlib.Path('art12-layer-guide-output'); OUT.mkdir(exist_ok=True)
EXPECTED={
 'plate':'Structural base that locates the movement.',
 'keyless':'Winds the mainspring and sets the hands.',
 'train':'Carries stored power and regulates each tick.',
 'bridges':'Holds gear pivots and barrels in alignment.',
 'balance':'Oscillates with its hairspring to pace time.',
 'calendar':'Transfers rotation to the hands and calendar.'}
R={'base_release':RID,'candidate_only_overlay':False,'production_changed':False,
   'scope':'Exact locally served sealed release with no UI overlay; Chromium software rendering, not device/GPU performance.',
   'candidate_overlay_hits':0,'viewports':{},'errors':[],'release_http_errors':[]}

async def run():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await browser.new_page(viewport={'width':430,'height':932},device_scale_factor=1,is_mobile=True,has_touch=True,reduced_motion='reduce')
  page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  page.on('response',lambda response:R['release_http_errors'].append({'status':response.status,'url':response.url}) if '/preview-b/releases/' in response.url and response.status>=400 else None)
  try:
   await page.goto(BASE+f'preview-b/releases/{RID}/atelier-preview.html?mesh={RID[:12]}',wait_until='domcontentloaded')
   await page.wait_for_timeout(15000)
   frames=[f for f in page.frames if RID in f.url]
   assert frames,'Expected immutable release iframe did not load'
   f=frames[0]
   await f.locator('body[data-ready=true]').wait_for(timeout=240000)
   await f.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'")
   await page.wait_for_timeout(2500)
   assert not R['release_http_errors'],R['release_http_errors']
   assert R['candidate_overlay_hits']==0,R['candidate_overlay_hits']
   assert not await f.evaluate('window.__ART12_LAYER_GUIDANCE__')
   for w,h in [(430,932),(932,430)]:
    await page.set_viewport_size({'width':w,'height':h});await page.wait_for_timeout(1200)
    canvas=f.locator('#assembly-canvas');before=await canvas.bounding_box()
    await f.locator('.task-dock [data-mode=explode]').click(force=True)
    await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
    layer=f.locator('#atelier-layer-focus');note=f.locator('#atelier-explosion-note');overview=f.locator('#atelier-layer-overview');slider=f.locator('#atelier-explosion')
    baseline=(await note.inner_text()).strip();assert baseline
    assert await note.get_attribute('role')=='status' and await note.get_attribute('aria-live')=='polite'
    assert 'atelier-explosion-note' in (await slider.get_attribute('aria-describedby') or '').split()
    assert await overview.is_disabled()
    report={'before_canvas':before,'baseline_note':baseline,'layers':{}}
    R['viewports'][f'{w}x{h}']=report
    for i,(layer_id,expected) in enumerate(EXPECTED.items()):
     if i==0:
      await layer.focus();await layer.press('ArrowDown');await layer.press('Enter')
     else: await layer.select_option(layer_id)
     await f.wait_for_function('id=>assemblyInspect().layerFocus.selected===id',arg=layer_id)
     await f.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'")
     snap=await f.evaluate('assemblyInspect()');copy=(await note.inner_text()).strip()
     assert copy==expected,(layer_id,copy,expected)
     assert await layer.input_value()==layer_id and await overview.is_enabled()
     assert await note.get_attribute('data-layer-active')=='true'
     style=await note.evaluate('(e)=>({display:getComputedStyle(e).display,position:getComputedStyle(e).position,clip:getComputedStyle(e).clipPath})')
     assert style['display']!='none' and style['position']!='absolute' and style['clip'] in ('none','inset(0px)'),style
     assert await canvas.bounding_box()==before
     nb=await note.bounding_box();pb=await f.locator('#context').bounding_box();dock=await f.locator('.task-dock').bounding_box()
     assert nb and pb and dock and pb['height']<=165.5,{'note':nb,'panel':pb}
     dims=await note.evaluate('(e)=>({clientWidth:e.clientWidth,scrollWidth:e.scrollWidth,clientHeight:e.clientHeight,scrollHeight:e.scrollHeight})')
     assert dims['scrollWidth']<=dims['clientWidth']+1 and dims['scrollHeight']<=dims['clientHeight']+1,dims
     assert nb['x']>=0 and nb['x']+nb['width']<=w+.5 and nb['y']>=0 and nb['y']+nb['height']<=h+.5
     assert nb['y']>=pb['y']-.5 and nb['y']+nb['height']<=pb['y']+pb['height']+.5
     assert pb['y']+pb['height']<=dock['y']+.5,{'panel':pb,'dock':dock}
     report['layers'][layer_id]={'copy':copy,'runtime_selected':snap['layerFocus']['selected'],'member_count':len(snap['layerFocus']['members']),'copy_box':nb,'panel_box':pb,'copy_style':style}
     # Preserve the keyboard-selection assertion but dismiss Chromium's native select popup before visual evidence.
     await layer.evaluate('(e)=>e.blur()')
     await f.locator('#atelier-explosion-note').click(force=True)
     await page.wait_for_timeout(150)
     await page.screenshot(path=str(OUT/f'{w}-{layer_id}.png'))
    await overview.click();await f.wait_for_function("!assemblyInspect().layerFocus.selected&&assemblyInspect().explosion.amount===1")
    assert await layer.input_value()=='' and await overview.is_disabled() and (await note.inner_text()).strip()==baseline
    # Close hides the panel only; reopening must either retain the true focused layer and matching copy or report neutral after the runtime resets it.
    await layer.select_option('balance');await f.wait_for_function("assemblyInspect().layerFocus.selected==='balance'")
    await f.locator('#close').click();assert await f.locator('#context').evaluate('(e)=>e.hidden')
    retained=await f.evaluate('assemblyInspect()');assert retained['layerFocus']['selected']=='balance'
    await f.locator('.task-dock [data-mode=explode]').click(force=True)
    await f.wait_for_function("!document.querySelector('#context').hidden")
    await f.wait_for_function("()=>{const x=assemblyInspect().layerFocus.selected;return x===null||x==='balance'}")
    active=await f.evaluate('assemblyInspect()');note_text=(await note.inner_text()).strip()
    assert note_text==(EXPECTED['balance'] if active['layerFocus']['selected']=='balance' else baseline)
    # A zero scrub clears focus through the runtime and restores neutral help.
    await layer.select_option('calendar');await f.wait_for_function("assemblyInspect().layerFocus.selected==='calendar'")
    await slider.evaluate("e=>{e.value='0';e.dispatchEvent(new Event('input',{bubbles:true}))}")
    await f.wait_for_function("!assemblyInspect().layerFocus.selected&&assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating")
    assert await layer.input_value()=='' and await layer.is_disabled() and await overview.is_disabled()
    assert (await note.inner_text()).strip()==baseline and await canvas.bounding_box()==before
    # Reassembly button has the same reset behavior.
    await f.locator('.task-dock [data-mode=explode]').click(force=True)
    await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
    await layer.select_option('balance');await f.wait_for_function("assemblyInspect().layerFocus.selected==='balance'")
    await f.locator('#atelier-reassemble').click()
    await f.wait_for_function("!assemblyInspect().layerFocus.selected&&assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating")
    assert await layer.input_value()=='' and (await note.inner_text()).strip()==baseline
    # Switching mode clears the active explanation without changing the canvas box.
    await f.locator('.task-dock [data-mode=explode]').click(force=True)
    await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
    await layer.select_option('train');await f.wait_for_function("assemblyInspect().layerFocus.selected==='train'")
    await f.locator('.task-dock [data-mode=inside]').click(force=True)
    await f.wait_for_function("assemblyInspect().layerFocus.selected===null")
    assert await canvas.bounding_box()==before
    report.update(overview_restored=True,close_reopen_copy_matches_state=True,zero_scrub_clears=True,reassemble_clears=True,mode_exit_clears=True,canvas_stable=True)
   assert not R['errors'],R['errors']
   assert not R['release_http_errors'],R['release_http_errors']
   R.update(passed=True,final_note='Exact sealed ART-12 runtime; no route overlay or device performance claim.')
  except Exception as e:
   R.update(passed=False,failure=repr(e));raise
  finally:
   (OUT/'BROWSER_REPORT.json').write_text(json.dumps(R,indent=2))
   await browser.close()
asyncio.run(run())
