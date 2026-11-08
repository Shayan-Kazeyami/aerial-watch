import asyncio,json,pathlib
from playwright.async_api import async_playwright
ROOT=pathlib.Path('preview-b/releases/949a4881d119910ca28bdf5ef4d67dfdebc59df579e02a6de946db48668510c8')
s=(ROOT/'assembly-review.js').read_text();s=s.replace('composer.render();','metalApply();composer.render();');s+='\n'+pathlib.Path('qa-metal-hook.js').read_text();(ROOT/'assembly-review.js').write_text(s)
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':1000,'height':800},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));await page.goto('http://127.0.0.1:8765/'+str(ROOT)+'/atelier-preview.html?caseStudy=fine-combined&quality=low',wait_until='domcontentloaded');await page.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().parametricCase.enabled',timeout=240000)
  pathlib.Path('metal-output').mkdir(exist_ok=True);states=[]
  whole=await page.evaluate('()=>__metalWhole()');await page.wait_for_timeout(1500);await page.screenshot(path='metal-output/whole-candidate.png')
  base=await b.new_page(viewport={'width':1000,'height':800},device_scale_factor=1);await base.goto('http://127.0.0.1:8765/'+str(ROOT)+'/atelier-preview.html?quality=low',wait_until='domcontentloaded');await base.wait_for_function('window.assemblyInspect && !assemblyInspect().loading',timeout=240000);baseline=await base.evaluate('()=>__metalWhole()');await base.wait_for_timeout(1500);await base.screenshot(path='metal-output/whole-baseline.png');await base.close()
  pathlib.Path('metal-output/whole-state.json').write_text(json.dumps({'candidate':whole,'baseline':baseline},indent=2))
  for sx in [-1,1]:
   for sy in [-1,1]:
    for sz in [-1,1]:
     for plain in [False,True]:
      r=await page.evaluate('(v)=>__metalQA(...v)',[sx,sy,sz,plain]);states.append(r);await page.wait_for_timeout(1500);await page.screenshot(path=f'metal-output/root-{sx}-{sy}-{sz}-{plain}.png')
  pathlib.Path('metal-output/report.json').write_text(json.dumps({'states':states,'errors':errors},indent=2));await b.close()
asyncio.run(run())
