import numpy as np,json
from pathlib import Path
from collections import Counter
O=Path('strap-density-study/wide-uv14-lower-right');D=Path('strap-density-study/neck-v13-qa/lower-right/strap-density-study');ts=[np.load(O/f'new-patch-{m}.npz')['triangles']for m in range(3)];key=lambda a,b:tuple(sorted([tuple(a.astype(float)),tuple(b.astype(float))]));counts=Counter(key(t[i,:3],t[(i+1)%3,:3])for a in ts for t in a for i in range(3));cut=np.load(D/'end-shell-audit/interface-segment-attributes.npz');rows=[]
for m,triangles in enumerate(ts):
 sel=cut['sourcePrimitiveTriangle'][:,0]==m;ep=cut['positions'][sel];uv=cut['uv'][sel];delta=ep[:,1]-ep[:,0]
 for fi,t in enumerate(triangles):
  ids=set(j for i in range(3)if counts[key(t[i,:3],t[(i+1)%3,:3])]==1 for j in [i,(i+1)%3])
  for k in ids:
   p=t[k,:3].astype(float);f=np.clip(((p-ep[:,0])*delta).sum(1)/np.maximum((delta*delta).sum(1),1e-30),0,1);d=np.linalg.norm(p-ep[:,0]-f[:,None]*delta,axis=1);u=uv[:,0]+f[:,None]*(uv[:,1]-uv[:,0]);e=np.linalg.norm(u-t[k,6:],axis=1);e[d>3e-6]=np.inf;j=int(e.argmin());rows.append(dict(material=m,face=fi,corner=k,position=p.tolist(),distance=float(d[j]),uvError=float(e[j]),uv=t[k,6:].tolist(),sourceUV=u[j].tolist()))
(O/'interface-check.json').write_text(json.dumps(rows,indent=2));errs=np.array([r['uvError']for r in rows]);print('corners',len(rows),'UV',np.quantile(errs,[0,.5,.9,.99,1]),'bad',sum(errs>1e-5));print(sorted(rows,key=lambda r:-r['uvError'])[:3])
