import numpy as np,json,os,sys,subprocess
from pathlib import Path
D=Path('strap-density-study');A=Path(os.environ.get('UV14_ARRAY_DIR',str(D/'wide-uv14')));O=D/'uv14-candidate';O.mkdir(exist_ok=True)
for mi in [0,2]:
 for pi in range(3):
  src=np.load(D/f'input-{mi}-{pi}.npz');old=np.concatenate([src['positions'][src['faces']],src['normals'][src['faces']],src['uv'][src['faces']]],2).astype('<f4')
  if mi==0:
   t=np.load(A/f'round-cap-0-{pi}.npz')['triangles'].copy();t[:,:,0]*=-1;t[:,:,3]*=-1;t=t[:,[0,2,1]]
  else:t=old
  # Preserve every exact source corner; only normalize newly interpolated normals.
  t=np.ascontiguousarray(t);source=old.reshape(-1,8).copy();source[source==0]=0;keys=set(x.tobytes()for x in source);flat=t.reshape(-1,8);q=flat.copy();q[q==0]=0;preserve=np.array([x.tobytes()in keys for x in q]);n=flat[:,3:6];length=np.linalg.norm(n.astype(float),axis=1);mask=(abs(length-1)>5e-7)&~preserve;n[mask]=(n[mask].astype(float)/length[mask,None]).astype('<f4');assert abs(np.linalg.norm(n.astype(float),axis=1)-1).max()<3e-6;np.savez_compressed(O/f'round-cap-{mi}-{pi}.npz',triangles=t)
os.environ['STRAP_STUDY_DIR']=str(O.resolve())
for s in ['export_all.py','compact_export.py']:subprocess.run([sys.executable,str(Path('strap-qa')/s if Path('strap-qa').exists() else Path('strap-density-study/ci/all-ends' if s=='export_all.py' else 'strap-density-study/ci')/s)],check=True)
