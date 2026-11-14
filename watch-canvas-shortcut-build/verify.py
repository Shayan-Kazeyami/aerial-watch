from pathlib import Path
import json,hashlib
q=Path(__file__).parent;old='48438e79481a6258e2ae563e943d25a516c2e5a515f15a6335bdb08197ca752d';new=(q/'release-id.txt').read_text();a=Path('watch-utf8-text-build/staging/preview-b/releases')/old;b=q/'staging/preview-b/releases'/new;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ma=json.loads((a/'deployment-manifest.json').read_text());mb=json.loads((b/'deployment-manifest.json').read_text())
for root,m,rid in [(a,ma,old),(b,mb,new)]:
 assert hashlib.sha256(json.dumps({k:m[k]for k in ['schemaVersion','localFiles','references']},separators=(',',':')).encode()).hexdigest()==rid
 for f in m['localFiles']+m['references']:
  p=root.parent/f.get('ownerReleaseId',rid)/f['path'];assert sha(p)==f['sha256'] and p.stat().st_size==f['sizeBytes']
x={f['path']:f for f in ma['localFiles']};y={f['path']:f for f in mb['localFiles']};assert x.keys()==y.keys();changes=sorted(n for n in x if x[n]!=y[n]);assert changes==['assembly-review.js','quality-study/viewer-revision.js','quality-study/viewer-revision.json'];assert ma['references']==mb['references'];assert sha(b/'assembly-component-labels.js')=='1c811a0b185bdbd8e13f99c6aa44d088015b94e28b1fd10c0c99f6d0303f8fdb';assert sha(b/'assembly-crown-hotspot.js')=='948c0e5c83e32de20d19548666f7d8898d9ca40c8d53b8a9d28bd832e1f73373'
(q/'VERIFY.json').write_text(json.dumps({'baseRelease':old,'candidateRelease':new,'both_closures':298,'changed_local_files':changes,'references_unchanged':True,'crown_fix_preserved':True,'explorer_labels_preserved':True,'all_other_runtime_files_preserved':True,'browser_tested':False,'deployment':False},indent=2)+'\n');print('PASS both closures, exact three changes, references/crown fix preserved')

oldtext=(a/'assembly-review.js').read_text();newtext=(b/'assembly-review.js').read_text();base=(q/'BASE_HANDLER.txt').read_text();candidate=(q/'CANDIDATE_HANDLER.txt').read_text();assert oldtext.count(base)==1;assert newtext==oldtext.replace(base,candidate,1);assert all(token not in newtext for token in ['Â·','â€¦','â†’','Ã—']);print('PASS integrated handler exact; all other current source bytes and UTF8 fixes preserved')
