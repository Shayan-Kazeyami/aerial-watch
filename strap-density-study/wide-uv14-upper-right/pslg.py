import sys
sys.path.insert(0,'/tmp/strap-remesh-deps')
import numpy as np,json,triangle
from collections import defaultdict
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely import set_precision
O=Path('strap-density-study/wide-uv14-upper-right');D=Path('strap-density-study/neck-v13-qa/upper-right/strap-density-study/shell/uv-v10');target={m:np.load(O/f'target-{m}.npz')['triangles'].astype(float)for m in range(3)};groups=defaultdict(list);knots=defaultdict(list);edgepos={}
def key(a,b):return tuple(sorted([tuple(a.astype('<f4')),tuple(b.astype('<f4'))]))
def snap_constraint(b,orig):
 b=b.copy();p=b@orig[:,:3];eps=float(np.spacing(np.abs(orig[:,:3]).astype('<f4')).max())
 # Existing triangle corners are immutable. Only added chart constraints snap.
 if np.max(b)>1-1e-10:return np.eye(3)[b.argmax()]
 options=[]
 for i in range(3):
  ids=[j for j in range(3)if j!=i];a,c=orig[ids[0],:3],orig[ids[1],:3];d=c-a;f=np.clip((p-a)@d/max(d@d,1e-30),0,1);dist=np.linalg.norm(p-a-f*d)
  if dist<=eps:options.append((dist,ids,f))
 if options:
  _,ids,f=min(options,key=lambda x:x[0]);b[:]=0;b[ids[0]]=1-f;b[ids[1]]=f
 return b
for m in range(3):
 z=np.load(O/f'raw-transfer-{m}.npz')
 for t,bc,sf in zip(z['triangles'],z['barycentric'],z['sourceFace']):
  sf=tuple(sf);orig=target[sf[0]][sf[1]];bc=np.array([snap_constraint(b,orig) for b in bc]);groups[sf].append((m,t,bc))
  for b in bc:
   iz=np.where(abs(b)<1e-7)[0]
   if len(iz)!=1:continue
   ii=[i for i in range(3)if i!=iz[0]];a,c=orig[ii[0],:3],orig[ii[1],:3];k=key(a,c);rev=tuple(a.astype('<f4'))>tuple(c.astype('<f4'));f=b[ii[0]]if rev else b[ii[1]];edgepos[k]=(c,a)if rev else(a,c);knots[k].append(float(f))
for k,fs in knots.items():
 a,b=edgepos[k];length=np.linalg.norm(b-a);v=np.unique(np.clip(np.r_[0,fs,1],0,1));cuts=np.r_[0,np.where(np.diff(v)*length>float(np.spacing(np.abs(np.r_[a,b]).astype('<f4')).max()))[0]+1,len(v)];out=[]
 for l,r in zip(cuts[:-1],cuts[1:]):
  x=v[l:r];f=0. if x[0]==0 else 1. if x[-1]==1 else float(np.median(x));out.append(f)
 knots[k]=out
def canon(b,orig):
 b=snap_constraint(b,orig);b[abs(b)<1e-8]=0;b[abs(b-1)<1e-8]=1;iz=np.where(b==0)[0]
 if len(iz)>=2:b[:]=np.eye(3)[b.argmax()]
 elif len(iz)==1:
  ii=[i for i in range(3)if i!=iz[0]];a,c=orig[ii[0],:3],orig[ii[1],:3];k=key(a,c);rev=tuple(a.astype('<f4'))>tuple(c.astype('<f4'));f=b[ii[0]]if rev else b[ii[1]];f=min(knots.get(k) or [0.,1.],key=lambda x:abs(x-f));b[:]=0;b[ii[0]]=f if rev else 1-f;b[ii[1]]=1-f if rev else f
 return b
out=[[],[],[]];origins=[[],[],[]];report=[];newcounts=0
for sf,children in groups.items():
 orig=target[sf[0]][sf[1]];V=[np.eye(3)[i]for i in range(3)];lookup={tuple(orig[i,:3].astype('<f4')):i for i in range(3)};segments=[]
 def vertex(b):
  b=canon(b,orig);p=(b@orig[:,:3]).astype('<f4');k=tuple(p)
  if k not in lookup:lookup[k]=len(V);V.append(b)
  return lookup[k]
 # Original triangle boundary, expanded by globally shared edge knots.
 for i,j in [(0,1),(1,2),(2,0)]:
  a,c=orig[i,:3],orig[j,:3];k=key(a,c);rev=tuple(a.astype('<f4'))>tuple(c.astype('<f4'));chain=[]
  for f in sorted(knots.get(k,[0,1]),reverse=rev):
   b=np.zeros(3);b[i]=f if rev else 1-f;b[j]=1-f if rev else f;chain.append(vertex(b))
  segments.extend((a,b)for a,b in zip(chain[:-1],chain[1:])if a!=b)
 for m,t,bc in children:
  ids=[vertex(b)for b in bc]
  segments.extend((a,b)for a,b in zip(ids,np.roll(ids,-1))if a!=b)
 V=np.array(V);segments=np.unique(np.sort(np.array(segments),axis=1),axis=0)
 # Node crossings introduced by coalescing sub-Float32 chart-only constraints.
 lines=unary_union([set_precision(LineString(V[[a,b],1:]),1e-8)for a,b in segments]);parts=list(lines.geoms)if hasattr(lines,'geoms')else[lines];uv=[];segs=[];lk={}
 for line in parts:
  xy=np.array(line.coords)
  for a,b in zip(xy[:-1],xy[1:]):
   ids=[]
   for p in [a,b]:
    k=tuple(np.round(p,13))
    if k not in lk:lk[k]=len(uv);uv.append(p)
    ids.append(lk[k])
   if ids[0]!=ids[1]:segs.append(ids)
 uv=np.array(uv)
 # Coalesce chart-only near-collinearity before triangulation, measured in world
 # units. Keep exact target boundary vertices fixed. Grid noding otherwise makes
 # microscopically displaced points on one chart line into inverted F32 slivers.
 eps=float(np.spacing(np.abs(orig[:,:3]).astype('<f4')).max())
 for iteration in range(3):
  moved=False
  for a,b in sorted(segs,key=lambda e:-np.linalg.norm(uv[e[1]]-uv[e[0]])):
   d=uv[b]-uv[a];ll=d@d
   if ll<1e-24:continue
   fac=((uv-uv[a])@d)/ll;proj=uv[a]+fac[:,None]*d
   delta=(proj-uv)@(orig[1:,:3]-orig[0,:3]);dist=np.linalg.norm(delta,axis=1)
   boundary=(np.minimum.reduce([abs(uv[:,0]),abs(uv[:,1]),abs(1-uv.sum(1))])<1e-9)
   ids=np.flatnonzero((fac>1e-9)&(fac<1-1e-9)&(dist>1e-13)&(dist<eps*.55)&(~boundary))
   if len(ids):uv[ids]=proj[ids];moved=True
  if not moved:break
 splitsegs=[]
 for a,b in segs:
  d=uv[b]-uv[a];ll=d@d
  if ll<1e-24:continue
  fac=((uv-uv[a])@d)/ll;err=np.linalg.norm(uv-uv[a]-fac[:,None]*d,axis=1);ids=np.flatnonzero((fac>=-1e-10)&(fac<=1+1e-10)&(err<1e-7));ids=ids[np.argsort(fac[ids])];splitsegs.extend((i,j)for i,j in zip(ids[:-1],ids[1:])if i!=j)
 segs=np.unique(np.sort(np.array(splitsegs,dtype=int),axis=1),axis=0);(O/'progress.json').write_text(json.dumps({'source':[int(x)for x in sf],'vertices':len(uv),'segments':len(segs)}));np.savez(O/'current-pslg.npz',vertices=np.array(uv),segments=segs);result=triangle.triangulate(dict(vertices=np.array(uv),segments=segs),'pQ')
 if 'triangles'not in result:raise RuntimeError(('missing',sf))
 B=np.c_[1-result['vertices'].sum(1),result['vertices']];geom=(B@orig[:,:3]).astype('<f4').astype(float)
 # All old boundary endpoints are exact; shared knot geometry comes from canonical edge endpoints.
 for k,b in enumerate(B):
  iz=np.where(abs(b)<1e-8)[0]
  if len(iz)>=2:geom[k]=orig[b.argmax(),:3]
  elif len(iz)==1:
   ii=[i for i in range(3)if i!=iz[0]];a,c=orig[ii[0],:3],orig[ii[1],:3];ky=key(a,c);rev=tuple(a.astype('<f4'))>tuple(c.astype('<f4'));f=b[ii[0]]if rev else b[ii[1]];f=min(knots.get(ky,[f]),key=lambda x:abs(x-f));lo,hi=(c,a)if rev else(a,c);geom[k]=((1-f)*lo+f*hi).astype('<f4')
 childBC=np.array([c[2]for c in children]);A=childBC[:,0,1:];b=childBC[:,1,1:]-A;c=childBC[:,2,1:]-A;det=b[:,0]*c[:,1]-b[:,1]*c[:,0];det=np.where(abs(det)<1e-25,1e-25,det)
 for f in result['triangles']:
  bs=B[f];center=bs[:,1:].mean(0);d=center-A;x=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/det;y=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/det;bc=np.c_[1-x-y,x,y];good=np.where(bc.min(1)>=-1e-7)[0]
  if len(good):pick=good[0]
  else:pick=int(np.maximum(-bc,0).sum(1).argmin())
  m,t,oldbc=children[pick];d=bs[:,1:]-A[pick];x=(d[:,0]*c[pick,1]-d[:,1]*c[pick,0])/det[pick];y=(b[pick,0]*d[:,1]-b[pick,1]*d[:,0])/det[pick];interp=np.c_[1-x-y,x,y];tr=bs@orig;tr[:,:3]=geom[f];tr[:,6:]=interp@t[:,6:];gn=np.cross(tr[1,:3]-tr[0,:3],tr[2,:3]-tr[0,:3]);on=np.cross(orig[1,:3]-orig[0,:3],orig[2,:3]-orig[0,:3])
  if gn@on<0:tr=tr[[0,2,1]]
  if np.linalg.norm(gn)>0:out[m].append(tr);origins[m].append(sf)
 newcounts+=len(result['triangles'])
 if len(report)<5:report.append(dict(source=sf,raw=len(children),pslg=len(result['triangles'])))
# Apply identical new boundary knots to retained cut triangles only.
allout=[];boundary_records=[]
for m in range(3):
 old=np.load(D/f'outside-{m}.npz')['triangles'].astype('<f4').astype(float);outside=[]
 for t in old:
  po=[]
  for a,b in zip(t,np.roll(t,-1,axis=0)):
   po.append(a);ky=key(a[:3],b[:3]);rev=tuple(a[:3])>tuple(b[:3]);vals=knots.get(ky,[])
   for f in sorted(vals,reverse=rev):
    fac=1-f if rev else f
    if fac<=1e-8 or fac>=1-1e-8:continue
    q=a+(b-a)*fac;lo,hi=(b[:3],a[:3])if rev else(a[:3],b[:3]);q[:3]=((1-f)*lo+f*hi).astype('<f4');po.append(q);boundary_records.append((lo.copy(),hi.copy(),float(f),q[:3].copy()))
  if len(po)==3:outside.append(t)
  else:
   po=np.array(po);outside.extend(np.array([po.mean(0),a,b])for a,b in zip(po,np.roll(po,-1,axis=0)))
 new=np.array(out[m]).astype('<f4');p=new[:,:,:3].astype(float);valid=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)>0;new=new[valid];origin=np.array(origins[m])[valid];whole=np.concatenate([outside,new]).astype('<f4');p=whole[:,:,:3].astype(float);valid=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)>0;np.savez_compressed(O/f'new-patch-{m}.npz',triangles=new,sourceFace=origin);np.savez_compressed(O/f'round-cap-0-{m}.npz',triangles=whole[valid]);allout.append(whole[valid]);print(m,len(new),flush=True)
np.savez_compressed(O/'boundary-knots.npz',edges=np.array([[a,b]for a,b,f,p in boundary_records]),fraction=np.array([f for a,b,f,p in boundary_records]),points=np.array([p for a,b,f,p in boundary_records]));np.savez_compressed(O/'output.npz',triangles=np.concatenate(allout));(O/'pslg-report.json').write_text(json.dumps(dict(faces=newcounts,examples=report),indent=2,default=lambda x:x.item()))
