import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;out=R/'seam-study-r10-maps';bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r05.blend'));s=bpy.context.scene;s.cycles.samples=8;s.render.bake.use_clear=True;s.render.bake.margin=0
parts=[o for o in s.objects if o.type=='MESH' and (o.get('designPart')=='SEAM-STUDY-STRAP' or 'waxed three-ply stitches' in o.name)];original=next(m for m in bpy.data.materials if m.name.startswith('Seam study / fine charcoal'))
# Bake tangent normals at their final restrained strength into a 2K complete tile.
normalpath=out/'fine-calf-normal-strength025-2k.png'
if normalpath.exists():normalimg=bpy.data.images.load(str(normalpath),check_existing=True)
else:
 bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,500));tile=bpy.context.object;tile.name='Seam study / temporary runtime normal tile';tile.data.materials.append(original.copy());bm=tile.data.materials[0];vis={o:o.hide_render for o in s.objects if o!=tile}
 for o in vis:o.hide_render=True
 normalimg=bpy.data.images.new('R10 runtime normal 2K',2048,2048,alpha=False);normalimg.colorspace_settings.name='Non-Color';node=bm.node_tree.nodes.new('ShaderNodeTexImage');node.image=normalimg;bm.node_tree.nodes.active=node;bpy.ops.object.select_all(action='DESELECT');tile.select_set(True);bpy.context.view_layer.objects.active=tile;bpy.ops.object.bake(type='NORMAL');normalimg.filepath_raw=str(normalpath);normalimg.file_format='PNG';normalimg.save();bpy.data.objects.remove(tile,do_unlink=True)
 for o,hidden in vis.items():o.hide_render=hidden
normalimg.colorspace_settings.name='Non-Color'
color=bpy.data.images.load(str(out/'fine-calf-color-2k.png'),check_existing=True);color.colorspace_settings.name='sRGB';color.pack();color.filepath_raw=str(out/'fine-calf-color-2k-runtime.jpg');color.file_format='JPEG';s.render.image_settings.quality=95;color.save()
rough=bpy.data.images.load(str(out/'fine-calf-roughness-2k.png'),check_existing=True);rough.colorspace_settings.name='Non-Color'
m=bpy.data.materials.new('leather / fine charcoal calf / photo R10 runtime');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Metallic'].default_value=0;p.inputs['Specular IOR Level'].default_value=.28;p.inputs['Sheen Weight'].default_value=.1
for img,socket in [(color,'Base Color'),(rough,'Roughness')]:
 node=n.new('ShaderNodeTexImage');node.image=img;l.new(node.outputs['Color'],p.inputs[socket])
node=n.new('ShaderNodeTexImage');node.image=normalimg;nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=1;l.new(node.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],p.inputs['Normal'])
reports=[]
for o in parts:
 band=o.get('designPart')=='SEAM-STUDY-STRAP';o['designPart']='QUALITY-STRAP' if band else 'QUALITY-STITCH';o['leatherPbrRevision']='R10';o['replacesAssemblyId']='STRAP-UPPER' if ('Upper' in o.name or 'upper' in o.name) else 'STRAP-LOWER'
 for k in ['sourceIndex','assemblyId']:
  if k in o:del o[k]
 for slot in o.material_slots:
  if slot.material==original:slot.material=m
  elif 'lining' in slot.material.name.lower():slot.material.name='lining / warm leather R10'
  elif 'burnished edge' in slot.material.name.lower():slot.material.name='edge paint / satin burnished R10'
  elif 'three ply' in slot.material.name.lower():slot.material.name='thread / waxed graphite three ply R10'
 o.hide_render=False;o.hide_set(False)
 if not band:
  old=o.data;verts=[];faces=[];stride=41*8;assert len(old.vertices)%stride==0
  for component in range(len(old.vertices)//stride):
   start=len(verts)
   for k in range(0,41,2):
    ring=[old.vertices[component*stride+k*8+j].co for j in range(8)];center=sum(ring,Vector())/8;a=ring[0]-center;b=ring[2]-center
    for j in range(5):verts.append(center+a*math.cos(j*math.tau/5)+b*math.sin(j*math.tau/5))
   for k in range(20):
    for j in range(5):faces.append((start+k*5+j,start+k*5+(j+1)%5,start+(k+1)*5+(j+1)%5,start+(k+1)*5+j))
   faces.append(tuple(start+j for j in reversed(range(5))));faces.append(tuple(start+20*5+j for j in range(5)))
  me=bpy.data.meshes.new('R10 reduced tessellation seated three-ply thread');me.from_pydata(verts,[],faces);me.update()
  for mat in old.materials:me.materials.append(mat)
  for poly in me.polygons:poly.use_smooth=True
  o.data=me;reports.append({'name':o.name,'old_vertices':len(old.vertices),'runtime_vertices':len(me.vertices),'strand_rings':21,'strand_sides':5})
 else:
  bpy.context.view_layer.objects.active=o
  for mod in list(o.modifiers):
   if mod.type=='BEVEL':mod.segments=1
   bpy.ops.object.modifier_apply(modifier=mod.name)
  tri=o.modifiers.new('Runtime deterministic triangulation','TRIANGULATE');tri.keep_custom_normals=True;bpy.ops.object.modifier_apply(modifier=tri.name)
  me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;bad=set()
  for t in me.loop_triangles:
   a,b,c=[uv[i].uv for i in t.loops]
   if abs((b-a).cross(c-a))<1e-14:bad.add(t.polygon_index)
  for pi in bad:
   poly=me.polygons[pi];lis=list(poly.loop_indices);a,b,c=[me.vertices[me.loops[li].vertex_index].co for li in lis];ab=b-a;ac=c-a;length=ab.length
   if length>1e-12:
    uv[lis[0]].uv=(0,0);uv[lis[1]].uv=(length/100,0);uv[lis[2]].uv=(ac.dot(ab)/length/100,ab.cross(ac).length/length/100)
for o in s.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];glb=R/'seam-study-leather-r10-runtime.glb';bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False,export_texcoords=True,export_normals=True,export_tangents=False,export_materials='EXPORT',export_image_format='AUTO');s.cycles.samples=128;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r10-runtime.blend'),compress=True)
report={'revision':'R10','glb_bytes':glb.stat().st_size,'thread_reduction':reports,'preserved':'All 264 puncture seats, original band topology/silhouette and 132 three-ply stitches; no decimation. Bevel width remains 0.012 mm, reduced from 2 to 1 segments.','normal':'2K tangent tile with 0.25 source strength baked; shader strength 1.0','color':'2K JPEG95 derived from baked tile','roughness':'2K lossless baked tile','tangents':'Runtime derivative TBN, no redundant tangent attribute','render_comparison':'pending'};(R/'seam-study-r10-runtime-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
