from pathlib import Path
import hashlib,json,os
Q=Path(__file__).resolve().parent
OLD='bfbaaf3576738da1930718602031607bbc6d5b57a1a504fd5c231be3ccc160c0'
B=Path('watch-shell-home-build/staging/preview-b/releases')/OLD
P=Path('watch-backplate-317-integration')
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((B/'deployment-manifest.json').read_bytes())
canonical=lambda m:json.dumps({k:m[k] for k in ['schemaVersion','localFiles','references']},separators=(',',':')).encode()
assert sha(canonical(manifest))==OLD
for f in manifest['localFiles']+manifest['references']:
 s=B.parent/f.get('ownerReleaseId',OLD)/f['path'];b=s.read_bytes();assert sha(b)==f['sha256'] and len(b)==f['sizeBytes']
input_pins={'original.js': '2d074b1e93189ccb54a2c5400f407c3ec29e949a714a0dab17f168c3789cf38a', 'candidate.js': 'd4d608edd43bda3499216267e9f07f644f9ad01d45df4167dba815d5739f9f10', 'review.patch.json': '9264cd753b50e3fc5b2d100779b3dad315a080eb6a3818cf1914a78330842139'}
for name,digest in input_pins.items():assert sha((P/name).read_bytes())==digest,name
assert (B/'assembly-backplate.js').read_bytes()==(P/'original.js').read_bytes()
patch=json.loads((P/'review.patch.json').read_text());review=(B/'assembly-review.js').read_text();assert sha(review.encode())==patch['source_sha256']
for old,new in patch['replacements']:
 assert review.count(old)==1;review=review.replace(old,new,1)
changes={'assembly-backplate.js':(P/'candidate.js').read_bytes(),'assembly-review.js':review.encode()}
files={f['path']:dict(f)for f in manifest['localFiles']}
def put(n,b):changes[n]=b;files[n]={'path':n,'sizeBytes':len(b),'sha256':sha(b)}
for n,b in list(changes.items()):put(n,b)
rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']}for f in sorted(files.values(),key=lambda f:f['path'])if '/'not in f['path']and Path(f['path']).suffix in ['.html','.js','.css']]
v={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(rf,separators=(',',':')).encode()),'files':rf}
put('quality-study/viewer-revision.json',(json.dumps(v,indent=2)+'\n').encode());put('quality-study/viewer-revision.js',('export default '+json.dumps(v,separators=(',',':'))+';\n').encode())
can={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':manifest['references']};rid=sha(json.dumps(can,separators=(',',':')).encode());out={**can,'releaseId':rid,'referenceLayout':manifest['referenceLayout'],'assetClosure':manifest['assetClosure']}
root=Q/'staging';root.mkdir(exist_ok=False);stage=root/'preview-b/releases'/rid
for f in can['localFiles']+can['references']:
 dst=root/'preview-b/releases'/f.get('ownerReleaseId',rid)/f['path'];dst.parent.mkdir(parents=True,exist_ok=True)
 if f['path']in changes and 'ownerReleaseId'not in f:dst.write_bytes(changes[f['path']])
 else:os.link((B.parent/f.get('ownerReleaseId',OLD)/f['path']).resolve(),dst)
 assert sha(dst.read_bytes())==f['sha256']and dst.stat().st_size==f['sizeBytes']
receipt={'schemaVersion':2,'releaseId':rid,'algorithm':'SHA-256','fileCount':len(files),'totalBytes':sum(f['sizeBytes']for f in files.values()),'referenceCount':len(can['references']),'referencedBytes':sum(f['sizeBytes']for f in can['references'])}
(stage/'deployment-manifest.json').write_text(json.dumps(out,indent=2)+'\n');(stage/'release-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
for name in ['index.html','watch-home-coordinated-successor.js','watch-home-loading-v4.css']:
 original=(B.parents[2]/name).read_bytes();updated=original.replace(OLD.encode(),rid.encode());assert updated.replace(rid.encode(),OLD.encode())==original;(root/name).write_bytes(updated)
report={'baseRelease':OLD,'releaseId':rid,'closureFiles':len(can['localFiles'])+len(can['references']),'changedLocalPaths':sorted(changes),'sourceModuleSHA256':sha((P/'original.js').read_bytes()),'candidateModuleSHA256':sha(changes['assembly-backplate.js']),'sourceReviewSHA256':patch['source_sha256'],'candidateReviewSHA256':sha(changes['assembly-review.js']),'referenceFilesUnchanged':True,'additionalCPUArrayBytesAvoided':79976,'trianglesUnchanged':3068,'scope':'Local immutable candidate only; module/CPU integration reviewed, full viewer/custom brushed shader browser acceptance and publication unverified.','sourceEdits':False,'remoteEdits':False,'mainEdits':False}
(Q/'release-id.txt').write_text(rid);(Q/'BUILD.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
