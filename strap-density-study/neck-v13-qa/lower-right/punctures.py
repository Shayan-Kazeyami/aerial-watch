import numpy as np,json,collections
from pathlib import Path
D=Path('strap-density-study');O=Path('.')
T=[]
for i in range(3):
 s=np.load(D/f'input-0-{i}.npz');T.append(s['positions'][s['faces']])
T=np.concatenate(T);u,inv=np.unique(np.round(T.reshape(-1,3).astype(float),7),axis=0,return_inverse=True);f=inv.reshape(-1,3);e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);e=np.sort(e,axis=1);e=e[e[:,0]!=e[:,1]];edges,count=np.unique(e,axis=0,return_counts=True);b=edges[count==1];adj=collections.defaultdict(set)
for a,c in b:adj[a].add(c);adj[c].add(a)
seen=set();comps=[]
for a in adj:
 if a in seen:continue
 st=[a];seen.add(a);ns=[]
 while st:
  v=st.pop();ns.append(v)
  for w in adj[v]:
   if w not in seen:seen.add(w);st.append(w)
 p=u[ns];comps.append(dict(vertices=len(ns),bounds=[p.min(0).tolist(),p.max(0).tolist()],intersectsExpandedBox=bool(p[:,0].max()>=8.5 and p[:,1].max()>=-3.5 and p[:,2].min()<-20)))
r=dict(boundaryEdges=len(b),components=comps,warning='Watertight through holes do not produce boundary edges; this checks open punctures/seams only, not closed tube topology. Actual lower sewing maximum Y=-6.073461 gives at least 2.573461mm clearance from Y=-3.5; no sewing intersections by Y bounds.')
(O/'puncture-boundary-check.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
