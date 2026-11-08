import numpy as np,json,collections
from pathlib import Path
R=Path('strap-density-study/end-shell-audit');X=9.4;Y=-3.
def clip(poly,tri,axis,val,keep):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=(a@tri)[axis]-val;db=(b@tri)[axis]-val
  if da*keep>=-1e-13:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+da/(da-db)*(b-a))
 # adjacent duplicate removal
 ans=[]
 for v in out:
  if not ans or np.linalg.norm(v-ans[-1])>1e-11:ans.append(v)
 if len(ans)>1 and np.linalg.norm(ans[0]-ans[-1])<1e-11:ans.pop()
 return ans

def merge(polys):
 if len(polys)==1:return polys
 # split collinear shared edges at all local corners, cancel internal edges
 pts=np.unique(np.round(np.array([v for po in polys for v in po]),12),axis=0);edges=collections.Counter()
 for po in polys:
  for a,b in zip(po,po[1:]+po[:1]):
   d=b-a;l=d@d
   if l<1e-22:continue
   t=((pts-a)@d)/l;err=np.linalg.norm(pts-a-t[:,None]*d,axis=1);ids=np.flatnonzero((t>=-1e-9)&(t<=1+1e-9)&(err<1e-9));ids=ids[np.argsort(t[ids])]
   for u,v in zip(ids[:-1],ids[1:]):
    if edges[v,u]:edges[v,u]-=1
    else:edges[u,v]+=1
 todo=[e for e,c in edges.items() if c];loops=[]
 while todo:
  a,b=todo.pop();loop=[a];cur=b
  while cur!=a:
   loop.append(cur);ii=next(i for i,e in enumerate(todo) if e[0]==cur);_,cur=todo.pop(ii)
  po=[pts[i] for i in loop];changed=True
  while changed and len(po)>3:
   changed=False
   for i in range(len(po)):
    a,b,c=po[i-1],po[i],po[(i+1)%len(po)];d=c-a;tt=((b-a)@d)/(d@d)
    if np.linalg.norm(b-a-tt*d)<1e-10:
     po.pop(i);changed=True;break
  loops.append(po)
 return loops

def triangulate(poly):
 # barycentric coords first2 are 2D, inherited CCW orientation
 ids=list(range(len(poly)));xy=np.array(poly)[:,:2];out=[]
 def cr(a,b):return a[0]*b[1]-a[1]*b[0]
 area=sum(cr(xy[i],xy[(i+1)%len(xy)]) for i in range(len(xy)));sg=1 if area>0 else -1
 while len(ids)>3:
  for k,b in enumerate(ids):
   a=ids[k-1];c=ids[(k+1)%len(ids)]
   if cr(xy[b]-xy[a],xy[c]-xy[b])*sg<=1e-14:continue
   inside=False
   for j in ids:
    if j in [a,b,c]:continue
    v=xy[j];s=[cr(xy[b]-xy[a],v-xy[a])*sg,cr(xy[c]-xy[b],v-xy[b])*sg,cr(xy[a]-xy[c],v-xy[c])*sg]
    if min(s)>-1e-12:inside=True;break
   if not inside:out.append([poly[a],poly[b],poly[c]]);ids.pop(k);break
  else:raise ValueError('ear triangulation failed')
 if len(ids)==3:out.append([poly[i] for i in ids])
 return out
reports=[]
for pi in range(3):
 z=np.load(f'strap-density-study/input-0-{pi}.npz');p=z['positions'].astype(float);n=z['normals'].astype(float);uv=z['uv'].astype(float);f=z['faces'];tri=p[f];poss=[];norms=[];uvs=[];prov=[];barys=[];unchanged=removed=split=0
 for i,t in enumerate(tri):
  if t[:,0].max()<X or t[:,1].max()<Y or t[:,2].min()>-20:
   bs=[np.eye(3)];unchanged+=1
  elif (t[:,0]>=X).all() and (t[:,1]>=Y).all():removed+=1;continue
  else:
   po=list(np.eye(3));left=clip(po,t,0,X,-1);right=clip(po,t,0,X,1);bottom=clip(right,t,1,Y,-1) if right else[];polys=[a for a in [left,bottom] if len(a)>=3]
   if not polys:removed+=1;continue
   bs=[]
   try:
    for poly in merge(polys):bs.extend(triangulate(poly))
   except Exception:
    print('FAIL',pi,i,polys,flush=True);raise
   split+=1
  for bary in bs:
   bary=np.array(bary);poss.append(bary@t);norms.append(bary@n[f[i]]);uvs.append(bary@uv[f[i]]);prov.append(i);barys.append(bary)
 pp=np.array(poss);nn=np.array(norms);uu=np.array(uvs);np.savez_compressed(R/f'preserved-outside-{pi}.npz',positions=pp,normals=nn,uv=uu,sourceTriangle=np.array(prov),barycentric=np.array(barys));reports.append({'primitive':pi,'sourceFaces':len(f),'unchangedFaces':unchanged,'removedFaces':removed,'splitSourceFaces':split,'outputFaces':len(pp),'note':'Triangle soup, unnormalized source-linear normals retained for provenance. Normalize only newly cut interpolated normals at export; retain source cornervalues exactly.'})
# Each original cut segment carries its OWN chart attributes, do not average across materials
s=np.load(R/'cut-x9.4-y-3.0.npz');pts=s['segments'];labels=s['sourcePrimitiveTriangle'];ns=[];us=[];bs=[]
for seg,(pi,fi) in zip(pts,labels):
 z=np.load(f'strap-density-study/input-0-{pi}.npz');t=z['positions'][z['faces'][fi]].astype(float);M=np.vstack([t.T,np.ones(3)]);b=np.array([np.linalg.lstsq(M,np.r_[v,1.],rcond=None)[0] for v in seg]);bs.append(b);ns.append(b@z['normals'][z['faces'][fi]]);us.append(b@z['uv'][z['faces'][fi]])
np.savez_compressed(R/'interface-segment-attributes.npz',positions=pts,normals=np.array(ns),uv=np.array(us),sourcePrimitiveTriangle=labels,barycentric=np.array(bs));(R/'export-report.json').write_text(json.dumps(reports,indent=2));print(reports)
