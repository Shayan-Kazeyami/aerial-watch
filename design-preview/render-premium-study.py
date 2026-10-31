"""Reversible Blender study using real repository geometry, not a product image mockup.
Does not overwrite source GLBs. Candidate visual design only; no manufacturing claims.
Run: blender -b --python design-preview/render-premium-study.py
"""
import bpy, math, os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT,'rebuild/assembly.glb'))
source=list(bpy.context.scene.objects)
def material(name,color,metal=0,rough=.4):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
steel=material('Satin steel',(.48,.53,.58),.92,.29)
polished=material('Polished edge',(.72,.77,.81),1,.16)
gold=material('Muted champagne',(.56,.39,.19),.85,.29)
graphite=material('Graphite dial',(.009,.019,.023),.18,.32)
blue=material('Blued hands',(.015,.09,.20),.85,.2)
leather=material('Charcoal leather',(.014,.018,.017),0,.65)
ruby=material('Ruby bearing',(.22,.012,.035),.4,.24)
for o in source:
 if o.type!='MESH':continue
 aid=o.get('assemblyId','');idx=o.get('sourceIndex',-1)
 if aid in ['DIAL','CHAPTER'] or 'CRYSTAL' in aid:
  o.hide_render=True;continue
 if 'STRAP' in aid or 'KEEPER' in aid:mat=leather
 elif aid in ['HOUR','MINUTE','SECONDS']:mat=blue
 elif 'BEZEL' in aid:mat=polished
 elif idx>=0:
  desc=(o.get('description','')+' '+o.name).lower()
  mat=ruby if any(x in desc for x in ['rubis','jewel']) else gold if any(x in desc for x in ['roue','wheel','barillet']) else steel
 else:mat=steel
 o.data.materials.clear();o.data.materials.append(mat)
# Preserve source movement; replace selected front presentation plates only in this study.
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT,'quality-study/front-architecture-r07.glb'))
for o in list(bpy.context.scene.objects):
 if 'replacementForSourceIndex' in o:
  idx=o['replacementForSourceIndex']
  for old in source:
   if old.get('sourceIndex',-999)==idx:old.hide_render=True
  o.data.materials.clear();o.data.materials.append(steel if idx!=149 else graphite)
def cylinder(name,radius,depth,loc,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=radius,depth=depth,location=loc);o=bpy.context.object;o.name=name
 if mat:o.data.materials.append(mat)
 return o
def cut(o,r,xy):
 cutter=cylinder('Temporary cutter',r,3,(*xy,3.4),None)
 mod=o.modifiers.new('True aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
def bevel(o,width=.04):
 b=o.modifiers.new('Fine machined bevel','BEVEL');b.width=width;b.segments=3
 o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
plate=cylinder('Authored premium dial candidate',16.40,.22,(0,0,3.36),graphite)
windows=[(-3.5138,8.0626,3.6),(-7.9988,-.0163,4.16)]
for x,y,r in windows:cut(plate,r,(x,y))
cut(plate,1.08,(0,0));bevel(plate,.035)
# Narrow aperture edges separate the dark face from the underlying movement.
for i,(x,y,r) in enumerate(windows):
 ring=cylinder('Aperture bevel '+str(i),r+.10,.055,(x,y,3.50),gold);cut(ring,r,(x,y));bevel(ring,.014)
# Deliberately simple, readable applied hour furniture.
for hour in range(12):
 a=hour*math.pi/6
 bpy.ops.mesh.primitive_cube_add(size=1,location=(14.65*math.sin(a),14.65*math.cos(a),3.56))
 o=bpy.context.object;o.name='Applied hour marker '+str(hour or 12);o.dimensions=(.26,1.05,.12);o.rotation_euler.z=-a
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(gold);bevel(o,.04)
for minute in range(60):
 if minute%5==0:continue
 a=minute*math.pi/30;bpy.ops.mesh.primitive_cube_add(size=1,location=(15.65*math.sin(a),15.65*math.cos(a),3.49));o=bpy.context.object;o.name='Minute track';o.dimensions=(.045,.22,.018);o.rotation_euler.z=-a;o.data.materials.append(steel)
def text(body,loc,size,mat):
 c=bpy.data.curves.new(body,'FONT');c.body=body;c.align_x='CENTER';c.size=size;c.space_character=1.22;c.extrude=.002;o=bpy.data.objects.new(body,c);bpy.context.collection.objects.link(o);o.location=loc;o.data.materials.append(mat)
text('A E R I A L',(4.1,7.5,3.49),.95,gold)
text('KAZEYAMI STUDIO',(4.1,6.25,3.49),.34,steel)
text('OM10  /  MANUAL',(3.8,-8.7,3.49),.37,steel)
# Neutral studio composition: native model units are millimetres.
world=bpy.data.worlds.new('Studio world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.18,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;bpy.context.scene.world=world
floor=material('Backdrop',(.025,.035,.037),.12,.5)
bpy.ops.mesh.primitive_plane_add(size=600,location=(0,0,-10));bpy.context.object.data.materials.append(floor)
def light(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
light('Large key',(-35,15,65),65000,32);light('Soft fill',(40,-10,35),25000,30);light('Rim strip',(0,55,25),45000,25)
bpy.ops.object.camera_add(location=(0,-8,105));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,2))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=53
scene=bpy.context.scene;scene.camera=camera;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=False;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.render.filepath=os.path.join(ROOT,'design-preview','premium-face-study-r02.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'design-preview','premium-face-study-r02.blend'))
bpy.ops.render.render(write_still=True)
