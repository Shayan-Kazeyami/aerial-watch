"""Restore exact retained-source UV interpolation only within same seeded chart.
Reject distant-atlas mismatches: this is not chart assignment or UV clamping.
"""
import numpy as np,json
from pathlib import Path
from collections import Counter
O=Path('strap-density-study/wide-uv14-upper-right');D=Path('strap-density-study/neck-v13-qa/upper-right/strap-density-study');patch=[np.load(O/f'new-patch-{m}.npz')['triangles'].copy()for m in range(3)];key=lambda a,b:tuple(sorted([tuple(a),tuple(b)]));counts=Counter(key(t[i,:3],t[(i+1)%3,:3])for a in patch for t in a for i in range(3));cut=np.load(D/'end-shell-audit/interface-segment-attributes.npz');rows=[];whole=[]
for m,ts in enumerate(patch):
 sel=cut['sourcePrimitiveTriangle'][:,0]==m;ep=cut['positions'][sel];uv=cut['uv'][sel];dd=ep[:,1]-ep[:,0]
 for fi,t in enumerate(ts):
  ids=set(j for i in range(3)if counts[key(t[i,:3],t[(i+1)%3,:3])]==1 for j in [i,(i+1)%3])
  for k in ids:
   p=t[k,:3].astype(float);f=np.clip(((p-ep[:,0])*dd).sum(1)/np.maximum((dd*dd).sum(1),1e-30),0,1);dist=np.linalg.norm(p-ep[:,0]-f[:,None]*dd,axis=1);uu=uv[:,0]+f[:,None]*(uv[:,1]-uv[:,0]);err=np.linalg.norm(uu-t[k,6:],axis=1);err[dist>3e-6]=np.inf;j=int(err.argmin())
   if err[j]>1e-4:raise RuntimeError(('chart mismatch, refuse corner overwrite',m,fi,k,float(err[j])))
   rows.append(float(err[j]));t[k,6:]=uu[j]
 z=np.load(O/f'round-cap-0-{m}.npz')['triangles'].copy();z[-len(ts):]=ts;whole.append(z);np.savez_compressed(O/f'new-patch-{m}.npz',triangles=ts);np.savez_compressed(O/f'round-cap-0-{m}.npz',triangles=z)
np.savez_compressed(O/'output.npz',triangles=np.concatenate(whole));(O/'exact-interface-report.json').write_text(json.dumps({'corners':len(rows),'maxSameChartUVCorrection':max(rows)},indent=2))
