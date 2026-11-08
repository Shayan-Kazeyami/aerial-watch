import sys
sys.path.insert(0,'/tmp/strap-remesh-deps')
import numpy as np,json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
D=Path('strap-density-study/neck-v13-qa/upper-left/strap-density-study');O=Path('strap-density-study/wide-uv14');profile=np.load(D/'end-shell-audit/xcut_outer_profile-path.npz')['positions'];L=np.r_[0,np.cumsum(np.linalg.norm(np.diff(profile,axis=0),axis=1))];S=L/L[-1];aa=profile[:-1,1:];dd=np.diff(profile[:,1:],axis=0);den=(dd*dd).sum(1)
def project(p):
 result=[]
 for start in range(0,len(p),500):
  q=p[start:start+500];delta=q[:,None,1:]-aa;fac=np.clip((delta*dd).sum(2)/den,0,1);dist=np.linalg.norm(delta-fac[:,:,None]*dd,axis=2);j=dist.argmin(1);s=S[j]+fac[np.arange(len(q)),j]*(S[j+1]-S[j]);result.extend(s)
 return np.c_[p[:,0],result]
allp=[];allu=[];allm=[];allids=[];alllabels=[];base=0;report=[]
for mi in [0,2]:
 z=np.load(D/f'input-0-{mi}.npz');T=z['positions'][z['faces']].astype(float);UV=z['uv'][z['faces']].astype(float);g=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);g/=np.maximum(np.linalg.norm(g,axis=1,keepdims=True),1e-30);mask=(T[:,:,0].max(1)>8.49999)&(T[:,:,1].max(1)>-3.50001)&(T[:,:,2].min(1)<-20);ids=np.flatnonzero(mask);T=T[mask];UV=UV[mask];parent=np.arange(len(T));edges={}
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,t in enumerate(T):
  for a,b in [(0,1),(1,2),(2,0)]:
   k=tuple(sorted([tuple(np.round(np.r_[t[a],UV[i,a]],6)),tuple(np.round(np.r_[t[b],UV[i,b]],6))]))
   if k in edges:parent[find(i)]=find(edges[k])
   else:edges[k]=i
 _,labels=np.unique([find(i)for i in range(len(T))],return_inverse=True);ps=project(T.reshape(-1,3)).reshape(-1,3,2);ab=ps[:,1]-ps[:,0];ac=ps[:,2]-ps[:,0];area=np.abs(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0]);keep=area>1e-12
 def clip(poly,axis,value):
  out=[]
  for a,b in zip(poly,np.roll(poly,-1,axis=0)):
   da=a[axis]-value;db=b[axis]-value
   if da>=-1e-12:out.append(a)
   if (da>0)!=(db>0):
    q=a+(b-a)*da/(da-db);q[axis]=value;out.append(q)
  return np.array(out)
 for lab in np.unique(labels):
  fi=np.flatnonzero(labels==lab);gid=base;base+=1;n=0
  for j in fi:
   poly=np.c_[T[j],UV[j]]
   for axis,value in [(0,8.5),(1,-3.5)]:
    if len(poly)<3:break
    poly=clip(poly,axis,value)
   if len(poly)<3:continue
   for k in range(1,len(poly)-1):
    tr=poly[[0,k,k+1]]
    if np.linalg.norm(np.cross(tr[1,:3]-tr[0,:3],tr[2,:3]-tr[0,:3]))<1e-13:continue
    allp.append(tr[:,:3]);allu.append(tr[:,3:]);allm.append(mi);allids.append(ids[j]);alllabels.append(gid);n+=1
  report.append(dict(chart=gid,material=mi,faces=n))
 print(mi,len(T),len(np.unique(labels)),flush=True)
P=np.array(allp);PS=project(P.reshape(-1,3)).reshape(-1,3,2);np.savez_compressed(O/'source-domains.npz',positions=P,uv=np.array(allu),param=PS,materials=allm,sourceFaces=allids,labels=alllabels);(O/'domains.json').write_text(json.dumps(report));print('charts',base,'faces',len(P))
