"""Private source-barycentric dual-end subtraction; append disjoint own-source patches."""
import numpy as np,json,hashlib
from pathlib import Path
D=Path('strap-density-study').resolve();O=D/'combined-uv-v11';O.mkdir(exist_ok=True)
# Existing robust per-source polygon merge/ear clipping routines, no source mutation.
ns={};exec((D/'end-shell-audit/export_interfaces.py').read_text().split('reports=[]')[0],ns)
clip,merge,triangulate=(ns[k]for k in ['clip','merge','triangulate'])
ends={0:[('upper-right',D, np.array([1,1,1])),('upper-left',D/'other-ends-v9/upper-left/strap-density-study',np.array([-1,1,1]))],2:[('lower-right',D/'other-ends-v9/lower-right/strap-density-study',np.array([1,1,-1])),('lower-left',D/'other-ends-v9/lower-left/strap-density-study',np.array([-1,1,-1]))]}
def stitcher(base):
 code=(base/'shell/stitch_ordered.py').read_text().split("q=np.load(O/'raw.npz')")[0]
 code=code.replace("D=Path('strap-density-study')",f'D=Path({str(base)!r})');env={};exec(code,env);return env['split']
def cut_triangle(t,hinge):
 if not ((t[:,2].min()<-20)if hinge==0 else(t[:,2].max()>20)):return [np.eye(3)]
 polys=[list(np.eye(3))]
 for side in [1,-1]:
  tc=t.copy();tc[:,0]*=side;result=[]
  for poly in polys:
   coords=np.array(poly)@tc
   if coords[:,0].max()<9.4 or coords[:,1].max()<-3:result.append(poly);continue
   if (coords[:,0]>=9.4).all()and(coords[:,1]>=-3).all():continue
   left=clip(poly,tc,0,9.4,-1);right=clip(poly,tc,0,9.4,1);bottom=clip(right,tc,1,-3,-1)if right else[]
   result.extend(p for p in [left,bottom]if len(p)>=3)
  polys=result
 if not polys:return []
 if len(polys)==1 and np.array_equal(polys[0],np.eye(3)):return[np.eye(3)]
 return [b for poly in merge(polys)for b in triangulate(poly)]
def patch(name,base,mi):
 mp=[0,1,2]if name.startswith('upper')else[0,2,1];ci=mp.index(mi)
 return np.load(base/'shell/uv-v11'/f'new-patch-{ci}.npz')['triangles']
rows=[]
for mesh in [0,2]:
 splitters=[(name,base,sign,stitcher(base))for name,base,sign in ends[mesh]]
 for mi in range(3):
  src=np.load(D/f'input-{mesh}-{mi}.npz');attrs=np.c_[src['positions'],src['normals'],src['uv']][src['faces']].astype(float);ret=[];pro=[];bary=[]
  for fi,t in enumerate(attrs):
   for b in cut_triangle(t[:,:3],mesh):
    b=np.array(b);ret.append(b@t);pro.append(fi);bary.append(b)
  ret=np.array(ret);pro=np.array(pro);bary=np.array(bary);ret=np.concatenate([ret,bary],axis=2)
  for name,base,sign,split in splitters:
   temp=ret.copy();temp[:,:,:3]*=sign;temp[:,:,3:6]*=sign
   if np.prod(sign)<0:temp=temp[:,[0,2,1]]
   temp,owners=split(temp);pro=pro[owners]
   # recover original barycentrics after inserted boundary knots from true source positions
   bs=[]
   temp[:,:,:3]*=sign;temp[:,:,3:6]*=sign
   if np.prod(sign)<0:temp=temp[:,[0,2,1]]
   ret=temp
  bary=ret[:,:,8:11].copy();ret=ret[:,:,:8];np.savez_compressed(O/f'outside-{mesh}-{mi}.npz',triangles=ret,sourceTriangle=pro,barycentric=bary)
  parts=[ret];labels=[np.full(len(ret),-1)]
  for ei,(name,base,sign,split)in enumerate(splitters):
   t=patch(name,base,mi).copy();t[:,:,:3]*=sign;t[:,:,3:6]*=sign
   if np.prod(sign)<0:t=t[:,[0,2,1]]
   parts.append(t);labels.append(np.full(len(t),ei))
  final=np.concatenate(parts).astype('<f4');labels=np.concatenate(labels);tt=final[:,:,:3].astype(float);good=np.linalg.norm(np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]),axis=1)>0;final=final[good];labels=labels[good]
  p=O/f'round-cap-{mesh}-{mi}.npz';np.savez_compressed(p,triangles=final,ownerEnd=labels)
  rows.append(dict(mesh=mesh,primitive=mi,sourceFaces=len(attrs),retainedFaces=len(ret),finalFaces=len(final),zeroFacesFiltered=int((~good).sum()),sha256=hashlib.sha256(p.read_bytes()).hexdigest()));print(rows[-1],flush=True)
(O/'assembly-report.json').write_text(json.dumps(rows,indent=2))
