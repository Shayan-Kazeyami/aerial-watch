import asyncio,json,pathlib,base64,hashlib,traceback
from playwright.async_api import async_playwright
RID='99d5275244fdabbc301fba262d59e612e7f511121e5e79a5dae5bf936e222e75'
R=pathlib.Path('preview-b/releases')/RID
O=pathlib.Path('marked-output');O.mkdir(exist_ok=True)
HOOK=r'''
window.__marked={
 pause(){stopTour();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();dirty=true;},
 pose(t){this.pause();clock.seek(t,{track:'mechanism'});applyClockPose(clock.seek(t,{track:'hands'}));dirty=true;},
 macro(){this.pause();view('face',false);cameraTween=null;controls.enableDamping=false;controls.target.set(-7.4,5.6,1.2);camera.position.copy(controls.target).add(new THREE.Vector3(-1.5,2,17));camera.lookAt(controls.target);controls.update();dirty=true;},
 async shot(){cancelAnimationFrame(animationFrame);composer.render();return renderer.domElement.toDataURL('image/png');},
 list(){return source.map(m=>({id:m.userData.sourceIndex,name:m.name,description:m.userData.description,position:m.position.toArray(),world:m.getWorldPosition(new THREE.Vector3()).toArray(),visible:m.visible,vertices:m.geometry.attributes.position.count}));},
 ray(x,y){let ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2(x,y),camera);return ray.intersectObjects(scene.children,true).slice(0,10).map(h=>({name:h.object.name,userData:h.object.userData,point:h.point.toArray(),face:h.faceIndex}));},
 render(){composer.render();},
 isolate(ids){for(const m of source)m.visible=ids.includes(m.userData.sourceIndex);for(const m of exterior)m.visible=false;if(premiumFace)premiumFace.group.visible=false;if(qualityDesign)qualityDesign.group.visible=false;for(const m of openPlates)m.visible=false;dirty=true;}
};
'''
(R/'qa-marked-review.js').write_text((R/'assembly-review.js').read_text()+'\n'+HOOK)
(R/'qa-marked-atelier.js').write_text((R/'atelier-preview.js').read_text().replace('./assembly-review.js?v=atelier-local-1','./qa-marked-review.js'))
(R/'qa-marked.html').write_text((R/'atelier-preview.html').read_text().replace('atelier-preview.js','qa-marked-atelier.js'))
async def main():
 report={'release':RID,'errors':[],'renderer':'Chromium SwiftShader','phaseSamples':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  pg=await b.new_page(viewport={'width':900,'height':900},device_scale_factor=1);pg.on('pageerror',lambda e:report['errors'].append(str(e)))
  try:
   await pg.goto(f'http://127.0.0.1:8765/{R}/qa-marked.html?quality=efficient&paused=1',wait_until='domcontentloaded')
   await pg.wait_for_function('window.__marked && window.assemblyInspect && assemblyInspect().presentation.interactive',timeout=240000)
   await pg.evaluate('__marked.macro()');report['runtime']=await pg.evaluate('assemblyInspect()');report['sources']=await pg.evaluate('__marked.list()')
   for i,t in enumerate([0,1/28,1/14,3/28]):
    await pg.evaluate('(t)=>__marked.pose(t)',t);await pg.wait_for_timeout(300)
    data=await pg.evaluate('__marked.shot()');(O/f'macro-{i}.png').write_bytes(base64.b64decode(data.split(',')[1]));print('IMAGE_START '+f'macro-{i}.png',flush=True);print(data.split(',')[1],flush=True);print('IMAGE_END '+f'macro-{i}.png',flush=True)
    report['phaseSamples'].append({'t':t,'inspect':await pg.evaluate('assemblyInspect()')})
   report['rayGrid']=await pg.evaluate('(()=>{const r=[];for(let x=-.5;x<=.5;x+=.1)for(let y=-.5;y<=.5;y+=.1)r.push({x,y,hits:__marked.ray(x,y)});return r})()')
   (O/'report.json').write_text(json.dumps(report,indent=2));print('REPORT '+json.dumps(report),flush=True)
  except Exception as e:
   report['failure']=str(e);(O/'report.json').write_text(json.dumps(report,indent=2));raise
  finally:await b.close()
asyncio.run(main())
