import sys,json,numpy as np
sys.path.insert(0,'/tmp/strap-remesh-deps')
from pathlib import Path
from scipy.spatial import cKDTree
from shapely.geometry import Polygon
import triangle
D=Path('strap-density-study');A=D/'end-shell-audit';O=D/'shell/ordered-v9';O.mkdir(exist_ok=True)
outer=np.load(A/'xcut_outer_profile-path.npz');p=outer['positions'];seg=outer['sourcePrimitiveTriangle'][:,0];L=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];S=L/L[-1]
bot=np.load(A/'bottom_attachment-path.npz')['positions'];bo=bot[24:][::-1];bi=bot[:17];bc=bot[16:25][::-1]
def param(q):return np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]/np.linalg.norm(np.diff(q,axis=0),axis=1).sum()
Uo=param(bo);Ui=param(bi)
def interp(t,v,q):return np.stack([np.interp(t,v,q[:,i])for i in range(q.shape[1])],-1)
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
# Adaptive contour sample keeps every material seam; original first-row knots retained.
ss=np.unique(np.r_[np.linspace(0,1,97),S[np.r_[False,np.diff(seg)!=0,False]]])
us=np.array([0,.12,.30,.52,.72,.88,1])
tris=[];mats=[];boundary=[]
def add(a,b,c,mat):
 t=np.array([a,b,c]);
 if np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))>1e-13:tris.append(t);mats.append(int(mat))
def stitch(a,sa,b,sb,material):
 i=j=0
 while i<len(a)-1 or j<len(b)-1:
  if j==len(b)-1 or (i<len(a)-1 and sa[i+1]<=sb[j+1]):add(a[i],a[i+1],b[j],material((sa[i]+sa[i+1]+sb[j])/3));i+=1
  else:add(a[i],b[j+1],b[j],material((sa[i]+sb[j]+sb[j+1])/3));j+=1
# Source section keeps the cylindrical roll; lower tangent legs follow exact bottom-cut paths.
from goal_profile import goal_at
from height_field import source_x
def surface(u,s):
 cut=interp(s,S,p);goal=goal_at(cut);goal[0]=bo[-1];goal[-1]=bi[-1];q=cut*(1-u)+goal*u;w=smooth((-cut[:,1]-2.4)/.6);side=s<.5;bottom=np.where(side[:,None],interp(np.full(len(s),u),Uo,bo),interp(np.full(len(s),u),Ui,bi));start=np.where(side[:,None],bo[0],bi[0]);end=np.where(side[:,None],bo[-1],bi[-1]);linear=start*(1-u)+end*u;q+=w[:,None]*(bottom-linear);return q
prev=p;prevs=S
for u in us[1:]:
 row=surface(u,ss);stitch(prev,prevs,row,ss,lambda s:seg[min(np.searchsorted(S,s,side='right')-1,len(seg)-1)]);prev,prevs=row,ss
# Round edge: ellipse in cap-normal/cross-section-normal plane, eight segments.
end=prev.copy();tangent=np.gradient(end[:,1:],ss,axis=0);norm=np.stack([-tangent[:,1],tangent[:,0]],1);norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-20)
# Choose inward normal towards the roll center for upper arc.
ix=np.argmax(end[:,1]);
if np.dot(norm[ix],np.array([-.95,-22.4])-end[ix,1:])<0:norm=-norm
w=smooth((end[:,1]+2.0)/.30);width=.04*w
# Flat cap away from preserved bottom attachment collar.
def capx(y,z):
 order=np.argsort(bc[:,2]);b=np.interp(z,bc[order,2],bc[order,0]);ww=smooth((y+3)/.35);base=b*(1-ww)+9.975*ww;w=smooth((-y-2.15)/.30);return base*(1-w)+source_x(y,z,base)*w
for theta in np.linspace(0,np.pi/2,9)[1:]:
 row=end.copy();row[:,1:]+=norm*width[:,None]*(1-np.cos(theta));row[:,0]+= (capx(row[:,1],row[:,2])-end[:,0])*np.sin(theta)*w;stitch(prev,ss,row,ss,lambda s:1);prev=row
outerCore=prev.copy()
# Bore wall and its small inner return. Preserve original circle boundary and material seams.
bq=np.load(A/'bore-loop.npz');bp=bq['positions'];tags=bq['sourcePrimitiveTriangle'][:,0];bp=np.vstack([bp,bp[0]]);BS=param(bp);bbb=np.unique(np.r_[np.linspace(0,1,65),BS[np.r_[False,np.diff(tags)!=0,False]]]);cur=bp;curS=BS
for x in [9.65,9.90,9.95]:
 row=interp(bbb,BS,bp);row[:,0]=x;stitch(row,bbb,cur,curS,lambda s:tags[min(np.searchsorted(BS,s,side='right')-1,len(tags)-1)]);cur,curS=row,bbb
base=cur.copy();rad=base[:,1:]-[-.95,-22.4];rad/=np.linalg.norm(rad,axis=1,keepdims=True)
for th in np.linspace(0,np.pi/2,9)[1:]:
 row=base.copy();row[:,0]=9.95+.025*np.sin(th);row[:,1:]+=rad*.025*(1-np.cos(th));stitch(row,bbb,cur,bbb,lambda s:1);cur=row
boreCore=cur[:-1]
# Constrained cap core, exact bottom material boundary, with reconstructed flat leather island.
outline=np.vstack([outerCore,bc[1:-1][::-1]])
pol=Polygon(outline[:,1:]);print('outline',pol.is_valid,pol.area)
if not pol.is_valid:
 from shapely.validation import explain_validity
 print(explain_validity(pol));np.save(O/'outline.npy',outline);raise RuntimeError('Cap outline self-intersection')
isrc=np.load(A/'paint-island-boundary.npz')['positions'];island=np.array(Polygon(isrc[:,1:]).convex_hull.exterior.coords)[:-1];ip=np.c_[capx(island[:,0],island[:,1]),island]
loops=[outline,boreCore,ip];vertices=[];segments=[];holes=[]
for k,loop in enumerate(loops):
 off=len(vertices);vertices.extend(loop[:,1:].tolist());segments.extend([[off+i,off+(i+1)%len(loop)]for i in range(len(loop))]);
 if k:holes.append(list(Polygon(loop[:,1:]).representative_point().coords)[0])
from shapely.geometry import Point
domain=Polygon(outline[:,1:],[boreCore[:,1:],ip[:,1:]])
for yy in np.arange(-2.96,-2.10,.08):
 for zz in np.arange(-24.2,-20.6,.08):
  if domain.contains(Point(yy,zz)):vertices.append([yy,zz])
tt=triangle.triangulate(dict(vertices=np.array(vertices),segments=np.array(segments),holes=np.array(holes)),'pYa.05q20');v2=tt['vertices'];v3=np.c_[capx(v2[:,0],v2[:,1]),v2];v3[:sum(map(len,loops))]=np.vstack(loops)
for f in tt['triangles']:add(*v3[f],1)
it=triangle.triangulate(dict(vertices=island,segments=np.array([[i,(i+1)%len(island)]for i in range(len(island))])),'pY')
for f in it['triangles']:add(*ip[f],0)
T=np.array(tris);M=np.array(mats);np.savez_compressed(O/'raw.npz',triangles=T,materials=M);json.dump(dict(new_faces=len(T),per_primitive=[int((M==i).sum())for i in range(3)],outer_rows=len(us),boundary_retained=True,cap_island='source material0 retained on planar convex chart; microscopic fold removed'),open(O/'report.json','w'),indent=2);print(len(T),np.bincount(M))
