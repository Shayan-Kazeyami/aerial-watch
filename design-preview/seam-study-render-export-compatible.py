import bpy
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r10-export-compatible.blend'));s=bpy.context.scene;s.cycles.samples=128;s.render.resolution_x=1100;s.render.resolution_y=1100;s.render.filepath=str(R/'seam-study-r10-export-compatible-macro.png');bpy.ops.render.render(write_still=True)
