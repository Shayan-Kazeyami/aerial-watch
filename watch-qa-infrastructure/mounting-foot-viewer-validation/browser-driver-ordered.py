"""Unexecuted reviewed-scope browser entrypoint. Does not create a server or upload."""
import asyncio,json,time,io
from pathlib import Path
from PIL import Image,ImageChops
from playwright.async_api import async_playwright
from legacy_ui_actions import set_visible_finish
from keyboard_motion import pause_native_keyboard
Q=Path(__file__).resolve().parent;RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
async def main():
 out=Q/'browser-evidence-ordered';out.mkdir(exist_ok=True);report={'accepted':False,'scope':'SOURCE EVIDENCE ONLY original finished beauty and ordered glass/target rays; no strict-gate revision, tag, candidate or optimization acceptance','events':[],'pairs':[]}
 page=None;probe=(Q/'actionability-probe-source-side.js').read_text();probeSerial=0
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
   async with asyncio.timeout(600):
    page=await browser.new_page(viewport={'width':1280,'height':900},device_scale_factor=1);page.set_default_timeout(30000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await op('navigate',page.goto(f'http://127.0.0.1:8765/preview-b/releases/{RID}/assembly-review.html?quality=efficient',timeout=300000),300)
    await op('registration-ready',page.wait_for_function("()=>{try{return window.__mountingFootQA.register().length===3&&!assemblyInspect().loading}catch{return false}}",timeout=300000),300)
    report['preActionability']=await op('pre-action-probe',page.evaluate(probe))
    report['keyboardMotion']=await pause_native_keyboard(page,op)
    report['registration']=await page.evaluate('window.__mountingFootQA.register()');report['metadata']=await page.evaluate('window.__mountingFootQA.metadata()');report['browser']=browser.version
    assert report['metadata']['renderer'],'renderer identity absent'
    canvas=page.locator('#stage canvas').first
    async def capture(name):
     data=await op('capture-'+name,canvas.screenshot(timeout=60000),60);im=Image.open(io.BytesIO(data)).convert('RGB');assert im.width>0 and im.height>0;assert any(a!=b for a,b in im.getextrema()),'blank';(out/(name+'.png')).write_bytes(data);return im
    await capture('context')
    assert (await page.evaluate('assemblyInspect().finish')) is True,'original studio finish required, no diagnostic material changes'
    name='Seconds / axial mounting foot 350';await op('save-camera',page.evaluate('window.__mountingFootQA.saveCamera()'))
    try:
     report['framing']=await op('source-side-fit',page.evaluate('(name)=>window.__mountingFootQA.frame(name,5)',name))
     images=[];observations=[]
     for label in ['source','source-return']:
      prior=await op('request-frame',page.evaluate('window.__mountingFootQA.requestFrame()'))
      await op('paint',page.wait_for_function('(prior)=>window.__mountingFootQA.frameNumber()>prior',arg=prior,timeout=25000))
      observations.append(await op('ordered-source-evidence',page.evaluate('(name)=>window.__mountingFootQA.orderedEvidence(name)',name)))
      images.append(await capture(label));roi=observations[-1]['roi'];im=images[-1];rect=(max(0,int((roi['left']+1)*im.width/2)),max(0,int((1-roi['top'])*im.height/2)),min(im.width,int((roi['right']+1)*im.width/2)+1),min(im.height,int((1-roi['bottom'])*im.height/2)+1));assert rect[2]>rect[0]and rect[3]>rect[1];im.crop(rect).save(out/(label+'-original-beauty-roi.png'));report.setdefault('originalBeautyCrops',[]).append({'label':label,'rect':rect,'scope':'unaltered crop, manual source-foot identification required'})
     assert images[0].size==images[1].size and ImageChops.difference(images[0],images[1]).getbbox()is None,'source repeatability'
     assert observations[0]==observations[1],'ordered source scene identity/ray drift'
     try:
      strict=await op('original-strict-first-hit',page.evaluate('(name)=>window.__mountingFootQA.evidence(name)',name));report['strictFirstHitPassed']=True;report['strictEvidence']=strict
     except Exception as e:
      if 'target occluded in actual scene'not in str(e):raise
      report['strictFirstHitPassed']=False;report['strictFirstHitFailure']=str(e)
     report['orderedTargetRays']=sum(x['targetIndex']>=0 for x in observations[0]['rays'])
     report['sourceObservations']=observations;report['candidateActivated']=False
    except BaseException as e:report['primaryFailure']=repr(e);raise
    finally:
     try:report['cameraRestoration']=await op('camera-restore',page.evaluate('window.__mountingFootQA.restoreCamera()'))
     except BaseException as e:
      report['cameraCleanupFailure']=repr(e)
      if 'primaryFailure'not in report:raise
    assert not errors;report['pageErrors']=errors;report['evidenceCollectionComplete']=True

  except BaseException as e:report['primaryFailure']=repr(e);raise
  finally:
   try:await op('normal-close',browser.close());report['normalClosePassed']=True
   except BaseException as e:
    report['cleanupFailure']=repr(e)
    if 'primaryFailure'not in report:raise
   finally:report['evidenceCollected']=bool(report.get('evidenceCollectionComplete')and report.get('normalClosePassed')and not report.get('cameraCleanupFailure'));report['sourceAccessVerified']=False;report['accepted']=False;(out/'REPORT.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':asyncio.run(main())
