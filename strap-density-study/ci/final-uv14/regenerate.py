"""Rebuild four own-source UV14 ends, validated density, and one sealed QA release.
No Git operations, production deployment, or browser-quality substitutions.
"""
import os,sys,json,hashlib,shutil,subprocess,time,argparse
from pathlib import Path
P=argparse.ArgumentParser();P.add_argument('--source',default='preview-b/releases/949a4881d119910ca28bdf5ef4d67dfdebc59df579e02a6de946db48668510c8/leather-assets/r14');P.add_argument('--owner',default='preview-b/releases/43e516fa6ed3a4be7e8b308bc35c1955dc811b710042e38cdbaeaf868b7c8932');args=P.parse_args()
D=Path('strap-density-study');CI=D/'ci/final-uv14';S=Path(args.source).resolve();receipt=Path('strap-output/sealed-release.json');receipt.parent.mkdir(exist_ok=True);D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(S/'geometry.bin')=='ae62f1a0e32f2bbe0e2591dff0a0664d676102e12b8f71db8e5adc1912f309c4','immutable R18 source differs'
os.environ.update(STRAP_SOURCE_ASSET_DIR=str(S),STRAP_STUDY_DIR=str(D.resolve()),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
steps=[]
def run(*cmd):
 start=time.time();print('+',' '.join(map(str,cmd)),flush=True);subprocess.run(list(map(str,cmd)),check=True);steps.append(dict(command=list(map(str,cmd)),seconds=round(time.time()-start,3)));(receipt.parent/'regeneration-steps.json').write_text(json.dumps(steps,indent=2))
def py(path,*params):run(sys.executable,path,*params)
py(CI/'audit-source.py')
for end in ['upper-left','upper-right','lower-right','lower-left']:
 base=D/'neck-v13-qa'/end;run('bash',base/'regenerate.sh')
 out=D/('wide-uv14' if end=='upper-left' else 'wide-uv14-'+end);out.mkdir(exist_ok=True)
 if end=='upper-left':
  (D/'material-boundary-study').mkdir(exist_ok=True);py(CI/'loft-params-upper-left.py')
 run('bash',out/'regenerate.sh');py(out/'quality.py')
 interface=json.loads((out/'interface-check.json').read_text());assert interface and all(0<=r['uvError']<=1e-6 and r['distance']<=3e-6 for r in interface),(end,'source interface UV gate failed')
 # Pin the generated own-source patch and interface knots for combined assembly.
 # Hashes describe THIS run, not a hardcoded local near-zero normal encoding.
 stable=out/'stable-20261108';stable.mkdir(exist_ok=True);files=[*(f'new-patch-{m}.npz' for m in range(3)),'boundary-knots.npz']
 for name in files:shutil.copy2(out/name,stable/name)
 (stable/'generated-identity.json').write_text(json.dumps({n:sha(stable/n) for n in files},indent=2))
py(D/'combined-uv14/assemble.py');py(D/'combined-uv14/normalize_arrays.py');py(CI/'verify-combined.py',D/'combined-uv14')
py(D/'integration-uv14/reconstruct-density.py',S,D/'integration-uv14/ci-density',D/'ci-reduced-inputs')
py(D/'integration-uv14/assemble-ci.py',D/'combined-uv14/assemble.py',D/'ci-reduced-inputs',D/'ci-final-candidate',S)
py(CI/'verify-combined.py',D/'ci-final-candidate')
run('node',D/'integration-uv11/build-minimal-uv14.mjs',D/'ci-final-candidate/round-cap-candidate',args.owner,'preview-b',receipt)
r=json.loads(receipt.read_text());assert r.get('promotionAllowed') is False;assert Path(r['releasePath']).is_dir();print('Sealed QA candidate:',r['releasePath'],flush=True)
