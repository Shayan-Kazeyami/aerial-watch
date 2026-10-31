import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r04.blend'))
s=bpy.context.scene;s.camera.location=(18,47,7);s.camera.rotation_euler=(Vector((7.6,29,-9))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=10;s.render.resolution_x=800;s.render.resolution_y=800;s.cycles.samples=96;s.render.filepath=str(R/'seam-study-r04-seam-detail.png');bpy.ops.render.render(write_still=True)
