import pathlib,json,base64,gzip,hashlib,shutil,subprocess,os,re
Q=pathlib.Path('strap-combined-qa');BASE=pathlib.Path(os.environ.get('WATCH_BASE','preview-b/releases/75756356ca7b944a5143c519b75d3cac2f8aa62cfcf40302b249f7eefda85f69'));os.environ['WATCH_BASE']=str(BASE)
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((BASE/'deployment-manifest.json').read_text());assert m['releaseId']=='75756356ca7b944a5143c519b75d3cac2f8aa62cfcf40302b249f7eefda85f69'
# Check every source closure byte before composition and materialize refs only
# into a private encoder source, never mutate the immutable source release.
for f in m['localFiles']+m['references']:
 p=BASE.parent/f['ownerReleaseId']/f['path'] if 'ownerReleaseId'in f else BASE/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes'] and sha(b)==f['sha256'],f['path']
assert sha((BASE/'rebuild/assembly.glb').read_bytes())=='bf9f71e73096eb95a5751054db7ae52dc659fe4be5ebe898657df924f82bc462'
assert sha((BASE/'leather-assets/r14/geometry.bin').read_bytes())=='97377092fcfc6f5a7e934e083f71a1d5e99c9d2007a1b5c3ba38a2b6a6dc61e3'
for name,b in json.loads(gzip.decompress(base64.b64decode((Q/'inputs.b64').read_bytes()))).items():
 p=Q/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(base64.b64decode(b))
# Encoder vendor files remain private; runtime shared references keep ownership.
encoder=Q/'encoder-source';shutil.copytree(BASE/'vendor',encoder/'vendor',dirs_exist_ok=True) if(BASE/'vendor').exists()else None
for f in m['references']:
 if f['path'].startswith('vendor/meshopt/'):
  d=encoder/f['path'];d.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(BASE.parent/f['ownerReleaseId']/f['path'],d)
subprocess.run(['python',str(Q/'apply-leather.py')],check=True)
subprocess.run(['python',str(Q/'keeper/compose.py'),str(BASE/'rebuild/assembly.glb'),str(Q/'work/rebuild/assembly.glb')],check=True)
env=dict(os.environ,WATCH_BASE=str(encoder));subprocess.run(['node',str(Q/'encode.mjs')],env=env,check=True)
leather=json.loads((Q/'leather-export-report.json').read_text());assert leather['candidateSHA256']=='f7e7a7638b7ac58a3d3f568cbbcc0baa989d840d9b989e10b0c72485298ed0d5'
assembly=json.loads((Q/'work/rebuild/assembly.json').read_text());assert assembly['candidateSha256']=='e471d63c55ce81bbc82257602341ae0ce98d96f98a7d078baa1aa4ca72d2d258'
encoding=json.loads((Q/'encoding-report.json').read_text());files={f['path']:dict(f)for f in m['localFiles']};out=Q/'release';out.mkdir(exist_ok=True)
def put(n,b):
 p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);files[n]={'path':n,'sizeBytes':len(b),'sha256':sha(b)}
changed=['leather-assets/r14/leather.gltf','leather-assets/r14/geometry.bin','rebuild/assembly.glb','optimized-assets/rebuild__assembly.meshopt.glb.gz']
for n in changed:put(n,(Q/'work'/n).read_bytes())
s=(BASE/'assembly-leather-authoring-identity.js').read_text();identity=json.loads(s[s.index('Object.freeze(')+14:s.rfind(')')]);s=(Q/'candidate-identity.js').read_text();candidate=json.loads(s[s.index('Object.freeze(')+14:s.rfind(')')]);
for k in ['expectedGeometry','meshes','topologyCandidate']:identity[k]=candidate[k]
identity['status']='QA-only structured puncture charts plus canonical keeper attributes; not promoted';identity['hardware'].update(expectedSha256=assembly['candidateSha256'],expectedBytes=assembly['candidateBytes'],verificationScope='Canonical assembly after keeper rigid reuse; sampled keeper shape tolerance recorded separately')
put('assembly-leather-authoring-identity.js',('export const AUTHORED_LEATHER_IDENTITY=Object.freeze('+json.dumps(identity,indent=2)+');\n').encode())
s=(BASE/'assembly-optimized-loading.js').read_text();s,n=re.subn(r'const GZIP_DECODED_BYTES=\d+;',f"const GZIP_DECODED_BYTES={encoding['meshoptBytes']};",s);assert n==1;put('assembly-optimized-loading.js',s.encode())
rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']}for f in sorted(files.values(),key=lambda f:f['path'])if '/'not in f['path']and pathlib.Path(f['path']).suffix in ['.html','.js','.css']]
rev={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(rf,separators=(',',':')).encode()),'files':rf}
for n,b in [('quality-study/viewer-revision.json',json.dumps(rev,indent=2)+'\n'),('quality-study/viewer-revision.js','export default '+json.dumps(rev,separators=(',',':'))+';\n')]:put(n,b.encode())
can={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':m['references']};rid=sha(json.dumps(can,separators=(',',':')).encode());manifest={**can,'releaseId':rid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']};(out/'deployment-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'release-receipt.json').write_text(json.dumps({'schemaVersion':2,'releaseId':rid,'algorithm':'SHA-256','fileCount':len(files),'totalBytes':sum(f['sizeBytes']for f in files.values()),'referenceCount':len(m['references']),'referencedBytes':sum(f['sizeBytes']for f in m['references'])},indent=2)+'\n')
stage=BASE.parent/rid
for n in [f['path']for f in can['localFiles']]+['deployment-manifest.json','release-receipt.json']:
 s=out/n if(out/n).exists()else BASE/n;d=stage/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,d)
for f in can['localFiles']:assert sha((stage/f['path']).read_bytes())==f['sha256'],f['path']
(Q/'release-id.txt').write_text(rid);(Q/'build-report.json').write_text(json.dumps({'baseRelease':m['releaseId'],'releaseId':rid,'sourceGuardPassed':True,'sourceClosureFiles':len(m['localFiles'])+len(m['references']),'leather':leather,'keeper':assembly,'encoding':encoding,'productionChanged':False},indent=2));print('QA release',rid)
