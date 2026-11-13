from pathlib import Path
import numpy as np,json,math
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
import mapbox_earcut
root=Path('mechanism-plates-qa');rows=json.load(open(root/'cap-loops.json'));cyls=json.load(open(root/'cylinders.json'));reports=[]
for row,crow in zip(rows,cyls):
 if row['sourceIndex']!=100:continue
 sid=row['sourceIndex'];d=Path('mechanism-planar-study')/str(sid);p=np.fromfile(d/'position.bin','f4').reshape(-1,3).astype('f8');norm=np.fromfile(d/'normal.bin','f4').reshape(-1,3).astype('f8');f=np.fromfile(d/'original-index.bin','u4').reshape(-1,3);q=p[f];vp,first,inv=np.unique(np.round(p,5),axis=0,return_index=True,return_inverse=True);exact=p[first];wf=inv[f]
 replacements={};remove=np.zeros(len(f),bool);generated=[];pairs=[]
 def emit(points,normals,faces):generated.append((np.array(points),np.array(normals),np.array(faces)))
 for pairIndex,pair in enumerate(crow['pairs']):
  
  if pairIndex!=7:continue
  a,b=dict(pair['a']),dict(pair['b']);a['y']=float(np.median(p[np.abs(p[:,1]-a['y'])<1e-5,1]));b['y']=float(np.median(p[np.abs(p[:,1]-b['y'])<1e-5,1]));r=(a['radius']+b['radius'])/2;n=a['vertices'];assert n==b['vertices']
  center=(np.array(a['center'])+b['center'])/2;circle=exact[a['ids']][:,[0,2]];circle=circle[np.argsort(np.arctan2(circle[:,1]-center[1],circle[:,0]-center[0]))];circleRad= circle-center;circleRad/=np.linalg.norm(circleRad,axis=1)[:,None];theta=np.arctan2(circleRad[:,1],circleRad[:,0]);assert np.array_equal(np.sort(circle,axis=0),np.sort(exact[b['ids']][:,[0,2]],axis=0))
  width=.025 if pairIndex==7 else 0.
  for loop in [a,b]:replacements[tuple(sorted(loop['ids']))]=circle+circleRad*width
  rad=np.column_stack([np.cos(theta),np.zeros(n),np.sin(theta)]);sample=np.unique(f[pair['faces']]);rr=p[sample].copy();rr[:,0]-=center[0];rr[:,2]-=center[1];rr[:,1]=0;sign=np.sign(np.sum(norm[sample]*rr));assert sign==-1
  if width:
   # Explicit inner quarter-rounds remove material; no bore constriction and no blanket modifier.
   # Endpoints have exactly cap and bore normals; retain minimum mid-wall radius and axial bounds.
   profiles=[]
   for t in np.linspace(0,np.pi/2,4):profiles.append((r+width-width*np.sin(t),a['y']+width-width*np.cos(t),-np.sin(t),-np.cos(t)))
   for t in np.linspace(np.pi/2,0,4):profiles.append((r+width-width*np.sin(t),b['y']-width+width*np.cos(t),-np.sin(t),np.cos(t)))
  else:profiles=[(r,a['y'],-1,0),(r,b['y'],-1,0)]
  points=[];normals=[]
  for radius,y,nr,ny in profiles:
   points.extend(np.column_stack([(circle+circleRad*(radius-r))[:,0],np.full(n,y),(circle+circleRad*(radius-r))[:,1]]));normals.extend([[nr*np.cos(t),ny,nr*np.sin(t)]for t in theta])
  points=np.array(points);normals=np.array(normals);faces=[]
  for rowIndex in range(len(profiles)-1):
   for i in range(n):
    j=(i+1)%n;u=rowIndex*n;v=(rowIndex+1)*n;faces.extend([[u+i,u+j,v+j],[u+i,v+j,v+i]])
  faces=np.array(faces);cross=np.cross(points[faces[:,1]]-points[faces[:,0]],points[faces[:,2]]-points[faces[:,0]]);dot=(cross*normals[faces[:,0]]).sum(1);faces[dot<0]=faces[dot<0][:,[0,2,1]];emit(points,normals,faces);remove[pair['faces']]=True;pairs.append(dict(center=center.tolist(),radius=r,depths=[a['y'],b['y']],before=a['vertices'],after=n,chordError=r*(1-math.cos(math.pi/n)),bevelWidth=width,bevelSegments=3 if width else 0))
 for cap in row['caps']:
  if not any(tuple(sorted(l['ids']))in replacements for l in cap['loops']):continue
  y=float(np.median(p[np.abs(p[:,1]-cap['y'])<1e-5,1]));normalCross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);mask=np.all(np.abs(q[:,:,1]-y)<1e-5,axis=1)&(normalCross[:,1]*cap['orientation']>1e-12);cf=f[mask];cross=np.cross(q[mask,1]-q[mask,0],q[mask,2]-q[mask,0]);sign=np.sign(cross[:,1].sum());assert np.all(sign*cross[:,1]>-1e-10)
  loops=[replacements.get(tuple(sorted(l['ids'])),exact[l['ids']][:,[0,2]])for l in cap['loops']];polys=[Polygon(x)for x in loops];parents=[]
  for i,poly in enumerate(polys):
   candidates=[j for j,p2 in enumerate(polys)if j!=i and p2.area>poly.area and p2.covers(poly.representative_point())];parents.append(min(candidates,key=lambda j:polys[j].area)if candidates else None)
  def depth(i):return 0 if parents[i]is None else 1+depth(parents[i])
  for i,loop in enumerate(loops):
   if depth(i)%2:continue
   rings=[loop]+[loops[j]for j in range(len(loops))if parents[j]==i];xz=np.concatenate(rings);ends=np.cumsum([len(x)for x in rings]).astype('u4');lookup={tuple(v):i for i,v in enumerate(xz)};dt=constrained_delaunay_triangles(Polygon(rings[0],rings[1:]));faces=np.array([[lookup[tuple(v)] for v in np.array(t.exterior.coords)[:3]] for t in dt.geoms]);points=np.column_stack([xz[:,0],np.full(len(xz),y),xz[:,1]]);normals=np.tile([0,sign,0],(len(xz),1));c=np.cross(points[faces[:,1]]-points[faces[:,0]],points[faces[:,2]]-points[faces[:,0]]);faces[c[:,1]*sign<0]=faces[c[:,1]*sign<0][:,[0,2,1]];emit(points,normals,faces)
  remove[mask]=True
 parts=[(p,norm,f[~remove])]+generated;pp=[];nn=[];ff=[];off=0
 for a,b,c in parts:pp.append(a);nn.append(b);ff.append(c+off);off+=len(a)
 pp=np.concatenate(pp).astype('f4');nn=np.concatenate(nn).astype('f4');ff=np.concatenate(ff).astype('u4');used=np.unique(ff);remap=np.zeros(len(pp),'u4');remap[used]=np.arange(len(used));ff=remap[ff];pp=pp[used];nn=nn[used];_,first,inv=np.unique(np.concatenate([pp,nn],axis=1),axis=0,return_index=True,return_inverse=True);pp=pp[first];nn=nn[first];ff=inv[ff].astype('u4')
 def topology(p,f):
  _,v=np.unique(np.round(p.astype('f8'),5),axis=0,return_inverse=True);t=v[f];e=np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]),axis=1);_,n=np.unique(e,axis=0,return_counts=True);return {'boundaryEdges':int((n==1).sum()),'nonmanifoldEdges':int((n>2).sum())}
 before=topology(p,f);after=topology(pp,ff);out=root/'source-preserving-front-bevel'/str(sid);out.mkdir(parents=True,exist_ok=True);pp.tofile(out/'position.bin');nn.tofile(out/'normal.bin');ff.tofile(out/'index.bin');report=dict(sourceIndex=sid,trianglesBefore=len(f),trianglesAfter=len(ff),beforeTopology=before,afterTopology=after,analyticBores=pairs);reports.append(report);print(sid,len(f),len(ff),before,after)
(root/'source-preserving-front-bevel-report.json').write_text(json.dumps(reports,indent=2))
