"""Transport exact already-verified Linux build bytes; never rebuild or relax release hashes."""
from pathlib import Path,PurePosixPath
import json,hashlib,tarfile,gzip,io,os,sys
sha=lambda b:hashlib.sha256(b).hexdigest();PREFIXES=('watch-normal-stream-build/staging/','watch-crown-key-build/staging/');MAX_TOTAL=512*1024*1024;MAX_FILE=32*1024*1024
if sys.argv[1]=='pack':
 out=Path('crown-payload');out.mkdir(exist_ok=False);files=[]
 for prefix in PREFIXES:
  for p in sorted(Path(prefix).rglob('*')):
   assert not p.is_symlink()
   if p.is_file():
    b=p.read_bytes();assert len(b)<=MAX_FILE;files.append({'path':p.as_posix(),'bytes':len(b),'sha256':sha(b)})
 assert len(files)==606 and sum(f['bytes'] for f in files)<=MAX_TOTAL
 metadata={'files':files,'scope':'exact alreadyverified Linux build roots; no source/code execution from payload'};raw=(json.dumps(metadata,indent=2)+'\n').encode();(out/'payload.json').write_bytes(raw)
 with (out/'payload.tar.gz').open('xb') as archive:
  with gzip.GzipFile(filename='',fileobj=archive,mode='wb',mtime=0) as compressed:
   with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.USTAR_FORMAT) as tar:
    for f in files:
     b=Path(f['path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'];info=tarfile.TarInfo(f['path']);info.size=len(b);info.mode=0o644;info.mtime=0;info.uid=info.gid=0;tar.addfile(info,io.BytesIO(b))
 result={'archive_sha256':sha((out/'payload.tar.gz').read_bytes()),'manifest_sha256':sha(raw),'files':len(files)};print(json.dumps(result))
 if os.environ.get('GITHUB_OUTPUT'):
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:
   for k in ['archive_sha256','manifest_sha256']:f.write(k+'='+result[k]+'\n')
elif sys.argv[1]=='unpack':
 source=Path('crown-payload');raw=(source/'payload.json').read_bytes();archive=(source/'payload.tar.gz').read_bytes();assert sha(raw)==os.environ['EXPECTED_MANIFEST_SHA256'];assert sha(archive)==os.environ['EXPECTED_ARCHIVE_SHA256'];metadata=json.loads(raw);files=metadata['files'];assert len(files)==606 and len({f['path'] for f in files})==606;assert sum(f['bytes'] for f in files)<=MAX_TOTAL
 allowed={}
 for f in files:
  p=PurePosixPath(f['path']);assert not p.is_absolute() and '..' not in p.parts and '.' not in p.parts and p.as_posix()==f['path'];assert f['path'].startswith(PREFIXES) and 0<=f['bytes']<=MAX_FILE;allowed[f['path']]=f
 for prefix in PREFIXES:
  assert not Path(prefix).exists(),'refuse overwrite existing staged evidence'
  assert all(not parent.is_symlink() for parent in [Path(prefix),*Path(prefix).parents]),'symlink output parent'
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r|gz') as tar:
  seen=set()
  for member in tar:
   assert member.name not in seen and len(seen)<606;seen.add(member.name)
   assert member.isfile() and member.name in allowed and member.size==allowed[member.name]['bytes'];f=allowed[member.name];b=tar.extractfile(member).read(MAX_FILE+1);assert len(b)==f['bytes'] and sha(b)==f['sha256'];p=Path(member.name);assert all(not parent.is_symlink() for parent in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
   # Existing parent symlinks cannot redirect writes outside declared roots.
   assert all(not parent.is_symlink() for parent in [p,*p.parents])
   with p.open('xb') as out:out.write(b)
  assert seen==set(allowed)
 print('606 exact sealed build-root files transferred; original prepare must recheck canonical release and bootstrap before browser')
else:raise AssertionError('pack or unpack required')
