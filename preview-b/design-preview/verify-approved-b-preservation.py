import bpy,hashlib,json,struct,os
root=os.path.dirname(os.path.abspath(__file__))
def snap(path):
 bpy.ops.wm.open_mainfile(filepath=path)
 out={}
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and ('sourceIndex' in o or o.get('assemblyId') in ['HOUR','MINUTE','SECONDS']):
   h=hashlib.sha256()
   for v in o.data.vertices:h.update(struct.pack('fff',*v.co))
   out[o.name]={'vertices':h.hexdigest(),'matrix':list(sum((list(r) for r in o.matrix_world),[])),'verts':len(o.data.vertices)}
 return out
base=snap(root+'/fixed-movement-cutaway-r01.blend');new=snap(root+'/approved-b-face-r02.blend')
changed=[n for n in base if base[n]!=new.get(n)]
r={'checked_source_and_hand_meshes':len(base),'changed':changed,'pass':not changed,'checks':'Exact local vertex SHA256 and world transform equality; no claim of full assembly interference clearance.'}
open(root+'/approved-b-preservation.json','w').write(json.dumps(r,indent=2));print('PRESERVATION',r);assert not changed
