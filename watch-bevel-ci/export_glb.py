import numpy as np,json,struct,hashlib
from pathlib import Path
D=np.load('watch-bevel/candidate.npz');chunks=[];views=[];acc=[];offset=0
for name,dtype,ct,typ in [('position','f4',5126,'VEC3'),('normal','f4',5126,'VEC3'),('uv','f4',5126,'VEC2'),('index','u4',5125,'SCALAR')]:
 a=D[name].astype(dtype);b=a.tobytes();views.append({'buffer':0,'byteOffset':offset,'byteLength':len(b)});ac={'bufferView':len(views)-1,'componentType':ct,'count':a.size if typ=='SCALAR' else len(a),'type':typ}
 if name=='position':ac.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 acc.append(ac);chunks.append(b);offset+=len(b)
j={'asset':{'version':'2.0','generator':'Aerial Watch targeted bevel and density revision'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':'CASE','extras':{'assemblyId':'CASE','revision':'hybrid-cap030-density-r01'}}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3}]}],'accessors':acc,'bufferViews':views,'buffers':[{'byteLength':offset}]};s=json.dumps(j,separators=(',',':')).encode();s+=b' '*((-len(s))%4);b=struct.pack('<III',0x46546c67,2,28+len(s)+offset)+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',offset,0x004e4942)+b''.join(chunks);Path('watch-bevel/candidate.glb').write_bytes(b);print(hashlib.sha256(b).hexdigest(),len(b))
