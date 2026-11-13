import json,struct,gzip,hashlib
from pathlib import Path
p=Path('qa-backplate-sharing');base=Path('preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6');manifest=json.load(open(base/'deployment-manifest.json'));report=[]
for route,name in [('raw','rebuild/assembly.glb'),('meshopt','optimized-assets/rebuild__assembly.meshopt.glb.gz')]:
 f=base/name;original=f.read_bytes();entry=next(x for x in manifest['localFiles'] if x['path']==name);assert hashlib.sha256(original).hexdigest()==entry['sha256'];b=gzip.decompress(original) if name.endswith('.gz') else original;n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);binary=b[28+n:];node=next(x for x in j['nodes'] if x.get('extras',{}).get('assemblyId')=='REAR-CRYSTAL');mesh=j['meshes'][node['mesh']];node=dict(node);node['mesh']=0;node.pop('children',None)
 for q in mesh['primitives']:q.pop('material',None)
 j['nodes']=[node];j['meshes']=[mesh];j['scenes']=[{'nodes':[0]}];j['scene']=0
 for k in ['materials','images','textures','samplers','animations','skins','cameras']:j.pop(k,None)
 jb=json.dumps(j,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);out=struct.pack('<III',0x46546c67,2,28+len(jb)+len(binary))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(binary),0x004e4942)+binary;(p/(route+'-rear-only.glb')).write_bytes(out);report.append({'route':route,'canonical_input':str(f),'canonical_sha256':entry['sha256'],'all_binary_buffer_bytes_preserved':True,'harness_asset_sha256':hashlib.sha256(out).hexdigest(),'scope':'Exact real rear-crystal geometry source;scene reachability/material metadata reduced for isolated PBR/picking harness;not wholeviewer'})
(p/'freshness-and-render-inputs.json').write_text(json.dumps({'main_commit':'b84a51ec91b715aa70408e8bff6e988e29d93edb','canonical_release':'e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6','module_sha256':hashlib.sha256((base/'assembly-backplate.js').read_bytes()).hexdigest(),'routes':report},indent=2));print(report)

module=(base/'assembly-backplate.js').read_text();assert hashlib.sha256(module.encode()).hexdigest()=='2d074b1e93189ccb54a2c5400f407c3ec29e949a714a0dab17f168c3789cf38a'
module=module.replace("'./vendor/three.module.js'","'../preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6/vendor/three.module.js'")
(p/'original.mjs').write_text(module)
(p/'candidate.mjs').write_text(module.replace('rearCrystal.geometry.clone()','rearCrystal.geometry').replace('geometry.dispose();material.dispose();','material.dispose();'))
