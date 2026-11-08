import numpy as np,json,struct,hashlib
from pathlib import Path
z=np.load('metal-recovery/cap-study/hybrid-smooth-v3.npz');p=z['position'][:,[0,2,1]]*np.array([1,1,-1]);n=z['normal'][:,[0,2,1]]*np.array([1,1,-1]);uv=z['uv'];idx=z['index'];arrays=[p.astype('<f4'),n.astype('<f4'),uv.astype('<f4'),idx.astype('<u4')];views=[];acc=[];parts=[];off=0
for i,a in enumerate(arrays):
 b=a.tobytes();views.append({'buffer':0,'byteOffset':off,'byteLength':len(b),'target':34963 if i==3 else 34962});count=a.size if i==3 else len(a);row={'bufferView':i,'componentType':5125 if i==3 else 5126,'count':count,'type':'SCALAR' if i==3 else 'VEC2' if i==2 else 'VEC3'}
 if i==0:row.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 acc.append(row);parts.append(b);off+=len(b)
j={'asset':{'version':'2.0','generator':'private hybrid root/source terminal candidate'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':'CASE_HYBRID_PRIVATE','extras':{'assemblyId':'CASE','revision':'hybrid-source-cap015-v3'}}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3,'mode':4}]}],'bufferViews':views,'accessors':acc,'buffers':[{'byteLength':off}]};s=json.dumps(j,separators=(',',':')).encode();s+=b' '*((-len(s))%4);out=struct.pack('<III',0x46546c67,2,28+len(s)+off)+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',off,0x004e4942)+b''.join(parts);Path('metal-recovery/cap-study/hybrid-smooth-v3.glb').write_bytes(out);print(len(out),hashlib.sha256(out).hexdigest())
