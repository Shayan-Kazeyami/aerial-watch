"""Bounded matched published-e79 bytes vs frozen0116. Never release approval."""
import asyncio, pathlib, json, os, base64, hashlib, traceback, time, urllib.parse
from PIL import Image,ImageStat
from playwright.async_api import async_playwright
from instrumentation import action,bounded_run,record,sample_loop
ROOT=pathlib.Path(__file__).resolve().parent
RID='011614d052b49dd32652ec25e31bd471addef053bfda24510d7741485fe37192'
KIND=os.environ['QA_UI_KIND'];assert KIND in ['mobile','desktop']
W,H=(430,932) if KIND=='mobile' else (1280,800)
O=ROOT/('evidence-'+KIND);O.mkdir(exist_ok=True)
LOG=O/'actions.jsonl'
R={'kind':KIND,'passed':False,'scope':'Same-runner fresh-browser published e79 baseline bytes versus frozen0116; both local HTTP, not public-live census.','arms':{},'limits':['Fixed baseline then candidate order, one sample each: no statistical regression claim.','External15s process sampler; no periodic renderer heartbeat.','Running motion clock phases differ; screenshots are visual gates, not pixel-diff twins.']}
ARGS=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']

async def run_action(name,operation,timeout=90):
    return await action(LOG,R.get('currentArm','setup')+':'+name,lambda:asyncio.wait_for(operation(),timeout))

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
    R['currentArm']=name
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

async def viewer(browser,context,host,data,spec):
    expectedRID=spec["release"]
    data["identity"]=spec
    data['hostViewport']=host.viewport_size;assert data['hostViewport']=={'width':W,'height':H}
    await run_action('viewer:load-root',lambda:host.goto(spec['root']+'?quality=efficient&normalStream=1',wait_until='domcontentloaded',timeout=120000),120)
    await run_action('viewer:ready-body',lambda:host.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000),300)
    frame=next(f for f in host.frames if '/'+expectedRID+'/' in f.url);data['url']=frame.url
    data['frameParameters']=dict(urllib.parse.parse_qsl(urllib.parse.urlparse(frame.url).query))
    await run_action('viewer:ready-camera',lambda:frame.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"&&window.assemblyInspect?.().presentation.interactive',timeout=300000),300)
    await run_action('viewer:root-overlay-hidden',lambda:host.locator('#watch-loading').wait_for(state='hidden',timeout=120000),120)
    data['revision']=await run_action('viewer:boot-revision',lambda:frame.evaluate("async()=>(await import('./quality-study/viewer-revision.js')).default"),30)
    assert data['revision']['digest']==spec['viewerDigest']
    data['browserSourceSHA256']=await run_action('viewer:source-identity',lambda:frame.evaluate("async()=>{const b=await(await fetch(new URL('./assembly-review.js',location.href))).arrayBuffer();return [...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('')}"),30)
    assert data['browserSourceSHA256']==spec['sourceSHA256']
    data['initial']=await run_action('viewer:initial-state',lambda:frame.evaluate('assemblyInspect()'),30);assert data['initial']['sourceMeshes']==166
    assert data['initial']['animation'] and data['initial']['interiorAnimation']
    data['viewport']=await run_action('viewer:viewport-state',lambda:frame.evaluate('({innerWidth,innerHeight,meta:document.querySelector(\"meta[name=viewport]\")?.content,stage:document.getElementById(\"stage\").getBoundingClientRect().toJSON()})'),30)
    assert data['viewport']['innerWidth']==W and data['viewport']['innerHeight']==H and data['viewport']['meta']
    expectedHeight=760 if KIND=='mobile' else 546
    assert abs(data['viewport']['stage']['width']-W)<.01 and abs(data['viewport']['stage']['height']-expectedHeight)<.01
    async def detail_state():
        return await frame.evaluate("()=>new Promise(resolve=>{document.addEventListener('atelier:capture-detail-state',e=>resolve(e.detail),{once:true});document.dispatchEvent(new CustomEvent('atelier:request-capture-detail'))})")
    # One bounded read-only snapshot request per iteration, not a renderer heartbeat.
    async def wait_detail():
        for attempt in range(36):
            state=await asyncio.wait_for(detail_state(),5)
            if state.get('ready'):return state
            await asyncio.sleep(5)
        raise TimeoutError('Full detail did not become ready')
    data['detail']=await run_action('viewer:full-detail',wait_detail,185)
    assert data['detail']['phase']=='full' and data['detail']['activeNormalIdentity']['sha256']=='bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585'
    data['observedRenderer']=await run_action('viewer:renderer-info',lambda:frame.evaluate('(()=>{const a=assemblyInspect(),c=document.getElementById("assembly-canvas"),gl=c.getContext("webgl2"),d=gl?.getExtension("WEBGL_debug_renderer_info");return {renderQuality:a.renderQuality,canvas:[c.width,c.height],backendIndicator:document.getElementById("atelier-backend-indicator")?.textContent??null,contextAttributes:gl?.getContextAttributes(),unmaskedRenderer:d?gl.getParameter(d.UNMASKED_RENDERER_WEBGL):null}})()'),30)
    assert data['observedRenderer']['backendIndicator']=='WebGL2'
    assert data['observedRenderer']['unmaskedRenderer'],'Observed renderer identity unavailable'
    assert data['observedRenderer']['canvas']==[W,expectedHeight]
    session=await context.new_cdp_session(host);data['captures']=[]
    data['captures'].append(await capture(session,host,frame,'#stage',spec['label']+'-efficient'))
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
    data['beforeBalancedCapture']=await run_action('viewer:balanced-state',lambda:frame.evaluate('({ready:document.body.dataset.ready,cameraReady:document.getElementById("stage").dataset.cameraReady,quality:assemblyInspect().renderQuality})'),30)
    data['balancedRenderer']=await run_action('viewer:balanced-renderer-info',lambda:frame.evaluate('(()=>{const a=assemblyInspect(),c=document.getElementById("assembly-canvas");return {renderer:a.renderer??null,GPU:a.GPU??null,renderQuality:a.renderQuality,canvas:[c.width,c.height],backendIndicator:document.getElementById("atelier-backend-indicator")?.textContent??null}})()'),30)
    assert data['balancedRenderer']['canvas']==[round(W*1.5),round(expectedHeight*1.5)]
    data['captures'].append(await capture(session,host,frame,'#stage',spec['label']+'-balanced'))
    data['final']=await run_action('viewer:final-state',lambda:frame.evaluate('assemblyInspect()'),30)

async def main():
    assert pathlib.Path('coordinated-release-successor/release-id.txt').read_text().strip()==RID
    stop=asyncio.Event();sampler=asyncio.create_task(sample_loop(stop,O/'process-samples.jsonl',interval=15))
    try:
        async with async_playwright() as p:
            specs=json.loads((ROOT/'identities.json').read_text())
            for spec in specs:
                await one_arm(p,spec['label'],lambda b,c,h,d:viewer(b,c,h,d,spec),1100)
                if R['arms'][spec['label']]['cleanupFailure']:
                    R['remainingArmsSkipped']='Prior normal browser cleanup failed; later arm would not have proven process isolation'
                    break
            if len(R['arms'])==len(specs) and all(a['completed']for a in R['arms'].values()):
                baseline,candidate=[R['arms'][x['label']]for x in specs]
                assert baseline['frameParameters']==candidate['frameParameters']
                for field in ['viewport','observedRenderer','balancedRenderer']:
                    R.setdefault('comparability',{})[field]={'baseline':baseline[field],'candidate':candidate[field]}
                assert baseline['observedRenderer']['canvas']==candidate['observedRenderer']['canvas']
                assert baseline['observedRenderer']['unmaskedRenderer']==candidate['observedRenderer']['unmaskedRenderer']
                assert baseline['balancedRenderer']['canvas']==candidate['balancedRenderer']['canvas']
                for field in ['view','studioTour','animation','interiorAnimation','crystals','finish']:
                    assert baseline['initial'][field]==candidate['initial'][field],('state mismatch',field)
                for field in ['camera','target']:
                    delta=max(abs(a-b)for a,b in zip(baseline['initial'][field],candidate['initial'][field]))
                    R.setdefault('cameraComparability',{})[field+'MaxDifference']=delta
                    assert delta<.0001,('camera/target mismatch',field,delta)
                R['matchedArmsCompleted']=True
    except Exception as error:
        R['comparisonFailure']=repr(error);R['comparisonTraceback']=traceback.format_exc();raise
    finally:
        stop.set()
        try:await asyncio.wait_for(sampler,5)
        except Exception as error:R['samplerShutdownError']=repr(error)
        R['diagnosticFinished']=True;(O/'report.json').write_text(json.dumps(R,indent=2))
    # Every required image/control must succeed; cleanup failures remain visible.
    if not all(a['completed'] and not a['cleanupFailure'] for a in R['arms'].values()):raise RuntimeError('Matched diagnostic incomplete or cleanup failed; inspect report, not release approval')
if __name__=='__main__':asyncio.run(main())
