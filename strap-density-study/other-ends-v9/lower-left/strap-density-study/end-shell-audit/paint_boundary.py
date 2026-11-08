import numpy as np,json,collections
from pathlib import Path
R=Path('strap-density-study/end-shell-audit');X=9.4;Y=-3.;d=np.load('strap-density-study/input-0-1.npz');p=d['positions'].astype(float);n=d['normals'].astype(float);uv=d['uv'].astype(float);f=d['faces'];tr=p[f];P=[];N=[];U=[];F=[];B=[];TI=[]
exec(open(R/'export_interfaces.py').read().split('reports=[]')[0].split('def clip',1)[0] if False else 'pass')
def clip(po,tri,axis,value):
 out=[]
 for a,b in zip(po,po[1:]+po[:1]):
  da=(a@tri)[axis]-value;db=(b@tri)[axis]-value
  if da>=0:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+da/(da-db)*(b-a))
 return out
for ti in np.flatnonzero((tr[:,:,0].max(1)>=X)&(tr[:,:,1].max(1)>=Y)&(tr[:,:,2].min(1)<-20)):
 po=clip(list(np.eye(3)),tr[ti],0,X);po=clip(po,tr[ti],1,Y) if po else[]
 for j in range(1,len(po)-1):
  bs=np.array([po[0],po[j],po[j+1]]);ps=bs@tr[ti]
  if np.linalg.norm(np.cross(ps[1]-ps[0],ps[2]-ps[0]))<1e-15:continue
  P.extend(ps);N.extend(bs@n[f[ti]]);U.extend(bs@uv[f[ti]]);B.extend(bs);TI.extend([ti]*3)
P=np.array(P);N=np.array(N);U=np.array(U);B=np.array(B);TI=np.array(TI);F=np.arange(len(P)).reshape(-1,3);np.savez_compressed(R/'paint-removed-soup.npz',positions=P,normal=N,uv=U,faces=F,sourceTriangle=TI,barycentric=B)
reports=[]
for dig in [8,7,6,5]:
 pts,first,rev=np.unique(np.round(P,dig),axis=0,return_index=True,return_inverse=True);t=rev[F];ed=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);sourcecorn=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]);eds=np.sort(ed,axis=1);u,ix,c=np.unique(eds,axis=0,return_index=True,return_counts=True);boundary=u[c==1];src=sourcecorn[ix[c==1]];adj=collections.defaultdict(list)
 for k,(a,b) in enumerate(boundary):
  if a!=b:adj[a].append((b,k));adj[b].append((a,k))
 seen=set();components=[]
 for a in adj:
  if a in seen:continue
  stack=[a];nodes=[];seen.add(a)
  while stack:
   v=stack.pop();nodes.append(v)
   for w,k in adj[v]:
    if w not in seen:seen.add(w);stack.append(w)
  xyz=pts[nodes];rr=np.hypot(xyz[:,1]+.95,xyz[:,2]+22.4);deg=dict(collections.Counter(len(adj[v]) for v in nodes));components.append({'nodes':len(nodes),'degrees':deg,'bounds':[xyz.min(0).tolist(),xyz.max(0).tolist()],'radial':[float(rr.min()),float(rr.max())]})
  if dig==7 and set(deg)=={2}:
   seq=[];es=[];cur=nodes[0];prev=-1
   while cur not in seq:
    seq.append(cur);nx,ek=next((v,k) for v,k in adj[cur] if v!=prev);es.append(ek);prev,cur=cur,nx
   name='bore' if rr.max()<1 else 'outer' if len(nodes)>100 else 'island';xyz=P[first[seq]];corners=[]
   for v,ek in zip(seq,es):
    a0,b0=src[ek];corners.append(a0 if rev[a0]==v else b0)
   corners=np.array(corners);np.savez_compressed(R/f'paint-{name}-boundary.npz',positions=xyz,normals=N[corners],uv=U[corners],sourceTriangle=TI[corners],barycentric=B[corners],sourceSoupCorner=corners)
 reports.append({'digits':dig,'faces':len(F),'boundaryEdges':len(boundary),'nonmanifoldEdges':int((c>2).sum()),'components':components})
(R/'paint-boundary-report.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports,indent=2))
