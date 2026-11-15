from pathlib import Path
import hashlib,json,shutil,sys
Q=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
roots={'baseline':('watch-shell-home-build/staging','bfbaaf3576738da1930718602031607bbc6d5b57a1a504fd5c231be3ccc160c0','f02f88014eedd44769f5dce54c784b07d391aae6523da1d7bd2582cdfaa8f23f'),'candidate':('watch-backplate-317-build/staging','ababdaee0577934bfcdb140d4c68087d804a39d55c4513e222bbf376d25da54d','6b1fc969fd8cba0cfa1480a828d2ccb1b45c477292c244b910b999abdf9bc93f')};report={}
for arm,(root,rid,expected_review)in roots.items():
 b=Q.parent/root;s=b/'preview-b/releases'/rid;m=json.loads((s/'deployment-manifest.json').read_bytes());assert sha(json.dumps({k:m[k]for k in ['schemaVersion','localFiles','references']},separators=(',',':')).encode())==rid;assert len(m['localFiles'])+len(m['references'])==298
 for f in m['localFiles']+m['references']:
  p=b/'preview-b/releases'/f.get('ownerReleaseId',rid)/f['path'];data=p.read_bytes();assert len(data)==f['sizeBytes']and sha(data)==f['sha256']
 review=(s/'assembly-review.js').read_bytes();assert sha(review)==expected_review
 qa_review=review+(Q/'hook.js').read_bytes();bootstrap=(s/'atelier-preview.js').read_bytes();old=b"import('./assembly-review.js?v=atelier-local-1')";assert bootstrap.count(old)==1;qa_bootstrap=bootstrap.replace(old,b"import('./g317-qa-review.js?v=g317-1')");html=(s/'atelier-preview.html').read_bytes();assert html.count(b'src="atelier-preview.js"')==1;qa_html=html.replace(b'src="atelier-preview.js"',b'src="g317-qa-bootstrap.js"')
 extra={'g317-qa-review.js':qa_review,'g317-qa-bootstrap.js':qa_bootstrap,'g317-qa.html':qa_html};report[arm]={'rid':rid,'root':root,'closureFiles':298,'expectedOriginalReviewSHA256':expected_review,'namedQAFiles':{n:sha(v)for n,v in extra.items()},'canonicalFilesUnchanged':True,'qaOnlyObserversAndImportRedirect':True}
 if '--materialize'in sys.argv:
  out=Q/('prepared-'+arm);assert not out.exists();shutil.copytree(b,out)
  for n,data in extra.items():(out/'preview-b/releases'/rid/n).write_bytes(data)
(Q/'QA_CLOSURE.json').write_text(json.dumps(report,indent=2)+'\n');print('Both canonical298 closures verified; three separately named QA files declared for each arm, originals unchanged')
