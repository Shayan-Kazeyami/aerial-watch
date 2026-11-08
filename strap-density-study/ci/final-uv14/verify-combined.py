"""Exact exported-Float32 closure gate; original defects may be removed, never added."""
import sys,json,numpy as np
from pathlib import Path
D=Path('strap-density-study');O=Path(sys.argv[1]);report=[]
def audit(t):
 p,f=np.unique(t.reshape(-1,3),axis=0,return_inverse=True);f=f.reshape(-1,3);e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);u,inv,c=np.unique(np.sort(e,axis=1),axis=0,return_inverse=True,return_counts=True);w=np.bincount(inv,weights=np.where(e[:,0]<e[:,1],1,-1));_,fc=np.unique(np.sort(f,axis=1),axis=0,return_counts=True);area=np.linalg.norm(np.cross(t[:,1].astype(float)-t[:,0],t[:,2].astype(float)-t[:,0]),axis=1);return {tuple(p[x].ravel())for x in u[c==1]},{tuple(p[x].ravel())for x in u[c>2]},dict(faces=len(t),winding=int(((c==2)&(w!=0)).sum()),zero=int((area==0).sum()),duplicates=int((fc>1).sum()),nonfinite=int((~np.isfinite(t)).sum()))
for mesh in [0,2]:
 src=[];dst=[]
 for m in range(3):
  z=np.load(D/f'input-{mesh}-{m}.npz');src.append(z['positions'][z['faces']]);dst.append(np.load(O/f'round-cap-{mesh}-{m}.npz')['triangles'][:,:,:3])
 sb,sn,sr=audit(np.concatenate(src).astype('<f4'));db,dn,dr=audit(np.concatenate(dst).astype('<f4'));row=dict(mesh=mesh,source=sr,candidate=dr,sourceBoundary=len(sb),candidateBoundary=len(db),sourceNonmanifold=len(sn),candidateNonmanifold=len(dn),exactBoundaryMatch=sb==db,noNewNonmanifold=dn<=sn);report.append(row);assert sb==db,row;assert dn<=sn,row;assert all(dr[k]==0 for k in ['winding','zero','duplicates','nonfinite']),row
(O/'strict-combined-gate.json').write_text(json.dumps(report,indent=2));print(report)
