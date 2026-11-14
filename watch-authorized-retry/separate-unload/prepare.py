"""Record/guard exact published baseline entry and both immutable source identities."""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
Q=pathlib.Path('coordinated-release-successor')
BASE='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
CAND='011614d052b49dd32652ec25e31bd471addef053bfda24510d7741485fe37192'
assert (Q/'release-id.txt').read_text().strip()==CAND
for n in ['index.html','watch-home-caseback-e79b2236.js','watch-home-loading-v4.css']:
    assert pathlib.Path(n).read_bytes()==(Q/'entry-baseline'/n).read_bytes(),('published root drift',n)
specs=[]
for label,rid,base,root in [('published-e79',BASE,pathlib.Path('preview-b/releases')/BASE,'http://127.0.0.1:8766/'),('frozen-0116',CAND,Q/'staging/preview-b/releases'/CAND,'http://127.0.0.1:8765/')]:
    manifest=json.loads((base/'deployment-manifest.json').read_text());assert manifest['releaseId']==rid
    revision=json.loads((base/'quality-study/viewer-revision.json').read_text())
    source=(base/'assembly-review.js').read_bytes();sha=hashlib.sha256(source).hexdigest()
    expected=next(f['sha256']for f in manifest['localFiles']if f['path']=='assembly-review.js');assert sha==expected
    specs.append({'label':label,'release':rid,'root':root,'viewerDigest':revision['digest'],'sourceSHA256':sha,'sourceBytes':len(source),'manifestSHA256':hashlib.sha256((base/'deployment-manifest.json').read_bytes()).hexdigest()})
(ROOT/'identities.json').write_text(json.dumps(specs,indent=2))
