import pathlib,json,numpy as np
R=pathlib.Path('marked-mesh-qa');out={}
for d in (R/'parts').iterdir():
 p=np.fromfile(d/'position.bin','f4').reshape(-1,3);old=np.fromfile(d/'index.bin','u4').reshape(-1,3);new=np.fromfile(d/'opt-0.008.bin','u4').reshape(-1,3)
 protected=(np.abs(p[:,2])<=19) if d.name=='case' else (p[:,1]<=-5)
 protected|=np.hypot(p[:,1]+.95,np.abs(p[:,2])-22.4)<1
 exact=old[protected[old].all(1)];lookup={tuple(x) for x in new};assert all(tuple(x)in lookup for x in exact),d.name
 def deg(f):
  q=p[f].astype('f8');area=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1);return {tuple(x)for x in f[area<=1e-12]}
 assert not (deg(new)-deg(old)),d.name
 out[d.name]={'exactProtectedTriangles':len(exact),'before':len(old),'after':len(new),'newDegenerateFaces':0}
(R/'protected-proof.json').write_text(json.dumps(out,indent=2));print(out)
