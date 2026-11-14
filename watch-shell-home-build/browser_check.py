import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
Q=Path(__file__).resolve().parent;B=Q.parent/'watch-import-readiness-build/staging/preview-b/releases/e157f07921363a07a67dffd367bbc5bec2392691313632a4169d951974abb5a2';C=Q/'staging/preview-b/releases'/(Q/'release-id.txt').read_text()
def line(p):return next(x for x in (p/'atelier-preview.js').read_text().splitlines() if x.startswith("document.addEventListener('keydown',e=>{if(e.key==='Escape'"))
r=(B/'assembly-review.js').read_text();start=r.index("renderer.domElement.addEventListener('keydown', event => {");canvas=r[start:r.index('\n// Project one known crown anchor',start)]
async def main():
 rows=[]
 async with async_playwright() as p:
  browser=await asyncio.wait_for(p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True),30)
  try:
   page=await browser.new_page()
   async def run(which,tag='canvas',mod='',interior=False,prevented=False,key='Home'):
    await page.set_content('<canvas id="canvas"></canvas><button id="button">control</button><input id="input"><select id="select"></select><textarea id="textarea"></textarea>')
    return await page.evaluate('''({shell,canvas,tag,mod,interior,prevented,key})=>{
     window.stats={home:0,views:[],closed:0,stops:0};const document=window.document;const renderer={domElement:document.getElementById('canvas')};const loading=false,failed=false,interiorView=interior;const stopTour=()=>stats.stops++;const view=x=>stats.views.push(x);const closeContext=()=>stats.closed++;const $=id=>id==='movement-only'?{checked:false}:id==='context'?{hidden:false}:{click(){stats.home++}};const camera={zoom:1,updateProjectionMatrix(){}};const THREE={MathUtils:{clamp:x=>x}},controls={minZoom:.4,maxZoom:12};let dirty=false;
     const add=document.addEventListener.bind(document);let docHandler;document.addEventListener=(k,f)=>{docHandler=f;add(k,f)};eval(canvas);eval(shell);document.addEventListener=add;
     const e=new KeyboardEvent(key==='x'?'keydown':'keydown',{key,bubbles:true,cancelable:true,[mod]:true});if(prevented)e.preventDefault();document.getElementById(tag).dispatchEvent(e);document.removeEventListener('keydown',docHandler);return {...stats,prevented:e.defaultPrevented};
    }''',{'shell':line(B if which=='baseline' else C),'canvas':canvas,'tag':tag,'mod':mod,'interior':interior,'prevented':prevented,'key':key})
   for mod in ['ctrlKey','metaKey','altKey']:
    a=await run('baseline',mod=mod);b=await run('candidate',mod=mod);assert a['home']==1 and b['home']==0 and not b['views'] and not b['prevented'];rows.append({'case':mod,'baseline':a,'candidate':b})
   for interior in [False,True]:
    a=await run('baseline',interior=interior);b=await run('candidate',interior=interior);assert a['home']==1 and b['home']==0 and b['views']==['interior' if interior else 'face'];rows.append({'case':'canvas-'+str(interior),'baseline':a,'candidate':b})
   for tag,prevented,want in [('button',False,1),('button',True,0),('input',False,0),('select',False,0),('textarea',False,0)]:
    b=await run('candidate',tag=tag,prevented=prevented);assert b['home']==want;rows.append({'case':tag+str(prevented),'candidate':b})
   for key in ['Escape','x','+']:
    a=await run('baseline',key=key);b=await run('candidate',key=key);assert a==b;rows.append({'case':key,'baseline':a,'candidate':b})
   (Q/'BROWSER_RESULT.json').write_text(json.dumps({'status':'PASS','cases':rows,'scope':'Native Chromium DOM dispatchEvent with exact extracted listeners; real target-to-document bubbling, synthetic KeyboardEvent, not full viewer or physical keyboard'},indent=2)+'\n')
  finally:await asyncio.wait_for(browser.close(),15)
asyncio.run(asyncio.wait_for(main(),80))
