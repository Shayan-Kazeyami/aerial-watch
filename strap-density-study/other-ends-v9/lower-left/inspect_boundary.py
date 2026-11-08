import numpy as np,collections,json
z=np.load('strap-density-study/end-shell-audit/paint-removed-soup.npz');p=z['positions'];f=z['faces'];u,first,rev=np.unique(np.round(p,8),axis=0,return_index=True,return_inverse=True);t=rev[f];e=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);ed,c=np.unique(np.sort(e,1),axis=0,return_counts=True);ed=ed[c==1];adj=collections.defaultdict(list)
for i,(a,b) in enumerate(ed):adj[a].append((b,i));adj[b].append((a,i))
for v,nb in adj.items():
 if len(nb)>2:print('pinch',v,u[v],[(w,u[w].tolist())for w,i in nb])
# Greedy boundarycycles at pinch preserving every edge
used=set();cycles=[]
for i,(a,b) in enumerate(ed):
 if i in used:continue
 seq=[a];cur=b;used.add(i)
 while cur!=a:
  seq.append(cur);opts=[(v,k) for v,k in adj[cur] if k not in used]
  if not opts:raise RuntimeError((cur,seq))
  cur,k=opts[0];used.add(k)
 pts=p[first[seq]];cycles.append(pts);print('cycle',len(pts),'bounds',pts.min(0),pts.max(0),'yzarea',abs((pts[:,1]*np.roll(pts,-1,axis=0)[:,2]-pts[:,2]*np.roll(pts,-1,axis=0)[:,1]).sum())/2)
np.savez_compressed('boundary-cycles.npz',**{f'cycle_{i}':v for i,v in enumerate(cycles)})
