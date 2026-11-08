import os
import numpy as np,json,hashlib
from pathlib import Path
D=Path(os.environ['STRAP_STUDY_DIR']); X=9.9604301; R0=1.5804276; R=.04; CY=-.95;CZ=-22.4
# Bounded quarter-round at exposed upper-right leather roll end. Bore untouched.
def deform(p):
 p=np.asarray(p,dtype=float);o=p.copy(); y=p[...,1]-CY;z=p[...,2]-CZ;r=np.hypot(y,z);a=np.abs(np.arctan2(z,y));t=np.clip((np.deg2rad(75)-a)/np.deg2rad(30),0,1);w=t*t*(3-2*t);rad=R*w;u=X-p[...,0];v=R0-r;aa=rad-u;bb=rad-v;d=np.hypot(aa,bb);mask=(rad>1e-8)&(u>=-2e-5)&(v>=-2e-5)&(aa>0)&(bb>0)&(d>rad)
 factor=np.where(mask,rad/np.maximum(d,1e-30),1);nx=X-rad+aa*factor;nr=R0-rad+bb*factor;o[...,0]=np.where(mask,nx,p[...,0]);o[...,1]=np.where(mask,CY+y*nr/np.maximum(r,1e-30),p[...,1]);o[...,2]=np.where(mask,CZ+z*nr/np.maximum(r,1e-30),p[...,2]);return o

def cut(poly,fn,value):
 vals=np.array([fn(v[:3])-value for v in poly]);
 if vals.min()>=-1e-10 or vals.max()<=1e-10:return [poly]
 sides=[[],[]]
 for i,a in enumerate(poly):
  b=poly[(i+1)%len(poly)];va=vals[i];vb=vals[(i+1)%len(poly)];
  for si in [0,1]:
   if (va>=-1e-10 if si else va<=1e-10):sides[si].append(a)
  if va*vb< -1e-20:
   # Scalar linear interpolation makes cut consistent across source neighbours.
   q=a+(b-a)*(va/(va-vb));sides[0].append(q);sides[1].append(q)
 return [np.array(s)for s in sides if len(s)>=3]
reports=[]
for pi in range(3):
 q=np.load(D/f'input-0-{pi}.npz');A=np.c_[q['positions'],q['normals'],q['uv']].astype(float);T=A[q['faces']];allout=[];sourceids=[];affected=0
 for sourceid,rawtri in enumerate(T):
  tri=np.c_[rawtri,np.eye(3)];p=tri[:,:3];rr=np.hypot(p[:,1]-CY,p[:,2]-CZ)
  hit=(p[:,0].max()>X-R-1e-4 and p[:,0].min()<X+2e-5 and rr.max()>R0-.13-1e-4 and rr.min()<R0+1e-4 and p[:,1].max()>CY and p[:,2].min()<CZ+R0 and p[:,2].max()>CZ-R0)
  if not hit:allout.append(tri);sourceids.append(sourceid);continue
  polys=[tri]; untouched=[]
  # Local normal field transition is explicitly sampled, not smeared over long source triangles.
  for fn,vals in [(lambda p:p[0],[9.60,9.68,9.76,9.84,9.90]),(lambda p:np.hypot(p[1]-CY,p[2]-CZ),[R0-.13,R0-.10,R0-.07])]:
   for val in vals:polys=[s for poly in polys for s in cut(poly,fn,val)]
  # Trim scope first; never subdivide the long unaffected body span.
  for fn,val in [(lambda p:p[0],X-R),(lambda p:np.hypot(p[1]-CY,p[2]-CZ),R0-R)]:
   pieces=[s for poly in polys for s in cut(poly,fn,val)];polys=[]
   for poly in pieces:
    if fn(poly[:,:3].mean(0))<val-1e-10:untouched.append(poly)
    else:polys.append(poly)
  # One arc parameter across both legs, not a Cartesian 8x8 cell grid.
  fn=lambda p:(p[0]-X)+(R0-np.hypot(p[1]-CY,p[2]-CZ))
  for val in np.linspace(-R,R,9)[1:-1]:polys=[s for poly in polys for s in cut(poly,fn,val)]
  polys+=untouched
  affected+=1
  for poly in polys:
   for k in range(1,len(poly)-1):
    t=poly[[0,k,k+1]].copy();orig=t[:,:3].copy();new=deform(orig);t[:,:3]=new
    for vi in range(3):
     yy=new[vi,1]-CY;zz=new[vi,2]-CZ;rr=np.hypot(yy,zz);angle=abs(np.arctan2(zz,yy));taper=np.clip((np.deg2rad(75)-angle)/np.deg2rad(30),0,1);aw=taper*taper*(3-2*taper);rad=R*aw
     xx=np.clip((orig[vi,0]-9.60)/(X-R-9.60),0,1);xx=xx*xx*(3-2*xx);rw=np.clip((rr-(R0-.13))/.09,0,1);rw=rw*rw*(3-2*rw);weight=xx*rw*aw
     if weight<1e-12:continue
     nx=max(0,new[vi,0]-(X-rad));nr=max(0,rr-(R0-rad))
     if np.hypot(nx,nr)<1e-9:continue
     nn=np.array([nx,nr*yy/rr,nr*zz/rr]);nn/=max(np.linalg.norm(nn),1e-30);n=t[vi,3:6];n/=max(np.linalg.norm(n),1e-30);nn=n*(1-weight)+nn*weight;nn/=max(np.linalg.norm(nn),1e-30);t[vi,3:6]=nn
    if np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))>1e-15:allout.append(t);sourceids.append(sourceid)
 O=np.array(allout).astype('<f4'); fp=O[:,:,:3].astype(float); valid=np.linalg.norm(np.cross(fp[:,1]-fp[:,0],fp[:,2]-fp[:,0]),axis=1)>0; O=O[valid];np.savez_compressed(D/f'round-cap-0-{pi}.npz',triangles=O[:,:,:8],barycentric=O[:,:,8:],source_faces=np.array(sourceids)[valid]);r=dict(primitive=pi,source_faces=len(T),candidate_faces=len(O),source_faces_subdivided=affected,max_radius_mm=R,angular_full_radius_degrees=45,angular_taper_end_degrees=75);reports.append(r);print(r,flush=True)
json.dump(reports,open(D/'round-cap-report.json','w'),indent=2)
