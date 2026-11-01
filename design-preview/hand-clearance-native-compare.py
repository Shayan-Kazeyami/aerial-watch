import bpy,json,struct
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'visual-master-r02.blend'))
b=(R.parent/'rebuild/assembly.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);binary=28+n;results={}
for node in g['nodes']:
 key=node.get('extras',{}).get('assemblyId')
 if key not in ['SECONDS','SECONDS-STAFF']:continue
 points=[]
 for prim in g['meshes'][node['mesh']]['primitives']:
  a=g['accessors'][prim['attributes']['POSITION']];v=g['bufferViews'][a['bufferView']];assert a['componentType']==5126
  for i in range(a['count']):
   x,y,z=struct.unpack_from('<3f',b,binary+v.get('byteOffset',0)+a.get('byteOffset',0)+i*v.get('byteStride',12))
   if key=='SECONDS':y-=.32
   elif y>2.94:y=2.94+(y-2.94)*(3.68-2.94)/(4-2.94)
   # Emulate runtime Float32BufferAttribute assignment, then glTF Y-up -> native Z-up.
   y=struct.unpack('<f',struct.pack('<f',y))[0];points.append((x,-z,y))
 o=next(o for o in bpy.context.scene.objects if o.get('displayAssemblyId')==key)
 native={tuple(round(v,6) for v in p.co) for p in o.data.vertices};runtime={tuple(round(v,6) for v in p) for p in points};assert native==runtime,key
 results[key]={'actual_runtime_glb_corrected_unique_positions':len(runtime),'native_corrected_unique_positions':len(native),'position_sets_identical_at_1e6_mm':True}
audit=json.loads((R/'hand-clearance-native-audit.json').read_text());audit['actual_runtime_glb_comparison']=results;(R/'hand-clearance-native-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(results))
