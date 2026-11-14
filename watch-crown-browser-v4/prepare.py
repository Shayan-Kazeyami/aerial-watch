from pathlib import Path
import hashlib,json,shutil,sys
Q=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
roots={'baseline':('watch-normal-stream-build/staging','c9d2d1a59b4efacb6d4b44824baefd047dab96351b0086fa8bfe1032168c31bc'),'candidate':('watch-crown-key-build/staging','bd55a594260f4627127bcdb1975c2f9902eede87d0528669e02a111552ba939d')}
hook='''\n// QA-only read-only state telemetry; no turns, render calls, or availability overrides.\nwindow.__crownParityQA={ready:()=>!loading&&!failed&&!contextLost&&!backendIdentity.deviceLostReason&&presentationGate.snapshot().interactive&&currentCaptureDetail().phase==='full'&&!cameraTween&&!crownInteraction.active&&!crownVisual?.active,snapshot:()=>({crown:crownInteraction.snapshot(),settingSeconds,view:currentView,canvas:[renderer.domElement.width,renderer.domElement.height],timeOrigin:performance.timeOrigin,disposed:lifecycle.disposed})};\n'''
report={}
for arm,(root,rid) in roots.items():
 b=Q.parent/root;s=b/'preview-b/releases'/rid;m=json.loads((s/'deployment-manifest.json').read_text());assert sha(json.dumps({k:m[k] for k in ['schemaVersion','localFiles','references']},separators=(',',':')).encode())==rid
 rows=m['localFiles']+m['references'];assert len(rows)==298
 for f in rows:
  data=(b/'preview-b/releases'/f.get('ownerReleaseId',rid)/f['path']).read_bytes();assert len(data)==f['sizeBytes'] and sha(data)==f['sha256']
 original=(s/'assembly-review.js').read_bytes();assert sha(original)=='18acb2b6eea2a0a26b80dd173fc48a8bece76e6f2a66238ef84e3c57e0c79ae7';overlay=original+hook.encode()
 if '--materialize' in sys.argv:
  out=Q/('prepared-'+arm);assert not out.exists();shutil.copytree(b,out);(out/'preview-b/releases'/rid/'assembly-review.js').write_bytes(overlay)
 report[arm]={'rid':rid,'closureFiles':298,'overlay':{'assembly-review.js':sha(overlay)},'originalReview':sha(original)}
(Q/'QA_CLOSURE.json').write_text(json.dumps(report,indent=2)+'\n')
print('Both exact closures verified; only read-only QA telemetry declared')
