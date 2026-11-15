from pathlib import Path
import json,hashlib,sys
Q=Path(__file__).resolve().parent;F=Q.parent/'watch-face-evidence-batch-v3';H=lambda b:hashlib.sha256(b).hexdigest();expectedFaceFreeze='7089d5981b04691f165b5150e869cffd064cd167ef27fd3ed3b799340796f32a';assert H((F/'FREEZE_DRAFT.json').read_bytes())==expectedFaceFreeze
for n,h in json.loads((F/'FREEZE_DRAFT.json').read_text()).items():assert H((F/n).read_bytes())==h,n
routing=Q.parent/'watch-shell-home-build/staging/preview-b/releases/bfbaaf3576738da1930718602031607bbc6d5b57a1a504fd5c231be3ccc160c0/assembly-optimized-loading.js';routingText=routing.read_text();assert "'premium-face/face-svg04.glb':'optimized-assets/premium-face__face-svg04.meshopt.glb'"in routingText;assert "'rebuild/assembly.glb':'optimized-assets/rebuild__assembly.meshopt.glb.gz'"in routingText
face=json.loads((F/'SERVED_SHA256.json').read_text());closure=json.loads((Q/'QA_CLOSURE.json').read_text());assert len(face)==12
expectedFaceFrames=[]
for obj,shots,wires,arms in [('q333',[(m,None)for m in ['near','grazing']],[False],['A','B','A2']),('q402',[(m,p)for p in [397,1158]for m in ['near','grazing']],[False,True],['A','B','A2']),('q401',[(m,p)for p in [None,35,186,8]for m in ['fit-front','fit-grazing']],[False],['A','A2'])]:
 for mode,parent in shots:
  for wire in wires:
   for arm in arms:expectedFaceFrames.append(f'{obj}-{parent}-{mode}-'+('wire'if wire else'pbr')+'-'+arm)
assert len(expectedFaceFrames)==46
manifest={'assetRouteModuleSHA256':H(routing.read_bytes()),'g317':closure,'face':{'rid':closure['baseline']['rid'],'namedQAFiles':face,'expectedFrameKeysPerRoute':expectedFaceFrames,'componentFreeze':expectedFaceFreeze},'assetRoutePaths':{'raw':{'assembly':'/rebuild/assembly.glb','face':'/premium-face/face-svg04.glb'},'meshopt':{'assembly':'/optimized-assets/rebuild__assembly.meshopt.glb.gz','face':'/optimized-assets/premium-face__face-svg04.meshopt.glb'}},'viewport':[1280,900],'deviceScaleFactor':1,'routes':['raw','meshopt'],'canonicalSources':{'assembly':'6ac638843c56eb4ae2f3d9ee1135facaac085ae70e2292f2b3d30f9673340039','face':'9766f3b04c56d698e52b999771ea494ac5ca49341da2ed8b22ec57fd6ac2a51c'},'quality':'Human paired actual-render review required; q401 source gap0.019mm remains; no GPU/performance/adoption/finalization acceptance.'}
raw=(json.dumps(manifest,indent=2)+'\n').encode();out=Q/'EXPECTED_EXECUTION.json'
if '--materialize'in sys.argv:
 assert out.read_bytes()==raw,'External expected manifest differs; do not self-update during run'
 root=Q/'prepared-baseline'/'preview-b/releases'/closure['baseline']['rid'];assert root.is_dir()
 for name,h in face.items():
  b=(F/'served'/name).read_bytes();assert H(b)==h;dest=root/name
  with dest.open('xb')as f:f.write(b)
 print('Twelve independently named face files added; canonical298 filenames unchanged. External execution manifest preserved.')
elif '--verify'in sys.argv:assert out.read_bytes()==raw;print('External expected manifest verified, not self-updated')
else:out.write_bytes(raw);print('Prepared external expected source/frame manifest locally; no run/materialization')
