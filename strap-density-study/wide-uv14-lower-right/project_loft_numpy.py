import numpy as np,json
from pathlib import Path
from scipy.spatial import cKDTree
O=Path('strap-density-study/wide-uv14-lower-right');q=np.load('strap-density-study/wide-uv14-lower-right/loft-param-triangles.npz');T=q['triangles'].astype(float);U=q['profileU'];S=q['profileS'];cent=T.mean(1);tree=cKDTree(cent);radius=np.linalg.norm(T-cent[:,None,:],axis=2).max()
def closest(points,tris):
 a=tris[:,:,0,:];b=tris[:,:,1,:];c=tris[:,:,2,:];p=points[:,None,:];ab=b-a;ac=c-a;ap=p-a;d00=(ab*ab).sum(2);d01=(ab*ac).sum(2);d11=(ac*ac).sum(2);d20=(ap*ab).sum(2);d21=(ap*ac).sum(2);den=d00*d11-d01*d01;den=np.where(abs(den)<1e-30,1e-30,den);v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;bc=np.stack([1-v-w,v,w],2);pp=(tris*bc[:,:,:,None]).sum(2);dist=((pp-p)**2).sum(2);dist[bc.min(2)<0]=np.inf
 for k,l in [(0,1),(1,2),(2,0)]:
  aa=tris[:,:,k,:];dd=tris[:,:,l,:]-aa;t=np.clip(((p-aa)*dd).sum(2)/np.maximum((dd*dd).sum(2),1e-30),0,1);qq=aa+t[:,:,None]*dd;ds=((qq-p)**2).sum(2);better=ds<dist;cc=np.zeros_like(bc);cc[:,:,k]=1-t;cc[:,:,l]=t;bc[better]=cc[better];dist[better]=ds[better]
 pick=dist.argmin(1);return pick,bc[np.arange(len(points)),pick],dist[np.arange(len(points)),pick]
def project(P):
 points,inv=np.unique(P.reshape(-1,3),axis=0,return_inverse=True);out=[];ds=[]
 for st in range(0,len(points),64):
  p=points[st:st+64];_,seed=tree.query(p,k=8);_,_,dd=closest(p,T[seed]);ids=tree.query_ball_point(p,np.sqrt(dd)+radius+1e-10);width=max(map(len,ids));ids=np.array([np.pad(a,(0,width-len(a)),mode='edge')for a in ids]);i,bc,dist=closest(p,T[ids]);fi=ids[np.arange(len(p)),i];out.extend(np.c_[(bc*U[fi]).sum(1),(bc*S[fi]).sum(1)]);ds.extend(np.sqrt(dist))
 return np.array(out)[inv].reshape(P.shape[:-1]+(2,)),np.array(ds)[inv].reshape(P.shape[:-1])
z=np.load(O/'source-domains.npz');d={k:z[k]for k in z.files};d['param'],d['projectionDistance']=project(d['positions'])
# Exact retained-source cut provenance overrides nearest-surface ambiguity.
# Bottom boundary belongs to profile endpoint0/1 even when nearby collar facets
# are marginally closer after Float32 source/interpolated-coordinate differences.
pts=d['positions'].reshape(-1,3);par=d['param'].reshape(-1,2)
ends=[]
for ti in range(len(T)):
 for a,b in [(0,1),(1,2),(2,0)]:
  if max(abs(T[ti,[a,b],1]+3.5))<2e-6 and abs(S[ti,a]-S[ti,b])<1e-7 and min(abs(S[ti,a]),abs(S[ti,a]-1))<1e-7:ends.append((T[ti,a],T[ti,b],U[ti,a],U[ti,b],S[ti,a]))
for k in np.where(abs(pts[:,1]+3.5)<1e-8)[0]:
 candidates=[]
 for a,b,ua,ub,ss in ends:
  dd=b-a;f=np.clip((pts[k]-a)@dd/(dd@dd),0,1);candidates.append((np.linalg.norm(pts[k]-a-f*dd),ua+f*(ub-ua),ss))
 dist,uu,ss=min(candidates);par[k]=[uu,ss]
par[abs(pts[:,0]-8.5)<1e-8,0]=0
np.savez_compressed(O/'source-loft.npz',**d)
D=Path('strap-density-study/neck-v13-qa/lower-right/strap-density-study/shell/uv-v10')
for m in range(3):
 z=np.load(D/f'new-patch-{m}.npz');d={k:z[k]for k in z.files};sel=d['kind']==0;ps=np.zeros((len(sel),3,2));ds=np.zeros((len(sel),3));ps[sel],ds[sel]=project(d['triangles'][sel,:,:3]);d['param']=ps;d['projectionDistance']=ds;np.savez_compressed(O/f'target-{m}.npz',**d);print(m,'projected',int(sel.sum()),flush=True)
# Use final stitched target boundary, which contains exact source-interface knots
# absent from raw loft segments. Retain each target endpoint's chosen U coordinate.
ends=[]
for m in range(3):
 zz=np.load(O/f'target-{m}.npz');tt=zz['triangles'];pp=zz['param'];ss=zz['profileS'];kk=zz['kind']
 for ti in np.where(kk==0)[0]:
  for a,b in [(0,1),(1,2),(2,0)]:
   if max(abs(tt[ti,[a,b],1]+3.5))<2e-6 and abs(ss[ti,a]-ss[ti,b])<1e-7 and min(abs(ss[ti,a]),abs(ss[ti,a]-1))<1e-7:ends.append((tt[ti,a,:3].astype(float),tt[ti,b,:3].astype(float),pp[ti,a,0],pp[ti,b,0],ss[ti,a]))
z=np.load(O/'source-loft.npz');d={k:z[k]for k in z.files};pts=d['positions'].reshape(-1,3);par=d['param'].reshape(-1,2)
for k in np.where(abs(pts[:,1]+3.5)<1e-8)[0]:
 candidates=[]
 for a,b,ua,ub,ss in ends:
  dd=b-a;f=np.clip((pts[k]-a)@dd/max(dd@dd,1e-30),0,1);candidates.append((np.linalg.norm(pts[k]-a-f*dd),ua+f*(ub-ua),ss))
 dist,uu,ss=min(candidates);par[k]=[uu,ss]
np.savez_compressed(O/'source-loft.npz',**d)
