import sys;sys.path.insert(0,'/tmp/case-topology-deps');sys.path.insert(0,'/tmp/marked-py')
import numpy as np,json,triangle,trimesh
from scipy.interpolate import PchipInterpolator
P='case-topology-lane/opposite-negative/'
p=np.fromfile(P+'current/position.bin',np.float32).reshape(-1,3);n=np.fromfile(P+'current/normal.bin',np.float32).reshape(-1,3);uv=np.fromfile(P+'current/uv.bin',np.float32).reshape(-1,2);idx=np.fromfile(P+'current/index.bin',np.uint32).reshape(-1,3);l=np.load(P+'labels.npy');a=np.mod(np.arctan2(p[:,2],p[:,0]),2*np.pi);m=(l==0)&(a>=330*np.pi/180)&(a<=355*np.pi/180);selected=m[idx].all(1);srcidx=idx[selected]
ed=np.sort(srcidx[:,[0,1,1,2,2,0]].reshape(-1,2),axis=1);edges,c=np.unique(ed,axis=0,return_counts=True);boundary=edges[c==1];bv=np.unique(boundary);lut={int(v):i for i,v in enumerate(bv)};segments=[[lut[int(x)],lut[int(y)]] for x,y in boundary]
# Use source UV as exact surface parameter. Cut boundaries retain original indices/attributes.
mer=np.where((l==0)&(p[:,0]<0)&(abs(p[:,2])<1e-5))[0];mer=mer[np.argsort(uv[mer,1])];t=uv[mer,1];keep=np.r_[True,np.diff(t)>1e-7];mer=mer[keep];t=t[keep]
fr=PchipInterpolator(t,-p[mer,0]);fy=PchipInterpolator(t,p[mer,1]);fnx=PchipInterpolator(t,-n[mer,0]);fny=PchipInterpolator(t,n[mer,1]);dense=np.linspace(0,1,10001);curve=np.c_[fr(dense),fy(dense)];norm=np.c_[fnx(dense),fny(dense)];norm/=np.linalg.norm(norm,axis=1)[:,None]
knots=[0,len(dense)-1]
while True:
 add=[]
 for j,k in zip(knots[:-1],knots[1:]):
  f=(dense[j:k+1]-dense[j])/(dense[k]-dense[j]);chord=curve[j]+f[:,None]*(curve[k]-curve[j]);nn=norm[j]+f[:,None]*(norm[k]-norm[j]);nn/=np.linalg.norm(nn,axis=1)[:,None];err=np.linalg.norm(curve[j:k+1]-chord,axis=1)/.001;ne=np.degrees(np.arccos(np.clip(np.sum(norm[j:k+1]*nn,axis=1),-1,1)))/.12;e=np.maximum(err,ne);h=int(e.argmax())
  if e[h]>1:add.append(j+h)
 if not add:break
 knots=sorted(knots+add)
# Keep narrow boundary collar; unlike isolated proof, full patch boundary is exact.
us=np.linspace(uv[bv,0].max()-(uv[bv,0].max()-uv[bv,0].min())+.008,uv[bv,0].max()-.008,33);vs=np.unique(np.r_[.002,dense[knots][(dense[knots]>.002)&(dense[knots]<.998)],.998]);grid=np.array([[u,v]for v in vs for u in us]);off=len(bv);nu=len(us)
for j in range(len(vs)):
 for k in range(nu-1):segments.append([off+j*nu+k,off+j*nu+k+1])
for j in range(len(vs)-1):
 for k in range(nu):segments.append([off+j*nu+k,off+(j+1)*nu+k])
regions=[[float((us[k]+us[k+1])/2),float((vs[j]+vs[j+1])/2),1,1] for j in range(len(vs)-1)for k in range(nu-1)];regions.append([float((uv[bv,0].min()+us[0])/2),.5,2,.000004]);vertices=np.r_[uv[bv],grid];result=triangle.triangulate(dict(vertices=vertices,segments=np.array(segments),regions=np.array(regions)),'pYaQ');quv=result['vertices'];tri=result['triangles']
uvnew=quv[off:];ang=(1-uvnew[:,0])*2*np.pi;v=uvnew[:,1];rn=fr(v);pn=np.c_[rn*np.cos(ang),fy(v),rn*np.sin(ang)];nx=fnx(v);ny=fny(v);nn=np.c_[nx*np.cos(ang),ny,nx*np.sin(ang)];nn/=np.linalg.norm(nn,axis=1)[:,None]
source=trimesh.Trimesh(p,srcidx,process=False);near,dist,tid=trimesh.proximity.closest_point(source,pn);weights=trimesh.triangles.points_to_barycentric(source.triangles[tid],near);nn=(n[srcidx[tid]]*weights[:,:,None]).sum(1);nn/=np.linalg.norm(nn,axis=1)[:,None]
pp=np.r_[p,pn].astype('f4');nn=np.r_[n,nn].astype('f4');uu=np.r_[uv,uvnew].astype('f4');mapping=np.r_[bv,np.arange(len(p),len(pp))];newtri=mapping[tri]
# Orient by transferred source normals.
q=pp[newtri];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);good=np.sum(fn*nn[newtri].mean(1),axis=1)>0;newtri[~good]=newtri[~good][:,[0,2,1]]
ii=np.r_[idx[~selected],newtri].astype('u4');used=np.unique(ii);remap=np.full(len(pp),-1);remap[used]=np.arange(len(used));out=P+'integrated';import os;os.makedirs(out,exist_ok=True)
for name,arr in [('position',pp[used]),('normal',nn[used]),('uv',uu[used]),('index',remap[ii].astype('u4'))]:arr.tofile(out+'/'+name+'.bin')
np.savez(P+'integration-proof-data.npz',boundary=bv,selected=selected,newtri=newtri,position=pp,normal=nn,uv=uu)
report=dict(beforeTriangles=len(idx),afterTriangles=len(ii),removedTriangles=len(srcidx),replacementTriangles=len(newtri),profileRows=len(vs),angularColumns=nu,exactBoundaryVertices=len(bv),sourceOutsideTrianglesByteExact=True,sourceBoundaryAttributesByteExact=True,uvMethod='exact source cylinder chart, adaptive meridian reconstruction',status='unpublished candidate; manifold/distance/shading QA pending')
open(P+'integrated-report.json','w').write(json.dumps(report,indent=2));print(report)
