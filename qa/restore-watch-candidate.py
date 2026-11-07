"""Restore already-authorized immutable project blobs for an isolated, read-only QA run."""
import base64, hashlib, io, json, os, pathlib, tarfile, time, urllib.request
REPO='Shayan-Kazeyami/aerial-watch'
PARTS=['d9a00186e205f1cb8925a8b33af76e3eba25bc9c','6d43bc7acb7a3d47b40bb9d50568436bb3234df0','42ec55237ceafc293ffa72312e10e217aa892e1e','e8910935d682b43f8b0846c9fca709795bb362f5','b4381e180811a42e4656a691dc0f3e3d394f85fc','18dde5e2d4d1ec69a46c265218f7e37de92cbfc8','943f3b56fd3fef960593cd8bf64243ae6ea857a2']
SOURCE='58dff3d53dea777cd4320a9ebb96bfd35e5cae71eba0542983bc27c67c2163be'
CAP_BLOB='ca58dc317c9fde0d21c2be1b3f71fc11bfbcdcb3'
CAP='a67fd85abfb9e2fb992a95bd85a82eefe530e50d2b2fbd7d1feecdf0b35f8a0b'
root=pathlib.Path('candidate');root.mkdir(exist_ok=False)
def sha(b): return hashlib.sha256(b).hexdigest()
def fetch(blob):
 req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/git/blobs/{blob}',headers={'Accept':'application/vnd.github.raw+json','Authorization':'Bearer '+os.environ['GH_TOKEN'],'X-GitHub-Api-Version':'2022-11-28','User-Agent':'watch-readonly-qa'})
 for attempt in range(3):
  try:
   with urllib.request.urlopen(req,timeout=120) as r:
    data=r.read();typ=r.headers.get('Content-Type','')
   if 'application/json' in typ:
    value=json.loads(data);assert value['encoding']=='base64';data=base64.b64decode(value['content'])
   assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'Git blob integrity failure'
   return data
  except Exception:
   if attempt==2:raise
   time.sleep(2**attempt)
def unpack(data,expected):
 assert sha(data)==expected,'Bundle integrity failure'
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz')as t:
  for m in t.getmembers():
   p=pathlib.PurePosixPath(m.name)
   assert m.isfile() and not p.is_absolute() and '..' not in p.parts,'Unsafe archive member'
   out=root.joinpath(*p.parts);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(t.extractfile(m).read())
unpack(b''.join(fetch(x)for x in PARTS),SOURCE)
manifest=json.loads((root/'exact-source-identities.json').read_text())
restored=0
for row in manifest:
 p=pathlib.PurePosixPath(row['path']);assert not p.is_absolute() and '..' not in p.parts
 out=root.joinpath(*p.parts)
 if not out.exists():
  out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(fetch(row['gitBlob']));restored+=1
 assert out.stat().st_size==row['bytes'] and sha(out.read_bytes())==row['sha256'],'Source identity mismatch'
print(f'Exact source closure verified: {len(manifest)} files; restored {restored} binary assets.')
unpack(fetch(CAP_BLOB),CAP)
print('Frozen cap v2 bundle verified and applied. No repository or deployment writes.')
