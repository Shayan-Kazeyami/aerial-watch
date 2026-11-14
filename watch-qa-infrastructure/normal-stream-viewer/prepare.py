from pathlib import Path
import os,json,hashlib
Q=Path(__file__).resolve().parent;B=Path(os.environ['WATCH_BASE']);rid=B.name
assert rid=='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
sha=lambda b:hashlib.sha256(b).hexdigest();manifest=(B/'deployment-manifest.json').read_bytes();assert sha(manifest)=='3324ba95a8c2c08125637a34e8bb757ab4bab77754cffe84221a07327a9d2fa2'
m=json.loads(manifest);arm=os.environ['QA_ARM'];assert arm in ['baseline','candidate'];out=Q/('prepared-v2-'+arm);out.mkdir(exist_ok=False)
files=m['localFiles']+m['references'];assert len(files)==297
for f in files:
 owner=f.get('ownerReleaseId',rid);data=(B.parent/owner/f['path']).read_bytes();assert len(data)==f['sizeBytes'] and sha(data)==f['sha256'];p=out/'preview-b/releases'/owner/f['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
S=out/'preview-b/releases'/rid;original=(S/'assembly-review.js').read_bytes();assert sha(original)=='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee';hook=(Q/'snapshot-hook.js').read_bytes();(S/'assembly-review.js').write_bytes(original+b'\n'+hook)
if arm=='candidate':
 candidate=(Q.parent/'normal-stream-browser/candidate.mjs').read_bytes();assert sha(candidate)=='89ff6e1bc368731c77499830cda4a4682e9798c234fcb47df0b96a3d579d62d2';(S/'assembly-fetch-progressive-normal.js').write_bytes(candidate)
report={'arm':arm,'manifestFiles':len(files),'originalRuntimePrefixVerified':True,'runtimeHookSHA256':sha(hook),'fetchSHA256':sha((S/'assembly-fetch-progressive-normal.js').read_bytes()),'htmlUnchanged':True,'qaCopyNotImmutableRelease':True,'sealedSourcesUntouched':True};(Q/('PREPARED-'+arm+'.json')).write_text(json.dumps(report,indent=2));print(report)
