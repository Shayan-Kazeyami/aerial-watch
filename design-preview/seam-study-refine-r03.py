import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r02.blend'))
report=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.get('designPart')!='SEAM-STUDY-STRAP':continue
 me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;bad=set()
 for t in me.loop_triangles:
  a,b,c=[uv[i].uv for i in t.loops]
  if abs((b-a).cross(c-a))<1e-16:bad.add(t.polygon_index)
 for pi in bad:
  p=me.polygons[pi];axis=max(range(3),key=lambda k:abs(p.normal[k]));dims=[k for k in range(3) if k!=axis]
  for li in p.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co;uv[li].uv=(co[dims[0]]/300,co[dims[1]]/300)
 zero=0
 for t in me.loop_triangles:
  a,b,c=[uv[i].uv for i in t.loops]
  if abs((b-a).cross(c-a))<1e-16 and t.area>1e-10:zero+=1
 report.append({'name':o.name,'reprojected_cut_polygons':len(bad),'collapsed_nondegenerate_triangles':zero})
(R/'seam-study-r03-uv-audit.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r03.blend'),compress=True);s=bpy.context.scene;s.render.filepath=str(R/'seam-study-r03-macro.png');bpy.ops.render.render(write_still=True)
