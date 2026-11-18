import pathlib,json,hashlib,struct,gzip,urllib.parse,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=pathlib.Path(__file__).resolve().parent
BASE='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6';RID=(OUT/'release-id.txt').read_text().strip();releases=ROOT/'preview-b/releases';base=releases/BASE;new=releases/RID
sha=lambda b:hashlib.sha256(b).hexdigest();compact=lambda x:json.dumps(x,separators=(',',':')).encode()
bm=json.loads((base/'deployment-manifest.json').read_text());m=json.loads((new/'deployment-manifest.json').read_text());assert sha(compact({k:m[k] for k in ['schemaVersion','localFiles','references']}))==RID==m['releaseId']
assert m['references']==bm['references'];assert m['referenceLayout']==bm['referenceLayout'];assert len(m['localFiles'])==len(bm['localFiles'])==181
paths=set();changes=[]
for f in m['localFiles']+m['references']:
 p=(releases/f['ownerReleaseId'] if 'ownerReleaseId'in f else new)/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes'] and sha(b)==f['sha256'],str(p);paths.add(p.resolve())
 if 'ownerReleaseId'not in f and b!=(base/f['path']).read_bytes():changes.append(f['path'])
assert sorted(changes)==['assembly-mechanism-batch.js','quality-study/viewer-revision.js','quality-study/viewer-revision.json'],changes
rev=json.loads((new/'quality-study/viewer-revision.json').read_text());assert rev['digest']==sha(compact(rev['files']))
expected=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']} for f in m['localFiles'] if '/'not in f['path'] and pathlib.Path(f['path']).suffix in ['.html','.css','.js']]
assert rev['files']==expected;assert (new/'quality-study/viewer-revision.js').read_text()=='export default '+compact(rev).decode()+';\n'
physical=0;gltf_count=0;compressed=0;virtual={}
for f in m['localFiles']+m['references']:
 name=f['path'];p=(releases/f['ownerReleaseId'] if 'ownerReleaseId'in f else new)/name
 if not name.endswith(('.gltf','.glb','.glb.gz')):continue
 raw=p.read_bytes()
 if name.endswith('.gz'):raw=gzip.decompress(raw);compressed+=1
 else:gltf_count+=1
 if name.endswith('.gltf'):d=json.loads(raw)
 else:
  magic,ver,total=struct.unpack_from('<III',raw);assert magic==0x46546c67 and ver==2 and total==len(raw)
  length,typ=struct.unpack_from('<II',raw,12);assert typ==0x4e4f534a;d=json.loads(raw[20:20+length])
 for kind in ['buffers','images']:
  for item in d.get(kind,[]):
   uri=item.get('uri');
   if not uri or uri.startswith('data:'):continue
   assert not urllib.parse.urlsplit(uri).scheme and not uri.startswith('/'),uri
   target=(p.parent/urllib.parse.unquote(uri)).resolve()
   if target.is_file():assert target in paths,str(target);physical+=1
   else:
    parts=sorted(target.parent.glob(target.name+'.part*'),key=lambda q:int(q.suffix.replace('.part','')));assert parts
    assert all(q.resolve()in paths for q in parts);blob=b''.join(q.read_bytes() for q in parts)
    logical=str(pathlib.PurePosixPath(name).parent/uri);virtual[logical]={'path':logical,'bytes':len(blob),'sha256':sha(blob)}
closure={'gltfCount':gltf_count,'realReferences':physical,'virtualTextures':list(virtual.values())};assert closure==m['assetClosure']==bm['assetClosure'],closure
for f in m['localFiles']:
 if f['path'].endswith('.js'):subprocess.run(['node','--check',str(new/f['path'])],check=True,capture_output=True)
receipt=json.loads((new/'release-receipt.json').read_text());assert receipt['releaseId']==RID and receipt['fileCount']==181 and receipt['referenceCount']==116 and receipt['totalBytes']==sum(f['sizeBytes']for f in m['localFiles']) and receipt['referencedBytes']==sum(f['sizeBytes']for f in m['references'])
for name in ['index.html','watch-home-caseback-e79b2236.js','deployment-manifest.json']:
 assert (ROOT/name).read_bytes()==subprocess.check_output(['git','-C',str(ROOT),'show','b84a51ec:'+name]),name
report={'releaseId':RID,'bound_files_verified':len(paths),'local_code_and_metadata_changes':changes,'viewer_revision_digest':rev['digest'],'assetClosure':closure,'additional_gzip_glb_verified':compressed,'public_loader_and_root_manifest_unchanged':True,'source_assets_changed':False,'physical_gpu_tested':False}
(OUT/'VERIFICATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
