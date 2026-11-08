import numpy as np,json
from scipy.spatial import cKDTree
from collections import defaultdict,deque
from pathlib import Path
D=Path('strap-density-study');A=D/'end-shell-audit';O=D/'shell/uv-v10';q=np.load(O/'stitched-new.npz');T=q['triangles'];M=q['materials'];PS=q['profileS'];K=q['kind'];P=np.concatenate([np.load(O/f'outside-{i}.npz')['triangles'][:,:,:3]for i in range(3)])
# Orient new connected faces from retained surface edge directions.
def key(p):return tuple(np.round(p,7))
edges=defaultdict(list);outside={}
for i,t in enumerate(T):
 for k in range(3):
  a,b=key(t[k]),key(t[(k+1)%3]);
  if a==b:continue
  edges[tuple(sorted([a,b]))].append((i,1 if a<b else -1))
for t in P:
 for k in range(3):
  a,b=key(t[k]),key(t[(k+1)%3]);
  if a!=b:outside[tuple(sorted([a,b]))]=1 if a<b else -1
adj=defaultdict(list);flip={};conflicts=0
for e,v in edges.items():
 if len(v)==2:
  (a,sa),(b,sb)=v;adj[a].append((b,sa==sb));adj[b].append((a,sa==sb))
 elif len(v)==1 and e in outside:
  i,sg=v[0];flip[i]=int(sg==outside[e])
queue=deque(flip)
while queue:
 a=queue.popleft()
 for b,op in adj[a]:
  f=flip[a]^op
  if b in flip:conflicts+=int(flip[b]!=f)
  else:flip[b]=f;queue.append(b)
for i in range(len(T)):
 if i not in flip:
  flip[i]=int(np.cross(T[i,1]-T[i,0],T[i,2]-T[i,0])[0]<0)
T=np.array([t[[0,2,1]]if flip[i]else t for i,t in enumerate(T)]);PS=np.array([p[[0,2,1]]if flip[i]else p for i,p in enumerate(PS)])
print('orientation conflicts',conflicts)
# Geometric smooth normal field on coherent new shell; exact source boundary normals override.
# Semantic normal charts: the designed zero-width lower neck is a hard crease,
# so do not average outer loft normals with the cap's normal at that crease.
flat=T.reshape(-1,3); group=np.repeat(K==3,3).astype(int);group[flat[:,1]>-2.0000001]=0
p4,iv=np.unique(np.c_[np.round(flat,8),group],axis=0,return_inverse=True);p=p4[:,:3];f=iv.reshape(-1,3);cross=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);fn=cross/np.maximum(np.linalg.norm(cross,axis=1,keepdims=True),1e-30);nn=np.zeros_like(p)
for k in range(3):
 a=T[:,(k+1)%3]-T[:,k];b=T[:,(k+2)%3]-T[:,k];w=np.arctan2(np.linalg.norm(np.cross(a,b),axis=1),(a*b).sum(1));np.add.at(nn,f[:,k],fn*w[:,None])
nn/=np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-30);N=nn[f]
# Exact closest point and barycentric attribute projection; retain material chart identity.
def closest(points,tris):
 a=tris[:,:,0,:];b=tris[:,:,1,:];c=tris[:,:,2,:];p=points[:,None,:];ab=b-a;ac=c-a;ap=p-a;d00=(ab*ab).sum(2);d01=(ab*ac).sum(2);d11=(ac*ac).sum(2);d20=(ap*ab).sum(2);d21=(ap*ac).sum(2);den=d00*d11-d01*d01;den=np.where(abs(den)<1e-30,1e-30,den);v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;u=1-v-w;bc=np.stack([u,v,w],2);pp=(tris*bc[:,:,:,None]).sum(2);dist=((pp-p)**2).sum(2);dist[(bc.min(2)<0)]=np.inf
 for k,l in [(0,1),(1,2),(2,0)]:
  aa=tris[:,:,k,:];bb=tris[:,:,l,:];dd=bb-aa;t=np.clip(((p-aa)*dd).sum(2)/np.maximum((dd*dd).sum(2),1e-30),0,1);qq=aa+t[:,:,None]*dd;ds=((qq-p)**2).sum(2);better=ds<dist;cc=np.zeros_like(bc);cc[:,:,k]=1-t;cc[:,:,l]=t;bc[better]=cc[better];dist[better]=ds[better]
 pick=dist.argmin(1);return pick,bc[np.arange(len(points)),pick],dist[np.arange(len(points)),pick]
from chart_uv import map_uv
outputs=[];errors=[]
for mi in range(3):
 mask=M==mi;t=T[mask];n=N[mask];flat=t.reshape(-1,3);src=np.load(D/f'input-0-{mi}.npz');sp=src['positions'][src['faces']];su=src['uv'][src['faces']];sn=src['normals'][src['faces']];sel=(sp[:,:,0].max(1)>8.4)&(sp[:,:,1].max(1)>-3.8)&(sp[:,:,2].min(1)<-20);sp=sp[sel];su=su[sel];sn=sn[sel];tree=cKDTree(sp.mean(1));verts,vi=np.unique(sp.reshape(-1,3),axis=0,return_inverse=True);vfaces=defaultdict(list)
 for fi,ids0 in enumerate(vi.reshape(-1,3)):
  for v in ids0:vfaces[v].append(fi)
 vtree=cKDTree(verts);uvs=[];maxerr=0
 for start in range(0,len(flat),200):
  pts=flat[start:start+200];_,cent=tree.query(pts,k=min(16,len(sp)));_,nearv=vtree.query(pts,k=min(8,len(verts)));candidates=[np.unique(np.r_[c,*[vfaces[v]for v in vs]])for c,vs in zip(cent,nearv)];width=max(map(len,candidates));ids=np.array([np.pad(c,(0,width-len(c)),mode='edge')for c in candidates]);ii,bc,dist=closest(pts,sp[ids]);ids=ids[np.arange(len(pts)),ii];uvs.append((su[ids]*bc[:,:,None]).sum(1))
  if np.sqrt(dist).max()>maxerr:maxerr=float(np.sqrt(dist).max());worst=pts[dist.argmax()].tolist()
 uv=np.concatenate(uvs).reshape(-1,3,2)
 # Source boundary normals/UV using closest retained cut segments, independently per primitive.
 cut=np.load(A/'interface-segment-attributes.npz');sm=cut['sourcePrimitiveTriangle'][:,0]==mi;ep=cut['positions'][sm];en=cut['normals'][sm];eu=cut['uv'][sm];flatn=n.reshape(-1,3);flatuv=uv.reshape(-1,2)
 for start in range(0,len(flat),500):
  pts=flat[start:start+500];d=ep[:,1]-ep[:,0];tau=np.clip(((pts[:,None,:]-ep[None,:,0])*d[None,:,:]).sum(2)/np.maximum((d*d).sum(1),1e-30),0,1);dist=np.linalg.norm(pts[:,None,:]-(ep[None,:,0]+tau[:,:,None]*d[None,:,:]),axis=2);ii=dist.argmin(1);match=dist[np.arange(len(pts)),ii]<2e-7;fac=tau[np.arange(len(pts)),ii];indices=np.arange(start,start+len(pts))[match];ns=en[ii,0]*(1-fac[:,None])+en[ii,1]*fac[:,None];us=eu[ii,0]*(1-fac[:,None])+eu[ii,1]*fac[:,None];flatn[indices]=ns[match];flatuv[indices]=us[match]
 new=map_uv(np.concatenate([t,n,uv],2),PS[mask],K[mask],mi);np.savez_compressed(O/f'new-patch-{mi}.npz',triangles=new.astype('<f4'),profileS=PS[mask],kind=K[mask]);old=np.load(O/f'outside-{mi}.npz')['triangles'];whole=np.concatenate([old,new]).astype('<f4');area=np.linalg.norm(np.cross(whole[:,1,:3].astype(float)-whole[:,0,:3],whole[:,2,:3]-whole[:,0,:3]),axis=1);zero=area==0;print('mat',mi,'new',len(new),'projectionmax',maxerr,'worst',worst,'zero',zero.sum());whole=whole[~zero];np.savez_compressed(O/f'round-cap-0-{mi}.npz',triangles=whole);errors.append(dict(primitive=mi,max_source_projection_distance_mm=maxerr,new_faces=len(new),float32_zero_faces_removed=int(zero.sum())))
json.dump(dict(orientation_conflicts=conflicts,primitives=errors),open(O/'attribute-report.json','w'),indent=2)
