import pathlib,json,hashlib
R=pathlib.Path('crown-unified-qa');out=R/'release';out.mkdir(exist_ok=True)
base=pathlib.Path('layer-focus-qa/recovery-21474059/preview-b/releases/214740598c3327efb618f559ce587911d3893bd97a060a53172277877480a8b2');m=json.loads((base/'deployment-manifest.json').read_text());files={f['path']:dict(f) for f in m['localFiles']};sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
 p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);files[n]={'path':n,'sizeBytes':len(b),'sha256':sha(b)}
for name in ['assembly-crown-hotspot.js','assembly-review.js']:put(name,(R/name).read_bytes())
rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']} for f in sorted(files.values(),key=lambda f:f['path']) if '/'not in f['path']and pathlib.Path(f['path']).suffix in ['.html','.js','.css']]
rev={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(rf,separators=(',',':')).encode()),'files':rf}
for n,b in [('quality-study/viewer-revision.json',json.dumps(rev,indent=2)+'\n'),('quality-study/viewer-revision.js','export default '+json.dumps(rev,separators=(',',':'))+';\n')]:put(n,b.encode())
can={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':m['references']};rid=sha(json.dumps(can,separators=(',',':')).encode())
(out/'deployment-manifest.json').write_text(json.dumps({**can,'releaseId':rid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']},indent=2)+'\n')
(out/'release-receipt.json').write_text(json.dumps({'schemaVersion':2,'releaseId':rid,'algorithm':'SHA-256','canonicalization':'SHA-256 of UTF-8 JSON.stringify({schemaVersion:2,localFiles,references}); each array sorted lexicographically by path; field order as shown in manifest','fileCount':len(files),'totalBytes':sum(f['sizeBytes']for f in files.values()),'referenceCount':len(m['references']),'referencedBytes':sum(f['sizeBytes']for f in m['references'])},indent=2)+'\n')
for f in can['localFiles']+can['references']:
 p=(base.parent/f['ownerReleaseId']/f['path'])if 'ownerReleaseId'in f else (out/f['path']if(out/f['path']).exists()else base/f['path']);b=p.read_bytes();assert len(b)==f['sizeBytes']and sha(b)==f['sha256'],f['path']
(R/'release-id.txt').write_text(rid);print(rid)
