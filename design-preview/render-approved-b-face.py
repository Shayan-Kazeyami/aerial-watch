"""B study: source movement transforms unchanged; front styling only.
Static hand-height check, not full moving assembly validation.
"""
import bpy, math, os, json
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'design-preview/fixed-movement-cutaway-r01.blend'))
source={o.name:tuple(tuple(r) for r in o.matrix_world) for o in bpy.context.scene.objects if 'sourceIndex' in o or o.get('assemblyId')=='SECONDS'}
for o in list(bpy.context.scene.objects):
 if o.name.startswith(('Authored premium dial','Aperture bevel')):bpy.data.objects.remove(o,do_unlink=True)
graphite=bpy.data.materials.get('Graphite dial') or bpy.data.materials.new('Graphite dial');graphite.use_nodes=True;gold=bpy.data.materials['Muted champagne'];steel=bpy.data.materials['Satin steel']
def cylinder(name,r,depth,loc,mat=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=160,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name
 if mat:o.data.materials.append(mat)
 return o
def cut(o,r,xy):
 c=cylinder('cut',r,4,(*xy,3.4));m=o.modifiers.new('aperture','BOOLEAN');m.operation='DIFFERENCE';m.object=c
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
plate=cylinder('B continuous left aperture dial',16.4,.22,(0,0,3.36),graphite)
# Continuous opening, retaining original gear positions; no movement edits.
control=[(-3.7,15.4),(-8.8,12.5),(-13.1,7.6),(-15.4,1.0),(-14.1,-6.7),(-10.3,-11.9),(-5.2,-14.2),(-2.5,-10.5),(-2.4,-6.0),(-3.8,-1.1),(-2.5,3.0),(-.2,6.7),(-.7,11.0)]
points=[]
for i in range(len(control)):
 p0,p1,p2,p3=[Vector(control[j%len(control)]) for j in (i-1,i,i+1,i+2)]
 for step in range(16):
  t=step/16;v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);points.append(v)
n=len(points);verts=[(p.x,p.y,z) for z in (1.5,5.5) for p in points]
faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh=bpy.data.meshes.new('Smooth crescent cut');mesh.from_pydata(verts,[],faces);mesh.update()
c=bpy.data.objects.new('Smooth crescent cutter',mesh);bpy.context.collection.objects.link(c)
m=plate.modifiers.new('Continuous machined opening','BOOLEAN');m.operation='DIFFERENCE';m.object=c
bpy.context.view_layer.objects.active=plate;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
# Fine warm-metal perimeter follows the same exact cut path.
curve=bpy.data.curves.new('Crescent perimeter','CURVE');curve.dimensions='3D';curve.bevel_depth=.075;curve.bevel_resolution=3
sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
for knot,p in zip(sp.points,points):knot.co=(p.x,p.y,3.49,1)
sp.use_cyclic_u=True;trim=bpy.data.objects.new('Champagne aperture rim',curve);bpy.context.collection.objects.link(trim);trim.data.materials.append(gold)
cut(plate,1.08,(0,0))
b=plate.modifiers.new('dial edge bevel','BEVEL');b.width=.045;b.segments=3
cx,cy=-7.998827934265137,-.016291368752717972
ring=cylinder('Seconds chapter ring',3.7,.14,(cx,cy,3.50),graphite);cut(ring,3.10,(cx,cy))
for i in range(60):
 a=i*math.pi/30;radius=3.43
 bpy.ops.mesh.primitive_cube_add(size=1,location=(cx+radius*math.sin(a),cy+radius*math.cos(a),3.60))
 o=bpy.context.object;o.name='Seconds tick %02d'%i;o.dimensions=(.06 if i%5==0 else .035,.34 if i%5==0 else .16,.04);o.rotation_euler.z=-a;o.data.materials.append(gold if i%5==0 else steel)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
hand=next(o for o in bpy.context.scene.objects if o.get('assemblyId')=='SECONDS')
pts=[hand.matrix_world@v.co for v in hand.data.vertices];low=min(v.z for v in pts)
check={'seconds_pivot_xy_mm':[cx,cy],'hand_min_z_mm':low,'chapter_max_z_mm':3.62,'vertical_gap_mm':low-3.62,'hand_max_radius_mm':max(math.hypot(v.x-cx,v.y-cy) for v in pts),'source_transforms_unchanged':all(tuple(tuple(r) for r in bpy.data.objects[n].matrix_world)==m for n,m in source.items()),'scope':'Static full-hand minimum height over ring; not complete rotating assembly/structural validation.'}
assert check['source_transforms_unchanged'];assert check['vertical_gap_mm']>0
open(os.path.join(ROOT,'design-preview/approved-b-face-check.json'),'w').write(json.dumps(check,indent=2))

# Material refinement only: no movement vertices/transforms modified.
p=graphite.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.004,.004,.005,1);p.inputs['Roughness'].default_value=.47;p.inputs['Metallic'].default_value=.12
nodes=graphite.node_tree.nodes;links=graphite.node_tree.links
tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=8;tex.inputs['Detail'].default_value=2
geo=nodes.new('ShaderNodeNewGeometry');links.new(geo.outputs['Position'],tex.inputs['Vector'])
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.23;bump.inputs['Distance'].default_value=.025;links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
p=gold.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.61,.43,.24,1);p.inputs['Roughness'].default_value=.24
p=steel.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.42,.46,.50,1);p.inputs['Roughness'].default_value=.25
# Tiny bevel shader captures existing machined edges without moving mesh vertices.
bevelnode=steel.node_tree.nodes.new('ShaderNodeBevel');bevelnode.inputs['Radius'].default_value=.025;bevelnode.samples=3;steel.node_tree.links.new(bevelnode.outputs['Normal'],p.inputs['Normal'])
sapphire=bpy.data.materials.new('Sapphire bearing jewels');sapphire.use_nodes=True;p=sapphire.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.008,.025,.38,1);p.inputs['Roughness'].default_value=.12;p.inputs['Metallic'].default_value=.05;p.inputs['Transmission Weight'].default_value=.35;p.inputs['IOR'].default_value=1.76
jewels=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and 'sourceIndex' in o and 'pierre' in (o.name+' '+o.get('description','')).lower():
  jewels.append(o.name) # Keep prior neutral bearing materials; user rejected blue accents.
# Keep actual hand geometry, polish its original material.
blue=bpy.data.materials['Blued hands'];p=blue.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.008,.065,.15,1);p.inputs['Roughness'].default_value=.19
for hour in [0,1,2,3,4,5,6]:
 angle=hour*math.pi/6
 bpy.ops.mesh.primitive_cube_add(size=1,location=(14.65*math.sin(angle),14.65*math.cos(angle),3.56));o=bpy.context.object;o.name='B applied hour %02d'%hour;o.dimensions=(.32,1.20,.12);o.rotation_euler.z=-angle
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(gold);m=o.modifiers.new('Polished chamfer','BEVEL');m.width=.035;m.segments=3
# Seconds ring fine metal edging; its top stays below the recorded tick-height bound.
for radius in [3.10,3.70]:
 bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=.035,major_segments=160,minor_segments=8,location=(cx,cy,3.56));bpy.context.object.name='Seconds warm metal edge';bpy.context.object.data.materials.append(gold)
def label(body,x,y,size,mat):
 c=bpy.data.curves.new(body,'FONT');c.body=body;c.align_x='CENTER';c.size=size;c.space_character=1.3;c.extrude=.001
 o=bpy.data.objects.new(body,c);bpy.context.collection.objects.link(o);o.location=(x,y,3.49);o.data.materials.append(mat)
label('A E R I A L',7,-.15,1.05,gold);label('KAZEYAMI STUDIO',7,-1.5,.54,steel)
# Pair of discreet radial tabs ties chapter ring to dial; below the hand sweep.
for angle in [math.pi/2,3*math.pi/2]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(cx+3.88*math.sin(angle),cy+3.88*math.cos(angle),3.42));o=bpy.context.object;o.name='Chapter attachment study';o.dimensions=(.62,.24,.12);o.data.materials.append(graphite)
# Less flat lighting with enough fill to read the movement.
bpy.context.scene.world.node_tree.nodes['Background'].inputs[1].default_value=.22
for name,power in [('Large key',65000),('Soft fill',11000),('Rim strip',42000)]:bpy.data.objects[name].data.energy=power
check['bearing_material_parts']=jewels
check['presentation_hidden_plates']=[0,149,155]
check['caution']='Cutaway presentation: three existing front plates hidden. Not a structural or manufacturing design.'
open(os.path.join(ROOT,'design-preview/approved-b-face-check.json'),'w').write(json.dumps(check,indent=2))
scene=bpy.context.scene;scene.cycles.samples=256;scene.camera.location=(0,0,105);scene.camera.rotation_euler=(Vector((0,0,2))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.camera.data.ortho_scale=54
scene.render.filepath=os.path.join(ROOT,'design-preview/approved-b-face-r02.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'design-preview/approved-b-face-r02.blend'),compress=True)
bpy.ops.render.render(write_still=True)
print('CHECK',json.dumps(check))
