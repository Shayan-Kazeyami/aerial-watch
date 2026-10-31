import json,struct,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;p=R/'seam-study-leather-r10-runtime.glb';raw=p.read_bytes();jlen=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+jlen]);start=20+jlen;blen=struct.unpack_from('<I',raw,start)[0];binary=raw[start+8:start+8+blen];target=next(i for i in d['images'] if 'roughness' in i.get('name',''));vid=target['bufferView'];jpeg=(R/'seam-study-r10-maps/fine-calf-roughness-2k-runtime.jpg').read_bytes();assert jpeg[:2]==b'\xff\xd8';rebuilt=bytearray();hashes=[]
for i,v in enumerate(d['bufferViews']):
 while len(rebuilt)%4:rebuilt.append(0)
 old=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];data=jpeg if i==vid else old
 if i!=vid:hashes.append(hashlib.sha256(old).hexdigest()==hashlib.sha256(data).hexdigest())
 v['byteOffset']=len(rebuilt);v['byteLength']=len(data);rebuilt.extend(data)
while len(rebuilt)%4:rebuilt.append(0)
target['mimeType']='image/jpeg';target['name']='fine-calf-roughness-2k-runtime-jpeg95';d['buffers'][0]['byteLength']=len(rebuilt);js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);total=12+8+len(js)+8+len(rebuilt);result=struct.pack('<4sII',b'glTF',2,total)+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(rebuilt),b'BIN\0')+rebuilt;p.write_bytes(result);assert all(hashes)
a=R/'seam-study-r10-runtime-audit.json';report=json.loads(a.read_text());report.update({'glb_bytes':len(result),'roughness':'2K JPEG95, Blender Raw encoding, JPEG embedded directly without re-expanding to PNG; see compression audit','nonroughness_bufferViews_hash_identical':all(hashes)});a.write_text(json.dumps(report,indent=2));print('RUNTIME_BYTES',len(result))
