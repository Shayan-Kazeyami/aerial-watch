import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r10-export-compatible.blend'));s=bpy.context.scene;parts=[o for o in s.objects if o.type=='MESH' and o.get('leatherPbrRevision')=='R10']
for o in parts:
 if o.get('designPart')=='QUALITY-STRAP':
  tri=o.modifiers.new('Export-safe triangulation after edge bevel','TRIANGULATE');tri.keep_custom_normals=True
for o in s.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];glb=R/'seam-study-leather-r10.glb';bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_image_format='AUTO');bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r10-export-compatible.blend'),compress=True)
p=R/'seam-study-r10-export-audit.json';report=json.loads(p.read_text());report['glb_bytes']=glb.stat().st_size;report['triangulated_after_bevel_for_tangents']=True;p.write_text(json.dumps(report,indent=2))
