import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'seam-study-r10-maps';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r05.blend'))
s=bpy.context.scene;s.cycles.samples=16;s.render.bake.use_clear=True;s.render.bake.margin=0
parts=[o for o in s.objects if o.type=='MESH' and (o.get('designPart')=='SEAM-STUDY-STRAP' or 'waxed three-ply stitches' in o.name)]
assert len(parts)==4
names=[o.name for o in parts];original=next(m for m in bpy.data.materials if m.name.startswith('Seam study / fine charcoal'))
# Bake a complete material tile, NOT overlapping physical-scale band UVs.
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,500));tile=bpy.context.object;tile.name='Seam study / temporary material bake tile';tile.data.materials.append(original.copy());bakeMat=tile.data.materials[0]
visibility={o:o.hide_render for o in s.objects if o!=tile}
for o in visibility:o.hide_render=True
images={}
for kind,typ in [('color','DIFFUSE'),('roughness','ROUGHNESS')]:
 existing=out/('fine-calf-'+kind+'-2k.png')
 if existing.exists():
  images[kind]=bpy.data.images.load(str(existing),check_existing=True);images[kind].colorspace_settings.name='sRGB' if kind=='color' else 'Non-Color';continue
 img=bpy.data.images.new('R10 fine calf '+kind,2048,2048,alpha=False);img.colorspace_settings.name='sRGB' if kind=='color' else 'Non-Color'
 node=bakeMat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;bakeMat.node_tree.nodes.active=node
 bpy.ops.object.select_all(action='DESELECT');tile.select_set(True);bpy.context.view_layer.objects.active=tile
 s.render.bake.use_pass_direct=False;s.render.bake.use_pass_indirect=False;s.render.bake.use_pass_color=True;bpy.ops.object.bake(type=typ)
 img.filepath_raw=str(out/('fine-calf-'+kind+'-2k.png'));img.file_format='PNG';img.save();images[kind]=img;bakeMat.node_tree.nodes.remove(node)
bpy.data.objects.remove(tile,do_unlink=True)
for o,hidden in visibility.items():o.hide_render=hidden
mat=bpy.data.materials.new('leather / fine charcoal calf / photo R10');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF');p.inputs['Metallic'].default_value=0;p.inputs['Specular IOR Level'].default_value=.28;p.inputs['Sheen Weight'].default_value=.10
for kind,img in images.items():
 node=n.new('ShaderNodeTexImage');node.image=img;l.new(node.outputs['Color'],p.inputs['Base Color' if kind=='color' else 'Roughness'])
node=n.new('ShaderNodeTexImage');node.image=bpy.data.images.get('leather_white_nor_gl_4k.png');assert node.image
normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.25;l.new(node.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],p.inputs['Normal'])
for o in parts:
 isband=o.get('designPart')=='SEAM-STUDY-STRAP';o['designPart']='QUALITY-STRAP' if isband else 'QUALITY-STITCH';o['leatherPbrRevision']='R10';o['replacesAssemblyId']='STRAP-UPPER' if ('Upper' in o.name or 'upper' in o.name) else 'STRAP-LOWER'
 for key in ['sourceIndex','assemblyId']:
  if key in o:del o[key]
 for slot in o.material_slots:
  if slot.material==original:slot.material=mat
  elif 'lining' in slot.material.name.lower():slot.material.name='lining / warm leather R10'
  elif 'burnished edge' in slot.material.name.lower():slot.material.name='edge paint / satin burnished R10'
  elif 'three ply' in slot.material.name.lower():slot.material.name='thread / waxed graphite three ply R10'
 o.hide_render=False;o.hide_set(False)
for o in parts:
 if o.get('designPart')=='QUALITY-STRAP':
  tri=o.modifiers.new('Export-safe triangulation after edge bevel','TRIANGULATE');tri.keep_custom_normals=True
for o in s.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0]
glb=R/'seam-study-leather-r10.glb';bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_image_format='AUTO')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r10-export-compatible.blend'),compress=True)
report={'revision':'R10','objects':names,'authored_mesh_objects':len(parts),'glb_bytes':glb.stat().st_size,'maps':{'color':'2048 full material tile, shader baked sRGB','roughness':'2048 full material tile, shader baked non-color','normal':'original unchanged 4096 OpenGL scan, strength 0.25'},'physical_uv_scale_mm':100,'normal_source':'Poly Haven Leather White CC0','append_from_native_r05':names};(R/'seam-study-r10-export-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
# Render intentionally deferred until parent resumes heavy work.
s.cycles.samples=128;s.render.filepath=str(R/'seam-study-r10-export-compatible-macro.png')
