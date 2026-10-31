import bpy,json,struct,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'seam-study-r10-maps';bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r10-runtime.blend'));s=bpy.context.scene;parts=[o for o in s.objects if o.type=='MESH' and o.get('leatherPbrRevision')=='R10'];bands=[o for o in parts if o.get('designPart')=='QUALITY-STRAP'];names=[o.name for o in bands]
with bpy.data.libraries.load(str(R/'seam-study-r10-export-compatible.blend'),link=False) as (a,b):b.objects=names
for o,hi in zip(bands,b.objects):
 mats=list(o.data.materials);o.data=hi.data.copy();indices=[poly.material_index for poly in o.data.polygons];o.data.materials.clear()
 for m in mats:o.data.materials.append(m)
 for poly,index in zip(o.data.polygons,indices):poly.material_index=index
 bpy.data.objects.remove(hi,do_unlink=True)
 me=o.data;uv=me.uv_layers.active.data;me.calc_loop_triangles()
 def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
 for t in me.loop_triangles:
  a,b,c=[(f32(uv[i].uv.x),f32(1-uv[i].uv.y)) for i in t.loops];area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
  if area<1e-16 and t.area>1e-10:
   for li,v in zip(t.loops,[(.25,.25),(.25001,.25),(.25,.25001)]):uv[li].uv=v
# Re-encode the baked normal with maximum PNG compression, preserving every 8-bit value.
m=next(m for m in bpy.data.materials if m.name.startswith('leather / fine charcoal calf / photo R10 runtime'));node=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and 'normal' in n.image.name);img=node.image
oldview=(s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma);s.view_settings.view_transform='Raw';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=100
path=out/'fine-calf-normal-strength025-2k-lossless.png';img.save_render(str(path),scene=s);packed=bpy.data.images.load(str(path),check_existing=True);packed.colorspace_settings.name='Non-Color';a=np.array(img.pixels[:],dtype=np.float32);b=np.array(packed.pixels[:],dtype=np.float32);assert np.max(np.abs(a-b))<1e-7;node.image=packed;s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma=oldview
for o in s.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.export_scene.gltf(filepath=str(R/'seam-study-leather-r10-runtime.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False,export_texcoords=True,export_normals=True,export_tangents=False,export_materials='EXPORT',export_image_format='AUTO',export_jpeg_quality=95);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r10-runtime.blend'),compress=True)
p=R/'seam-study-r10-runtime-audit.json';d=json.loads(p.read_text());d['bevel_restored']='Exact high-detail two-segment band geometry restored from compatible master; only thread tessellation reduced.';d['normal_png_lossless_reencode']={'bytes':path.stat().st_size,'max_decoded_pixel_difference':float(np.max(np.abs(a-b)))};p.write_text(json.dumps(d,indent=2));print(d['normal_png_lossless_reencode'],flush=True)
