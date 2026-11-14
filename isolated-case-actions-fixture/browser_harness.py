"""Unexecuted bounded bootstrap-only lane; no lifecycle/disposal acceptance."""
import asyncio,json,time,sys,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from server import inventory
R=Path(__file__).resolve().parent
async def bounded(awaitable,seconds=15):return await asyncio.wait_for(awaitable,seconds)
async def main():
 from playwright.async_api import async_playwright
 out=R/'browser-results';out.mkdir(exist_ok=False)
 expected={k:h for k,(p,h)in inventory().items()};prep=json.loads((R/'PREPARATION.json').read_text())
 report={'status':'NOT_COMPLETED','cycles':[],'cleanup_errors':[],'global_limit_seconds':1200,'per_arm_seconds':180,'lifecycle_identity_disposal_checks':'HOLD_UNINSTRUMENTED','abort_cases':'NOT_RUN','memory_claims':False}
 browser=None;context=None;deadline=time.monotonic()+1200
 async def cleanup(obj,name):
  if obj:
   try:await bounded(obj.close(),10)
   except BaseException as e:report['cleanup_errors'].append({'owner':name,'error':repr(e)})
 try:
  async with asyncio.timeout(1200):
   async with async_playwright()as p:
    try:
     executable=Path(p.chromium.executable_path)
     report['executable_sha256']=hashlib.sha256(executable.read_bytes()).hexdigest()
     report['chromium_sandbox_requested']=True
     report['playwright_version']=__import__('importlib.metadata',fromlist=['version']).version('playwright')
     assert report['playwright_version']=='1.62.0','Unexpected Playwright version'
     browser=await bounded(p.chromium.launch(chromium_sandbox=True,headless=True,timeout=30000),35);report['browser_version']=browser.version
     for variant in ('baseline','candidate','candidate','baseline'):
      for cycle in range(10):
       row={'variant':variant,'cycle':cycle,'errors':[],'responses':[],'status':'FAIL'};report['cycles'].append(row);tasks=[]
       try:
        async with asyncio.timeout(min(180,max(.01,deadline-time.monotonic()))):
         context=await bounded(browser.new_context(viewport={'width':1280,'height':800},service_workers='block'))
         page=await bounded(context.new_page());page.set_default_timeout(15000)
         page.on('pageerror',lambda e,row=row:row['errors'].append(str(e)))
         async def response(r,row=row,variant=variant):
          path=urlsplit(r.url).path;key=path.removeprefix('/'+variant)
          want=prep['overrides'][variant+'-assembly-hybrid-case.js']if key.endswith('/assembly-hybrid-case.js')else expected.get(key)
          got=await bounded(r.header_value('X-Fixture-SHA256'),5)
          row['responses'].append({'url':r.url,'status':r.status,'expected_sha256':want,'served_sha256':got,'pin_match':bool(want and got==want)})
         page.on('response',lambda r,handler=response,owned_tasks=tasks:owned_tasks.append(asyncio.create_task(handler(r))))
         async def route(req):
          if req.request.url.startswith('http://127.0.0.1:8768/'+variant+'/'):await req.continue_()
          else:row['errors'].append('Blocked external URL '+req.request.url);await req.abort()
         await bounded(context.route('**/*',route))
         await page.goto('http://127.0.0.1:8768/'+variant+'/?quality=efficient&normalStream=1',wait_until='domcontentloaded',timeout=30000)
         frame=page.frame_locator('#watch-viewer');await frame.locator('body[data-ready="true"]').wait_for(timeout=120000)
         child=page.frames[1] if len(page.frames)==2 else None
         assert child is not None,'Ambiguous viewer frame'
         snapshot=await bounded(child.evaluate('()=>window.assemblyInspect?.().hybridCase'));row['hybridCase']=snapshot
         assert snapshot and snapshot.get('active')is True and snapshot.get('ownsGeometry')is True,'Hybrid not active/owned'
         row['before_teardown_screenshot']=f'{len(report["cycles"]):02d}-{variant}.png'
         await bounded(page.screenshot(path=str(out/row['before_teardown_screenshot']),timeout=15000),20)
         await bounded(asyncio.gather(*tasks),10)
         installers=[x for x in row['responses']if urlsplit(x['url']).path.endswith('/assembly-hybrid-case.js')]
         assert installers and all(x['pin_match']for x in installers),'Missing/wrong variant installer'
         assert not row['errors'] and all(x['status']<400 and x['pin_match']for x in row['responses']),'Response/error mismatch'
         row['status']='AWAITING_CONTEXT_CLOSE_AND_RESPONSE_DRAIN'
       except BaseException as e:
        row['failure']=repr(e);raise
       finally:
        # Close first: callbacks remain cycle-bound until the context stops producing responses.
        prior_error=sys.exc_info()[0] is not None
        cleanup_before=len(report['cleanup_errors'])
        await cleanup(context,'context');context=None
        row['normalClosePassed']=len(report['cleanup_errors'])==cleanup_before
        try:
         # A bounded drain over a growing list, not gather's initial snapshot.
         async with asyncio.timeout(10):
          cursor=0
          while cursor<len(tasks):
           batch=tasks[cursor:];cursor=len(tasks)
           results=await asyncio.gather(*batch,return_exceptions=True)
           if any(isinstance(x,BaseException)for x in results):
            row.setdefault('response_errors',[]).extend(repr(x)for x in results if isinstance(x,BaseException))
        except BaseException as e:row.setdefault('response_errors',[]).append(repr(e))
        pending=[t for t in tasks if not t.done()]
        row['pendingResponses']=len(pending)
        for t in pending:t.cancel()
        if pending:
         try:await bounded(asyncio.gather(*pending,return_exceptions=True),5)
         except BaseException as e:report['cleanup_errors'].append({'owner':'response_tasks','error':repr(e)})
        row['cancelledResponses']=sum(t.cancelled()for t in tasks)
        installers=[x for x in row['responses']if urlsplit(x['url']).path.endswith('/assembly-hybrid-case.js')]
        finalized=(row['normalClosePassed'] and not row.get('response_errors') and not row['pendingResponses'] and not row['cancelledResponses'] and not row['errors'] and bool(installers) and all(x['status']<400 and x['pin_match']for x in row['responses']))
        if not prior_error and finalized:row['status']='UI_BOOTSTRAP_OBSERVED_ONLY'
        else:
         row['status']='HOLD_INCOMPLETE_OR_FAILED_FINALIZATION'
         if not prior_error:raise RuntimeError('Cycle finalization failed; stopping')
     report['status']='BOOTSTRAP_ONLY_COMPLETED_NOT_LIFECYCLE_PASS'
    finally:
     before=len(report['cleanup_errors']);await cleanup(browser,'browser');browser=None
     report['normalBrowserClosePassed']=len(report['cleanup_errors'])==before
     if not report['normalBrowserClosePassed']:report['status']='HOLD_BROWSER_CLOSE_FAILED'
 except BaseException as e:report['primary_failure']=repr(e);report['status']='STOPPED_FIRST_FAILURE'
 finally:
  await cleanup(context,'remaining_context');await cleanup(browser,'remaining_browser')
  if report['cleanup_errors'] and report['status']=='BOOTSTRAP_ONLY_COMPLETED_NOT_LIFECYCLE_PASS':report['status']='HOLD_CLEANUP_FAILED'
  (out/'REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
 return 0 if report['status']=='BOOTSTRAP_ONLY_COMPLETED_NOT_LIFECYCLE_PASS' and not report['cleanup_errors'] else 1
if __name__=='__main__':raise SystemExit(asyncio.run(main()))
