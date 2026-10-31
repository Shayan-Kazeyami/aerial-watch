import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r10-runtime.blend'));s=bpy.context.scene;parts=[o for o in s.objects if o.type=='MESH' and o.get('leatherPbrRevision')=='R10'];m=next(m for m in bpy.data.materials if m.name.startswith('leather / fine charcoal calf / photo R10 runtime'))
for n in m.node_tree.nodes:
 if n.type=='TEX_IMAGE' and 'roughness' in n.image.name:n.image.file_format='JPEG'
s.render.image_settings.quality=95
for o in s.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];glb=R/'seam-study-leather-r10-runtime.glb';bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False,export_texcoords=True,export_normals=True,export_tangents=False,export_materials='EXPORT',export_image_format='AUTO',export_jpeg_quality=95);bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r10-runtime.blend'),compress=True)
p=R/'seam-study-r10-runtime-audit.json';report=json.loads(p.read_text());report['glb_bytes']=glb.stat().st_size;report['roughness']='2K JPEG95 baked tile; lossless normal remains PNG';report['color']='2K JPEG95 baked tile';p.write_text(json.dumps(report,indent=2));print('RUNTIME_BYTES',glb.stat().st_size,flush=True)
