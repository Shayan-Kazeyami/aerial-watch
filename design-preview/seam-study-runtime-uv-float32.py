import bpy,struct,json
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r10-runtime.blend'));s=bpy.context.scene;parts=[o for o in s.objects if o.type=='MESH' and o.get('leatherPbrRevision')=='R10'];fix=[]
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
for o in parts:
 if o.get('designPart')!='QUALITY-STRAP':continue
 me=o.data;uv=me.uv_layers.active.data;me.calc_loop_triangles();count=0
 for t in me.loop_triangles:
  a,b,c=[(f32(uv[i].uv.x),f32(1-uv[i].uv.y)) for i in t.loops];area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
  if area<1e-16 and t.area>1e-10:
   for li,v in zip(t.loops,[(.25,.25),(.25001,.25),(.25,.25001)]):uv[li].uv=v
   count+=1
 fix.append({'name':o.name,'float32_subpixel_sliver_uvs_repaired':count})
for o in s.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.export_scene.gltf(filepath=str(R/'seam-study-leather-r10-runtime.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False,export_texcoords=True,export_normals=True,export_tangents=False,export_materials='EXPORT',export_image_format='AUTO',export_jpeg_quality=95);bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r10-runtime.blend'),compress=True);p=R/'seam-study-r10-runtime-audit.json';d=json.loads(p.read_text());d['float32_uv_repair']=fix;p.write_text(json.dumps(d,indent=2));print(fix,flush=True)
