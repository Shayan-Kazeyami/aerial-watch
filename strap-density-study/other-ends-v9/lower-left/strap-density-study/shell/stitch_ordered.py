import numpy as np,json
from pathlib import Path
D=Path('strap-density-study');A=D/'end-shell-audit';O=D/'shell/ordered-v9';bq0=np.load(A/'bottom_attachment-path.npz');bot=bq0['positions'];paint=np.flatnonzero(bq0['sourcePrimitiveTriangle'][:,0]==1);lo,hi=paint[0],paint[-1];paths=[bot[hi+1:][::-1],bot[:lo+1]];us=np.array([0,.12,.30,.52,.72,.88,1]);data=[]
for p in paths:
 s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];s/=s[-1];u=np.unique(np.r_[us,s]);points=np.stack([np.interp(u,s,p[:,i])for i in range(3)],1);data.append((p,s,u,points))
def locate(x,p,s):
 a=p[:-1];d=np.diff(p,axis=0);t=np.clip(((x-a)*d).sum(1)/(d*d).sum(1),0,1);dist=np.linalg.norm(a+t[:,None]*d-x,axis=1);i=dist.argmin();return dist[i],s[i]+t[i]*(s[i+1]-s[i])
def split(T):
 out=[];owners=[]
 for fi,t in enumerate(T):
  done=False
  for k in range(3):
   l=(k+1)%3;third=(k+2)%3
   if max(abs(t[k,1]+3),abs(t[l,1]+3))>1e-7:continue
   for p,s,u,points in data:
    da,ua=locate(t[k,:3],p,s);db,ub=locate(t[l,:3],p,s)
    if max(da,db)>1e-6 or abs(ua-ub)<1e-10:continue
    ids=np.flatnonzero((u>min(ua,ub)+1e-9)&(u<max(ua,ub)-1e-9));ids=ids if ua<ub else ids[::-1]
    if not len(ids):continue
    verts=[t[k]]
    for i in ids:
     q=t[k]+(t[l]-t[k])*(u[i]-ua)/(ub-ua);q[:3]=points[i];verts.append(q)
    verts.append(t[l])
    for a,b in zip(verts[:-1],verts[1:]):out.append([a,b,t[third]]);owners.append(fi)
    done=True;break
   if done:break
  if not done:out.append(t);owners.append(fi)
 return np.array(out),np.array(owners)
q=np.load(O/'raw.npz');t,ids=split(q['triangles']);np.savez_compressed(O/'stitched-new.npz',triangles=t,materials=q['materials'][ids]);print('new',len(q['triangles']),len(t))
for i in range(3):
 q=np.load(A/f'preserved-outside-{i}.npz');t=np.concatenate([q['positions'],q['normals'],q['uv']],2);t,ids=split(t);np.savez_compressed(O/f'outside-{i}.npz',triangles=t);print('outside',i,len(t))
