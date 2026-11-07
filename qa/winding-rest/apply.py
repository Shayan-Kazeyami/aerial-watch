from pathlib import Path
import json,hashlib,os,subprocess,sys
r=Path(sys.argv[1]).resolve();h=Path(__file__).resolve().parent
assert r.name=='candidate' and not(r/'.git').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(r/'assembly-winding.js')=='64229191508478fe868f8a5387f0d8414ddf6e87e14096d285646c6eb323683c'
assert sha(r/'assembly-review.js')=='489a16d2349ccb2691f3d1724cf4a6b1e65f9ea8638902872e2903f3f2b269a9'
assert sha(r/'deployment-manifest.json')=='ea0c1718b2f9383e7e628dcde22973082bb92d54335f7ef5f655b297eb922b8a'
def put(p,b):
 assert not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.rest-tmp');assert not t.exists();t.write_bytes(b);os.replace(t,p)
for name in ['tests/winding-rest-continuity.test.mjs','tests/fixtures/winding-before-rest.mjs']:
 assert not(r/name).exists();put(r/name,(h/name).read_bytes())
put(r/'assembly-winding.js',(h/'assembly-winding.js').read_bytes())
assert sha(r/'assembly-winding.js')=='6b98fac61688c7c4900b1e1ad80685c157fa286a0d86667a6ed832b5f9d43415'
m=json.loads((r/'deployment-manifest.json').read_text());rows={x['path']:x for x in m['files']};rows['assembly-winding.js'].update(sha256=sha(r/'assembly-winding.js'),sizeBytes=(r/'assembly-winding.js').stat().st_size)
put(r/'deployment-manifest.json',(json.dumps(m,indent=2)+'\n').encode())
for name in ['quality-study/viewer-revision.json','quality-study/viewer-revision.js']:put(r/name,(r/name).read_bytes())
subprocess.run(['node','tools/capture-provenance.mjs'],cwd=r,check=True)
for name in ['quality-study/viewer-revision.json','quality-study/viewer-revision.js']:rows[name].update(sha256=sha(r/name),sizeBytes=(r/name).stat().st_size)
put(r/'deployment-manifest.json',(json.dumps(m,indent=2)+'\n').encode())
print('REST_CANDIDATE_SOURCE',json.loads((r/'quality-study/viewer-revision.json').read_text())['digest'])
