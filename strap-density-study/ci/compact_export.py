import numpy as np
import os
import json,hashlib,copy
from pathlib import Path
D=Path(os.environ['STRAP_STUDY_DIR'])/'round-cap-candidate';j=json.load(open(D/'leather.gltf'));old=(D/'geometry.bin').read_bytes();refs=set()
for m in j['meshes']:
 for p in m['primitives']:
  refs.update(p['attributes'].values());refs.add(p['indices'])
  for t in p.get('targets',[]):refs.update(t.values())
assert not j.get('skins') and not j.get('animations')
accs=[];views=[];buf=bytearray();amap={};vmap={}
indexrefs={p['indices']for m in j['meshes']for p in m['primitives']}
for ai in sorted(refs):
 a=copy.deepcopy(j['accessors'][ai]);vi=a['bufferView']
 if ai in indexrefs and a['componentType']==5125:
  bv=j['bufferViews'][vi];off=bv.get('byteOffset',0)+a.get('byteOffset',0);vals=np.frombuffer(old,dtype='<u4',count=a['count'],offset=off)
  if vals.max()<65536:
   while len(buf)%4:buf.append(0)
   data=vals.astype('<u2').tobytes();newvi=len(views);views.append(dict(buffer=0,byteOffset=len(buf),byteLength=len(data)));buf.extend(data);a['bufferView']=newvi;a['componentType']=5123;a.pop('byteOffset',None);amap[ai]=len(accs);accs.append(a);continue
 if vi not in vmap:
  v=copy.deepcopy(j['bufferViews'][vi]);offset=v.get('byteOffset',0);data=old[offset:offset+v['byteLength']]
  while len(buf)%4:buf.append(0)
  v['byteOffset']=len(buf);buf.extend(data);vmap[vi]=len(views);views.append(v)
 a['bufferView']=vmap[vi];amap[ai]=len(accs);accs.append(a)
for m in j['meshes']:
 for p in m['primitives']:
  p['indices']=amap[p['indices']];p['attributes']={k:amap[v]for k,v in p['attributes'].items()}
  for t in p.get('targets',[]):
   for k,v in t.items():t[k]=amap[v]
j['accessors']=accs;j['bufferViews']=views;j['buffers']=[dict(uri='geometry.bin',byteLength=len(buf))];(D/'geometry.bin').write_bytes(buf);json.dump(j,open(D/'leather.gltf','w'),separators=(',',':'));j['images']=json.load(open(D.parent.parent/'metal-recovery/source/leather-assets/r14/leather.gltf'))['images'] if False else json.load(open(Path(os.environ['STRAP_SOURCE_ASSET_DIR'])/'leather.gltf'))['images'];json.dump(j,open(D/'leather-dropin.gltf','w'),separators=(',',':'));report=dict(bytes=len(buf),sha256=hashlib.sha256(buf).hexdigest(),unused_storage_removed=len(old)-len(buf));json.dump(report,open(D.parent/'compact-export.json','w'),indent=2);print(report)
