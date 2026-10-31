import bpy
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seconds-attachment-r02.blend'));s=bpy.context.scene;s.cycles.samples=48;s.render.resolution_x=1400;s.render.resolution_y=1400;s.render.resolution_percentage=100;s.render.filepath=str(R/'seconds-attachment-overall-front.png');bpy.ops.render.render(write_still=True)
