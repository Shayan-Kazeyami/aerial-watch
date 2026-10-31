"""Build original-gear cutaway input for the approved B renderer, from tracked source GLB.
Run with Blender before render-approved-b-face.py. Does not modify original assets.
"""
from pathlib import Path
path=Path(__file__).resolve().parent/'render-premium-study.py'
code=path.read_text()
start=code.index('# Preserve source movement;');end=code.index('# Neutral studio composition:')
code=code[:start]+"\nfor o in source:\n if o.get('sourceIndex',-1) in [0,155,149]:o.hide_render=True\n"+code[end:]
code=code.replace('premium-face-study-r02','fixed-movement-cutaway-r01').replace('bpy.ops.render.render(write_still=True)','')
exec(compile(code,str(path),'exec'),{'__file__':str(path)})
