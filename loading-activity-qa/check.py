import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('loading-activity-evidence');O.mkdir(exist_ok=True)
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox']);R=[]
  try:
   for reduced in [False,True]:
    page=await b.new_page(viewport={'width':430,'height':932},reduced_motion='reduce' if reduced else 'no-preference')
    await page.route('**/preview-b/releases/**/atelier-preview.html*',lambda route:route.fulfill(content_type='text/html',body='<!doctype html><html><body style="background:#191b1a"></body></html>'))
    await page.goto('http://127.0.0.1:8765/loading-activity-qa/index.html',wait_until='load');f=next(f for f in page.frames if f!=page.main_frame)
    state={'enabled':True,'pending':['baseline','proposal','premiumFace','leather','antialias'],'phase':'loading'}
    async def emit(s):await f.evaluate('(s)=>document.dispatchEvent(new CustomEvent("atelier:presentation-state",{detail:s}))',s)
    async def snap():return await page.evaluate('''()=>({value:document.querySelector('#watch-progress').getAttribute('aria-valuenow'),state:document.querySelector('#watch-loading').dataset.state,hidden:document.querySelector('#watch-loading').hidden,animation:getComputedStyle(document.querySelector('#watch-progress'),'::after').animationName,transform:getComputedStyle(document.querySelector('#watch-progress'),'::after').transform})''')
    await emit(state);a=await snap();await page.wait_for_timeout(900);c=await snap();assert a['value']==c['value']=='6';assert c['animation']==('none' if reduced else 'watch-loading-activity');assert reduced or a['transform']!=c['transform']
    await page.screenshot(path=str(O/f'loading-reduced-{reduced}.png'))
    state['pending']=['leather'];await emit(state);await page.wait_for_timeout(900);d=await snap();assert int(d['value'])>6 and int(d['value'])<100
    # No guessed time-based progress during a stalled phase.
    await page.wait_for_timeout(1800);assert (await snap())['value']==d['value']
    state['interactive']=True;await emit(state);ready=await snap();assert ready['value']=='100' and ready['animation']=='none';await page.wait_for_timeout(800);assert (await snap())['hidden']
    # Actual iframe reload starts a new lifecycle, rather than retaining 100%.
    await f.goto(f.url);await page.wait_for_timeout(100);again=await snap();assert not again['hidden'] and int(again['value'])<100
    await emit({'phase':'error'});err=await snap();assert err['hidden'] and err['value']!='100'
    R.append({'reduced':reduced,'initial':a,'stalled':c,'progress':d,'ready':ready,'reloaded':again,'error':err});await page.close()
   (O/'report.json').write_text(json.dumps({'passed':True,'cases':R},indent=2))
  finally:await b.close()
asyncio.run(main())
