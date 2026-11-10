import asyncio,json,pathlib,base64,hashlib
from playwright.async_api import async_playwright
RID='99d5275244fdabbc301fba262d59e612e7f511121e5e79a5dae5bf936e222e75'
R=pathlib.Path('preview-b/releases')/RID;O=pathlib.Path('marked-output');O.mkdir(exist_ok=True)
module=pathlib.Path('marked-ci/assembly-carrier-tip.js').read_text();(R/'qa-carrier-tip.js').write_text(module)
source=(R/'assembly-review.js').read_text();hook="""
window.__marked={
 pose(t){stopTour();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();clock.seek(t,{track:'mechanism'});applyClockPose(clock.seek(0,{track:'hands'}));dirty=true;},
 macro(close=false){this.pose(0);view('face',false);cameraTween=null;controls.enableDamping=false;controls.target.set(...(close?[-8.8,6.4,1.3]:[-7.4,5.6,1.2]));camera.position.copy(controls.target).add(new THREE.Vector3(...(close?[-.6,.8,7]:[-1.5,2,17])));camera.lookAt(controls.target);controls.minDistance=0;controls.update();dirty=true;},
 shot(){cancelAnimationFrame(animationFrame);composer.render();return renderer.domElement.toDataURL('image/png');},
 rayGrid(){return (()=>{const meshes=[];scene.traverseVisible(o=>{if(o.isMesh&&!/crystal|backplate|floor/i.test(o.name))meshes.push(o)});const out=[];for(const x of [435,450,470,490,510,525,600,650])for(const y of [300,340,360,380,400,420]){const ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2(x/900*2-1,1-y/646*2),camera);out.push({x,y,hits:ray.intersectObjects(meshes,false).slice(0,3).map(h=>({name:h.object.name,data:h.object.userData,point:h.point.toArray()}))})}return out;})();},
 audit(){return {asset:verifiedStructuralSupportSHA256,tip:window.__tipAudit??null,camera:camera.position.toArray(),target:controls.target.toArray(),gl:backendIdentity};}
};
"""
needle='model.add(proposal.scene);resources.own(\'optional proposed plates\',disposeProposal);'
replacement=needle+"\n if(new URLSearchParams(location.search).get('tip')==='on'){const tip=repairCarrierTip(candidates.find(m=>m.userData.replacementForSourceIndex===0),{verifiedSHA256:verifiedStructuralSupportSHA256});window.__tipAudit=tip.audit;resources.own('local tip round',()=>tip.dispose());}"
assert needle in source
source="import {repairCarrierTip} from './qa-carrier-tip.js';\n"+source.replace(needle,replacement)+hook
(R/'qa-marked-review.js').write_text(source)
(R/'qa-marked-atelier.js').write_text((R/'atelier-preview.js').read_text().replace('./assembly-review.js?v=atelier-local-1','./qa-marked-review.js'))
(R/'qa-marked.html').write_text((R/'atelier-preview.html').read_text().replace('atelier-preview.js','qa-marked-atelier.js'))
async def main():
 report={'release':RID,'sourceSHA256':hashlib.sha256(source.encode()).hexdigest(),'moduleSHA256':hashlib.sha256(module.encode()).hexdigest(),'errors':[],'cases':[],'ao':'off for deterministic comparison'}
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for tip in ['off']:
    pg=await b.new_page(viewport={'width':900,'height':900},device_scale_factor=1);pg.on('pageerror',lambda e:report['errors'].append(str(e)))
    await pg.goto(f'http://127.0.0.1:8765/{R}/qa-marked.html?quality=efficient&paused=1&ao=off&tip={tip}',wait_until='domcontentloaded')
    await pg.wait_for_function('window.__marked && window.assemblyInspect && assemblyInspect().presentation.interactive',timeout=240000)
    for close in [True]:
     await pg.evaluate('(close)=>__marked.macro(close)',close);await pg.wait_for_timeout(300)
     report['visibleRays']=await pg.evaluate('__marked.rayGrid()');data=await pg.evaluate('__marked.shot()');name=f'{tip}-'+('close' if close else 'macro')+'.png';(O/name).write_bytes(base64.b64decode(data.split(',')[1]));print('IMAGE_START '+name,flush=True);print(data.split(',')[1],flush=True);print('IMAGE_END '+name,flush=True)
     report['cases'].append({'tip':tip,'close':close,'audit':await pg.evaluate('__marked.audit()')})
    await pg.close()
  finally:
   await b.close();(O/'report.json').write_text(json.dumps(report,indent=2));print('REPORT '+json.dumps(report),flush=True)
asyncio.run(main())
