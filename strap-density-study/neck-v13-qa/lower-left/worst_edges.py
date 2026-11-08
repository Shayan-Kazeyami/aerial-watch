import numpy as np,json,collections
from pathlib import Path
B=Path('strap-density-study/shell/uv-v10');T=[];K=[];ids=[]
for mi in range(3):
 q=np.load(B/f'new-patch-{mi}.npz');T.extend(q['triangles'][:,:,:3]);K.extend(q['kind']);ids.extend([[mi,j] for j in range(len(q['kind']))])
t=np.array(T).astype(float);k=np.array(K);fn=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(fn,axis=1)/2;fn/=np.maximum(2*area[:,None],1e-30);edges=collections.defaultdict(list)
for i in np.flatnonzero((t[:,:,1].max(1)<-2)&(t[:,:,1].min(1)>-2.95)&(area>1e-10)):
 for a,b in [(0,1),(1,2),(2,0)]:edges[tuple(sorted([tuple(np.round(t[i,a],7)),tuple(np.round(t[i,b],7))]))].append(i)
out=[]
for edge,ii in edges.items():
 if len(ii)!=2 or k[ii[0]]!=k[ii[1]]:continue
 a,b=ii;ang=float(np.degrees(np.arccos(np.clip(fn[a]@fn[b],-1,1))))
 if ang<10:continue
 e=np.array(edge);out.append(dict(kind=int(k[a]),angle=ang,edge=e.tolist(),length=float(np.linalg.norm(e[1]-e[0])),areas=area[ii].tolist(),faces=[ids[a],ids[b]],triangles=t[ii].tolist()))
out.sort(key=lambda q:-q['angle']);Path('worst-edges.json').write_text(json.dumps(out,indent=2));print(json.dumps(out[:3],indent=2))
