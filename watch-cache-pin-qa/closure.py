from pathlib import Path
import json,struct,gzip
r=Path('preview-b/releases/87a8607a738ba192c68f266db3f241e148f48f34216e7976c73cc062adb1f3e2');paths=['premium-face/face-svg04.glb','optimized-assets/premium-face__face-svg04.meshopt.glb','rebuild/assembly.glb','optimized-assets/rebuild__assembly.meshopt.glb.gz']
for name in paths:
 b=(r/name).read_bytes();b=gzip.decompress(b)if name.endswith('.gz')else b;magic,version,size=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and size==len(b);n,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a;j=json.loads(b[20:20+n]);uris=[x['uri']for section in ['buffers','images']for x in j.get(section,[])if x.get('uri')and not x['uri'].startswith('data:')];assert not uris,(name,uris);print(name,'self-contained GLB, no external resource URIs')
