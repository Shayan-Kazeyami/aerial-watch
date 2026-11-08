import numpy as np,json
from pathlib import Path
from collections import defaultdict
from chart_uv import profiles,map_uv
D=Path('strap-density-study');I=D/'shell/uv-v10';O=D/'shell/uv-v11';O.mkdir(exist_ok=True)
records=[];knots=defaultdict(list)
def key(a,b):return tuple(sorted([tuple(np.round(a,8)),tuple(np.round(b,8))]))
def clip(poly,v,sign):
 out=[]
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  da=a[8]-v;db=b[8]-v
  if da*sign>=-1e-12:out.append(a)
  if (da>0)!=(db>0):
   c=a+(b-a)*da/(da-db);c[8]=v;out.append(c)
 ans=[]
 for a in out:
  if not ans or np.linalg.norm(a[:3]-ans[-1][:3])>1e-12:ans.append(a)
 if len(ans)>1 and np.linalg.norm(ans[0][:3]-ans[-1][:3])<1e-12:ans.pop()
 return np.array(ans)
for mi in range(3):
 z=np.load(I/f'new-patch-{mi}.npz')
 for t,s,kind in zip(z['triangles'].astype(float),z['profileS'],z['kind']):
  polys=[np.c_[t,s,np.eye(3)]]
  if mi in [0,2] and kind in profiles:
   ss,uv,g,bounds,mats=profiles[kind]
   for val in ss[bounds[1:-1]]:
    if s.min()+1e-12<val<s.max()-1e-12:
     polys=[q for po in polys for q in [clip(po,val,1),clip(po,val,-1)]if len(q)>=3]
  for po in polys:
   for a in po:
    zeros=np.where(abs(a[9:])<1e-9)[0]
    if len(zeros)==1:
     ab=[x for x in range(3)if x!=zeros[0]];f=a[9+ab[1]];kk=key(t[ab[0],:3],t[ab[1],:3])
     if 1e-9<f<1-1e-9:knots[kk].append(a[:3].copy())
  records.append((mi,t,polys,kind))
for k,v in knots.items():knots[k]=np.unique(np.round(v,11),axis=0)
out=[[],[],[]];changes=0
for mi,t,polys,kind in records:
 for po in polys:
  poly=[]
  for a,b in zip(po,np.roll(po,-1,axis=0)):
   poly.append(a);same=np.where((abs(a[9:])<1e-9)&(abs(b[9:])<1e-9))[0]
   if len(same)!=1:continue
   ab=[x for x in range(3)if x!=same[0]];kk=key(t[ab[0],:3],t[ab[1],:3]);pts=knots.get(kk,[])
   if not len(pts):continue
   d=b[:3]-a[:3];length=d@d
   if length<1e-24:continue
   fac=((pts-a[:3])@d)/length;err=np.linalg.norm(pts-a[:3]-fac[:,None]*d,axis=1);ids=np.where((fac>1e-8)&(fac<1-1e-8)&(err<1e-7))[0]
   for ix in ids[np.argsort(fac[ids])]:
    row=a+(b-a)*fac[ix];row[:3]=pts[ix];poly.append(row);changes+=1
  poly=np.array(poly)
  # Center fan avoids dropping collinear interface knots; affine interpolation preserves geometry/normals.
  if len(poly)==3:triangles=[poly]
  else:
   c=poly.mean(0);triangles=[np.array([c,a,b])for a,b in zip(poly,np.roll(poly,-1,axis=0))]
  for tr in triangles:
   if np.linalg.norm(np.cross(tr[1,:3]-tr[0,:3],tr[2,:3]-tr[0,:3]))<1e-14:continue
   mapped=map_uv(tr[None,:,:8],tr[None,:,8],np.array([kind]),mi)[0];out[mi].append(mapped)
reports=[]
for mi in range(3):
 new=np.array(out[mi]).astype('<f4');old=np.load(I/f'outside-{mi}.npz')['triangles'];whole=np.concatenate([old,new]).astype('<f4');p=whole[:,:,:3].astype(float);keep=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)>0;whole=whole[keep]
 np.savez_compressed(O/f'new-patch-{mi}.npz',triangles=new);np.savez_compressed(O/f'round-cap-0-{mi}.npz',triangles=whole);reports.append(dict(primitive=mi,newFaces=len(new),finalFaces=len(whole)))
json.dump(dict(edgeKeys=len(knots),propagatedKnots=changes,primitives=reports),open(O/'report.json','w'),indent=2);print(reports)
