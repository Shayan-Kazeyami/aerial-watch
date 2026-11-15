from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
m=json.loads((p/'MANIFEST.json').read_text())
for f in m['files']:
    q=p/f['path'];b=q.read_bytes()
    assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],f['path']
    assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==f['gitBlobSHA1'],f['path']
actual={str(q.relative_to(p))for q in p.rglob('*')if q.is_file()}
assert actual=={f['path']for f in m['files']}|{'MANIFEST.json'}
assert not any(x in q.parts for q in p.rglob('*')for x in('.git','.github'))
print('Verified source-only backup:',len(m['files']),'files; not deployment or acceptance.')
