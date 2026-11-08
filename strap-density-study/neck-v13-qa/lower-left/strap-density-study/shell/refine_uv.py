import numpy as np,json
from pathlib import Path
from collections import defaultdict
from chart_uv import profiles,map_uv
D=Path('strap-density-study');I=D/'shell/uv-v10';O=D/'shell/uv-v11';O.mkdir(exist_ok=True)
records=[];knots=defaultdict(list)
# Parametric seam values closer than the source Float32 geometric precision share a knot.
# This avoids creating zero-width sliver strips whose geometry collapses on export.
param_snap={}
for kind in profiles:
 vals=np.concatenate([q['profileS'][q['kind']==kind].ravel() for q in [np.load(I/f'new-patch-{m}.npz')for m in range(3)]]);u,c=np.unique(vals,return_counts=True);mapped=u.copy();starts=np.r_[0,np.where(np.diff(u)>2e-7)[0]+1,len(u)]
 for a,b in zip(starts[:-1],starts[1:]):mapped[a:b]=u[a+np.argmax(c[a:b])]
 param_snap[kind]=(u,mapped)
def snap(kind,s):
 if kind not in param_snap or kind==0:return s
 u,v=param_snap[kind];ix=np.searchsorted(u,s);left=np.clip(ix-1,0,len(u)-1);right=np.clip(ix,0,len(u)-1);j=np.where(abs(u[left]-s)<abs(u[right]-s),left,right);return np.where(abs(u[j]-s)<2e-7,v[j],s)

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
  s=snap(kind,s);polys=[np.c_[t,s,np.eye(3)]]
  if mi in [0,2] and kind in profiles:
   ss,uv,g,bounds,mats=profiles[kind]
   for val in np.unique(snap(kind,ss[bounds[1:-1]])):
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
  # Use one exact split position on both sides of every old shared edge before Float32 export.
  for row in po:
   zeros=np.where(abs(row[9:])<1e-9)[0]
   if len(zeros)==1:
    ab=[x for x in range(3)if x!=zeros[0]];pts=knots.get(key(t[ab[0],:3],t[ab[1],:3]),[])
    if len(pts):
     dist=np.linalg.norm(pts-row[:3],axis=1);j=int(dist.argmin())
     if dist[j]<1e-8:row[:3]=pts[j]
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
# Match the exact retained source UV chart at true patch boundary corners, never blend atlas islands.
from collections import Counter
out=[np.array(v).astype('<f4')for v in out]
def bkey(a,b):return tuple(sorted([tuple(np.round(a.astype(float),8)),tuple(np.round(b.astype(float),8))]))
counts=Counter(bkey(t[k,:3],t[(k+1)%3,:3])for ts in out for t in ts for k in range(3));interfaces=np.load(D/'end-shell-audit/interface-segment-attributes.npz');boundaryCorrection=0.
for mi,ts in enumerate(out):
 sel=interfaces['sourcePrimitiveTriangle'][:,0]==mi;ep=interfaces['positions'][sel];eu=interfaces['uv'][sel];delta=ep[:,1]-ep[:,0]
 for tr in ts:
  for k in range(3):
   if not any(counts[bkey(tr[a,:3],tr[b,:3])]==1 for a,b in [(k,(k+1)%3),((k-1)%3,k)]):continue
   p=tr[k,:3].astype(float);tau=np.clip(((p-ep[:,0])*delta).sum(1)/np.maximum((delta*delta).sum(1),1e-30),0,1);dist=np.linalg.norm(p-ep[:,0]-tau[:,None]*delta,axis=1);uv=eu[:,0]+tau[:,None]*(eu[:,1]-eu[:,0]);err=np.linalg.norm(uv-tr[k,6:],axis=1);err[dist>2e-6]=np.inf;j=int(err.argmin());assert err[j]<1e-3,(mi,p,err[j]);boundaryCorrection=max(boundaryCorrection,float(err[j]));tr[k,6:]=uv[j]
reports=[]
for mi in range(3):
 new=np.array(out[mi]).astype('<f4');old=np.load(I/f'outside-{mi}.npz')['triangles'];whole=np.concatenate([old,new]).astype('<f4');p=whole[:,:,:3].astype(float);keep=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)>0;whole=whole[keep]
 np.savez_compressed(O/f'new-patch-{mi}.npz',triangles=new);np.savez_compressed(O/f'round-cap-0-{mi}.npz',triangles=whole);reports.append(dict(primitive=mi,newFaces=len(new),finalFaces=len(whole)))
json.dump(dict(edgeKeys=len(knots),propagatedKnots=changes,maxBoundaryUvCorrection=boundaryCorrection,primitives=reports),open(O/'report.json','w'),indent=2);print(reports)
