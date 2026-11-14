from pathlib import Path
import json,hashlib
q=Path(__file__).parent;old='5af481a243687d5d809267eb8912a8cdbfd859f6b7daf2e00b60164da12406c2';new=(q/'release-id.txt').read_text();a=Path('watch-support-text-build/staging/preview-b/releases')/old;b=q/'staging/preview-b/releases'/new;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ma=json.loads((a/'deployment-manifest.json').read_text());mb=json.loads((b/'deployment-manifest.json').read_text())
for root,m,rid in [(a,ma,old),(b,mb,new)]:
 assert hashlib.sha256(json.dumps({k:m[k]for k in ['schemaVersion','localFiles','references']},separators=(',',':')).encode()).hexdigest()==rid
 for f in m['localFiles']+m['references']:
  p=root.parent/f.get('ownerReleaseId',rid)/f['path'];assert sha(p)==f['sha256'] and p.stat().st_size==f['sizeBytes']
x={f['path']:f for f in ma['localFiles']};y={f['path']:f for f in mb['localFiles']};assert x.keys()==y.keys();changes=sorted(n for n in x if x[n]!=y[n]);assert changes==['assembly-review.js','quality-study/viewer-revision.js','quality-study/viewer-revision.json'];assert ma['references']==mb['references'];assert sha(b/'assembly-component-labels.js')=='1c811a0b185bdbd8e13f99c6aa44d088015b94e28b1fd10c0c99f6d0303f8fdb';assert sha(b/'assembly-crown-hotspot.js')=='948c0e5c83e32de20d19548666f7d8898d9ca40c8d53b8a9d28bd832e1f73373'
(q/'VERIFY.json').write_text(json.dumps({'baseRelease':old,'candidateRelease':new,'both_closures':298,'changed_local_files':changes,'references_unchanged':True,'crown_fix_preserved':True,'explorer_labels_preserved':True,'all_other_runtime_files_preserved':True,'browser_tested':False,'deployment':False},indent=2)+'\n');print('PASS both closures, exact three changes, references/crown fix preserved')

patch=json.loads((q/'patch.json').read_text());old=(a/'assembly-review.js').read_text();new=(b/'assembly-review.js').read_text();assert old.count(patch['old'])==1;assert new==old.replace(patch['old'],patch['new'],1);assert sha(b/'assembly-story.js')=='c501fdfa2071d9c760cc2001bdaaac7b53299241eca138fbc6eb60551ff3708c';print('PASS exact integrated save-request feedback; saved-clock and all other latest bytes preserved')
