"""Unexecuted reviewed-scope browser entrypoint. Does not create a server or upload."""
import asyncio,json,time,io
from pathlib import Path
from PIL import Image,ImageChops
from playwright.async_api import async_playwright
from legacy_ui_actions import pause_visible_motion,set_visible_finish
Q=Path(__file__).resolve().parent;RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
async def main():
 out=Q/'browser-evidence-legacy';out.mkdir(exist_ok=True);report={'accepted':False,'scope':'Pinned published legacy shell plus instrumented e79 runtime; nonatelier lighting/finishes; not live/default release approval','events':[],'pairs':[]}
 page=None;probe=(Q/'actionability-probe.js').read_text();probeSerial=0
 async def op(name,awaitable,seconds=30):
  nonlocal probeSerial
  start=time.monotonic()
  if page is not None and name.startswith('legacy-'):
   try:report.setdefault('actionabilityBefore',[]).append({'action':name,'snapshot':await asyncio.wait_for(page.evaluate(probe),5)})
   except BaseException as e:report.setdefault('probeFailures',[]).append(repr(e))
  try:return await asyncio.wait_for(awaitable,seconds)
  except BaseException:
   if page is not None and name!='normal-close':
    probeSerial+=1
    try:
     snapshot=await asyncio.wait_for(page.evaluate(probe),5);(out/f'actionability-{probeSerial}.json').write_text(json.dumps({'action':name,'snapshot':snapshot},indent=2))
    except BaseException as e:report.setdefault('probeFailures',[]).append(repr(e))
    try:await asyncio.wait_for(page.screenshot(path=str(out/f'failure-{probeSerial}.png'),timeout=10000),12)
    except BaseException as e:report.setdefault('failureScreenshotFailures',[]).append(repr(e))
   raise
  finally:report['events'].append({'name':name,'seconds':time.monotonic()-start})
 async with async_playwright()as p:
  browser=await op('launch',p.chromium.launch(headless=True))
  try:
   async with asyncio.timeout(1200):
    page=await browser.new_page(viewport={'width':1280,'height':900},device_scale_factor=1);page.set_default_timeout(30000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await op('navigate',page.goto(f'http://127.0.0.1:8765/preview-b/releases/{RID}/assembly-review.html?quality=efficient',timeout=300000),300)
    await op('registration-ready',page.wait_for_function("()=>{try{return window.__mountingFootQA.register().length===3&&!assemblyInspect().loading}catch{return false}}",timeout=300000),300)
    report['preActionability']=await op('pre-action-probe',page.evaluate(probe))
    await pause_visible_motion(page,op)
    report['registration']=await page.evaluate('window.__mountingFootQA.register()');report['metadata']=await page.evaluate('window.__mountingFootQA.metadata()');report['browser']=browser.version
    assert report['metadata']['renderer'],'renderer identity absent'
    canvas=page.locator('#stage canvas').first
    async def capture(name):
     data=await op('capture-'+name,canvas.screenshot(timeout=60000),60);im=Image.open(io.BytesIO(data)).convert('RGB');assert im.width>0 and im.height>0;assert any(a!=b for a,b in im.getextrema()),'blank';(out/(name+'.png')).write_bytes(data);return im
    await capture('context')
    for finished in [False,True]:
     await set_visible_finish(page,op,finished)
     for label in ['350','110','250']:
      spec=json.loads((Q.parents[1]/'isolated-mounting-feet-exact-index'/f'{label}.candidate.json').read_text());name=spec['name']
      for tilt in [0,.5]:
       await page.evaluate('window.__mountingFootQA.saveCamera()');transaction=False
       try:
        await page.evaluate('(spec)=>window.__mountingFootQA.prepare(spec)',spec);transaction=True
        framing=await page.evaluate('([name,tilt])=>window.__mountingFootQA.frame(name,tilt)',[name,tilt])
        images=[];picks=[]
        for mode in ['source','candidate','return']:
         prior=await page.evaluate('window.__mountingFootQA.requestFrame()')
         if mode=='candidate':await page.evaluate('window.__mountingFootQA.activate()')
         elif mode=='return':await page.evaluate('window.__mountingFootQA.restore()')
         await op('paint',page.wait_for_function('(prior)=>window.__mountingFootQA.frameNumber()>prior',arg=prior,timeout=30000))
         picks.append(await page.evaluate('(name)=>window.__mountingFootQA.evidence(name)',name));images.append(await capture(f'{label}-{finished}-{tilt}-{mode}'))
        assert images[0].size==images[1].size==images[2].size
        assert ImageChops.difference(images[0],images[2]).getbbox()is None,'source repeatability'
        assert ImageChops.difference(images[0],images[1]).getbbox()is None,'candidate pixels'
        assert picks[0]['rays']==picks[1]['rays']==picks[2]['rays'],'picking mismatch'
        assert picks[0]['identity']==picks[1]['identity']==picks[2]['identity'],'runtime transform/material/mesh identity drift'
        report['pairs'].append({'label':label,'finish':finished,'tilt':tilt,'framing':framing,'picks':picks,'passed':True})
       except BaseException as e:
        report['primaryFailure']=repr(e);raise
       finally:
        for cleanup,script in [('restore-dispose','window.__mountingFootQA.dispose()'),('camera-restore','window.__mountingFootQA.restoreCamera()')]:
         if cleanup=='restore-dispose' and not transaction:continue
         try:await op(cleanup,page.evaluate(script))
         except BaseException as e:
          report.setdefault('pairCleanupFailures',[]).append({'step':cleanup,'error':repr(e)})
          if 'primaryFailure'not in report:raise
    assert len(report['pairs'])==12 and not errors;report['pageErrors']=errors;report['fixturePassed']=True
  except BaseException as e:report['primaryFailure']=repr(e);raise
  finally:
   try:await op('normal-close',browser.close());report['normalClosePassed']=True
   except BaseException as e:
    report['cleanupFailure']=repr(e)
    if 'primaryFailure'not in report:raise
   finally:report['accepted']=bool(report.get('fixturePassed')and report.get('normalClosePassed')and not report.get('pairCleanupFailures'));(out/'REPORT.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':asyncio.run(main())
