import os
import numpy as np,json,copy,hashlib
from pathlib import Path
D=Path(os.environ['STRAP_STUDY_DIR']);S=Path(os.environ['STRAP_SOURCE_ASSET_DIR']);O=D/'round-cap-candidate';O.mkdir(exist_ok=True);j=json.load(open(S/'leather.gltf'));b=bytearray((S/'geometry.bin').read_bytes());report=[]
def put(a,typ,ctype):
 global b
 while len(b)%4:b.append(0)
 raw=a.tobytes();v=len(j['bufferViews']);j['bufferViews'].append(dict(buffer=0,byteOffset=len(b),byteLength=len(raw)));b.extend(raw);acc=dict(bufferView=v,componentType=ctype,count=len(a),type=typ)
 if typ=='VEC3':acc.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 i=len(j['accessors']);j['accessors'].append(acc);return i
for pi in range(3):
 t=np.load(D/f'round-cap-0-{pi}.npz')['triangles'];flat=t.reshape(-1,8);a,inv=np.unique(flat,axis=0,return_inverse=True);p=j['meshes'][0]['primitives'][pi];p['attributes']['POSITION']=put(np.ascontiguousarray(a[:,:3]),'VEC3',5126);p['attributes']['NORMAL']=put(np.ascontiguousarray(a[:,3:6]),'VEC3',5126);p['attributes']['TEXCOORD_0']=put(np.ascontiguousarray(a[:,6:]),'VEC2',5126);p['indices']=put(inv.astype('<u4'),'SCALAR',5125)
 area=np.linalg.norm(np.cross(t[:,1,:3].astype(float)-t[:,0,:3],t[:,2,:3].astype(float)-t[:,0,:3]),axis=1)/2;report.append(dict(primitive=pi,triangles=len(t),float32_zero_area=int((area==0).sum()),min_area=float(area.min())))
j['buffers'][0].update(uri='geometry.bin',byteLength=len(b))
for im in j.get('images',[]):
 if 'uri'in im and not im['uri'].startswith('data:'):im['uri']='../../metal-recovery/source/leather-assets/r14/'+im['uri']
(O/'geometry.bin').write_bytes(b);json.dump(j,open(O/'leather.gltf','w'),separators=(',',':'));json.dump(dict(geometry_sha256=hashlib.sha256(b).hexdigest(),primitives=report,not_release_ready=True),open(D/'round-cap-export.json','w'),indent=2);print(report)
