import numpy as np,json
from pathlib import Path
D=Path('strap-density-study');O=D/'combined-uv14';reports=[]
for mi in [0,2]:
 for pi in range(3):
  src=np.load(D/f'input-{mi}-{pi}.npz');source=np.c_[src['positions'],src['normals'],src['uv']].astype('<f4');source[source==0]=0;keys=set(v.tobytes()for v in source)
  p=O/f'round-cap-{mi}-{pi}.npz';z=np.load(p);keep={k:z[k]for k in z.files};t=np.ascontiguousarray(z['triangles']);f=t.reshape(-1,8);k=f.copy();k[k==0]=0;preserved=np.array([v.tobytes()in keys for v in k]);n=f[:,3:6];length=np.linalg.norm(n.astype(float),axis=1);mask=(abs(length-1)>5e-7)&~preserved;n[mask]=(n[mask].astype(float)/length[mask,None]).astype('<f4');err=abs(np.linalg.norm(n.astype(float),axis=1)-1);assert err.max()<3e-6;keep['triangles']=t;np.savez_compressed(p,**keep);reports.append(dict(mesh=mi,primitive=pi,changedCorners=int(mask.sum()),maxUnitError=float(err.max())))
(O/'normalization-report.json').write_text(json.dumps(reports,indent=2))
