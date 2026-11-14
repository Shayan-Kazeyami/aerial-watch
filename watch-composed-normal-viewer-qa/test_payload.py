"""Finite local payload transport checks, requires previously packed exact606file payload."""
from pathlib import Path
import os,tempfile,json,hashlib,subprocess
Q=Path(__file__).resolve().parent;source=Path('composed-payload').resolve();script=Q/'payload.py';sha=lambda b:hashlib.sha256(b).hexdigest();raw=(source/'payload.json').read_bytes();archive=(source/'payload.tar.gz').read_bytes();env={**os.environ,'EXPECTED_ARCHIVE_SHA256':sha(archive),'EXPECTED_MANIFEST_SHA256':sha(raw)};checks=[]
with tempfile.TemporaryDirectory() as d:
 root=Path(d);(root/'composed-payload').mkdir()
 for n in ['payload.tar.gz','payload.json']:(root/'composed-payload'/n).symlink_to(source/n)
 def run(e=env):return subprocess.run(['python',str(script),'unpack'],cwd=root,env=e,capture_output=True,text=True,timeout=60)
 r=run();assert r.returncode==0,r.stderr
 actual={p.as_posix():sha(p.read_bytes()) for prefix in ['watch-error-redaction-build/staging','watch-normal-stream-build/staging'] for p in (root/prefix).rglob('*') if p.is_file()};assert len(actual)==606
 for f in json.loads(raw)['files']:assert sha((root/f['path']).read_bytes())==f['sha256']
 checks.append('606 exact files verified after streaming unpack')
 r=run();assert r.returncode!=0 and 'refuse overwrite' in r.stderr;checks.append('overwrite rejected')
 r=run({**env,'EXPECTED_ARCHIVE_SHA256':'0'*64});assert r.returncode!=0;checks.append('wrong archive digest rejected')
 r=run({**env,'EXPECTED_MANIFEST_SHA256':'0'*64});assert r.returncode!=0;checks.append('wrong manifest digest rejected')
 (root/'composed-payload/payload.json').unlink();bad=json.loads(raw);bad['files'][0]['path']='../escape';b=json.dumps(bad).encode();(root/'composed-payload/payload.json').write_bytes(b)
 r=run({**env,'EXPECTED_MANIFEST_SHA256':sha(b)});assert r.returncode!=0;assert not (root.parent/'escape').exists();checks.append('traversal metadata rejected')
report={'passed':True,'noBrowser':True,'checks':checks,'helperSHA256':sha(script.read_bytes())};(Q/'PAYLOAD_LOCAL_TESTS_V2.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
