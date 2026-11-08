import numpy as np
from pathlib import Path
D=Path('strap-density-study');A=D/'end-shell-audit'
a=np.load(A/'interface-segment-attributes.npz')
profiles={}
for kind,name in [(0,'xcut_outer_profile-path'),(2,'bore-loop')]:
 q=np.load(A/f'{name}.npz');p=q['positions'];ids=q['sourceSegment'];p=np.vstack([p,p[0]])if kind==2 else p
 ss=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];ss/=ss[-1]
 uv=a['uv'][ids].copy();ep=a['positions'][ids];flip=np.linalg.norm(ep[:,0]-p[:-1],axis=1)>np.linalg.norm(ep[:,1]-p[:-1],axis=1);uv[flip]=uv[flip,::-1]
 grad=[]
 for pi,fi in a['sourcePrimitiveTriangle'][ids]:
  z=np.load(D/f'input-0-{pi}.npz');f=z['faces'][fi];t=z['positions'][f].astype(float);u=z['uv'][f].astype(float);g=np.linalg.lstsq(t[1:]-t[0],u[1:]-u[0],rcond=1e-12)[0];grad.append(g[0])
 grad=np.array(grad);seams=np.where(np.linalg.norm(uv[:-1,1]-uv[1:,0],axis=1)>1e-5)[0]+1;bounds=np.r_[0,seams,len(ids)]
 profiles[kind]=(ss,uv,grad,bounds,a['sourcePrimitiveTriangle'][ids,0])
bottom={}
for mi in [0,2]:
 ids=np.where((a['sourcePrimitiveTriangle'][:,0]==mi)&(abs(a['positions'][:,:,1]+3).max(1)<1e-8))[0];ep=a['positions'][ids];items=[]
 for eid,(pi,fi) in zip(ids,a['sourcePrimitiveTriangle'][ids]):
  z=np.load(D/f'input-0-{pi}.npz');f=z['faces'][fi];p=z['positions'][f].astype(float);u=z['uv'][f].astype(float);g=np.linalg.lstsq(p[1:]-p[0],u[1:]-u[0],rcond=1e-12)[0];items.append((p[0],u[0],g))
 bottom[mi]=(ep,items)
def map_uv(t,ps,kinds,mi):
 out=t.copy();reports=[]
 for i,(tri,s,kind) in enumerate(zip(t,ps,kinds)):
  if kind not in profiles or mi not in [0,2]:continue
  # Lower collar is seeded by its own source chart instead of extending an unrelated cut chart through it.
  onbottom=np.where(abs(tri[:,1]+3)<2e-7)[0]
  if kind==0 and (len(onbottom)>=2 or (tri[:,1].mean()+3 < tri[:,0].mean()-9.4)):
   ep,items=bottom[mi];center=tri[onbottom,:3].mean(0) if len(onbottom)>=2 else tri[:,:3].mean(0);d=ep[:,1]-ep[:,0];tau=np.clip(((center-ep[:,0])*d).sum(1)/np.maximum((d*d).sum(1),1e-30),0,1);dist=np.linalg.norm(center-ep[:,0]-tau[:,None]*d,axis=1);j=int(dist.argmin());p0,u0,g0=items[j];out[i,:,6:]=u0+(tri[:,:3]-p0)@g0;continue
  ss,uv,g,bounds,mats=profiles[kind];mid=float(s.mean());oncut=np.where(abs(tri[:,0]-9.4)<1e-7)[0]
  if len(oncut)>=2:mid=float(s[oncut].mean())
  ix=np.clip(np.searchsorted(ss,mid,side='right')-1,0,len(uv)-1);reg=np.clip(np.searchsorted(bounds,ix,side='right')-1,0,len(bounds)-2);lo,hi=bounds[reg],bounds[reg+1]-1
  for k in range(3):
   j=np.clip(np.searchsorted(ss,s[k],side='right')-1,lo,hi);fac=(s[k]-ss[j])/(ss[j+1]-ss[j]);base=uv[j,0]+fac*(uv[j,1]-uv[j,0]);out[i,k,6:]=base+(tri[k,0]-9.4)*g[j]
 return out
