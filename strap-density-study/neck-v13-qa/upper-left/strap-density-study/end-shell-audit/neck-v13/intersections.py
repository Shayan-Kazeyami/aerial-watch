import numpy as np,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path('strap-density-study/end-shell-audit/neck-v13');a=np.load('strap-density-study/shell/uv-v10/stitched-new.npz')['triangles'].astype(float);bb=np.concatenate([np.load(f'strap-density-study/shell/uv-v10/outside-{i}.npz')['triangles'][:,:,:3] for i in range(3)]).astype(float);mask=(bb[:,:,0].max(1)>8.49)&(bb[:,:,1].max(1)>-3.51)&(bb[:,:,2].min(1)<-20);b=bb[mask]
def tree(t):return BVHTree.FromPolygons(t.reshape(-1,3).tolist(),np.arange(t.size//3).reshape(-1,3).tolist(),all_triangles=True,epsilon=0.)
def inside(p,t):
 v0=t[1]-t[0];v1=t[2]-t[0];v2=p-t[0];d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1;den=d00*d11-d01*d01
 if abs(den)<1e-25:return False
 v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;return v>=-1e-7 and w>=-1e-7 and v+w<=1+1e-7

def cross(a,b):
 na=np.cross(a[1]-a[0],a[2]-a[0]);nb=np.cross(b[1]-b[0],b[2]-b[0]);la=np.linalg.norm(na);lb=np.linalg.norm(nb)
 if min(la,lb)<1e-15:return None
 na/=la;nb/=lb
 # Coplanar overlap: clip in 2D and report positive area, excluding mere boundary touch
 if np.max(abs((b-a[0])@na))<1e-7 and abs(na@nb)>1-1e-8:
  ax=np.argmax(abs(na));aa=np.delete(a,ax,1);bbb=np.delete(b,ax,1);sg=np.sign(np.cross(bbb[1]-bbb[0],bbb[2]-bbb[0]));poly=list(aa)
  for u,v in zip(bbb,np.roll(bbb,-1,axis=0)):
   out=[]
   if not poly:break
   for p,q in zip(poly,poly[1:]+poly[:1]):
    dp=np.cross(v-u,p-u)*sg;dq=np.cross(v-u,q-u)*sg
    if dp>=0:out.append(p)
    if (dp>=0)!=(dq>=0):out.append(p+dp/(dp-dq)*(q-p))
   poly=out
  ar=abs(sum(np.cross(p,q) for p,q in zip(poly,poly[1:]+poly[:1])))/2 if poly else 0
  return ('coplanarArea',float(ar)) if ar>1e-10 else None
 pts=[]
 for s,t,n in [(a,b,nb),(b,a,na)]:
  ds=(s-t[0])@n
  for i,j in [(0,1),(1,2),(2,0)]:
   if ds[i]*ds[j]<-1e-14:
    p=s[i]+ds[i]/(ds[i]-ds[j])*(s[j]-s[i])
    if inside(p,t):pts.append(p)
 if len(pts)>1:
  length=max(np.linalg.norm(p-q) for p in pts for q in pts)
  if length>1e-5:return ('crossingLength',float(length))
 return None
A=tree(a);B=tree(b);reports=[]
for label,pa,pb,pairs in [('new_self',a,a,A.overlap(A)),('new_outside',a,b,A.overlap(B))]:
 hits=[];tested=0
 for i,j in pairs:
  if label=='new_self' and i>=j:continue
  t,u=pa[i],pb[j]
  # Triangles sharing edge or vertex may legitimately touch, but do not skip broad geometric crossings.
  shared=(np.linalg.norm(t[:,None,:]-u[None,:,:],axis=2)<1e-7).sum()
  if shared>=2:continue
  tested+=1;hit=cross(t,u)
  if hit:hits.append({'a':int(i),'b':int(j),'type':hit[0],'measure':hit[1],'sharedCorners':int(shared),'center':t.mean(0).tolist()})
 reports.append({'kind':label,'broadPairs':len(pairs),'tested':tested,'hits':hits});print(label,len(pairs),tested,len(hits),flush=True)
(R/'intersection-report.json').write_text(json.dumps(reports,indent=2))
