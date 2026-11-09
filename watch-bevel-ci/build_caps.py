import numpy as np, json
from scipy.interpolate import CubicHermiteSpline,CubicSpline
from pathlib import Path
D=np.load('watch-bevel/baseline.npz');P,N,UV,F=[D[x].copy().astype(float if x!='index' else int) for x in ['position','normal','uv','index']]
# Keep source below shoulder transition. Shared clipped edge intersections are cached.
cut=23.8; radi=.30; top=24.30000114440918
ps=list(P);ns=list(N);uvs=list(UV);out=[];cache={}; d=cut-np.abs(P[:,2])
for f in F:
 if (d[f]>=0).all():out.append(f.tolist());continue
 if (d[f]<0).all():continue
 poly=[]
 for u,v in zip(f,np.roll(f,-1)):
  if d[u]>=0:poly.append(int(u))
  if (d[u]>=0)!=(d[v]>=0):
   key=tuple(sorted((int(u),int(v))))
   if key not in cache:
    u,v=key;t=d[u]/(d[u]-d[v]);p=P[u]+t*(P[v]-P[u]);n=N[u]+t*(N[v]-N[u]);n/=np.linalg.norm(n);cache[key]=len(ps);ps.append(p);ns.append(n);uvs.append(UV[u]+t*(UV[v]-UV[u]))
   poly.append(cache[key])
 for k in range(1,len(poly)-1):out.append([poly[0],poly[k],poly[k+1]])
P0=np.array(ps);N0=np.array(ns);U0=np.array(uvs);source_count=len(out)
def order(ids):
 c=P0[ids,:2].mean(0);t=np.arctan2(P0[ids,1]-c[1],P0[ids,0]-c[0]);ii=np.argsort(t);return ids[ii],t[ii],c
def periodic(t,v,q):return np.stack([np.interp(q,np.r_[t[-1]-2*np.pi,t,t[0]+2*np.pi],np.r_[v[-1,k],v[:,k],v[0,k]]) for k in range(v.shape[1])],1)
def zipper(a,ta,b,tb):
 out=[];i=j=0
 while i<len(a) or j<len(b):
  aa=ta[(i+1)%len(a)]+(2*np.pi if i+1>=len(a) else 0);bb=tb[(j+1)%len(b)]+(2*np.pi if j+1>=len(b) else 0)
  if j>=len(b) or (i<len(a) and aa<bb):out.append([a[i%len(a)],a[(i+1)%len(a)],b[j%len(b)]]);i+=1
  else:out.append([a[i%len(a)],b[(j+1)%len(b)],b[j%len(b)]]);j+=1
 return out
stats=[]
for sz in [-1,1]:
 for sx in [-1,1]:
  ids=np.flatnonzero((abs(P0[:,2]-sz*cut)<1e-6)&(P0[:,0]*sx>9));_,un=np.unique(np.round(P0[ids],6),axis=0,return_index=True);ids=ids[un];ids,tt,c=order(ids)
  shoulder=np.flatnonzero((abs(P[:,2]-sz*24.150001525878906)<1e-5)&(P[:,0]*sx>9));shoulder,ts,cs=order(shoulder)
  # Smooth radial interpolation of authored shoulder profile with its normals.
  q=np.linspace(-np.pi,np.pi,64,endpoint=False);v=P[shoulder,:2]-cs;r=np.linalg.norm(v,axis=1);n=N[shoulder];xy=n[:,:2];xy/=np.linalg.norm(xy,axis=1)[:,None]
  tangent=np.c_[-np.sin(ts),np.cos(ts)];rad=np.c_[np.cos(ts),np.sin(ts)];dr=-r*np.sum(xy*tangent,axis=1)/np.sum(xy*rad,axis=1)
  tq=np.r_[ts,ts[0]+2*np.pi];query=(q-ts[0])%(2*np.pi)+ts[0];rs=CubicHermiteSpline(tq,np.r_[r,r[0]],np.r_[dr,dr[0]])
  rr,rd=rs(query),rs(query,1);rays=np.c_[np.cos(q),np.sin(q)];tans=np.c_[-np.sin(q),np.cos(q)];dir=rr[:,None]*rays-rd[:,None]*tans;dir/=np.linalg.norm(dir,axis=1)[:,None]
  sh=cs+rr[:,None]*rays;nn=periodic(ts,N[shoulder],q);nn/=np.linalg.norm(nn,axis=1)[:,None];nz=sz*nn[:,2];alpha=np.arcsin(nz);slope=-nz/np.sqrt(1-nz*nz);zstart=top-radi+radi*nz
  sh+=((zstart-24.150001525878906)*slope)[:,None]*dir;cent=sh-radi*np.cos(alpha)[:,None]*dir
  start=np.c_[sh,sz*zstart];sn=np.c_[np.cos(alpha)[:,None]*dir,sz*nz];uv=periodic(ts,UV[shoulder],q)
  # C1 Hermite bridge from exact cut ring to new fillet shoulder.
  lo=periodic(tt,P0[ids],q);ln=periodic(tt,N0[ids],q);luv=periodic(tt,U0[ids],q);lo[:,2]=sz*cut
  prev=ids;tp=tt
  for k in range(1,5):
   t=k/4;L=zstart-cut;lo_slope=-sz*ln[:,2,None]*ln[:,:2]/np.sum(ln[:,:2]**2,axis=1)[:,None];hi_slope=slope[:,None]*dir
   xy=(2*t**3-3*t*t+1)*lo[:,:2]+(t**3-2*t*t+t)*L[:,None]*lo_slope+(-2*t**3+3*t*t)*start[:,:2]+(t**3-t*t)*L[:,None]*hi_slope
   pos=np.c_[xy,sz*(cut+t*L)];norm=(1-t)*ln+t*sn;norm/=np.linalg.norm(norm,axis=1)[:,None];new=np.arange(len(ps),len(ps)+len(q));ps.extend(pos);ns.extend(norm);uvs.extend((1-t)*luv+t*uv);out.extend(zipper(prev,tp,new,q));prev=new;tp=q
  for k in range(1,9):
   f=k/8;ang=alpha+f*(np.pi/2-alpha);pos=np.c_[cent+radi*np.cos(ang)[:,None]*dir,sz*(top-radi+radi*np.sin(ang))];norm=np.c_[np.cos(ang)[:,None]*dir,sz*np.sin(ang)];new=np.arange(len(ps),len(ps)+len(q));ps.extend(pos);ns.extend(norm);uvs.extend(uv);out.extend(zipper(prev,tp,new,q));prev=new;tp=q
  center=len(ps);ps.append(np.mean(np.array(ps)[prev],axis=0));ns.append([0,0,sz]);uvs.append(np.mean(uv,axis=0))
  for a,b in zip(prev,np.roll(prev,-1)):out.append([int(a),int(b),center])
  stats.append({'sx':sx,'sz':sz,'cutBoundary':len(ids),'rings':12,'ringVertices':64})
P,N,UV,F=np.array(ps),np.array(ns),np.array(uvs),np.array(out);tri=P[F[source_count:]];fl=np.sum(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])*N[F[source_count:]].mean(1),axis=1)<0;F[source_count:][fl]=F[source_count:][fl][:,::-1]
ids=np.unique(F);rev=np.full(len(P),-1);rev[ids]=np.arange(len(ids));P,N,UV,F=P[ids],N[ids],UV[ids],rev[F]
np.savez('watch-bevel/wide-cap.npz',position=P.astype('f4'),normal=N.astype('f4'),uv=UV.astype('f4'),index=F.astype('u4'));print(json.dumps({'triangles':len(F),'vertices':len(P),'radius':radi,'caps':stats},indent=2))
