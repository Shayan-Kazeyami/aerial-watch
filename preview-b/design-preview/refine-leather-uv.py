import bpy,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'rim-leather-r03.blend'))
def vertex_hash(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return h.hexdigest()
def uv_report(o):
 o.data.calc_loop_triangles();uv=o.data.uv_layers.active.data if o.data.uv_layers.active else None
 collapsed=0
 for tri in o.data.loop_triangles:
  if not uv:collapsed+=1;continue
  a,b,c=[uv[i].uv for i in tri.loops];x=b-a;y=c-a
  if abs(x.x*y.y-x.y*y.x)<1e-14:collapsed+=1
 return {'triangles':len(o.data.loop_triangles),'collapsed_uv_triangles':collapsed}
m=bpy.data.materials.new('R08 photo-grain charcoal calf');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Metallic'].default_value=0
if p.inputs.get('Specular IOR Level'):p.inputs['Specular IOR Level'].default_value=.27
if p.inputs.get('Sheen Weight'):p.inputs['Sheen Weight'].default_value=.08
def texture(name,noncolor=False):
 node=n.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(ROOT/'material-reference'/name),check_existing=True)
 if noncolor:node.image.colorspace_settings.name='Non-Color'
 return node
albedo=texture('brown_leather_albedo_1k.jpg');gray=n.new('ShaderNodeRGBToBW');l.new(albedo.outputs['Color'],gray.inputs[0]);value=n.new('ShaderNodeMapRange');value.clamp=True;value.inputs['From Min'].default_value=.015;value.inputs['From Max'].default_value=.12;value.inputs['To Min'].default_value=.006;value.inputs['To Max'].default_value=.011;l.new(gray.outputs[0],value.inputs['Value']);tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(.85,.92,1,1);l.new(value.outputs[0],tint.inputs[1]);l.new(tint.outputs[0],p.inputs['Base Color'])
rough=texture('brown_leather_rough_1k.png',True);rr=n.new('ShaderNodeMapRange');rr.inputs['To Min'].default_value=.48;rr.inputs['To Max'].default_value=.68;l.new(rough.outputs['Color'],rr.inputs['Value']);l.new(rr.outputs[0],p.inputs['Roughness'])
normal=texture('brown_leather_nor_gl_1k.png',True);nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.30;l.new(normal.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],p.inputs['Normal'])
reports=[]
for o in list(bpy.context.scene.objects):
 if o.type!='MESH' or o.get('designPart')!='QUALITY-STRAP':continue
 before=uv_report(o);geometry=vertex_hash(o)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 for uv in list(o.data.uv_layers):o.data.uv_layers.remove(uv)
 o.data.uv_layers.new(name='UVMap')
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.015,correct_aspect=True,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
 for slot in o.material_slots:
  if slot.material.name.startswith('R07 scanned charcoal'):slot.material=m
 assert vertex_hash(o)==geometry
 reports.append({'name':o.name,'before':before,'after':uv_report(o),'vertices_unchanged':True})
(ROOT/'leather-uv-audit.json').write_text(json.dumps(reports,indent=2)+'\n');print('LEATHER_UV_AUDIT',json.dumps(reports),flush=True)
scene=bpy.context.scene;scene.cycles.samples=96;scene.render.resolution_x=1100;scene.render.resolution_y=1100;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'rim-leather-r04.blend'),compress=True)
scene.camera.location=(24,48,36);target=Vector((0,27,-2));scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=31;scene.render.filepath=str(ROOT/'rim-leather-r04-macro.png');bpy.ops.render.render(write_still=True)
