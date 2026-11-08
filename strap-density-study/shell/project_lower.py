import numpy as np,json,ast
from scipy.spatial import cKDTree
from collections import defaultdict
from pathlib import Path
D=Path('strap-density-study');O=D/'shell/loft-v1'
code=ast.parse((D/'shell/attributes.py').read_text());fn=next(x for x in code.body if isinstance(x,ast.FunctionDef)and x.name=='closest');exec(compile(ast.Module(body=[fn],type_ignores=[]),'<closest>','exec'))
ss=[]
for i in range(3):q=np.load(D/f'input-0-{i}.npz');t=q['positions'][q['faces']].astype(float);m=(t[:,:,0].max(1)>9.3)&(t[:,:,1].max(1)>-3.3)&(t[:,:,2].min(1)<-20);ss.append(t[m])
sp=np.concatenate(ss);verts,iv=np.unique(sp.reshape(-1,3),axis=0,return_inverse=True);vf=defaultdict(list)
for i,row in enumerate(iv.reshape(-1,3)):
 for v in row:vf[v].append(i)
vt=cKDTree(verts);ct=cKDTree(sp.mean(1));q=np.load(O/'raw.npz');T=q['triangles'];p,inv=np.unique(T.reshape(-1,3),axis=0,return_inverse=True);mask=(p[:,1]<-2.15)&(p[:,1]>-2.9999999)&(p[:,0]>9.4000001);idsall=np.flatnonzero(mask);out=p.copy();errs=[]
for start in range(0,len(idsall),80):
 ids=idsall[start:start+80];pts=p[ids];_,ci=ct.query(pts,k=24);_,vi=vt.query(pts,k=12);cand=[np.unique(np.r_[c,*[vf[v]for v in vs]])for c,vs in zip(ci,vi)];n=max(map(len,cand));sel=np.array([np.pad(c,(0,n-len(c)),mode='edge')for c in cand]);ix,bc,ds=closest(pts,sp[sel]);fi=sel[np.arange(len(pts)),ix];target=(sp[fi]*bc[:,:,None]).sum(1);w=np.clip((-pts[:,1]-2.15)/.30,0,1);w=w*w*(3-2*w);out[ids]=pts*(1-w[:,None])+target*w[:,None];errs.extend(np.sqrt(ds).tolist())
np.savez_compressed(O/'raw.npz',triangles=out[inv.reshape(-1,3)],materials=q['materials']);json.dump(dict(projected_vertices=len(idsall),source_distance_before_max=max(errs),taper_y=[-2.15,-2.45],boundary_untouched=True),open(O/'projection-report.json','w'));print('projected',len(idsall),'max',max(errs))
