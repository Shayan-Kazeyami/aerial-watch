import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('movement-integrated-evidence');O.mkdir(exist_ok=True);R={'errors':[],'note':'Current live watch intercepted in QA browser only; no production changes; SwiftShader not phone FPS'}
async def main():
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);pg=await b.new_page(viewport={'width':1100,'height':1000});pg.set_default_timeout(180000);pg.on('pageerror',lambda e:R['errors'].append(str(e)))
  async def instrument(route):
   r=await route.fetch();await route.fulfill(response=r,body=await r.text()+'\n'+pathlib.Path('movement-qa-fixture/integrated-append.js').read_text())
  async def meshdata(route):
   k=route.request.url.split('/')[-1].split('.')[0];await route.fulfill(body=pathlib.Path(f'movement-fixture/data/97-after-{k}.bin').read_bytes(),content_type='application/octet-stream')
  await pg.route('**/assembly-review.js*',instrument);await pg.route('**/movement-candidate/*.bin',meshdata)
  try:
   await pg.goto('https://shayan-kazeyami.github.io/aerial-watch/',wait_until='domcontentloaded');f=None
   for _ in range(60):
    frames=[f for f in pg.frames if 'atelier-preview.html' in f.url]
    if frames:f=frames[0];break
    await pg.wait_for_timeout(1000)
   assert f,'No viewer iframe';await f.locator('body[data-ready=true]').wait_for(timeout=300000);await f.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000);R['url']=f.url;R['init']=await f.evaluate('movementTopologyQA.init()');assert R['init']['before']==21944 and R['init']['after']==17812
   async def compare(name,macro=False):
    await f.evaluate('movementTopologyQA.freeze()');await f.wait_for_function('movementTopologyQA.settled()',timeout=180000);await f.evaluate('(m)=>movementTopologyQA.pose(m)',macro);states={}
    for mode,on in [('before',False),('after',True)]:
     states[mode]=await f.evaluate('(on)=>movementTopologyQA.set(on)',on);await pg.screenshot(path=str(O/f'{name}-{mode}.png'))
    assert states['before']['camera']==states['after']['camera'];assert states['before']['matrix']==states['after']['matrix'];assert states['before']['material']==states['after']['material'];R[name]=states
   await compare('assembled');await f.locator('.task-dock [data-mode=explode]').click(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating',timeout=180000);await compare('exploded');await compare('wheel-macro',True);await f.locator('#home').click(force=True);await f.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating',timeout=180000);await compare('reset')
   start=await f.evaluate('movementTopologyQA.motion().mechanism');await f.locator('#play-motion').evaluate('e=>e.click()');await f.wait_for_function('(s)=>movementTopologyQA.motion().mechanism>s+.1',arg=start,timeout=180000);await f.evaluate('movementTopologyQA.freeze()');R['motionAdvanced']=True;assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);raise
  finally:
   (O/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True);await b.close()
asyncio.run(main())
