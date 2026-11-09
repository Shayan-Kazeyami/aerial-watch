import json,struct,numpy as np
from pathlib import Path
p=Path('watch-bevel/current/source/case-assets/hybrid-field-v7.glb');b=p.read_bytes();l=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+l]);buf=b[28+l:];pr=j['meshes'][0]['primitives'][0]
def a(i):
 x=j['accessors'][i];v=j['bufferViews'][x['bufferView']];return np.frombuffer(buf,dtype={5126:'f4',5123:'u2',5125:'u4'}[x['componentType']],count=x['count']*{'VEC3':3,'VEC2':2,'SCALAR':1}[x['type']],offset=v.get('byteOffset',0)+x.get('byteOffset',0)).reshape(x['count'],-1)
P=a(pr['attributes']['POSITION']);N=a(pr['attributes']['NORMAL']);UV=a(pr['attributes']['TEXCOORD_0']);F=a(pr['indices']).reshape(-1,3)
np.savez('watch-bevel/baseline.npz',position=P,normal=N,uv=UV,index=F)
print('bounds',P.min(0),P.max(0), 'shape',P.shape,F.shape)
for s in [-1,1]:
 ids=np.flatnonzero(P[:,2]*s>23.7)
 print(s,len(ids),'cap z',np.unique(np.round(P[ids,2],5)), 'xy bounds',P[ids].min(0),P[ids].max(0));print('normals',N[ids][:10])
print(j['nodes'])
