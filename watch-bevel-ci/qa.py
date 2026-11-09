import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('watch-bevel-output');build=json.loads((O/'build.json').read_text());C=pathlib.Path(build['releasePath']);B=pathlib.Path('preview-b/releases/dca5c072be394554f4ae293b0324e61a38f5b548cbab721f99f8cf80e13298bc');C=C.relative_to(pathlib.Path.cwd()) if C.is_absolute() else C
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':1000,'height':800},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  # Verify actual sealed entry without instrumentation before private view captures.
  await page.goto(f'http://127.0.0.1:8765/{C}/atelier-preview.html?quality=efficient&profileLoad=1',wait_until='domcontentloaded');await page.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=240000);await page.wait_for_timeout(3000);state=await page.evaluate('assemblyInspect()');assert state['hybridCase']['revision']=='hybrid-cap030-density-r01';assert state['hybridCase']['triangles']==371636;await page.screenshot(path=str(O/'sealed-whole.png'),timeout=180000);(O/'sealed-state.json').write_text(json.dumps(state,indent=2));await page.close()
  states=[]
  for label,root in [('baseline',B),('candidate',C)]:
   # Separate QA filenames: no modification to sealed modules or their manifest.
   review=(root/'assembly-review.js').read_text();assert review.count('composer.render();')>=1;review=review.replace('composer.render();','qaApply();composer.render();')+'\n'+pathlib.Path('watch-bevel-ci/hook.js').read_text();(root/'qa-review.js').write_text(review);s=(root/'atelier-preview.js').read_text().replace('./assembly-review.js?v=atelier-local-1','./qa-review.js');(root/'qa-atelier.js').write_text(s);s=(root/'atelier-preview.html').read_text().replace('atelier-preview.js','qa-atelier.js');(root/'qa-atelier.html').write_text(s)
   page=await b.new_page(viewport={'width':1000,'height':800},device_scale_factor=1);page.on('pageerror',lambda e:errors.append(str(e)));await page.goto(f'http://127.0.0.1:8765/{root}/qa-atelier.html?quality=efficient',wait_until='domcontentloaded');await page.wait_for_function('window.__bevelView && window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().presentation.interactive',timeout=240000)
   configs=[('whole',1,1,1,False)]+[('cap',sx,sz,1,False)for sx in [-1,1]for sz in [-1,1]]+[('root',sx,sz,side,False)for sx in [-1,1]for sz in [-1,1]for side in [-1,1]]+[('root',1,1,1,True)]
   for cfg in configs:
    s=await page.evaluate('(v)=>__bevelView(...v)',cfg);states.append({'label':label,**s});await page.wait_for_timeout(800);await page.screenshot(path=str(O/(label+'-'+'-'.join(map(str,cfg))+'.png')),timeout=180000)
   await page.close()
  (O/'qa-report.json').write_text(json.dumps({'states':states,'errors':errors,'scope':'Actual Three.js sealed startup plus same-pose isolated CASE captures using separate QA entry modules; software rendering only.'},indent=2));assert not errors,errors;await b.close()
asyncio.run(main())
