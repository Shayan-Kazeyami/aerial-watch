import bpy,bmesh,math,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'rim04-asymmetric.blend'))
def identity(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 for p in o.data.polygons:h.update(str(tuple(p.vertices)).encode())
 return [h.hexdigest(),[list(r)for r in o.matrix_world]]
source={o.name:identity(o)for o in bpy.context.scene.objects if o.type=='MESH'and('sourceIndex'in o or o.get('assemblyId')in['HOUR','MINUTE','SECONDS'])}
rim_identity=identity(bpy.data.objects['SVG broad sloped champagne wall'])
plate=bpy.data.objects['SVG unified dial and seconds support'];mat=plate.data.materials[0]
def mesh(name,vs,fs):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(mat);o['premiumFacePart']=True;return o
def union(o):
 m=plate.modifiers.new('Seconds underside union','BOOLEAN');m.operation='UNION';m.solver='EXACT';m.object=o;bpy.context.view_layer.objects.active=plate;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(o,do_unlink=True)
# A tapered closed annulus increases the visible section, leaving the full 6.2 mm face opening.
n=256;vs=[];fs=[];cx,cy=-7.998827934265137,-.016291368752717972
for r,z in [(4.085,3.48),(3.86,2.83),(3.40,2.83),(3.115,3.48)]:
 vs.extend((cx+r*math.cos(i*math.tau/n),cy+r*math.sin(i*math.tau/n),z)for i in range(n))
for k in range(4):
 for i in range(n):fs.append((k*n+i,k*n+(i+1)%n,((k+1)%4)*n+(i+1)%n,((k+1)%4)*n+i))
union(mesh('seconds-attachment-tapered-annulus',vs,fs))
# Wider bridge roots curve into the ring and existing dial, never adding gear-contacting posts.
for sy,end in [(cy+2.5,-2.92),(cy-2.5,-2.72)]:
 start=-5.36;N=32;vs=[]
 for z in [2.86,3.465]:
  for side in [-1,1]:
   for i in range(N+1):
    t=i/N;half=.26+.17*((2*t-1)**4);vs.append((start+(end-start)*t,sy+side*half,z))
 L=N+1;fs=[]
 for i in range(N):
  fs.extend([(i,i+1,L+i+1,L+i),(2*L+i,3*L+i,3*L+i+1,2*L+i+1),(i,2*L+i,2*L+i+1,i+1),(L+i,L+i+1,3*L+i+1,3*L+i)])
 fs.extend([(0,L,3*L,2*L),(N,2*L+N,3*L+N,L+N)])
 o=mesh('seconds-attachment-radiused-bridge',vs,fs)
 bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Soft machined edges','BEVEL');m.width=.065;m.segments=4;bpy.ops.object.modifier_apply(modifier=m.name);union(o)
plate['secondsAttachmentRevision']='Tapered annulus 0.74 mm total depth; twin 0.52–0.86 mm bridges, continuous dial union'
bm=bmesh.new();bm.from_mesh(plate.data);nonman=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();rem=set(bm.verts);components=0
while rem:
 components+=1;q=[rem.pop()]
 while q:
  for e in q.pop().link_edges:
   for v in e.verts:
    if v in rem:rem.remove(v);q.append(v)
bm.free()
deps=bpy.context.evaluated_depsgraph_get()
def tree(o):
 e=o.evaluated_get(deps);me=e.to_mesh();t=BVHTree.FromPolygons([o.matrix_world@v.co for v in me.vertices],[tuple(p.vertices)for p in me.polygons]);e.to_mesh_clear();return t
pt=tree(plate);hits=[]
for name in source:
 o=bpy.data.objects[name]
 if not o.hide_render:
  h=pt.overlap(tree(o))
  if h:hits.append({'object':name,'triangle_pairs':len(h)})
assert all(identity(bpy.data.objects[n])==v for n,v in source.items());assert identity(bpy.data.objects['SVG broad sloped champagne wall'])==rim_identity
result={'original_source_meshes_identical':len(source),'rim_mesh_identical':True,'dial_nonmanifold_edges':nonman,'dial_connected_components':components,'dial_volume':volume,'static_visible_source_surface_intersections':hits,'ring_face_preserved':{'center':[cx,cy],'inner_radius':3.1,'outer_radius':4.1,'top_z':3.57},'new_annulus_bottom_z':2.83,'bridge_width_min_max_mm':[.52,.86],'bridge_depth_mm':.605,'limitations':['Not manufacturing validation. No full moving-gear sweep. Triangle overlap is surface-only.','Ring remains suspended above movement by twin integrated bridges; no claim it rests on gears.']}
(R/'seconds-attachment-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
s=bpy.context.scene;s.cycles.samples=32;s.render.resolution_x=1200;s.render.resolution_y=1000;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(R/'seconds-attachment-r01.blend'),compress=True)
for name,target,loc,scale in [('front',(cx,cy,3),(cx,cy,45),12.8),('oblique',(cx+1,cy,2.6),(cx+15,cy-21,19),14.0),('side',(cx+1,cy,2.7),(cx+4,cy-29,13),14.0)]:
 s.camera.location=loc;s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.type='ORTHO';s.camera.data.ortho_scale=scale;s.render.filepath=str(R/('seconds-attachment-'+name+'.png'));bpy.ops.render.render(write_still=True)
