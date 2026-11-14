from pathlib import Path
import hashlib,json,shutil,os
Q=Path(__file__).resolve().parent; ROOT=Q.parents[1]; B=Path(os.environ.get('WATCH_BASE',str(ROOT/'strap-combined-qa/resume/recovery-09e3e0ae/preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'))); S=Q/'fixture';sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((B/'deployment-manifest.json').read_text());assert sha((B/'deployment-manifest.json').read_bytes())=='3324ba95a8c2c08125637a34e8bb757ab4bab77754cffe84221a07327a9d2fa2'
records=[]
def put(name,data):
 p=S/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==data,'immutable fixture drift '+name
 else:p.write_bytes(data)
 records.append(dict(path=name,sha256=sha(data),bytes=len(data)))
for name,pin in [('assembly-design.js','32b157ec3a9718b48f07f6eb9a4cfc4e9be3883a89f8cf0c1c68b9ba2c3aaa97'),('vendor/three.module.js','104f56145899722094556490d787aae0617cc2fc3382f31df02d724ea1aee341'),('vendor/three.core.js','613e370f76638fdef83926642bf256dc9615684922de1ce1f63a8583e5d78578')]:
 f=next(x for x in m['localFiles']+m['references'] if x['path']==name);p=B.parent/f['ownerReleaseId']/name if 'ownerReleaseId'in f else B/name;b=p.read_bytes();assert sha(b)==pin==f['sha256'];put(name,b)
src=(Q/'inputs/assembly-design.mjs').read_bytes();assert src.replace(b"'./three.mjs'",b"'./vendor/three.module.js'")==(S/'assembly-design.js').read_bytes()
c=(Q/'inputs/candidate-design.mjs').read_bytes();assert sha(c)=='8b7034cb6155a80440e4e804d65fa78b650a52ea6d63540d353094f7847e1ec8';assert c.count(b"'./three.mjs'")==1;put('candidate-design.js',c.replace(b"'./three.mjs'",b"'./vendor/three.module.js'"));put('index.html',b'<meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0}</style><script type="module" src="./fixture.js"></script>');put('fixture.js',(Q/'fixture.js').read_bytes());(Q/'IDENTITIES.json').write_text(json.dumps(records,indent=2));print('PASS exact published vendor/source; candidate import-only rewrite')
