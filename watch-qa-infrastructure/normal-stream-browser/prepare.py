from pathlib import Path
import os,json,hashlib,shutil
Q=Path(__file__).resolve().parent
S=Path(os.environ['WATCH_BASE'])
pins=json.loads((Q/'SOURCE_PINS.json').read_text())
assert hashlib.sha256((S/'deployment-manifest.json').read_bytes()).hexdigest()==pins['manifestSHA256']
for name,digest in pins['inputs'].items():
 p=S/name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
 if name.startswith('leather-assets/'):
  out=Q/'fixtures'/p.name;out.parent.mkdir(exist_ok=True);shutil.copyfile(p,out)
assert hashlib.sha256((Q/'candidate.mjs').read_bytes()).hexdigest()==pins['candidateSHA256']
assert hashlib.sha256((Q/'baseline.mjs').read_bytes()).hexdigest()==pins['inputs']['assembly-fetch-progressive-normal.js']
assert hashlib.sha256((Q/'assembly-progressive-normal.js').read_bytes()).hexdigest()==pins['inputs']['assembly-progressive-normal.js']
print('exact source and candidate pins verified')
