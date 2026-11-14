"""Build-only additive proposal atop pinned privacy/encoding feature; no source/ref/deploy writes."""
from pathlib import Path
import os,json,hashlib,shutil
Q=Path(__file__).resolve().parent;OLD='e157f07921363a07a67dffd367bbc5bec2392691313632a4169d951974abb5a2';B=Path(os.environ.get('SHELL_HOME_BASE','watch-import-readiness-build/staging/preview-b/releases/'+OLD));sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(B/'deployment-manifest.json').read_bytes();assert sha(raw)=='adbb73bccc923c7254577893817ef4e4699724dbcdaad02904f779c8530b1a8d';m=json.loads(raw);can={k:m[k] for k in ['schemaVersion','localFiles','references']};assert sha(json.dumps(can,separators=(',',':')).encode())==OLD
for f in m['localFiles']+m['references']:
 src=B.parent/f.get('ownerReleaseId',OLD)/f['path'];data=src.read_bytes();assert len(data)==f['sizeBytes'] and sha(data)==f['sha256'],str(src)
assert sha((B/'assembly-component-labels.js').read_bytes())=='1c811a0b185bdbd8e13f99c6aa44d088015b94e28b1fd10c0c99f6d0303f8fdb'
assert sha((B/'atelier-error-details.js').read_bytes())=='e28bdd29a032d5dad5d2a501b08c02536a386b22abb04fc7bc2796b9a843de58'
assert sha((B/'assembly-review.js').read_bytes())=='f02f88014eedd44769f5dce54c784b07d391aae6523da1d7bd2582cdfaa8f23f'
assert sha((B/'assembly-story.js').read_bytes())=='c501fdfa2071d9c760cc2001bdaaac7b53299241eca138fbc6eb60551ff3708c'
patch=json.loads((Q/'patch.json').read_text());source=(B/'atelier-preview.js').read_text();assert source.count(patch['old'])==1;candidate=source.replace(patch['old'],patch['new'],1).encode();assert sha(candidate)=='5699028e95b4a300ad149cae0473c28c40be62536460925e02e173a937dce820'
changes={'atelier-preview.js':candidate};files={f['path']:dict(f) for f in m['localFiles']}
def put(n,b):changes[n]=b;files[n]={'path':n,'sizeBytes':len(b),'sha256':sha(b)}
put('atelier-preview.js',candidate)
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
entryPins={'index.html': 'f9fe4542dc5d882d025dfd281cd50fe9b45ae5f7481b101c073b6bd1ddabfd0e', 'watch-home-coordinated-successor.js': '6249b8bd9e16cf2c557aa347828d4814b885988333f0dce8cce444f23760eec8', 'watch-home-loading-v4.css': '0db4e30c1e54f824152441bf5f566664df84ebf61d8996b8a78f9c4e271c5ee1'}
for name in ['index.html','watch-home-coordinated-successor.js','watch-home-loading-v4.css']:
 data=(entry/name).read_bytes();assert sha(data)==entryPins[name];new=data.replace(OLD.encode(),rid.encode()) if name!='watch-home-loading-v4.css' else data
 if name=='watch-home-coordinated-successor.js':assert data.count(OLD.encode())==1
 assert new.replace(rid.encode(),OLD.encode())==data
 (root/name).write_bytes(new)

(Q/'release-id.txt').write_text(rid)
(Q/'build-report.json').write_text(json.dumps({'baseRelease':'e157f07921363a07a67dffd367bbc5bec2392691313632a4169d951974abb5a2','releaseId':rid,'closureFiles':len(can['localFiles'])+len(can['references']),'changedPaths':sorted(changes),'scope':'isolated shell Home event ownership guard; no browser/deployment approval'},indent=2)+'\n')
print(rid)
