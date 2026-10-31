import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r04.blend'))
s=bpy.context.scene;s.camera.location=(0,0,105);s.camera.rotation_euler=(Vector((0,0,2))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=72;s.render.resolution_x=1200;s.render.resolution_y=1200;s.cycles.samples=128;s.render.filepath=str(R/'seam-study-r04-front.png');bpy.ops.render.render(write_still=True)
