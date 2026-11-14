import pathlib,hashlib,json
root=pathlib.Path(__file__).resolve().parent
source=root.parent/'watch-normal-stream-build/staging/preview-b/releases/c9d2d1a59b4efacb6d4b44824baefd047dab96351b0086fa8bfe1032168c31bc'
s=(source/'assembly-review.js').read_text()
old="attach:detail=>gltf.scene.add(detail.group)"
assert s.count(old)==2
new="attach:detail=>{if(window.__lazyFaultArm){const owner=window.__lazyFaultArm;window.__lazyFaultArm=null;const onAdded=()=>{detail.group.removeEventListener('added',onAdded);owner.dispose();};detail.group.addEventListener('added',onAdded);window.__lazyFaultGroup=detail.group;}gltf.scene.add(detail.group)}"
s=s.replace(old,new)
s+='''\n// ISOLATED QA ONLY: exercises actual lazy dial factory and actual loaded scene.
window.__lazyViewerQA={
 ready:()=>!loading&&!failed&&!contextLost&&!lifecycle.disposed&&presentationGate.snapshot().interactive&&backendIdentity.actual==='WebGL2',
 snapshot:()=>({disposed:lifecycle.disposed,solid:!!dialDetailLazy?.value,open:!!openDialDetailLazy?.value,interactive:presentationGate.snapshot().interactive}),
 exercise:(kind,fault=false)=>{
  if(!window.__lazyViewerQA.ready())throw Error('Viewer not ready');
  const owner=kind==='solid'?dialDetailLazy:kind==='open'?openDialDetailLazy:null;
  if(!owner||owner.value)throw Error('Fresh uncreated owner required');
  if(fault)window.__lazyFaultArm=owner;
  let result,error;try{result=owner.ensure();}catch(e){error=String(e);}
  const group=result?.group??window.__lazyFaultGroup;
  return {error:error??null,retained:!!owner.value,attached:!!group?.parent,reused:!fault&&owner.ensure()===result};
 }
};
'''
(root/'assembly-review.qa.js').write_text(s)
(root/'SOURCE_PINS.json').write_text(json.dumps({str(p.relative_to(root.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source/'assembly-review.js',source/'assembly-lazy-detail.js',root.parent/'watch-lazy-reentry/candidate.mjs',root/'assembly-review.qa.js']},indent=2)+'\n')
