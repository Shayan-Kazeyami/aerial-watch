import asyncio,json,pathlib,hashlib,traceback
from playwright.async_api import async_playwright
RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6';O=pathlib.Path('isolated-touch-selection-audit/evidence');O.mkdir(parents=True,exist_ok=True);R={'scope':'native CDP touch on original e79 app; private QA alias/counters only; no release patch','cases':[],'errors':[]}
async def run():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']);p=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=1,is_mobile=True,has_touch=True);p.set_default_timeout(180000)
  source=pathlib.Path('preview-b/releases/'+RID+'/assembly-review.js').read_text();R['sourceSHA256']=hashlib.sha256(source.encode()).hexdigest();assert R['sourceSHA256']=='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee'
  wrapped=source
  for name in ['clearSelection','select']:
   needle='function '+name+('() {'if name=='clearSelection'else'(mesh) {');assert wrapped.count(needle)==1;wrapped=wrapped.replace(needle,needle+f'window.__touchAudit.actions.push({{type:"{name}",t:performance.now()}});')
  wrapped+='''\nwindow.__touchAudit={actions:[],events:[],pause(){for(const id of ['animate','animate-movement']){const e=$(id);if(e.checked){e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}}stopTour();},capture(){composer.render();return renderer.domElement.toDataURL('image/png')}};for(const type of ['pointerdown','pointerup','pointercancel'])renderer.domElement.addEventListener(type,e=>__touchAudit.events.push({type,id:e.pointerId,primary:e.isPrimary,x:e.clientX,y:e.clientY}),true);'''
  R['wrapperSHA256']=hashlib.sha256(wrapped.encode()).hexdigest()
  async def alias(q):await q.fulfill(status=200,content_type='text/javascript',body=wrapped)
  async def boot(q):
   x=await q.fetch();s=await x.text();needle="import('./assembly-review.js?v=atelier-local-1')";assert s.count(needle)==1;await q.fulfill(response=x,body=s.replace(needle,"import('./assembly-touch-audit-private.js')"))
  await p.route('**/atelier-preview.js',boot);await p.route('**/assembly-touch-audit-private.js',alias);p.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await p.goto('http://127.0.0.1:8766/?quality=efficient',wait_until='domcontentloaded');await p.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=300000);f=next(f for f in p.frames if RID in f.url);await f.wait_for_function('window.__touchAudit&&document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000);await f.evaluate('__touchAudit.pause()');await f.locator('#home').tap();await f.wait_for_timeout(1500)
   canvas=f.locator('#assembly-canvas');box=await canvas.bounding_box();cdp=await p.context.new_cdp_session(p)
   # Find unobscured empty-canvas region; avoid crown and dock controls.
   pt=await f.evaluate('''()=>{const c=document.querySelector('#assembly-canvas'),r=c.getBoundingClientRect();for(const [u,v] of [[.15,.2],[.2,.3],[.8,.2]]){const x=r.left+r.width*u,y=r.top+r.height*v;if(document.elementFromPoint(x,y)===c)return {x,y}}throw Error('no unobscured canvas')}''');offset=await p.locator('#watch-viewer').bounding_box();x=pt['x']+offset['x'];y=pt['y']+offset['y'];R['point']={'x':x,'y':y}
   async def send(kind,points):await cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':points});await f.wait_for_timeout(75)
   def touch(id,x,y):return {'id':id,'x':x,'y':y,'radiusX':1,'radiusY':1,'force':1}
   for name,multi in [('single-tap',False),('two-finger-release',True)]:
    await f.evaluate('__touchAudit.actions=[];__touchAudit.events=[]');a=touch(1,x,y);bb=touch(2,x+50,y)
    await send('touchStart',[a])
    if multi:
     await send('touchStart',[a,bb]);await send('touchMove',[touch(1,x-20,y),bb]);await send('touchEnd',[bb])
    await send('touchEnd',[]);R['cases'].append({'name':name,**await f.evaluate('({actions:__touchAudit.actions,events:__touchAudit.events})')})
   assert not R['errors'];assert any(e['type']=='pointerup' and not e['primary']for e in R['cases'][1]['events']);R['nativeDiagnosticExecuted']=True
  except Exception as e:R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:(O/'report.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(run())
