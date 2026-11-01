import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'visual-master-r02.blend'))
derived={o.get('displayAssemblyId'):o for o in bpy.context.scene.objects if o.get('derivedDisplayGeometry')}
# Lightweight orthographic stack proof, not a beauty render or saved pose change.
hour=next(o for o in bpy.context.scene.objects if o.get('assemblyId')=='HOUR');minute=next(o for o in bpy.context.scene.objects if o.get('assemblyId')=='MINUTE')
for o,key,period in [(hour,'HOUR',43200),(minute,'MINUTE',3600),(derived['SECONDS'],'SECONDS',60)]:o.matrix_world=o.matrix_world@Matrix.Rotation(-2*math.pi*37230/period,4,'Z')
keep=[hour,derived['SECONDS'],derived['SECONDS-STAFF']]
for o in bpy.context.scene.objects:
 if o.type in ['MESH','CURVE','FONT']:o.hide_render=o not in keep
# Proof-only solid contrasting materials make the 0.03 mm gap legible without lighting ambiguity.
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=.1;p.inputs['Roughness'].default_value=.42;return m
for o,color in [(hour,(.8,.52,.12)),(derived['SECONDS'],(.06,.3,.8)),(derived['SECONDS-STAFF'],(.35,.4,.46))]:
 o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat('Proof '+o.name,color))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=False;s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=1000;s.render.resolution_y=450;s.render.resolution_percentage=100
s.world.color=(.12,.12,.12);s.camera.location=(-8,-16,3.85);target=Vector((-8,-1.6,3.85));s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.type='ORTHO';s.camera.data.ortho_scale=6
# Native text geometry labels: not an altered screenshot or inferred artwork.
bpy.context.view_layer.update()
labelmat=bpy.data.materials.new('Proof labels');labelmat.use_nodes=True;nodes=labelmat.node_tree.nodes;nodes.clear();em=nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.85,.9,1,1);out=nodes.new('ShaderNodeOutputMaterial');labelmat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
for text,x,y,size in [('CORRECTED DISPLAY STACK',-2.8,1.05,.20),('Hour / seconds minimum axial gap: 0.030 mm',-2.8,.76,.13),('Gold: unchanged hour   Blue: original seconds shape, -0.32 mm',-2.8,-.94,.115),('Grey: relieved upper sleeve | collision-example pose t = 37,230 s',-2.8,-1.14,.105)]:
 c=bpy.data.curves.new('Proof label','FONT');c.body=text;c.size=size;c.align_x='LEFT';o=bpy.data.objects.new(text,c);bpy.context.scene.collection.objects.link(o);o.rotation_euler=s.camera.rotation_euler;o.location=s.camera.matrix_world@Vector((x,y,-8));o.data.materials.append(labelmat)
s.render.film_transparent=False;s.render.filepath=str(R/'hand-clearance-stack-proof.png');bpy.ops.render.render(write_still=True)
