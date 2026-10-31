import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'seconds-attachment-r02.blend'))
def sig(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return h.hexdigest(),tuple(tuple(row)for row in o.matrix_world)
source={o.name:sig(o) for o in bpy.context.scene.objects if o.type=='MESH' and ('sourceIndex'in o or o.get('assemblyId')in ['HOUR','MINUTE','SECONDS'])}
target=bpy.data.objects['SVG broad sloped champagne wall'];mats=list(target.data.materials)
with bpy.data.libraries.load(str(R/'rim04-runtime.blend'),link=False) as (src,dst):dst.objects=['SVG broad sloped champagne wall']
imported=dst.objects[0];target.data=imported.data.copy();target.data.materials.clear()
for m in mats:target.data.materials.append(m)
for name in ['SVG champagne aperture rim','SVG lower champagne rim lip']:bpy.data.objects[name].data.bevel_resolution=2
for o in bpy.context.scene.objects:
 if o.get('premiumFacePart'):o['designRevision']='B-SVG-04'
m=bpy.data.materials.get('Graphite dial');p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.014,.016,.019,1);p.inputs['Roughness'].default_value=.48;p.inputs['Metallic'].default_value=.02
for n in m.node_tree.nodes:
 if n.type=='BUMP':n.inputs['Strength'].default_value=.08;n.inputs['Distance'].default_value=.01
assert all(sig(bpy.data.objects[k])==v for k,v in source.items())
(R/'runtime-assembly-audit.json').write_text(json.dumps({'source_meshes_unchanged':len(source),'rim_source':'rim04-runtime.blend','seconds_source':'seconds-attachment-r02.blend','revision':'B-SVG-04','status':'Geometry/material checkpoint; strap R09 remains pending replacement.'},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'visual-assembly-runtime-r01.blend'),compress=True)
