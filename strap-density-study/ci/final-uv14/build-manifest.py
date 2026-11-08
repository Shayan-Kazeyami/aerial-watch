"""Emit complete text-only Git tree additions; no push or binary assets."""
from pathlib import Path
import json,hashlib
ROOT=Path.cwd();D=Path('strap-density-study');O=D/'ci/final-uv14';files={}
def add(path,destination=None):
 p=Path(path);dest=str(destination or p);assert p.is_file(),p;data=p.read_text();assert '\x00'not in data,p;files[dest]=dict(path=dest,mode='100644',type='blob',content=data)
# Reviewed geometry generator tree, refreshed from actual current source files.
for entry in json.loads((D/'ci/wide-all/tree-entries.json').read_text()):
 p=entry['path']
 if p.startswith('strap-density-study/neck-v13-qa/') and '/end-shell-audit/neck-v13/'not in p:add(p)
# Every own-end mapping dependency, no rejected prototype scripts or NPZ payloads.
common=['source_domains.py','project_loft_numpy.py','transfer.py','pslg.py','repair_chart_slivers.py','exact_interface_uv.py','topology.py','interface_check.py','split_outside.py','quality.py','regenerate.sh','requirements.txt']
for end in ['upper-left','upper-right','lower-right','lower-left']:
 p=D/('wide-uv14' if end=='upper-left' else 'wide-uv14-'+end)
 for f in common:add(p/f)
 if end!='upper-left':add(p/'loft_params.py')
 if end=='lower-left':add(p/'coalesce_chart_knots.py')
for p in [D/'end-shell-audit/export_interfaces.py',D/'combined-uv14/assemble.py',D/'combined-uv14/normalize_arrays.py',D/'combined-wide-v13/normalize_arrays.py',D/'integration-uv14/reconstruct-density.py',D/'integration-uv14/assemble-ci.py',D/'integration-uv11/build-minimal-uv14.mjs',D/'ci/all-ends/export_all.py',D/'ci/compact_export.py']:
 add(p)
for p in sorted((D/'integration-uv14/ci-density').iterdir()):
 if p.is_file():assert p.suffix in ['.txt','.json'];add(p)
for p in sorted(Path('metal-recovery/integration-study/release-tools').rglob('*')):
 if p.is_file() and p.suffix in ['.js','.mjs','.json']:add(p)
for p in [O/'regenerate.py',O/'verify-combined.py',O/'audit-source.py',O/'loft-params-upper-left.py',O/'requirements.txt',O/'build-manifest.py']:
 add(p)
for p in [D/'integration-qa/qa.py',D/'integration-qa/qa-hook.js']:add(p)
add(O/'workflow.yml','.github/workflows/strap-cap-qa.yml')
entries=[files[k]for k in sorted(files)];(O/'tree-elements.json').write_text(json.dumps(entries,separators=(',',':')))
manifest=[dict(path=e['path'],bytes=len(e['content'].encode()),sha256=hashlib.sha256(e['content'].encode()).hexdigest())for e in entries];(O/'text-manifest.json').write_text(json.dumps(manifest,indent=2))
# Convenient bounded connector chunks; authoritative full tree remains above.
chunks=[];chunk=[];size=0
for e in entries:
 n=len(json.dumps(e).encode())
 if chunk and size+n>45000:chunks.append(chunk);chunk=[];size=0
 chunk.append(e);size+=n
if chunk:chunks.append(chunk)
for i,c in enumerate(chunks):(O/f'tree-{i:03d}.json').write_text(json.dumps(c,separators=(',',':')))
print('text files',len(entries),'bytes',sum(m['bytes']for m in manifest),'chunks',len(chunks))
