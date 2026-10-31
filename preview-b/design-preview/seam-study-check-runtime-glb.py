import json,struct,math
from pathlib import Path
R=Path(__file__).resolve().parent;p=R/'seam-study-leather-r10-runtime.glb';raw=p.read_bytes();length,typ=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+length]);pos=20+length;blen,btyp=struct.unpack_from('<II',raw,pos);binary=raw[pos+8:pos+8+blen]
assert raw[:4]==b'glTF';assert len(raw)==struct.unpack_from('<I',raw,8)[0]
meshes=doc.get('meshes',[]);nodes=[n for n in doc.get('nodes',[]) if 'mesh' in n];prims=[p for m in meshes for p in m['primitives']]
for n in nodes:
 e=n.get('extras',{});assert e.get('designPart') in ['QUALITY-STRAP','QUALITY-STITCH'];assert e.get('leatherPbrRevision')=='R10';assert 'sourceIndex' not in e
assert {n['extras']['replacesAssemblyId'] for n in nodes if n['extras']['designPart']=='QUALITY-STRAP'}=={'STRAP-UPPER','STRAP-LOWER'}
for p in prims:
 assert all(k in p['attributes'] for k in ['POSITION','NORMAL'])
 if 'normalTexture' in doc['materials'][p['material']]:assert all(k in p['attributes'] for k in ['TEXCOORD_0'])
def accessor(i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];fmt={5126:'f',5125:'I',5123:'H',5121:'B',5122:'h'}[a['componentType']];size=struct.calcsize(fmt)*dims;stride=v.get('byteStride',size);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 values=[struct.unpack_from('<'+fmt*dims,binary,offset+j*stride) for j in range(a['count'])]
 if a.get('normalized') and a['componentType']==5122:return [tuple(max(-1,x/32767) for x in row) for row in values]
 return values
checks=[]
for p in prims:
 norms=accessor(p['attributes']['NORMAL']);uvs=accessor(p['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in p['attributes'] else [];assert all(all(math.isfinite(x) for x in uv) for uv in uvs)
 err=max(abs(math.sqrt(sum(x*x for x in n))-1) for n in norms);assert err<1e-4
 zero=0;nondegeneratezero=0
 if uvs:
  ids=[x[0] for x in accessor(p['indices'])];positions=accessor(p['attributes']['POSITION'])
  for i in range(0,len(ids),3):
   a,b,c=[uvs[j] for j in ids[i:i+3]];area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
   if area<1e-16:
    zero+=1;x,y,z=[positions[j] for j in ids[i:i+3]];u=[y[k]-x[k] for k in range(3)];v=[z[k]-x[k] for k in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
    if sum(c*c for c in cross)>4e-20:nondegeneratezero+=1
 checks.append({'collapsed_uv_nondegenerate_triangles':nondegeneratezero,'collapsed_uv_triangles':zero,'vertices':len(norms),'triangles':doc['accessors'][p['indices']]['count']//3,'normal_max_unit_length_error':err})
report={'bytes':len(raw),'mesh_nodes':len(nodes),'runtime_primitives':len(prims),'triangle_count':sum(c['triangles'] for c in checks),'vertex_count':sum(c['vertices'] for c in checks),'node_names':[n['name'] for n in nodes],'materials':[m.get('name') for m in doc['materials']],'images':len(doc.get('images',[])),'extensions_used':doc.get('extensionsUsed',[]),'sourceIndex_absent':True,'attributes':['POSITION','NORMAL','TEXCOORD_0 on textured band primitives; derivative TBN'],'checks':checks,'normal_texture':[m.get('normalTexture') for m in doc['materials'] if 'normalTexture' in m]};(R/'seam-study-r10-runtime-glb-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
