import json,struct,numpy as np
from pathlib import Path
def load(path):
 b=Path(path).read_bytes();l=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+l]);buf=b[28+l:];pr=j['meshes'][0]['primitives'][0]
 def a(k):
  x=j['accessors'][k];v=j['bufferViews'][x['bufferView']];return np.frombuffer(buf,dtype={5126:'f4',5123:'u2',5125:'u4'}[x['componentType']],count=x['count']*{'VEC3':3,'VEC2':2,'VEC4':4,'SCALAR':1}[x['type']],offset=v.get('byteOffset',0)+x.get('byteOffset',0)).reshape(x['count'],-1)
 p=a(pr['attributes']['POSITION'])[:,[0,2,1]]*np.array([1,-1,1]); n=a(pr['attributes']['NORMAL'])[:,[0,2,1]]*np.array([1,-1,1]);return p,n,a(pr['indices']).reshape(-1,3)

A=20.55;B=21.45
base_load=load
def load(path):
 p,n,ix=base_load(path);b=Path(path).read_bytes();l=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+l]);buf=b[28+l:];pr=j['meshes'][0]['primitives'][0];a=j['accessors'][pr['attributes']['TEXCOORD_0']];v=j['bufferViews'][a['bufferView']];uv=np.frombuffer(buf,'f4',count=a['count']*2,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,2);return p,np.c_[n,uv],ix


def clip(p,n,ix,inside):
 ps=list(p);ns=list(n);faces=[];cache={}
 d=inside(p)
 for t in ix:
  dd=d[t]
  if (dd>=0).all():faces.append(t.tolist());continue
  if (dd<0).all():continue
  out=[]
  for u,v in zip(t,np.roll(t,-1)):
   if d[u]>=0:out.append(int(u))
   if (d[u]>=0)!=(d[v]>=0):
    key=tuple(sorted((int(u),int(v))))
    if key not in cache:
     # interpolate consistently from sorted edge
     u0,v0=key;r=d[u0]/(d[u0]-d[v0]);pt=p[u0]+r*(p[v0]-p[u0]);nr=n[u0]+r*(n[v0]-n[u0]);nr[:3]/=np.linalg.norm(nr[:3]);cache[key]=len(ps);ps.append(pt);ns.append(nr)
    out.append(cache[key])
  for k in range(1,len(out)-1):faces.append([out[0],out[k],out[k+1]])
 return np.array(ps),np.array(ns),np.array(faces)

def ring(p,y,sx,sy):
 ids=np.flatnonzero((abs(p[:,1]-sy*y)<1e-6)&(p[:,0]*sx>9))
 # collapse exact duplicate render vertices for boundary representation
 _,i=np.unique(np.round(p[ids],6),axis=0,return_index=True);ids=ids[i]
 center=np.array([sx*11.65,-.9]);v=p[ids][:,[0,2]]-center;theta=np.arctan2(v[:,1],v[:,0]);order=np.argsort(theta);return ids[order],theta[order],np.linalg.norm(v,axis=1)[order],center

def stitch(a,ta,b,tb):
 # closed zipper of angularly ordered rings, includes all boundary vertices
 out=[];ia=ib=0;na=len(a);nb=len(b)
 while ia<na or ib<nb:
  aa=ta[(ia+1)%na]+(2*np.pi if ia+1>=na else 0);bb=tb[(ib+1)%nb]+(2*np.pi if ib+1>=nb else 0)
  if ib>=nb or (ia<na and aa<bb):out.append([a[ia%na],a[(ia+1)%na],b[ib%nb]]);ia+=1
  else:out.append([a[ia%na],b[(ib+1)%nb],b[ib%nb]]);ib+=1
 return out

def periodic(t,r,tt):return np.interp(tt,np.r_[t[-1]-2*np.pi,t,t[0]+2*np.pi],np.r_[r[-1],r,r[0]])
p,n,ix=load('metal-recovery/live-case.glb');q,nn,ii=load('metal-recovery/default-case.glb');p,n,ix=clip(p,n,ix,lambda v:A-abs(v[:,1]));q,nn,ii=clip(q,nn,ii,lambda v:abs(v[:,1])-B)
# remove unreferenced, retaining render seams
ids=np.unique(ix);rev=np.full(len(p),-1);rev[ids]=np.arange(len(ids));p,n,ix=p[ids],n[ids],rev[ix]
ids=np.unique(ii);rev=np.full(len(q),-1);rev[ids]=np.arange(len(ids));q,nn,ii=q[ids],nn[ids],rev[ii]
P=list(p)+list(q);N=list(n)+list(nn);F=ix.tolist()+(ii+len(p)).tolist();proof=[]
for sy in [-1,1]:
 for sx in [-1,1]:
  ia,ta,ra,c=ring(p,A,sx,sy);ib,tb,rb,_=ring(q,B,sx,sy);ib+=len(p)
  # radial derivatives from endpoint normals: n_r dr/dy+n_y=0
  def slope(ids,t):
   nv=np.array(N)[ids,:3];rad=np.stack([np.cos(t),np.zeros(len(t)),np.sin(t)],axis=1);den=np.sum(nv*rad,axis=1);return -sy*nv[:,1]/np.where(abs(den)<1e-6,1e-6,den)
  da=slope(ia,ta);db=slope(ib,tb);tt=np.unique(np.r_[ta,tb]);ra1=periodic(ta,ra,tt);rb1=periodic(tb,rb,tt);da1=periodic(ta,da,tt);db1=periodic(tb,db,tt)
  prev=ia;tp=ta
  for step in range(1,12):
   t=step/12;L=B-A;r=(2*t**3-3*t**2+1)*ra1+(t**3-2*t**2+t)*L*da1+(-2*t**3+3*t**2)*rb1+(t**3-t**2)*L*db1
   points=np.stack([c[0]+r*np.cos(tt),np.full(len(tt),sy*(A+L*t)),c[1]+r*np.sin(tt)],axis=1)
   # derive smooth parametric normals using radial derivative in y and theta
   drdy=((6*t*t-6*t)*ra1+(3*t*t-4*t+1)*L*da1+(-6*t*t+6*t)*rb1+(3*t*t-2*t)*L*db1)/L
   drdt=np.gradient(r,tt);nv=np.stack([r*np.cos(tt)+drdt*np.sin(tt),-sy*r*drdy,r*np.sin(tt)-drdt*np.cos(tt)],axis=1);nv/=np.linalg.norm(nv,axis=1)[:,None]
   ids=np.arange(len(P),len(P)+len(points));P.extend(points);uv_a=np.array([periodic(ta,np.array(N)[ia,k],tt) for k in [3,4]]).T;uv_b=np.array([periodic(tb,np.array(N)[ib,k],tt) for k in [3,4]]).T;N.extend(np.c_[nv,(1-t)*uv_a+t*uv_b]);ff=stitch(prev,tp,ids,tt);F.extend(ff if sy>0 else [v[::-1] for v in ff]);prev=ids;tp=tt
  ff=stitch(prev,tp,ib,tb);F.extend(ff if sy>0 else [v[::-1] for v in ff]);proof.append({'sx':sx,'sy':sy,'sourceBoundary':len(ib),'r5Boundary':len(ia),'newRing':len(tt)})
P=np.array(P);N=np.array(N);F=np.array(F)
# fix bridge orientation by geometric normal dot interpolated normal only, not source faces
start=len(ix)+len(ii);t=P[F[start:]];cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);flip=np.sum(cross*N[F[start:],:3].mean(1),axis=1)<0;F[start:][flip]=F[start:][flip][:,::-1]
np.savez_compressed('metal-recovery/cap-study/hybrid-candidate.npz',position=P,normal=N[:,:3],uv=N[:,3:],index=F)
Path('metal-recovery/cap-study/graft-proof.json').write_text(json.dumps({'transitionY':[A,B],'triangles':len(F),'vertices':len(P),'rings':proof,'note':'Private feasibility mesh; UV preserved/interpolated, tangents omitted as original source; source tips beyond21.45 preserved, R5 roots below20.55 preserved; pending manifold checks.'},indent=2));print(proof,len(P),len(F))
