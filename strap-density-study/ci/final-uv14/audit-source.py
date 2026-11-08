import os
from pathlib import Path
import json,numpy as np,hashlib
R=Path(os.environ['STRAP_SOURCE_ASSET_DIR']);D=Path(os.environ['STRAP_STUDY_DIR']); j=json.load(open(R/'leather.gltf'));b=(R/'geometry.bin').read_bytes()
def arr(i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];return np.frombuffer(b,dtype=dt,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
report={'source_geometry_sha256':hashlib.sha256(b).hexdigest(),'primitives':[]}
for mi in [0,2]:
 for pi,pr in enumerate(j['meshes'][mi]['primitives']):
  p=arr(pr['attributes']['POSITION']);n=arr(pr['attributes']['NORMAL']);uv=arr(pr['attributes']['TEXCOORD_0']);f=arr(pr['indices']).reshape(-1,3);t=p[f].astype(float);area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)/2
  r=dict(mesh=mi,primitive=pi,material=pr['material'],vertices=len(p),triangles=len(f),area_percentiles_mm2=dict(zip(['min','p25','p50','p90','max'],np.percentile(area,[0,25,50,90,100]).tolist())),area_below_1e_6=int((area<1e-6).sum()),area_below_1e_4=int((area<1e-4).sum()))
  report['primitives'].append(r);np.savez(D/f'input-{mi}-{pi}.npz',positions=p,normals=n,uv=uv,faces=f);print(r)
json.dump(report,open(D/'audit.json','w'),indent=2)
