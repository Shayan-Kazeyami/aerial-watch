import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'rim04-asymmetric.blend'));s=bpy.context.scene;s.cycles.samples=32;s.render.resolution_x=1200;s.render.resolution_y=1000;s.render.resolution_percentage=100
cx,cy=-7.998827934265137,-.016291368752717972
s.camera.location=(cx+15,cy-21,19);s.camera.rotation_euler=(Vector((cx+1,cy,2.6))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.type='ORTHO';s.camera.data.ortho_scale=14;s.render.filepath=str(R/'seconds-attachment-baseline-oblique.png');bpy.ops.render.render(write_still=True)
