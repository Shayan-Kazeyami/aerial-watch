import json,struct,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;p=R/'seam-study-leather-r10-runtime.glb';raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);off=20+n;length=struct.unpack_from('<I',raw,off)[0];binary=raw[off+8:off+8+length];replacements={};maxangle=0;count=0
ids={pr['attributes']['NORMAL'] for m in d['meshes'] for pr in m['primitives']}
for ai in ids:
 a=d['accessors'][ai];assert a['componentType']==5126 and a['type']=='VEC3';v=d['bufferViews'][a['bufferView']];assert a.get('byteOffset',0)==0;stride=v.get('byteStride',12);data=bytearray()
 for j in range(a['count']):
  normal=struct.unpack_from('<3f',binary,v.get('byteOffset',0)+j*stride);q=tuple(max(-32767,min(32767,round(x*32767))) for x in normal);data.extend(struct.pack('<3hxx',*q));u=[x/32767 for x in q];la=math.sqrt(sum(x*x for x in normal));lb=math.sqrt(sum(x*x for x in u));dot=sum(x*y for x,y in zip(normal,u))/(la*lb);maxangle=max(maxangle,math.degrees(math.acos(max(-1,min(1,dot)))));count+=1
 replacements[a['bufferView']]=bytes(data);v['byteStride']=8;a['componentType']=5122;a['normalized']=True;a.pop('min',None);a.pop('max',None)
rebuilt=bytearray()
for i,v in enumerate(d['bufferViews']):
 while len(rebuilt)%4:rebuilt.append(0)
 data=replacements.get(i,binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);v['byteOffset']=len(rebuilt);v['byteLength']=len(data);rebuilt.extend(data)
while len(rebuilt)%4:rebuilt.append(0)
for key in ['extensionsUsed','extensionsRequired']:
 if 'KHR_mesh_quantization' not in d.setdefault(key,[]):d[key].append('KHR_mesh_quantization')
d['buffers'][0]['byteLength']=len(rebuilt);js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);p.write_bytes(struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(rebuilt))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(rebuilt),b'BIN\0')+rebuilt)
audit={'normal_attribute_encoding':'normalized signed 16-bit XYZ, 8-byte stride; positions and UVs remain float32','normal_vectors':count,'maximum_angular_error_degrees':maxangle,'glb_bytes':p.stat().st_size,'supported_by':'repository vendor/loaders/GLTFLoader.js includes KHR_mesh_quantization'};(R/'seam-study-r10-normal-quantization-audit.json').write_text(json.dumps(audit,indent=2));print(audit)
