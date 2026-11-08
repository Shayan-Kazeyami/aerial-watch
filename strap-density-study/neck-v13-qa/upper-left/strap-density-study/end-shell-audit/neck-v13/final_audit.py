import numpy as np,json,hashlib
from pathlib import Path
R=Path('strap-density-study/end-shell-audit/neck-v13');S=[];C=[];rows=[]
for i in range(3):
 z=np.load(f'strap-density-study/input-0-{i}.npz');src=np.c_[z['positions'],z['normals'],z['uv']][z['faces']].astype('f4');path=Path(f'strap-density-study/shell/uv-v10/round-cap-0-{i}.npz');t=np.load(path)['triangles'].astype('f4');S.append(src[:,:,:3]);C.append(t[:,:,:3]);src[src==0]=0;t[t==0]=0;keys={v.tobytes() for v in t};m=(src[:,:,1]<=-3.5).all(1);area=np.linalg.norm(np.cross(t[:,1,:3].astype(float)-t[:,0,:3],t[:,2,:3].astype(float)-t[:,0,:3]),axis=1)/2;rows.append({'primitive':i,'sourceFaces':len(src),'candidateFaces':len(t),'zeroAreaFaces':int((area==0).sum()),'sourceBelowCutFaces':int(m.sum()),'missingExactBelowCutAttributes':sum(v.tobytes() not in keys for v in src[m]),'fileSHA256':hashlib.sha256(path.read_bytes()).hexdigest()})
S=np.concatenate(S).astype(float);C=np.concatenate(C).astype(float)
def edges(t,d):
 p,rev=np.unique(np.round(t.reshape(-1,3),d),axis=0,return_inverse=True);f=rev.reshape(-1,3);e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);e=e[e[:,0]!=e[:,1]];u,ids,c=np.unique(np.sort(e,axis=1),axis=0,return_inverse=True,return_counts=True);b={tuple(p[v].ravel()) for v in u[c==1]};sign=np.where(e[:,0]<e[:,1],1,-1);w=np.bincount(ids,weights=sign);return b,int((c>2).sum()),int(((c==2)&(w!=0)).sum())
topo=[]
for d in [8,7,6,5]:
 sb,sn,sw=edges(S,d);cb,cn,cw=edges(C,d);topo.append({'digits':d,'sourceBoundary':len(sb),'candidateBoundary':len(cb),'boundarySetsEqual':sb==cb,'newBoundary':len(cb-sb),'missingBoundary':len(sb-cb),'sourceNonmanifold':sn,'candidateNonmanifold':cn,'sourceWindingMismatch':sw,'candidateWindingMismatch':cw})
out={'primitiveReports':rows,'topology':topo};(R/'final-report.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
