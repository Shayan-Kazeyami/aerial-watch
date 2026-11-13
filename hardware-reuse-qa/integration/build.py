import pathlib,json,hashlib,shutil,os
Q=pathlib.Path('hardware-reuse-qa/integration');BID='09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29';BASE=pathlib.Path(os.environ.get('WATCH_BASE',f'preview-b/releases/{BID}'));sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((BASE/'deployment-manifest.json').read_text());assert m['releaseId']==BID
for f in m['localFiles']+m['references']:
 p=BASE.parent/f['ownerReleaseId']/f['path']if 'ownerReleaseId'in f else BASE/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes']and sha(b)==f['sha256'],str(p)
assert sha((BASE/'assembly-mechanism-batch.js').read_bytes())=='af6343619941debdb5bfc973f5132fc544595903fd4532f9d2aaa7252da21c67'
files={f['path']:dict(f)for f in m['localFiles']};out=Q/'changes';out.mkdir(exist_ok=True)
def put(n,b):
 p=out/n;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(b);files[n]={'path':n,'sizeBytes':len(b),'sha256':sha(b)}
source=(Q/'accepted-batch.js').read_bytes();assert sha(source)=='038af9b7be897c1bcd367bcf5afd93cfc5ef68c42a57908c772061fa93bc108a'
assert source.count(b"'/hardware-reuse-qa/canonical-data.js'")==1
module=source.replace(b"'/hardware-reuse-qa/canonical-data.js'",b"'./assembly-hardware-canonical-data.js'")
put('assembly-mechanism-batch.js',module);put('assembly-hardware-canonical-data.js',(Q/'canonical-data.js').read_bytes())
assert b'/hardware-reuse-qa/'not in module
rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']}for f in sorted(files.values(),key=lambda f:f['path'])if '/'not in f['path']and pathlib.Path(f['path']).suffix in ['.html','.js','.css']]
rev={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(rf,separators=(',',':')).encode()),'files':rf}
for n,b in [('quality-study/viewer-revision.json',json.dumps(rev,indent=2)+'\n'),('quality-study/viewer-revision.js','export default '+json.dumps(rev,separators=(',',':'))+';\n')]:put(n,b.encode())
can={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':m['references']};rid=sha(json.dumps(can,separators=(',',':')).encode());manifest={**can,'releaseId':rid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']};(out/'deployment-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'release-receipt.json').write_text(json.dumps({'schemaVersion':2,'releaseId':rid,'algorithm':'SHA-256','fileCount':len(files),'totalBytes':sum(f['sizeBytes']for f in files.values()),'referenceCount':len(m['references']),'referencedBytes':sum(f['sizeBytes']for f in m['references'])},indent=2)+'\n')
stage=BASE.parent/rid
for n in [f['path']for f in can['localFiles']]+['deployment-manifest.json','release-receipt.json']:
 s=out/n if(out/n).exists()else BASE/n;d=stage/n;d.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(s,d)
for f in can['localFiles']:
 p=stage/f['path'];assert p.stat().st_size==f['sizeBytes']and sha(p.read_bytes())==f['sha256'],f['path']
assert(stage/'assembly-hardware-canonical-data.js').is_file();assert sha((stage/'rebuild/assembly.glb').read_bytes())=='e471d63c55ce81bbc82257602341ae0ce98d96f98a7d078baa1aa4ca72d2d258'
(Q/'release-id.txt').write_text(rid);(Q/'build-report.json').write_text(json.dumps({'baseMain':'f3c23832f6cb8af3463248355dd7f69ab5e7b6bf','baseRelease':BID,'releaseId':rid,'sourceClosureVerified':True,'releaseClosureVerified':True,'sourceClosureFiles':len(m['localFiles'])+len(m['references']),'localFileCount':len(files),'referenceCount':len(m['references']),'sourceAssemblyUnchanged':True,'releaseRelativeCanonicalImport':True,'acceptedModuleSHA256':sha(source),'productionModuleSHA256':sha(module),'productionChanged':False},indent=2));print(rid)
