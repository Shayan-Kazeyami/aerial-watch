from pathlib import Path
import json,hashlib,sys
root=Path(sys.argv[1]).resolve();s=json.loads((Path(__file__).parent/'guards.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=json.loads(json.dumps(s['baselineFirstPartyFiles']));w=next(x for x in s['payload'] if x['path']=='assembly-winding.js');r=next(x for x in expected if x['path']==w['path']);r.update(bytes=w['bytes'],sha256=w['afterSha256'])
actual=[{'path':x['path'],'bytes':(root/x['path']).stat().st_size,'sha256':sha(root/x['path'])}for x in expected]
assert actual==expected
h=hashlib.sha256(json.dumps(actual,separators=(',',':')).encode()).hexdigest();assert h==s['expectedAfterSourceDigest']
rev=json.loads((root/'quality-study/viewer-revision.json').read_text());assert rev['digest']==h and rev['files']==actual
for name,digest in s['protected'].items():
 if not name.startswith('quality-study/viewer-revision.'):assert sha(root/name)==digest,name
manifest=json.loads((root/'deployment-manifest.json').read_text());assert len({x['path']for x in manifest['files']})==len(manifest['files'])
for x in manifest['files']:assert sha(root/x['path'])==x['sha256'] and (root/x['path']).stat().st_size==x['sizeBytes'],x['path']
assert not (root/'assembly-fork-contact-detour.js').exists()
print(json.dumps({'status':'verified','actualDigest':h,'firstPartyFiles':len(actual),'manifestFiles':len(manifest['files']),'manifestSha256':sha(root/'deployment-manifest.json'),'protectedUnchanged':True,'scope':'independent actual source verification, not rendered acceptance'},indent=2))
