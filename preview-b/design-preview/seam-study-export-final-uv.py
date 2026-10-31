import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r10-export-compatible.blend'));s=bpy.context.scene;parts=[o for o in s.objects if o.type=='MESH' and o.get('leatherPbrRevision')=='R10'];fixed=[]
for o in parts:
 if o.get('designPart')!='QUALITY-STRAP':continue
 bpy.context.view_layer.objects.active=o
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;bad=set()
 for t in me.loop_triangles:
  a,b,c=[uv[i].uv for i in t.loops]
  if abs((b-a).cross(c-a))<1e-14:bad.add(t.polygon_index)
 for pi in bad:
  p=me.polygons[pi];axis=max(range(3),key=lambda k:abs(p.normal[k]));dims=[k for k in range(3) if k!=axis]
  for li in p.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co;uv[li].uv=(co[dims[0]]/100,co[dims[1]]/100)
 fixed.append({'name':o.name,'reprojected_final_bevel_triangles':len(bad)})
for o in s.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];glb=R/'seam-study-leather-r10.glb';bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_image_format='AUTO');bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r10-export-compatible.blend'),compress=True)
p=R/'seam-study-r10-export-audit.json';report=json.loads(p.read_text());report['glb_bytes']=glb.stat().st_size;report['final_bevel_uv_repair']=fixed;p.write_text(json.dumps(report,indent=2));print(fixed,flush=True)
