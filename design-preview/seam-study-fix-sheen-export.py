import json,struct,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;results=[]
for name in ['seam-study-leather-r10.glb','seam-study-leather-r10-runtime.glb']:
 p=R/name;raw=p.read_bytes();jlen=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+jlen]);binchunk=raw[20+jlen:];fixed=[]
 for m in d['materials']:
  e=m.get('extensions',{}).get('KHR_materials_sheen')
  if e is None:continue
  n=m.get('name','');weight=.10 if n.startswith('leather /') else .04 if n.startswith('lining /') else .25 if n.startswith('thread /') else None
  assert weight is not None,n;e['sheenColorFactor']=[weight]*3;fixed.append({'material':n,'authored_weight':weight,'exported_sheenColorFactor':[weight]*3})
 js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);result=struct.pack('<4sII',b'glTF',2,12+8+len(js)+len(binchunk))+struct.pack('<I4s',len(js),b'JSON')+js+binchunk;p.write_bytes(result);results.append({'file':name,'bytes':len(result),'binary_payload_unchanged':hashlib.sha256(binchunk).hexdigest()==hashlib.sha256(result[20+len(js):]).hexdigest(),'fixed':fixed})
(R/'seam-study-r10-sheen-export-audit.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2));p=R/'seam-study-r10-runtime-audit.json';a=json.loads(p.read_text());a['glb_bytes']=(R/'seam-study-leather-r10-runtime.glb').stat().st_size;a['sheen_export_fix']='Blender exporter discarded weights; corrected KHR_materials_sheen.sheenColorFactor to leather 0.10, lining 0.04, thread 0.25. See sheen audit.';p.write_text(json.dumps(a,indent=2))
