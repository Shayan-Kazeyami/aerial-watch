import pathlib,json,hashlib,shutil,subprocess,os,re,sys
Q=pathlib.Path('movement-retopo-qa/current-pack'); source=pathlib.Path('preview-b/releases');rid='09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29';BASE=source/rid;m=json.loads((BASE/'deployment-manifest.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
for f in m['localFiles']+m['references']:
 p=source/f.get('ownerReleaseId',rid)/f['path'];assert sha(p.read_bytes())==f['sha256'],p
encoder=pathlib.Path('strap-combined-qa/encoder-source')
for f in m['references']:
 if f['path'].startswith('vendor/meshopt/'):
  d=encoder/f['path'];d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/f['ownerReleaseId']/f['path'],d)
subprocess.run(['python3','movement-retopo-qa/compose-current.py',str(BASE/'rebuild/assembly.glb'),str(Q/'assembly.glb')],check=True)
s=pathlib.Path('movement-retopo-qa/serialized-current/reorder.mjs').read_text().replace("const dir='movement-retopo-qa/serialized-current'","const dir='movement-retopo-qa/current-pack'").replace("'../../strap-combined-qa/", "'../../strap-combined-qa/")
(Q/'reorder.mjs').write_text(s);subprocess.run(['node',str(Q/'reorder.mjs')],check=True)
s=pathlib.Path('movement-retopo-qa/serialized-current/encode.mjs').read_text().replace('movement-retopo-qa/serialized-current','movement-retopo-qa/current-pack/fetch');(Q/'fetch/encode.mjs').write_text(s);subprocess.run(['node',str(Q/'fetch/encode.mjs')],env={**os.environ,'WATCH_BASE':str(pathlib.Path('strap-combined-qa/encoder-source').resolve())},check=True)
files={f['path']:dict(f)for f in m['localFiles']};out=Q/'release';out.mkdir(exist_ok=True)
def put(n,b):
 p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);files[n]={'path':n,'sizeBytes':len(b),'sha256':sha(b)}
put('rebuild/assembly.glb',(Q/'fetch/assembly.glb').read_bytes());put('optimized-assets/rebuild__assembly.meshopt.glb.gz',(Q/'fetch/optimized-assets/rebuild__assembly.meshopt.glb.gz').read_bytes());e=json.loads((Q/'fetch/encoding-report.json').read_text())
s=(BASE/'assembly-leather-authoring-identity.js').read_text();identity=json.loads(s[s.index('Object.freeze(')+14:s.rfind(')')]);identity['hardware'].update(expectedSha256=e['rawSHA256'],expectedBytes=e['rawBytes'],verificationScope='Accepted strap keeper assembly plus structured wheel97 candidate; no unrelated changes');identity['status']='QA only: wheel97 contour structure; not promoted';put('assembly-leather-authoring-identity.js',('export const AUTHORED_LEATHER_IDENTITY=Object.freeze('+json.dumps(identity,indent=2)+');\n').encode())
s=(BASE/'assembly-optimized-loading.js').read_text();s,n=re.subn(r'const GZIP_DECODED_BYTES=\d+;',f"const GZIP_DECODED_BYTES={e['meshoptBytes']};",s);assert n==1;put('assembly-optimized-loading.js',s.encode())
# Preserve the authoritative native tip-phase under rendering-only retopology.
# This scalar is from all252 distinct native near-tip angles, with the unchanged
# source97 pivot. Reaveraging a reduced tessellation changes calibrated contacts.
s=(BASE/'assembly-motion.js').read_text();needle="const phase=Math.atan2(angles.reduce((sum,a)=>sum+Math.sin(teeth*a),0),angles.reduce((sum,a)=>sum+Math.cos(teeth*a),0))/teeth;";assert s.count(needle)==1
s=s.replace(needle,"// Native source97 tooth phase is authoritative across render retopology (252 original tip-angle samples).\n    const phase=index===97?0.025733054209403312:Math.atan2(angles.reduce((sum,a)=>sum+Math.sin(teeth*a),0),angles.reduce((sum,a)=>sum+Math.cos(teeth*a),0))/teeth;")
put('assembly-motion.js',s.encode())
rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']}for f in sorted(files.values(),key=lambda f:f['path'])if '/'not in f['path']and pathlib.Path(f['path']).suffix in ['.html','.js','.css']];rev={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(rf,separators=(',',':')).encode()),'files':rf}
for n,b in [('quality-study/viewer-revision.json',json.dumps(rev,indent=2)+'\n'),('quality-study/viewer-revision.js','export default '+json.dumps(rev,separators=(',',':'))+';\n')]:put(n,b.encode())
can={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':m['references']};newid=sha(json.dumps(can,separators=(',',':')).encode());manifest={**can,'releaseId':newid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']};(out/'deployment-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'release-receipt.json').write_text(json.dumps({'schemaVersion':2,'releaseId':newid,'algorithm':'SHA-256','fileCount':len(files),'totalBytes':sum(f['sizeBytes']for f in files.values()),'referenceCount':len(m['references']),'referencedBytes':sum(f['sizeBytes']for f in m['references'])},indent=2)+'\n')
serve=Q/'serve/preview-b/releases';serve.mkdir(parents=True,exist_ok=True)
for p in source.iterdir():
 if p.is_dir() and not(serve/p.name).exists():(serve/p.name).symlink_to(p.resolve(),target_is_directory=True)
stage=serve/newid
for n in [f['path']for f in can['localFiles']]+['deployment-manifest.json','release-receipt.json']:
 s=out/n if(out/n).exists()else BASE/n;d=stage/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,d)
for f in can['localFiles']:assert sha((stage/f['path']).read_bytes())==f['sha256']
(Q/'release-id.txt').write_text(newid);(Q/'build-report.json').write_text(json.dumps({'sourceRelease':rid,'candidateRelease':newid,'sourceHead':'f3c23832f6cb8af3463248355dd7f69ab5e7b6bf','encoding':e,'productionChanged':False},indent=2));print('LOCAL CANDIDATE',newid)
