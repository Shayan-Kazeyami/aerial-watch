"""Default verifies only. --apply requires separately authorized ephemeral R18 candidate. Winding only."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,copy
HERE=Path(__file__).resolve().parent
SPEC=json.loads((HERE/'guards.json').read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
def serialized(x):return (json.dumps(x,indent=2)+'\n').encode()
def safe(root,p):
 assert root in p.parents
 assert all(not q.is_symlink() for q in [p,*p.parents] if q==root or root in q.parents),p
def atomic(root,p,b):
 safe(root,p);p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_name(p.name+'.detour-merge-tmp');assert not t.exists();t.write_bytes(b);os.replace(t,p)
def manifest_guard(raw):
 assert SPEC['baselineManifestSha256'], 'R18 run receipt not yet bound; fail closed'
 assert sha(raw)==SPEC['baselineManifestSha256'], 'wrong R18 manifest bytes'
 m=json.loads(raw);paths=[x['path'] for x in m['files']]
 assert len(paths)==len(set(paths))
 return m
def preflight(root):
 assert root.is_dir() and not (root/'.git').exists()
 assert not root.is_symlink()
 assert not (root/'assembly-fork-contact-detour.js').exists(),'detour must remain absent'
 for name,h in SPEC['protected'].items():
  p=root/name;safe(root,p);assert file_sha(p)==h,'protected '+name
 manifest=manifest_guard((root/'deployment-manifest.json').read_bytes())
 rev=json.loads((root/'quality-study/viewer-revision.json').read_text())
 assert rev['digest']==SPEC['baselineSourceDigest'] and rev['files']==SPEC['baselineFirstPartyFiles']
 for x in rev['files']:
  p=root/x['path'];safe(root,p)
  assert file_sha(p)==x['sha256'] and p.stat().st_size==x['bytes'],'first party '+x['path']
 assert sha(json.dumps(rev['files'],separators=(',',':'),ensure_ascii=False).encode())==SPEC['baselineSourceDigest']
 for x in manifest['files']:
  p=root/x['path'];safe(root,p)
  assert p.stat().st_size==x['sizeBytes'] and file_sha(p)==x['sha256'],'manifest '+x['path']
 for x in SPEC['payload']:
  b=(HERE/'files'/x['path']).read_bytes();assert len(b)==x['bytes'] and sha(b)==x['afterSha256']
  p=root/x['path'];safe(root,p)
  if x['beforeSha256'] is None:assert not p.exists(),'new payload exists '+x['path']
  else:assert file_sha(p)==x['beforeSha256'],'before '+x['path']
 return manifest
def main():
 a=argparse.ArgumentParser();a.add_argument('root');a.add_argument('--apply',action='store_true');args=a.parse_args()
 supplied=Path(args.root);assert not supplied.is_symlink();root=supplied.resolve()
 manifest=preflight(root)
 print('PASS exact R18 lineage, full manifest bytes, protected terminal/cap/AVIF/capture and winding preconditions')
 if not args.apply:return
 allowed=Path(os.environ.get('RUNNER_TEMP','/tmp')).resolve()
 assert allowed in root.parents and root.name=='candidate','fresh temporary candidate directory required'
 rows={x['path']:x for x in manifest['files']}
 selected=SPEC['payload']
 for x in selected:
  atomic(root,root/x['path'],(HERE/'files'/x['path']).read_bytes())
  if not x['path'].startswith('tests/'):rows[x['path']]={'path':x['path'],'sizeBytes':x['bytes'],'sha256':x['afterSha256']}
 manifest['files']=sorted(rows.values(),key=lambda x:x['path'])
 atomic(root,root/'deployment-manifest.json',serialized(manifest))
 # Break any old hardlinks before the generator writes. No per-overlay revision is installed.
 for name in ['quality-study/viewer-revision.js','quality-study/viewer-revision.json']:
  atomic(root,root/name,(root/name).read_bytes())
 subprocess.run(['node','tools/capture-provenance.mjs'],cwd=root,check=True) # Exactly once.
 for name in ['quality-study/viewer-revision.js','quality-study/viewer-revision.json']:
  p=root/name;rows[name]={'path':name,'sizeBytes':p.stat().st_size,'sha256':file_sha(p)}
 manifest['files']=sorted(rows.values(),key=lambda x:x['path'])
 atomic(root,root/'deployment-manifest.json',serialized(manifest))
 for name,h in SPEC['protected'].items():
  if name not in ['quality-study/viewer-revision.js','quality-study/viewer-revision.json']:assert file_sha(root/name)==h,'changed protected '+name
 for x in SPEC['payload']:
  p=root/x['path']
  if x in selected:assert file_sha(p)==x['afterSha256']
  elif x['beforeSha256'] is None:assert not p.exists()
  else:assert file_sha(p)==x['beforeSha256']
 rev=json.loads((root/'quality-study/viewer-revision.json').read_text());assert len(rev['files'])==124 and rev['digest']==SPEC['expectedAfterSourceDigest']
 for x in rev['files']:assert file_sha(root/x['path'])==x['sha256'] and (root/x['path']).stat().st_size==x['bytes']
 for x in manifest['files']:assert file_sha(root/x['path'])==x['sha256'] and (root/x['path']).stat().st_size==x['sizeBytes']
 receipt={'sourceDigest':rev['digest'],'manifestSha256':file_sha(root/'deployment-manifest.json'),'payload':selected,'features':['winding'],'windingScope':SPEC['windingScope'],'protectedUnchanged':True,'sourceFiles':len(rev['files']),'manifestFiles':len(manifest['files']),'scope':SPEC['windingScope']['remaining'],'verifiedBrowser':False}
 atomic(root,root/'return-material-winding-receipt.json',serialized(receipt))
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
