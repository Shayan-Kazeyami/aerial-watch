"""Build-only additive proposal atop pinned privacy/encoding feature; no source/ref/deploy writes."""
from pathlib import Path
import os,json,hashlib,shutil
Q=Path(__file__).resolve().parent;OLD='3448182496cf6c2b906abe4b5a7128a9537ab745e8f992d4d55783fd389879e6';B=Path(os.environ.get('NORMAL_BASE','watch-error-redaction-build/staging/preview-b/releases/'+OLD));sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(B/'deployment-manifest.json').read_bytes();assert sha(raw)=='49260cf42c2993f5be0c7b8ec244ee1a6f525d8e6448a7a1aa8733f0671cf1f9';m=json.loads(raw);can={k:m[k] for k in ['schemaVersion','localFiles','references']};assert sha(json.dumps(can,separators=(',',':')).encode())==OLD
for f in m['localFiles']+m['references']:
 src=B.parent/f.get('ownerReleaseId',OLD)/f['path'];data=src.read_bytes();assert len(data)==f['sizeBytes'] and sha(data)==f['sha256'],str(src)
assert sha((B/'assembly-fetch-progressive-normal.js').read_bytes())=='743d45d45cf82371364f842051ce6313fae41fb83b862897dc7f1fa24207cc40'
assert sha((B/'atelier-error-details.js').read_bytes())=='e28bdd29a032d5dad5d2a501b08c02536a386b22abb04fc7bc2796b9a843de58'
assert sha((B/'assembly-review.js').read_bytes())=='18acb2b6eea2a0a26b80dd173fc48a8bece76e6f2a66238ef84e3c57e0c79ae7'
candidate=(Q/'candidate.mjs').read_bytes();assert sha(candidate)=='89ff6e1bc368731c77499830cda4a4682e9798c234fcb47df0b96a3d579d62d2'
changes={'assembly-fetch-progressive-normal.js':candidate};files={f['path']:dict(f) for f in m['localFiles']}
def put(n,b):changes[n]=b;files[n]={'path':n,'sizeBytes':len(b),'sha256':sha(b)}
put('assembly-fetch-progressive-normal.js',candidate)
rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']} for f in sorted(files.values(),key=lambda f:f['path']) if '/' not in f['path'] and Path(f['path']).suffix in ['.html','.js','.css']]
v={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(rf,separators=(',',':')).encode()),'files':rf}
put('quality-study/viewer-revision.json',(json.dumps(v,indent=2)+'\n').encode());put('quality-study/viewer-revision.js',('export default '+json.dumps(v,separators=(',',':'))+';\n').encode())
can={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':m['references']};rid=sha(json.dumps(can,separators=(',',':')).encode());manifest={**can,'releaseId':rid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']};receipt={'schemaVersion':2,'releaseId':rid,'algorithm':'SHA-256','fileCount':len(files),'totalBytes':sum(f['sizeBytes'] for f in files.values()),'referenceCount':len(m['references']),'referencedBytes':sum(f['sizeBytes'] for f in m['references'])}
root=Q/'staging';root.mkdir(exist_ok=False);stage=root/'preview-b/releases'/rid
for f in can['localFiles']+can['references']:
 owner=f.get('ownerReleaseId',rid);data=(B.parent/f.get('ownerReleaseId',OLD)/f['path']).read_bytes() if f['path'] not in changes or 'ownerReleaseId' in f else changes[f['path']];dst=root/'preview-b/releases'/owner/f['path'];dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);assert sha(data)==f['sha256'] and len(data)==f['sizeBytes']
for n,j in [('deployment-manifest.json',manifest),('release-receipt.json',receipt)]: (stage/n).write_text(json.dumps(j,indent=2)+'\n')
# Preserve pinned feature bootstrap/UI. ONLY immutable target changes in isolated staging.
entry=B.parents[2]
entryPins={'index.html': '78aed279f7e3f2a8274d540edf2d6a293bea04c137a0162d425f4cf6f3b79c47', 'watch-home-coordinated-successor.js': '7240a0d79626b0b0da367d22e1541b000e6dc36c9e6969570ba9d13db8921fd7', 'watch-home-loading-v4.css': '0db4e30c1e54f824152441bf5f566664df84ebf61d8996b8a78f9c4e271c5ee1'}
for name in ['index.html','watch-home-coordinated-successor.js','watch-home-loading-v4.css']:
 data=(entry/name).read_bytes();assert sha(data)==entryPins[name];new=data.replace(OLD.encode(),rid.encode()) if name!='watch-home-loading-v4.css' else data
 if name=='watch-home-coordinated-successor.js':assert data.count(OLD.encode())==1
 assert new.replace(rid.encode(),OLD.encode())==data
 (root/name).write_bytes(new)
fixtures=Q/'fixtures';fixtures.mkdir(exist_ok=False)
for name in ['normal-2048-existing-mips.ktx2','outer-normal-4k.ktx2.part0','outer-normal-4k.ktx2.part1']:shutil.copyfile(B/'leather-assets/r14'/name,fixtures/name)
(Q/'release-id.txt').write_text(rid);report={'passed':True,'baseFeatureCommit':'c8f3bc16ba61569536b2226732b27a778e67f804','baseRelease':OLD,'newRelease':rid,'closureFiles':len(can['localFiles'])+len(can['references']),'changedLocalPaths':sorted(changes),'referencesExact':can['references']==m['references'],'bootstrapOnlyTargetChanged':True,'privacyEncodingRuntimePreserved':True,'scope':'isolated feature build; no deployment/main/preview changes','holds':['Existing0116 UI/publicationholds remain','ActualviewerQA usede79 notthiscomposedrelease','No measured browserheap/FPS/speedclaim','Earlyfailedloadfull16.56MBalloc vs4/8MBbaseline']};(Q/'build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
