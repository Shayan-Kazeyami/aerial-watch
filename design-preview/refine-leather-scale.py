import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'rim-leather-r04.blend'))
m=bpy.data.materials['R08 photo-grain charcoal calf'];m.name='R09 fine photo-grain charcoal calf'
n=m.node_tree.nodes;l=m.node_tree.links
uv=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=4;l.new(uv.outputs['UV'],scale.inputs[0])
for x in n:
 if x.type=='TEX_IMAGE':l.new(scale.outputs[0],x.inputs['Vector'])
 if x.type=='NORMAL_MAP':x.inputs['Strength'].default_value=.5
for x in bpy.data.materials['Graphite dial'].node_tree.nodes:
 if x.type=='BUMP':x.inputs['Strength'].default_value=.23;x.inputs['Distance'].default_value=.018
s=bpy.context.scene;s.cycles.samples=128;bpy.ops.wm.save_as_mainfile(filepath=str(R/'rim-leather-r05.blend'),compress=True)
s.camera.location=(24,48,36);target=Vector((0,27,-2));s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=31;s.render.filepath=str(R/'rim-leather-r05-macro.png');bpy.ops.render.render(write_still=True)
