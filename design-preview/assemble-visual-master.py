import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'visual-assembly-runtime-r01.blend'))
def sig(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return h.hexdigest(),tuple(tuple(row)for row in o.matrix_world)
source={o.name:sig(o) for o in bpy.context.scene.objects if o.type=='MESH' and ('sourceIndex'in o or o.get('assemblyId')in ['HOUR','MINUTE','SECONDS'])}
for o in bpy.context.scene.objects:
 if o.get('designPart')in ['QUALITY-STRAP','QUALITY-STITCH']:o.hide_render=True
names=['Seam study / R05 / Upper strap · solid padded band and rolled ','Seam study / R05 / Lower strap · solid padded band and rolled ','Seam study / upper waxed three-ply stitches','Seam study / lower waxed three-ply stitches']
with bpy.data.libraries.load(str(R/'seam-study-r05.blend'),link=False) as (src,dst):
 assert all(n in src.objects for n in names);dst.objects=names
for o in dst.objects:bpy.context.scene.collection.objects.link(o);o.hide_render=False
assert all(sig(bpy.data.objects[k])==v for k,v in source.items())
report={'source_meshes_unchanged':len(source),'face':'constant-section SVG04 plus supported seconds ring','strap':'R05 new fine-grain native high-detail geometry','public_status':'Not published; runtime candidate separately verified','appended_objects':[o.name for o in dst.objects]}
(R/'visual-master-audit.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'visual-master-r01.blend'),compress=True)
for o in bpy.context.scene.objects:
 if o.type=='LIGHT':print('LIGHT',o.name,o.data.type,o.data.energy,list(o.location),getattr(o.data,'size',None))
 if o.get('assemblyId')in ['FRONT-CRYSTAL','REAR-CRYSTAL']:print('CRYSTAL',o.name,o.hide_render,list(o.dimensions))
