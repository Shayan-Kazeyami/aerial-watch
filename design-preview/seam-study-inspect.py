import bpy,bmesh
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'rim-leather-r05.blend'))
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.get('designPart')=='QUALITY-STRAP':
  bm=bmesh.new();bm.from_mesh(o.data);print('BASE',o.name,len(bm.verts),len(bm.faces),sum(not e.is_manifold for e in bm.edges),bm.calc_volume(),[(s.material.name) for s in o.material_slots],flush=True)
