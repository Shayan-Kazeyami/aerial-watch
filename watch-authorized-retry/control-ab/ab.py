"""Bounded same-runner simple-WebGL vs exact0116 viewer. Diagnostic, never approval."""
import asyncio, pathlib, json, os, base64, hashlib, traceback, time
from PIL import Image,ImageStat
from playwright.async_api import async_playwright
from instrumentation import action,bounded_run,record,sample_loop
ROOT=pathlib.Path(__file__).resolve().parent
RID='011614d052b49dd32652ec25e31bd471addef053bfda24510d7741485fe37192'
KIND=os.environ['QA_UI_KIND'];assert KIND in ['mobile','desktop']
W,H=(430,932) if KIND=='mobile' else (1280,800)
O=ROOT/('evidence-'+KIND);O.mkdir(exist_ok=True)
LOG=O/'actions.jsonl'
R={'kind':KIND,'release':RID,'passed':False,'scope':'Same runner sequential fresh-browser simple-WebGL2 control then exact0116 viewer. Diagnostic only; no physical GPU/FPS proof. No periodic renderer heartbeat.','arms':{},'limits':['Simple low-load control is not workload-equivalent to watch. Control success cannot prove application defect.','External process sampler15s may add small load; no repeated rAF probes.','Order is control then viewer, one attempt per arm, no automated retry.']}
ARGS=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']

async def run_action(name,operation,timeout=90):
    return await action(LOG,name,lambda:asyncio.wait_for(operation(),timeout))

async def capture(session,host,frame,selector,name):
    box=await run_action(name+':clip-preflight',lambda:frame.locator(selector).bounding_box(),15)
    x=max(0,box['x']);y=max(0,box['y']);w=min(W,box['x']+box['width'])-x;h=min(H,box['y']+box['height'])-y
    assert w>100 and h>100
    # Timestamp names distinguish preflight from actual CDP dispatch.
    shot=await run_action(name+':CDP-capture-dispatch',lambda:session.send('Page.captureScreenshot',{'format':'png','fromSurface':True,'captureBeyondViewport':False,'clip':{'x':x,'y':y,'width':w,'height':h,'scale':1}}),180)
    p=O/(name+'.png');p.write_bytes(base64.b64decode(shot['data']))
    im=Image.open(p).convert('RGB');stat=ImageStat.Stat(im);colors=len(im.getcolors(maxcolors=10000000)or[])
    assert max(stat.stddev)>5 and colors>100,(name,'blank-like screenshot',stat.stddev,colors)
    return {'path':p.name,'clip':box,'size':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'stddev':stat.stddev,'colors':colors}

async def failure_probe(browser,page):
    results={}
    async def one(label,op):
        try:results[label]={'ok':True,'value':await asyncio.wait_for(op(),3)}
        except Exception as error:results[label]={'ok':False,'error':repr(error)}
    session=await asyncio.wait_for(browser.new_browser_cdp_session(),3)
    await asyncio.gather(one('browser-process',lambda:session.send('Browser.getVersion')),one('host-DOM',lambda:page.evaluate('({now:performance.now(),state:document.readyState})')))
    return results

async def one_arm(playwright,name,operation,deadline):
    data={'completed':False,'failure':None,'cleanupFailure':None};R['arms'][name]=data
    browser=None;page=None
    try:
        browser=await run_action(name+':launch',lambda:playwright.chromium.launch(args=ARGS),60)
        data['browserVersion']=browser.version
        browser_info=await run_action(name+':browser-info-session',browser.new_browser_cdp_session,10)
        data['browserProduct']=await run_action(name+':browser-info',lambda:browser_info.send('Browser.getVersion'),10)
        context=await run_action(name+':context',lambda:browser.new_context(viewport={'width':W,'height':H},device_scale_factor=1,is_mobile=KIND=='mobile',has_touch=KIND=='mobile'),20)
        page=await context.new_page();page.set_default_timeout(90000);data['pageErrors']=[];page.on('pageerror',lambda e:data['pageErrors'].append(str(e)))
        await bounded_run(LOG,lambda:operation(browser,context,page,data),deadline)
        assert not data['pageErrors'],data['pageErrors'];data['completed']=True
    except asyncio.CancelledError:
        data['failure']='External cancellation';raise
    except Exception as error:
        data['failure']=repr(error);data['traceback']=traceback.format_exc()
        if browser and page:
            try:data['failureProbe']=await asyncio.wait_for(failure_probe(browser,page),8)
            except Exception as probe_error:data['failureProbeError']=repr(probe_error)
    finally:
        (O/'report.json').write_text(json.dumps(R,indent=2))
        if browser:
            try:await run_action(name+':browser-close',browser.close,30)
            except Exception as cleanup:data['cleanupFailure']=repr(cleanup)
        (O/'report.json').write_text(json.dumps(R,indent=2))

async def control(browser,context,page,data):
    await run_action('control:load',lambda:page.set_content((ROOT/'control.html').read_text()),30)
    await run_action('control:ready',lambda:page.wait_for_function('window.controlState?.frames>=3'),30)
    session=await context.new_cdp_session(page);data['captures']=[]
    for scale in [1,1.5]:
        await run_action('control:set-scale-'+str(scale),lambda:page.evaluate('x=>controlScale(x)',scale),10)
        await run_action('control:two-frames-'+str(scale),lambda:page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))'),30)
        data['captures'].append(await capture(session,page,page,'#stage','control-'+str(scale)))
    data['state']=await page.evaluate('controlState');assert not data['state']['contextLost']

async def viewer(browser,context,host,data):
    await run_action('viewer:load-root',lambda:host.goto('http://127.0.0.1:8765/?quality=efficient&normalStream=1',wait_until='domcontentloaded',timeout=120000),120)
    await run_action('viewer:ready-body',lambda:host.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000),300)
    frame=next(f for f in host.frames if '/'+RID+'/' in f.url);data['url']=frame.url
    await run_action('viewer:ready-camera',lambda:frame.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"&&window.assemblyInspect?.().presentation.interactive',timeout=300000),300)
    await run_action('viewer:root-overlay-hidden',lambda:host.locator('#watch-loading').wait_for(state='hidden',timeout=120000),120)
    data['revision']=await frame.evaluate("async()=>(await import('./quality-study/viewer-revision.js')).default")
    build=json.loads(pathlib.Path('coordinated-release-successor/build-report.json').read_text());assert data['revision']['digest']==build['viewerRevisionDigest']
    data['initial']=await frame.evaluate('assemblyInspect()');assert data['initial']['sourceMeshes']==166
    data['observedRenderer']=await frame.evaluate('(()=>{const a=assemblyInspect(),c=document.getElementById("assembly-canvas");return {renderer:a.renderer??null,GPU:a.GPU??null,renderQuality:a.renderQuality,canvas:[c.width,c.height],backendIndicator:document.getElementById("atelier-backend-indicator")?.textContent??null}})()')
    session=await context.new_cdp_session(host);data['captures']=[]
    data['captures'].append(await capture(session,host,frame,'#stage','viewer-efficient'))
    async def activate(selector):
        target=frame.locator(selector)
        if KIND=='mobile':await target.tap()
        else:await target.click()
    await run_action('viewer:open-quality',lambda:activate('.masthead button[data-mode="quality"]'))
    await run_action('viewer:select-balanced',lambda:activate('#context [data-quality="balanced"]'))
    await run_action('viewer:balanced-ready',lambda:frame.wait_for_function('assemblyInspect().renderQuality==="balanced"&&document.getElementById("stage").dataset.cameraReady==="true"',timeout=120000),120)
    await run_action('viewer:close-panel',lambda:activate('#close'))
    await run_action('viewer:panel-hidden',lambda:frame.locator('#context').wait_for(state='hidden'),30)
    await run_action('viewer:two-frames',lambda:frame.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))'),60)
    data['beforeBalancedCapture']=await frame.evaluate('({ready:document.body.dataset.ready,cameraReady:document.getElementById("stage").dataset.cameraReady,quality:assemblyInspect().renderQuality})')
    data['balancedRenderer']=await frame.evaluate('(()=>{const a=assemblyInspect(),c=document.getElementById("assembly-canvas");return {renderer:a.renderer??null,GPU:a.GPU??null,renderQuality:a.renderQuality,canvas:[c.width,c.height],backendIndicator:document.getElementById("atelier-backend-indicator")?.textContent??null}})()')
    data['captures'].append(await capture(session,host,frame,'#stage','viewer-balanced'))

async def main():
    assert pathlib.Path('coordinated-release-successor/release-id.txt').read_text().strip()==RID
    stop=asyncio.Event();sampler=asyncio.create_task(sample_loop(stop,O/'process-samples.jsonl',interval=15))
    try:
        async with async_playwright() as p:
            await one_arm(p,'simple-WebGL2',control,300)
            await one_arm(p,'exact-viewer',viewer,900)
    finally:
        stop.set()
        try:await asyncio.wait_for(sampler,5)
        except Exception as error:R['samplerShutdownError']=repr(error)
        R['diagnosticFinished']=True;(O/'report.json').write_text(json.dumps(R,indent=2))
    # Every required image/control must succeed; cleanup failures remain visible.
    if not all(a['completed'] and not a['cleanupFailure'] for a in R['arms'].values()):raise RuntimeError('A/B diagnostic incomplete or cleanup failed; inspect report, not release approval')
if __name__=='__main__':asyncio.run(main())
