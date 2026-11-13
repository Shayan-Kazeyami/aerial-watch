import pathlib,json,numpy as np,hashlib
R=pathlib.Path('marked-mesh-qa');B=R/'preview-b/releases'/(R/'release-id.txt').read_text();O=R/'changes';O.mkdir(exist_ok=True);j=json.loads((B/'leather-assets/r14/leather.gltf').read_text());raw=(B/'leather-assets/r14/geometry.bin').read_bytes();parts=[];offset=0;report=[]
def read(ai):
 a=j['accessors'][ai];v=j['bufferViews'][a['bufferView']];dims={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];return np.frombuffer(raw,dt,count=a['count']*dims,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,dims).copy()
# Resolve first because buffer views will be repacked.
data={i:read(i)for i in range(len(j['accessors']))};newdata=dict(data)
for mi in [0,2]:
 for pi,pr in enumerate(j['meshes'][mi]['primitives']):
  d=R/'parts'/f'leather-{mi}-{pi}';f=np.fromfile(d/'opt-0.008.bin','u4');used=np.unique(f);remap=np.zeros(len(data[pr['attributes']['POSITION']]),'u4');remap[used]=np.arange(len(used));newdata[pr['indices']]=remap[f].reshape(-1,1).astype(data[pr['indices']].dtype)
  for ai in pr['attributes'].values():newdata[ai]=data[ai][used]
  report.append({'mesh':mi,'primitive':pi,'before':len(data[pr['indices']])//3,'after':len(f)//3})
j['bufferViews']=[]
for ai,a in enumerate(j['accessors']):
 arr=newdata[ai];bb=arr.tobytes();a['bufferView']=len(j['bufferViews']);a.pop('byteOffset',None);a['count']=len(arr)
 if 'min'in a:a['min']=arr.min(0).tolist();a['max']=arr.max(0).tolist()
 j['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(bb)});parts.append(bb);offset+=len(bb);pad=(-offset)%4;parts.append(bytes(pad));offset+=pad
out=b''.join(parts);j['buffers']=[{'uri':'geometry.bin','byteLength':len(out)}];(O/'leather-assets/r14').mkdir(parents=True,exist_ok=True);(O/'leather-assets/r14/geometry.bin').write_bytes(out);(O/'leather-assets/r14/leather.gltf').write_text(json.dumps(j,separators=(',',':')))
s=(B/'assembly-leather-authoring-identity.js').read_text();ident=json.loads(s[s.index('Object.freeze(')+14:s.rfind(')')]);ident['id']='strap-lug-density-r16';ident['status']='Localized rolled-end simplification preserving UV, normal seams and original sewing';ident['lineage']+='; R16 localized rolled-end density pass';ident['expectedGeometry']['bytes']=len(out);ident['expectedGeometry']['sha256']=hashlib.sha256(out).hexdigest();ident['generator']='marked-mesh-qa/pack.py'
for m in ident.get('meshes',[]):
 for pi,p in enumerate(m['primitives']):
  pr=j['meshes'][m['index']]['primitives'][pi];a=j['accessors'][pr['attributes']['POSITION']];p['positionCount']=a['count'];p['indexCount']=j['accessors'][pr['indices']]['count'];p['bounds']={'min':a['min'],'max':a['max']}
ident['features']['densityR16']={'scope':'rolled ends with source y greater than -5 mm; unchanged sewing and other strap surfaces','tolerance':'0.008 mm attribute-aware simplifier error; independent sampled surface checks','topology':'no new flipped-normal triangles, welded boundary edges or non-manifold edges'}
(O/'assembly-leather-authoring-identity.js').write_text('export const AUTHORED_LEATHER_IDENTITY=Object.freeze('+json.dumps(ident,indent=2)+');\n')
# Case compaction preserves attribute values exactly.
d=R/'parts/case';p=np.fromfile(d/'position.bin','f4').reshape(-1,3);n=np.fromfile(d/'normal.bin','f4').reshape(-1,3);u=np.fromfile(d/'uv.bin','f4').reshape(-1,2);f=np.fromfile(d/'opt-0.008.bin','u4');used=np.unique(f);remap=np.zeros(len(p),'u4');remap[used]=np.arange(len(used));
for key,arr in [('position',p[used]),('normal',n[used]),('uv',u[used]),('index',remap[f])]:arr.tofile(R/'case'/('candidate-'+key+'.bin'))
(R/'pack-report.json').write_text(json.dumps({'leather':report,'case':{'before':350230,'after':len(f)//3},'leatherBytesBefore':len(raw),'leatherBytesAfter':len(out)},indent=2));print((R/'pack-report.json').read_text())
