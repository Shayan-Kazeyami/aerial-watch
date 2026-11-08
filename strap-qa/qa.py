import asyncio,json,pathlib,base64,os
from playwright.async_api import async_playwright
ROOT=pathlib.Path('preview-b/releases/43e516fa6ed3a4be7e8b308bc35c1955dc811b710042e38cdbaeaf868b7c8932');OUT=pathlib.Path('strap-output');OUT.mkdir(exist_ok=True)
s=(ROOT/'assembly-review.js').read_text();assert 'composer.render();'in s;s=s.replace('composer.render();','strapQaApply();composer.render();');s+='\n'+pathlib.Path('strap-qa/qa-hook.js').read_text();(ROOT/'assembly-review.js').write_text(s)
async def run():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await browser.new_page(viewport={'width':800,'height':640},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));states=[]
  try:
   await page.goto('http://127.0.0.1:8765/'+str(ROOT)+'/atelier-preview.html?quality=efficient&leather=craft14',wait_until='domcontentloaded');await page.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=240000);await page.wait_for_timeout(5000);setup=await page.evaluate('()=>__strapQaSetup()');setup['browser_version']=browser.version;setup['backend']='Chromium SwiftShader, --use-angle=swiftshader';(OUT/'setup.json').write_text(json.dumps(setup,indent=2));print('SETUP OK',flush=True)
   for normal in [True]:
    await page.evaluate("()=>{__strapQaView('upper/right/close','source');__strapQaQuality('balanced');}")
    await page.evaluate('(enabled)=>__strapQaNormalMap(enabled)',normal)
    prefix=os.environ['STRAP_QA_END'].replace('-','/')
    await page.evaluate('(p)=>__strapQaLit(...p.split("/"))',prefix)
    for view in [prefix+'/'+v for v in ['context','close','neck']]:
     if view.endswith('/neck'):await page.evaluate('(p)=>__strapQaRake(...p.split("/"))',prefix)
     for variant in ['source','candidate']:
      print('CAPTURE',view,variant,'normal',normal,flush=True);label=view.replace('/','-');state=await page.evaluate('(a)=>__strapQaView(...a)',[view,variant]);states.append(state);(OUT/'states.json').write_text(json.dumps(states,indent=2));capture=await page.evaluate('()=>__strapQaCapture()');(OUT/f'{label}-{variant}.png').write_bytes(base64.b64decode(capture.pop('png').split(',')[1]));(OUT/f'{label}-{variant}-capture.json').write_text(json.dumps(capture,indent=2));print('SAVED',view,variant,flush=True)
   for i in range(0,len(states),2):assert [m['maps']for m in states[i]['upper']]==[m['maps']for m in states[i+1]['upper']],'KTX maps changed'
  finally:
   (OUT/'errors.json').write_text(json.dumps(errors,indent=2));await browser.close()
asyncio.run(run())
